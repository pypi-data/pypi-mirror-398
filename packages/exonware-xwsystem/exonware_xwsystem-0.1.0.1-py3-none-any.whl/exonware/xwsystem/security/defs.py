#!/usr/bin/env python3
#exonware/xwsystem/security/types.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

Security types and enums for XWSystem.
"""

from enum import Enum


# ============================================================================
# SECURITY ENUMS
# ============================================================================

class SecurityLevel(Enum):
    """Security levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EncryptionAlgorithm(Enum):
    """Encryption algorithms."""
    AES_128 = "aes_128"
    AES_256 = "aes_256"
    RSA_2048 = "rsa_2048"
    RSA_4096 = "rsa_4096"
    CHACHA20 = "chacha20"
    BLAKE2B = "blake2b"
    SHA256 = "sha256"
    SHA512 = "sha512"


class HashAlgorithm(Enum):
    """Hash algorithms."""
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"
    BLAKE2B = "blake2b"
    BLAKE2S = "blake2s"
    PBKDF2 = "pbkdf2"
    SCRYPT = "scrypt"


class AuthenticationMethod(Enum):
    """Authentication methods."""
    PASSWORD = "password"
    TOKEN = "token"
    CERTIFICATE = "certificate"
    BIOMETRIC = "biometric"
    MULTI_FACTOR = "multi_factor"
    OAUTH = "oauth"
    SAML = "saml"
    LDAP = "ldap"


class AuthorizationLevel(Enum):
    """Authorization levels."""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class AuditEvent(Enum):
    """Audit event types."""
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS = "access"
    MODIFY = "modify"
    DELETE = "delete"
    CREATE = "create"
    EXECUTE = "execute"
    FAILED_ACCESS = "failed_access"


class OAuth2GrantType(Enum):
    """OAuth2 grant types."""
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    RESOURCE_OWNER = "password"
    REFRESH_TOKEN = "refresh_token"