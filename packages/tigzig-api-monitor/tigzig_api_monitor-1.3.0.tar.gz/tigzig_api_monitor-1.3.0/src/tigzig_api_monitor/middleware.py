"""
API Monitor Middleware for FastAPI applications.

Automatically captures request/response metrics and sends them to a central
monitoring service in a non-blocking manner.
"""

import os
import asyncio
from datetime import datetime
from typing import Optional, List, Set
from urllib.parse import urlparse

import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


# Default paths to exclude from logging (noise reduction)
DEFAULT_EXCLUDE_PATHS: Set[str] = {
    # Health checks & root probes
    "/",
    "/health",
    "/healthz",
    "/ready",
    "/robots.txt",
    "/favicon.ico",
    "/sitemap.xml",

    # Common vulnerability scanner targets (PHP/Laravel/WordPress)
    "/.env",
    "/wp-login.php",
    "/wp-admin",
    "/xmlrpc.php",
    "/admin",
    "/administrator",
    "/.git/config",
    "/config.php",
    "/phpinfo.php",
    "/info.php",
    "/server-status",
    "/.htaccess",
    "/web.config",
}

# Path prefixes to exclude (matched with startswith)
DEFAULT_EXCLUDE_PREFIXES: tuple = (
    "/vendor/",          # PHP composer paths
    "/_ignition/",       # Laravel debug
    "/api/actions",      # Common scanner probe
    "/_next/",           # Next.js internals
    "/static/",          # Static files (optional)
    "/.well-known/",     # ACME/Let's Encrypt
    "/wp-",              # WordPress paths
    "/js/",              # JS file probes
    "/css/",             # CSS file probes
)


class APIMonitorMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically monitor API requests.

    Usage:
        from fastapi import FastAPI
        from tigzig_api_monitor import APIMonitorMiddleware

        app = FastAPI()
        app.add_middleware(APIMonitorMiddleware, app_name="YOUR_APP")

        # RECOMMENDED: Whitelist mode - only log YOUR endpoints (v1.3.0+)
        app.add_middleware(
            APIMonitorMiddleware,
            app_name="YOUR_APP",
            include_prefixes=("/excel/", "/stock/", "/api/"),  # Only log these
        )

        # Alternative: Blacklist mode - exclude specific paths
        app.add_middleware(
            APIMonitorMiddleware,
            app_name="YOUR_APP",
            exclude_paths={"/internal", "/metrics"},
            exclude_prefixes=("/debug/",),
        )

    Environment Variables:
        API_MONITOR_URL: URL of the monitoring service (required)
        API_MONITOR_KEY: API key for authentication (required)
    """

    def __init__(
        self,
        app,
        app_name: str,
        include_prefixes: Optional[tuple] = None,
        exclude_paths: Optional[Set[str]] = None,
        exclude_prefixes: Optional[tuple] = None,
        include_noise: bool = False
    ):
        """
        Initialize the middleware.

        Args:
            app: The FastAPI/Starlette application
            app_name: Name to identify this application in logs
            include_prefixes: WHITELIST mode - only log paths starting with these prefixes.
                              If set, exclude_paths/exclude_prefixes are ignored.
                              Example: ("/excel/", "/stock/", "/api/")
            exclude_paths: BLACKLIST mode - exact paths to exclude from logging
            exclude_prefixes: BLACKLIST mode - path prefixes to exclude
            include_noise: If True, log everything (ignore all filters)
        """
        super().__init__(app)
        self.app_name = app_name
        self.monitor_url = os.getenv("API_MONITOR_URL", "")
        self.api_key = os.getenv("API_MONITOR_KEY", "")
        self.include_noise = include_noise

        # v1.3.0: Whitelist mode takes priority
        self.include_prefixes = include_prefixes

        # Build exclusion sets (only used if include_prefixes is not set)
        if include_noise:
            self.exclude_paths = set()
            self.exclude_prefixes = ()
        else:
            self.exclude_paths = DEFAULT_EXCLUDE_PATHS.copy()
            if exclude_paths:
                self.exclude_paths.update(exclude_paths)

            self.exclude_prefixes = DEFAULT_EXCLUDE_PREFIXES
            if exclude_prefixes:
                self.exclude_prefixes = DEFAULT_EXCLUDE_PREFIXES + exclude_prefixes

        # Log configuration
        if self.include_prefixes:
            print(f"[APIMonitor] {app_name}: WHITELIST mode - only logging: {self.include_prefixes}")
        elif not include_noise:
            print(f"[APIMonitor] {app_name}: BLACKLIST mode - using default exclusions")

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

    def _should_log(self, path: str) -> bool:
        """Check if this path should be logged.

        v1.3.0: Supports two modes:
        - WHITELIST mode (include_prefixes set): Only log paths matching prefixes
        - BLACKLIST mode (default): Log everything except excluded paths
        """
        # v1.3.0: Whitelist mode - only log if path matches include_prefixes
        if self.include_prefixes:
            return path.startswith(self.include_prefixes)

        # Blacklist mode - exclude specific paths
        # Check exact matches
        if path in self.exclude_paths:
            return False

        # Check prefix matches
        if path.startswith(self.exclude_prefixes):
            return False

        return True

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
        path = request.url.path

        # Check if this path should be logged
        should_log = self._should_log(path)

        if not should_log:
            # Skip logging, just pass through
            return await call_next(request)

        start_time = datetime.now()

        # Capture request details
        # v1.2.0: Send ALL headers as JSON dict so logger service can extract what it needs
        # This is future-proof - adding new header fields only requires updating logger service
        log_data = {
            "app_name": self.app_name,
            "endpoint": path,  # Path only, no query params
            "method": request.method,
            "client_ip": self._get_client_ip(request),
            "headers": dict(request.headers),  # ALL headers as JSON dict
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
