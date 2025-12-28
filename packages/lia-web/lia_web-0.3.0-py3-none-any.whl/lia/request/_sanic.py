# Re-export from cross for backwards compatibility
from cross.request._sanic import SanicHTTPRequestAdapter, convert_request_to_files_dict

__all__ = ["SanicHTTPRequestAdapter", "convert_request_to_files_dict"]
