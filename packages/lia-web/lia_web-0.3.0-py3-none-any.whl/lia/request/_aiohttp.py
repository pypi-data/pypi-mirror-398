# Re-export from cross for backwards compatibility
from cross.request._aiohttp import AiohttpHTTPRequestAdapter

__all__ = ["AiohttpHTTPRequestAdapter"]
