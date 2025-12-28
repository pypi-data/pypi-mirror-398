# Re-export from cross for backwards compatibility
from cross.request._django import AsyncDjangoHTTPRequestAdapter, DjangoHTTPRequestAdapter

__all__ = ["AsyncDjangoHTTPRequestAdapter", "DjangoHTTPRequestAdapter"]
