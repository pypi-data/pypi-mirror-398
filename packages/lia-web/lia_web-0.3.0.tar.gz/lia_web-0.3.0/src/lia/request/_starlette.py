# Re-export from cross for backwards compatibility
from cross.request._starlette import StarletteRequestAdapter

__all__ = ["StarletteRequestAdapter"]
