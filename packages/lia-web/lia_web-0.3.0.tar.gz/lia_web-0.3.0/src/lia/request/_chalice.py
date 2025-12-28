# Re-export from cross for backwards compatibility
from cross.request._chalice import ChaliceHTTPRequestAdapter

__all__ = ["ChaliceHTTPRequestAdapter"]
