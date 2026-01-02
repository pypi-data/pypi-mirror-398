from flask import Flask, Request, request
from usageflow.core import UsageFlowClient
import time
import re
from typing import Optional, Tuple, Dict, Any

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

        try:
            # Skip tracking for whitelisted routes
            if self.client.is_endpoint_whitelisted(route_path, request.method):
                return

            # Track only specific routes if tracklist is set
            if not self.client.is_endpoint_monitored(route_path, request.method):
                return
        except Exception:
            # If WebSocket is not connected, skip tracking for this request
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

        try:
            # Get ledger ID and allocate request
            ledger_id, has_rate_limit, response_tracking_field = self._guess_ledger_id()

            # Store metadata for later use
            request.usageflow_metadata = metadata
            request.usageflow_response_tracking_field = response_tracking_field

            # Check of url is blocked
            if self.client.is_endpoint_blocked(ledger_id):
                return {"error": "Endpoint blocked"}, 403

            success, result = self.client.allocate_request(ledger_id, metadata, has_rate_limit, response_tracking_field)
            
            if not success:
                error_message = result.get('error', 'Request fulfillment failed') if result else 'Request fulfillment failed'
                status_code = result.get('status_code', 400) if result else 400
                if status_code == 520:
                    return
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
        except Exception:
            # If WebSocket is not connected or any error occurs, skip tracking for this request
            pass

    def _after_request(self, response):
        """Handle request after it has been processed by the view"""
        if hasattr(request, "usageflow_event_id") and request.usageflow_event_id:
            try:
                config = self.client.get_config()
            except Exception:
                config = None  # Fail silently if WebSocket is not connected

            response_schema: dict = {}
            if config and config.get("extractResponseSchema", True):
                try:
                    response_schema = self.client.extract_schema(response.json)
                except Exception:
                    pass  # Fail silently if extraction fails

            metadata = request.usageflow_metadata
            response_tracking_field = request.usageflow_response_tracking_field

            response_tracking_value: int | None = None
            if response_tracking_field:
                try:
                    # Get the value of the response tracking field, but do not overwrite or create an unused variable
                    response_tracking_value = self._get_by_dot_notation(response.json, response_tracking_field)
                except Exception:
                    pass  # Fail silently if extraction fails

            metadata.update({
                "responseStatusCode": response.status_code,
                "responseHeaders": dict(response.headers),
                "requestDuration": int((time.time() - request.usageflow_start_time) * 1000),
                "responseSchema": response_schema,
            })
            
            try:
                self.client.fulfill_request(
                    request.usageflow_ledger_id,
                    request.usageflow_event_id,
                    metadata,
                    response_tracking_value
                )
            except Exception:
                pass  # Fail silently if WebSocket is not connected

        return response

    def _extract_user_id(self) -> str:
        """Extract user ID from JWT or headers"""
        token = self.client.extract_bearer_token(request.headers.get("Authorization"))
        if token:
            claims = self.client.decode_jwt_unverified(token)
            return claims.get("sub", "anonymous") if claims else "anonymous"
        return request.headers.get("X-User-ID", "anonymous")

    def _parse_jwt_cookie_field(self, field_name: str) -> Optional[Dict[str, str]]:
        """Parse JWT cookie field format: '[technique=jwt]cookieName[pick=claim]'"""
        technique_match = re.match(r'^\[technique=([^\]]+)\]', field_name)
        if not technique_match or technique_match.group(1) != 'jwt':
            return None

        pick_match = re.search(r'\[pick=([^\]]+)\]', field_name)
        if not pick_match:
            return None

        # Extract cookie name: everything between [technique=jwt] and [pick=...]
        technique_end = len(technique_match.group(0))
        pick_start = field_name.find('[pick=')
        if pick_start == -1 or pick_start <= technique_end:
            return None

        cookie_name = field_name[technique_end:pick_start]
        if not cookie_name:
            return None

        return {
            "cookieName": cookie_name,
            "claim": pick_match.group(1),
        }

    def _get_cookie_value(self, headers: Any, cookie_name: str) -> Optional[str]:
        """Parse and extract a specific cookie value from the Cookie header"""
        cookie_header = headers.get("Cookie") or headers.get("cookie")
        if not cookie_header:
            return None

        # Parse cookies from the Cookie header string
        # Format: "name1=value1; name2=value2; name3=value3"
        cookies = []
        for cookie in cookie_header.split(';'):
            parts = cookie.strip().split('=', 1)
            if len(parts) == 2:
                name = parts[0].strip()
                value = parts[1].strip()  # Handle values that might contain '='
                cookies.append({"name": name, "value": value})

        # Find the cookie with the matching name (case-insensitive)
        for cookie in cookies:
            if cookie["name"].lower() == cookie_name.lower():
                return cookie["value"]

        return None

    def _get_by_dot_notation(self, obj: Any, path: str) -> Any:
        """Access nested object properties using dot notation, supporting array iteration with [*]"""
        parts = path.split('.')
        result = obj

        for i, part in enumerate(parts):
            if result is None:
                return None

            # Check if this part contains array iteration [*]
            if '[*]' in part:
                # Split the part: e.g., "users[*]" -> "users" and remaining path
                array_key = part.replace('[*]', '')
                remaining_path = '.'.join(parts[i + 1:]) if i + 1 < len(parts) else None

                # Get the array
                if isinstance(result, dict):
                    array = result.get(array_key)
                else:
                    return None

                # If not an array, return None
                if not isinstance(array, list):
                    return None

                # If there's a remaining path, iterate and return the first matching element
                if remaining_path:
                    for item in array:
                        value = self._get_by_dot_notation(item, remaining_path)
                        if value is not None:
                            return value
                    return None
                else:
                    # No remaining path, return the first element of the array
                    return array[0] if array else None

            # Regular property access
            if isinstance(result, dict):
                result = result.get(part)
            elif isinstance(result, list):
                # If result is a list and we're trying to access a property,
                # we might want to handle this differently, but for now return None
                return None
            else:
                return None

        return result

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

            case "cookie":
                # Handle JWT cookie format: '[technique=jwt]cookieName[pick=claim]'
                jwt_cookie_match = self._parse_jwt_cookie_field(field_name)
                if jwt_cookie_match:
                    cookie_name = jwt_cookie_match["cookieName"]
                    claim = jwt_cookie_match["claim"]
                    cookie_value = self._get_cookie_value(request.headers, cookie_name)
                    if cookie_value:
                        claims = self.client.decode_jwt_unverified(cookie_value)
                        if claims and claim in claims:
                            return method + " " + url + " " + self.client.transform_to_ledger_id(claims[claim])
                else:
                    # Handle standard cookie access (e.g., "cookie.session" or "session")
                    cookie_value = None
                    if field_name.lower().startswith("cookie."):
                        cookie_name = field_name[7:]  # Remove "cookie." prefix
                        cookie_value = self._get_cookie_value(request.headers, cookie_name)
                    else:
                        # Use dot notation for regular headers
                        cookie_value = self._get_by_dot_notation(request.headers, field_name)

                    if cookie_value:
                        return method + " " + url + " " + self.client.transform_to_ledger_id(cookie_value)

        return None

    def _guess_ledger_id(self) -> Tuple[str, bool, None]:
        """Determine the ledger ID from the request"""
        method = request.method
        url = self._extract_request_url(request)

        try:
            # Try to get identity from policies first
            policies_map = self.client.get_policies_map()
            policy = policies_map.get(f"{method}:{url}")
            response_tracking_field = None
            if policy:
                if policy.is_response_tracking_enabled:
                    response_tracking_field = policy.response_tracking_field
            if policy and policy.identity_field_name and policy.identity_field_location:
                result = self._extract_identity_from_location(policy.identity_field_name, policy.identity_field_location)
                if result:
                    return result, policy.has_rate_limit, response_tracking_field
        except Exception:
            # If WebSocket is not connected, fall back to default
            pass

        return f"{method} {url}", False, None

__version__ = "0.3.4"
__all__ = ["UsageFlowMiddleware"] 