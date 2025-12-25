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
- **Noise filtering**: Automatically skips health checks, bots, and vulnerability scanners

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

## Whitelist Mode (v1.3.0+) - RECOMMENDED

The best way to filter noise is to **only log YOUR endpoints**. Use `include_prefixes` to specify which paths to log:

```python
# Only log paths starting with these prefixes
app.add_middleware(
    APIMonitorMiddleware,
    app_name="MY_BACKEND",
    include_prefixes=("/excel/", "/stock/", "/api/", "/mcp/"),
)
```

This is much cleaner than trying to exclude infinite junk paths. You know your endpoints - just whitelist them.

## Blacklist Mode (v1.1.0+)

If you prefer blacklist mode, the middleware automatically skips logging for:
- Health check endpoints (`/`, `/health`, `/healthz`, `/ready`)
- Static files (`/favicon.ico`, `/robots.txt`, `/sitemap.xml`)
- Vulnerability scanner probes (`/.env`, `/wp-admin`, `/vendor/phpunit/...`, etc.)
- Common bot paths (`/_next/`, `/js/`, `/css/`, etc.)

### Customize Blacklist

```python
# Add additional paths to exclude
app.add_middleware(
    APIMonitorMiddleware,
    app_name="MY_BACKEND",
    exclude_paths={"/internal", "/metrics", "/debug"},
    exclude_prefixes=("/admin/", "/private/"),
)

# Log everything (disable all filtering)
app.add_middleware(
    APIMonitorMiddleware,
    app_name="MY_BACKEND",
    include_noise=True,
)
```

## License

MIT
