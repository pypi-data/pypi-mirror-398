# UsageFlow FastAPI

FastAPI middleware for UsageFlow - Usage-based pricing made simple.

## Installation

```bash
pip install usageflow-fastapi
```

## Usage

```python
from fastapi import FastAPI
from usageflow.fastapi import UsageFlowMiddleware

app = FastAPI()

# Initialize UsageFlow middleware
app.add_middleware(
    UsageFlowMiddleware,
    api_key="your-api-key",
    pool_size=10  # Optional: Number of WebSocket connections (default: 10)
)

@app.get("/api/v1/users")
async def get_users():
    return {"users": ["user1", "user2"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Configuration

The middleware accepts the following parameters:

- `app`: Your FastAPI application instance (passed via `add_middleware`)
- `api_key`: Your UsageFlow API key (required)
- `pool_size` (optional): Number of WebSocket connections in the pool (default: 10)

Note: Whitelist and tracklist routes are now managed server-side via the UsageFlow dashboard, not through local parameters.

## Features

- Automatic usage tracking
- Request/response logging
- Rate limiting and quota management
- User identification via JWT tokens
- Custom metadata support
- Async support
- Endpoint blocking support
- Server-side whitelist and tracklist route filtering

## Documentation

For full documentation, visit [https://docs.usageflow.io](https://docs.usageflow.io)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
