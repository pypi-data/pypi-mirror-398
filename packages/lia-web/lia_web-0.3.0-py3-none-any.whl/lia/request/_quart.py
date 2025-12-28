# Re-export from cross for backwards compatibility
from cross.request._quart import QuartHTTPRequestAdapter

__all__ = ["QuartHTTPRequestAdapter"]
