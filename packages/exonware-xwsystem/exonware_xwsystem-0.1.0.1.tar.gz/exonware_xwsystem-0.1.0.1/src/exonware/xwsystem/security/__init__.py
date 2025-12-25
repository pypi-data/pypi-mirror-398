"""
XSystem Security Package

Provides security utilities including:
- Path validation and resource limits
- Advanced authentication (OAuth2, JWT, SAML)
- Cryptography and encryption
"""

from .path_validator import PathValidator, PathSecurityError
from .resource_limits import (
    GenericLimitError,
    ResourceLimits,
    get_resource_limits,
    reset_resource_limits,
)
from .auth import (
    OAuth2Provider,
    JWTProvider,
    SAMLProvider,
    EnterpriseAuth,
)
from .base import (
    AAuthProvider,
    ATokenInfo,
    AUserInfo,
)
from .errors import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    OAuth2Error,
    JWTError,
    SAMLError,
)
from .defs import OAuth2GrantType

__all__ = [
    # Path & Resources
    "PathValidator",
    "PathSecurityError",
    "ResourceLimits",
    "GenericLimitError",
    "get_resource_limits",
    "reset_resource_limits",
    # Authentication
    "OAuth2Provider",
    "JWTProvider",
    "SAMLProvider",
    "EnterpriseAuth",
    "AAuthProvider",
    "ATokenInfo",
    "AUserInfo",
    "AuthenticationError",
    "AuthorizationError",
    "TokenExpiredError",
    "OAuth2Error",
    "JWTError",
    "SAMLError",
    "OAuth2GrantType",
]
