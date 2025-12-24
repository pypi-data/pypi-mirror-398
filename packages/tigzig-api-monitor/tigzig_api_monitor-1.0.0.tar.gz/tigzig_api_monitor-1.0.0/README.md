# tigzig-api-monitor

Lightweight FastAPI middleware for centralized API monitoring. Automatically captures request/response metrics and sends them to a central monitoring service.

## Installation

```bash
pip install tigzig-api-monitor
```

## Quick Start

```python
from fastapi import FastAPI
from tigzig_api_monitor import APIMonitorMiddleware

app = FastAPI()

# Add the monitoring middleware
app.add_middleware(
    APIMonitorMiddleware,
    app_name="YOUR_APP_NAME",  # Required: identifies your app in logs
)
```

## Configuration

Set these environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `API_MONITOR_URL` | Yes | URL of the monitoring service (e.g., `https://logger.tigzig.com/log`) |
| `API_MONITOR_KEY` | Yes | API key for authentication |

## Features

- **Non-blocking**: Logs are sent asynchronously, never slowing down your API
- **Automatic capture**: Request method, endpoint, status code, response time
- **Privacy-safe**: IP addresses are hashed, not stored
- **Lightweight**: Minimal dependencies (just `httpx` and `starlette`)
- **Fire-and-forget**: Logging failures don't affect your API

## What Gets Logged

Each request automatically captures:
- App name (configured)
- Endpoint path (no query params for privacy)
- HTTP method (GET, POST, etc.)
- Response status code
- Response time in milliseconds
- Client IP (sent to service, hashed before storage)
- User-Agent header
- Origin header
- Referer path (no query params)

## Example

```python
import os
from fastapi import FastAPI
from tigzig_api_monitor import APIMonitorMiddleware

# Set environment variables (or use .env file)
os.environ["API_MONITOR_URL"] = "https://logger.tigzig.com/log"
os.environ["API_MONITOR_KEY"] = "your-api-key"

app = FastAPI()

# Add monitoring - that's it!
app.add_middleware(APIMonitorMiddleware, app_name="MY_BACKEND")

@app.get("/")
def read_root():
    return {"message": "Hello World"}

# Every request to this API will now be monitored automatically
```

## License

MIT
