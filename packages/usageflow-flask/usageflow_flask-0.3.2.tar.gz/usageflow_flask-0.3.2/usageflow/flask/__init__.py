from flask import Flask, Request, request
from usageflow.core import UsageFlowClient
import time
from typing import List, Optional, Tuple

class UsageFlowMiddleware:
    """
    Middleware to track API usage with UsageFlow.

    This middleware integrates with Flask to track API requests and responses,
    providing detailed usage analytics and insights.
    :param app: The Flask application instance
    :param api_key: The UsageFlow API key
    :param pool_size: Number of WebSocket connections in the pool (default: 10)
    :param whitelist_routes: List of routes to whitelist (skip tracking)
    :param tracklist_routes: List of routes to track only
    """
    def __init__(self, app: Flask, api_key: str, pool_size: int = 10):
                #  whitelist_routes: List[str] = None, tracklist_routes: List[str] = None
        self.app = app
        self.client = UsageFlowClient(api_key, pool_size)
        self.client.connect()  # Establish WebSocket connections
        # self.whitelist_routes = whitelist_routes or []
        # self.tracklist_routes = tracklist_routes or []
        self._init_middleware()

    def _init_middleware(self):
        """Initialize the middleware by registering before/after request handlers"""
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)

    def _before_request(self):
        """Handle request before it reaches the view"""
        request.usageflow_start_time = time.time()
        
        route_path = request.path

        print(f"route_path: {route_path}, request.method: {request.method}")

        # Skip tracking for whitelisted routes
        if  self.client.is_endpoint_whitelisted(route_path, request.method):
            return

        # Track only specific routes if tracklist is set
        if not self.client.is_endpoint_monitored(route_path, request.method):
            return

        # Prepare request metadata
        metadata = {
            "method": request.method,
            "url": self._extract_request_url(request),
            "rawUrl": request.path,
            "clientIP": request.remote_addr,
            "userAgent": request.headers.get("user-agent"),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "headers": {k: ("****" if "key" in k.lower() else v) for k, v in request.headers.items()},
            "queryParams": dict(request.args or {}),
            "pathParams": dict(request.view_args or {}),
            "body": request.get_json(silent=True),
        }

        # Store metadata for later use
        request.usageflow_metadata = metadata

        # Get ledger ID and allocate request
        ledger_id, has_rate_limit = self._guess_ledger_id()

        # Check of url is blocked
        if self.client.is_endpoint_blocked(ledger_id):
            return {"error": "Endpoint blocked"}, 403

        success, result = self.client.allocate_request(ledger_id, metadata, has_rate_limit)
        
        if not success:
            error_message = result.get('error', 'Request fulfillment failed') if result else 'Request fulfillment failed'
            status_code = result.get('status_code', 400) if result else 400
            
            if status_code == 429:
                return {"error": "Rate limit exceeded"}, 429
            elif status_code == 403:
                return {"error": "Access forbidden"}, 403
            elif status_code == 401:
                return {"error": "Unauthorized access"}, 401
            else:
                return {"error": error_message}, status_code

        # Store event ID and ledger ID for later use
        # The new format returns allocationId in the payload
        if result and isinstance(result, dict):
            if 'allocationId' in result:
                request.usageflow_event_id = result['allocationId']
            elif 'eventId' in result:
                request.usageflow_event_id = result['eventId']
            else:
                request.usageflow_event_id = None
        else:
            request.usageflow_event_id = None
        request.usageflow_ledger_id = ledger_id

    def _after_request(self, response):
        """Handle request after it has been processed by the view"""
        if hasattr(request, "usageflow_event_id") and request.usageflow_event_id:
            metadata = request.usageflow_metadata
            metadata.update({
                "responseStatusCode": response.status_code,
                "responseHeaders": dict(response.headers),
                "requestDuration": int((time.time() - request.usageflow_start_time) * 1000),
            })
            
            self.client.fulfill_request(
                request.usageflow_ledger_id,
                request.usageflow_event_id,
                metadata
            )

        return response

    def _extract_user_id(self) -> str:
        """Extract user ID from JWT or headers"""
        token = self.client.extract_bearer_token(request.headers.get("Authorization"))
        if token:
            claims = self.client.decode_jwt_unverified(token)
            return claims.get("sub", "anonymous") if claims else "anonymous"
        return request.headers.get("X-User-ID", "anonymous")

    def _extract_request_url(self, request: Request) -> str:
        """Extract the request URL from the request"""
        if request.url_rule:
            return request.url_rule.rule
        return request.path

    def _extract_identity_from_location(self, field_name: str, location: str) -> Optional[str]:
        """Extract identity from the specified location"""
        method = request.method
        url = self._extract_request_url(request)

        match location:
            case "path_params":
                if request.view_args and field_name in request.view_args:
                    return method + " " + url + " " + self.client.transform_to_ledger_id(request.view_args[field_name])

            case "query_params":
                if request.args and field_name in request.args:
                    return method + " " + url + " " + self.client.transform_to_ledger_id(request.args[field_name])

            case "body":
                try:
                    body_data = request.get_json(silent=True) or {}
                    if body_data and field_name in body_data:
                        return method + " " + url + " " + self.client.transform_to_ledger_id(body_data[field_name])
                except Exception:
                    pass

            case "headers" | "header":
                header_value = request.headers.get(field_name)
                if header_value:
                    return method + " " + url + " " + self.client.transform_to_ledger_id(header_value)

            case "bearer_token":
                auth_header = request.headers.get("Authorization")
                if auth_header:
                    token = self.client.extract_bearer_token(auth_header)
                    if token:
                        claims = self.client.decode_jwt_unverified(token)
                        if claims and field_name in claims:
                            return method + " " + url + " " + self.client.transform_to_ledger_id(claims[field_name])

        return None

    def _guess_ledger_id(self) -> Tuple[str, bool]:
        """Determine the ledger ID from the request"""
        method = request.method
        url = self._extract_request_url(request)

        # Try to get identity from policies first
        policies_map = self.client.get_policies_map()
        policy = policies_map.get(f"{method}:{url}")
        if policy and policy.identity_field_name and policy.identity_field_location:
            result = self._extract_identity_from_location(policy.identity_field_name, policy.identity_field_location)
            if result:
                return result, policy.has_rate_limit

        # If no policy match, try config
        # config = self.client.get_config()
        # if config:
        #     field_name = config.get("identityFieldName")
        #     location = config.get("identityFieldLocation")
        #     if field_name and location:
        #         result = self._extract_identity_from_location(field_name, location)
        #         if result:
        #             return result

        # Fallback to default ledgerId
        return f"{method} {url}", False

__version__ = "0.3.2"
__all__ = ["UsageFlowMiddleware"] 