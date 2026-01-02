# UsageFlow Flask

> ⚠️ **Beta Notice**: This package is currently in beta. While we strive to maintain stability, there may be breaking changes as we continue to improve the API.

The Flask package of UsageFlow provides easy integration with Flask applications for API usage tracking and management.

## Installation

```bash
pip install usageflow-flask
```

## Quick Start

```python
from flask import Flask, jsonify
from usageflow.flask import UsageFlowMiddleware

app = Flask(__name__)

# Initialize UsageFlow middleware
UsageFlowMiddleware(
    app,
    api_key="your_api_key_here",
    pool_size=10  # Optional: Number of WebSocket connections (default: 10)
)

@app.route("/api/v1/users")
def get_users():
    return jsonify({"users": ["user1", "user2"]})

if __name__ == "__main__":
    app.run()
```

## Configuration

The middleware accepts the following parameters:

- `app`: Your Flask application instance (required)
- `api_key`: Your UsageFlow API key (required)
- `pool_size` (optional): Number of WebSocket connections in the pool (default: 10)

## Features

- Automatic request tracking
- JWT token extraction and validation
- Request/response metadata collection
- Rate limiting and quota management
- Endpoint blocking support

## Development

To contribute to the project:

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Run tests:
   ```bash
   pytest
   ```

## License

MIT License
