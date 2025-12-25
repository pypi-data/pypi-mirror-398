#!/usr/bin/env python3
#exonware/xwsystem/http_client/defs.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

HTTP types and enums for XWSystem.
"""

from enum import Enum
from ..shared.defs import AuthType


# ============================================================================
# HTTP ENUMS
# ============================================================================

class HttpMethod(Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class HttpStatus(Enum):
    """HTTP status codes."""
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503


class ContentType(Enum):
    """Content types."""
    JSON = "application/json"
    XML = "application/xml"
    FORM = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"
    TEXT = "text/plain"
    HTML = "text/html"
    BINARY = "application/octet-stream"


class RetryStrategy(Enum):
    """Retry strategies."""
    NONE = "none"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"
