"""
tigzig-api-monitor: Lightweight FastAPI middleware for centralized API monitoring.
"""

from .middleware import APIMonitorMiddleware

__version__ = "1.3.0"
__all__ = ["APIMonitorMiddleware"]
