"""
API Monitor Middleware for FastAPI applications.

Automatically captures request/response metrics and sends them to a central
monitoring service in a non-blocking manner.
"""

import os
import asyncio
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class APIMonitorMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically monitor API requests.

    Usage:
        from fastapi import FastAPI
        from tigzig_api_monitor import APIMonitorMiddleware

        app = FastAPI()
        app.add_middleware(APIMonitorMiddleware, app_name="YOUR_APP")

    Environment Variables:
        API_MONITOR_URL: URL of the monitoring service (required)
        API_MONITOR_KEY: API key for authentication (required)
    """

    def __init__(self, app, app_name: str):
        """
        Initialize the middleware.

        Args:
            app: The FastAPI/Starlette application
            app_name: Name to identify this application in logs
        """
        super().__init__(app)
        self.app_name = app_name
        self.monitor_url = os.getenv("API_MONITOR_URL", "")
        self.api_key = os.getenv("API_MONITOR_KEY", "")

        if not self.monitor_url:
            print(f"[APIMonitor] WARNING: API_MONITOR_URL not set - monitoring disabled for {app_name}")
        if not self.api_key:
            print(f"[APIMonitor] WARNING: API_MONITOR_KEY not set - monitoring disabled for {app_name}")

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers."""
        # Check x-forwarded-for first (for proxied requests)
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    def _get_referer_path(self, request: Request) -> Optional[str]:
        """Extract path from referer header (no query params for privacy)."""
        referer = request.headers.get("referer", "")
        if referer:
            try:
                parsed = urlparse(referer)
                return parsed.path or "/"
            except Exception:
                pass
        return None

    async def _send_log(self, log_data: dict):
        """Send log data to monitoring service (fire-and-forget)."""
        if not self.monitor_url or not self.api_key:
            return

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    self.monitor_url,
                    json=log_data,
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": self.api_key
                    }
                )
        except Exception:
            # Silently ignore - logging failures should never affect the API
            pass

    async def dispatch(self, request: Request, call_next):
        """Process request and capture metrics."""
        start_time = datetime.now()

        # Capture request details
        log_data = {
            "app_name": self.app_name,
            "endpoint": request.url.path,  # Path only, no query params
            "method": request.method,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
            "origin": request.headers.get("origin"),
            "referer_path": self._get_referer_path(request),
            "content_length": request.headers.get("content-length"),
            "status_code": 500,  # Default, updated after response
            "response_time_ms": 0,
            "error_message": None
        }

        try:
            # Process the request
            response = await call_next(request)
            log_data["status_code"] = response.status_code

        except Exception as e:
            # Capture error details
            log_data["error_message"] = str(e)[:1000]
            raise

        finally:
            # Calculate response time
            end_time = datetime.now()
            log_data["response_time_ms"] = int((end_time - start_time).total_seconds() * 1000)

            # Send log in background (non-blocking)
            asyncio.create_task(self._send_log(log_data))

        return response
