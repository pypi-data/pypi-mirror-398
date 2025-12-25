#exonware/xwsystem/security/errors.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Security module errors - exception classes for security functionality.
"""


class SecurityError(Exception):
    """Base exception for security errors."""
    pass


class CryptographicError(SecurityError):
    """Raised when cryptographic operation fails."""
    pass


class EncryptionError(CryptographicError):
    """Raised when encryption operation fails."""
    pass


class DecryptionError(CryptographicError):
    """Raised when decryption operation fails."""
    pass


class HashError(CryptographicError):
    """Raised when hash operation fails."""
    pass


class SignatureError(CryptographicError):
    """Raised when signature operation fails."""
    pass


class KeyError(CryptographicError):
    """Raised when key operation fails."""
    pass


class KeyGenerationError(KeyError):
    """Raised when key generation fails."""
    pass


class KeyValidationError(KeyError):
    """Raised when key validation fails."""
    pass


class PathSecurityError(SecurityError):
    """Raised when path security check fails."""
    pass


class PathTraversalError(SecurityError):
    """Raised when path traversal attack is detected."""
    pass


class ResourceLimitError(SecurityError):
    """Raised when resource limit is exceeded."""
    pass


class ResourceQuotaError(ResourceLimitError):
    """Raised when resource quota is exceeded."""
    pass


class ResourceTimeoutError(ResourceLimitError):
    """Raised when resource operation times out."""
    pass


class SecurityValidationError(SecurityError):
    """Raised when security validation fails."""
    pass


class SecurityPermissionError(SecurityError):
    """Raised when security permission is denied."""
    pass


class SecurityConfigurationError(SecurityError):
    """Raised when security configuration is invalid."""
    pass


class SecurityPolicyError(SecurityError):
    """Raised when security policy is violated."""
    pass


# ============================================================================
# AUTHENTICATION ERRORS (Moved from enterprise)
# ============================================================================


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(SecurityError):
    """Raised when authorization fails."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when authentication token has expired."""
    pass


class OAuth2Error(AuthenticationError):
    """Raised when OAuth2 operation fails."""
    pass


class JWTError(AuthenticationError):
    """Raised when JWT operation fails."""
    pass


class SAMLError(AuthenticationError):
    """Raised when SAML operation fails."""
    pass