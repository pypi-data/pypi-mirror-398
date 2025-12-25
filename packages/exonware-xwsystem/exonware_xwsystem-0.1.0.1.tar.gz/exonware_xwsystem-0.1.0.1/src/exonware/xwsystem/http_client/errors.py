#exonware/xwsystem/http/errors.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

HTTP module errors - exception classes for HTTP client functionality.
"""

from typing import Any, Optional


class HttpError(Exception):
    """Base exception for HTTP client errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class HttpConnectionError(HttpError):
    """Raised when HTTP connection fails."""
    pass


class HttpTimeoutError(HttpError):
    """Raised when HTTP request times out."""
    pass


class HttpAuthenticationError(HttpError):
    """Raised when HTTP authentication fails."""
    pass


class HttpAuthorizationError(HttpError):
    """Raised when HTTP authorization fails."""
    pass


class HttpRedirectError(HttpError):
    """Raised when HTTP redirect fails."""
    pass


class HttpRetryError(HttpError):
    """Raised when HTTP retry operation fails."""
    pass


class HttpProxyError(HttpError):
    """Raised when HTTP proxy operation fails."""
    pass


class HttpSSLError(HttpError):
    """Raised when HTTP SSL operation fails."""
    pass


class HttpRequestError(HttpError):
    """Raised when HTTP request is invalid."""
    pass


class HttpResponseError(HttpError):
    """Raised when HTTP response is invalid."""
    pass


class HttpStatusError(HttpError):
    """Raised when HTTP status code indicates error."""
    pass


class HttpContentError(HttpError):
    """Raised when HTTP content operation fails."""
    pass


class HttpStreamError(HttpError):
    """Raised when HTTP streaming operation fails."""
    pass


class HttpSessionError(HttpError):
    """Raised when HTTP session operation fails."""
    pass
