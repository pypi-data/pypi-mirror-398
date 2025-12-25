#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Security protocol interfaces for XWSystem.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, Iterator, Callable, Protocol
from typing_extensions import runtime_checkable
import hashlib

# Import enums from types module
from .defs import (
    SecurityLevel,
    EncryptionAlgorithm,
    HashAlgorithm,
    AuthenticationMethod,
    AuthorizationLevel,
    AuditEvent
)


# ============================================================================
# SECURITY INTERFACES
# ============================================================================

class ISecure(ABC):
    """
    Interface for secure objects.
    
    Enforces consistent security behavior across XWSystem.
    """
    
    @abstractmethod
    def encrypt(self, data: Union[str, bytes], algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256) -> Union[str, bytes]:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            algorithm: Encryption algorithm
            
        Returns:
            Encrypted data
        """
        pass
    
    @abstractmethod
    def decrypt(self, encrypted_data: Union[str, bytes], algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256) -> Union[str, bytes]:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data
            algorithm: Encryption algorithm
            
        Returns:
            Decrypted data
        """
        pass
    
    @abstractmethod
    def hash(self, data: Union[str, bytes], algorithm: HashAlgorithm = HashAlgorithm.SHA256) -> str:
        """
        Hash data.
        
        Args:
            data: Data to hash
            algorithm: Hash algorithm
            
        Returns:
            Hash string
        """
        pass
    
    @abstractmethod
    def verify_hash(self, data: Union[str, bytes], hash_value: str, algorithm: HashAlgorithm = HashAlgorithm.SHA256) -> bool:
        """
        Verify data against hash.
        
        Args:
            data: Data to verify
            hash_value: Hash to verify against
            algorithm: Hash algorithm
            
        Returns:
            True if hash matches
        """
        pass
    
    @abstractmethod
    def generate_key(self, algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256) -> bytes:
        """
        Generate encryption key.
        
        Args:
            algorithm: Encryption algorithm
            
        Returns:
            Generated key
        """
        pass
    
    @abstractmethod
    def generate_salt(self, length: int = 32) -> bytes:
        """
        Generate random salt.
        
        Args:
            length: Salt length in bytes
            
        Returns:
            Generated salt
        """
        pass
    
    @abstractmethod
    def secure_random(self, length: int) -> bytes:
        """
        Generate secure random bytes.
        
        Args:
            length: Number of bytes to generate
            
        Returns:
            Random bytes
        """
        pass


# ============================================================================
# AUTHENTICATION INTERFACES
# ============================================================================

class IAuthenticatable(ABC):
    """
    Interface for authentication.
    
    Enforces consistent authentication behavior across XWSystem.
    """
    
    @abstractmethod
    def authenticate(self, credentials: dict[str, Any]) -> bool:
        """
        Authenticate user with credentials.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            True if authenticated
        """
        pass
    
    @abstractmethod
    def authorize(self, user: str, resource: str, action: str) -> bool:
        """
        Authorize user for resource action.
        
        Args:
            user: User identifier
            resource: Resource identifier
            action: Action to authorize
            
        Returns:
            True if authorized
        """
        pass
    
    @abstractmethod
    def logout(self, user: str) -> bool:
        """
        Logout user.
        
        Args:
            user: User identifier
            
        Returns:
            True if logged out
        """
        pass
    
    @abstractmethod
    def is_authenticated(self, user: str) -> bool:
        """
        Check if user is authenticated.
        
        Args:
            user: User identifier
            
        Returns:
            True if authenticated
        """
        pass
    
    @abstractmethod
    def get_user_permissions(self, user: str) -> list[str]:
        """
        Get user permissions.
        
        Args:
            user: User identifier
            
        Returns:
            List of permissions
        """
        pass
    
    @abstractmethod
    def set_user_permissions(self, user: str, permissions: list[str]) -> None:
        """
        Set user permissions.
        
        Args:
            user: User identifier
            permissions: List of permissions
        """
        pass
    
    @abstractmethod
    def validate_credentials(self, credentials: dict[str, Any]) -> bool:
        """
        Validate credential format.
        
        Args:
            credentials: Credentials to validate
            
        Returns:
            True if valid format
        """
        pass
    
    @abstractmethod
    def get_authentication_method(self) -> AuthenticationMethod:
        """
        Get authentication method.
        
        Returns:
            Authentication method
        """
        pass


# ============================================================================
# AUDIT INTERFACES
# ============================================================================

class IAuditable(ABC):
    """
    Interface for audit trails.
    
    Enforces consistent audit behavior across XWSystem.
    """
    
    @abstractmethod
    def log_action(self, action: AuditEvent, user: str, resource: str, details: dict[str, Any] = None) -> None:
        """
        Log audit action.
        
        Args:
            action: Audit event type
            user: User identifier
            resource: Resource identifier
            details: Additional details
        """
        pass
    
    @abstractmethod
    def get_audit_trail(self, user: Optional[str] = None, resource: Optional[str] = None, 
                       start_time: Optional[float] = None, end_time: Optional[float] = None) -> list[dict[str, Any]]:
        """
        Get audit trail.
        
        Args:
            user: Filter by user
            resource: Filter by resource
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            List of audit entries
        """
        pass
    
    @abstractmethod
    def clear_audit_trail(self, older_than: Optional[float] = None) -> int:
        """
        Clear audit trail.
        
        Args:
            older_than: Clear entries older than timestamp
            
        Returns:
            Number of entries cleared
        """
        pass
    
    @abstractmethod
    def export_audit_trail(self, file_path: str, format: str = "json") -> bool:
        """
        Export audit trail to file.
        
        Args:
            file_path: Export file path
            format: Export format
            
        Returns:
            True if exported successfully
        """
        pass
    
    @abstractmethod
    def get_audit_stats(self) -> dict[str, Any]:
        """
        Get audit statistics.
        
        Returns:
            Audit statistics dictionary
        """
        pass
    
    @abstractmethod
    def is_audit_enabled(self) -> bool:
        """
        Check if auditing is enabled.
        
        Returns:
            True if enabled
        """
        pass
    
    @abstractmethod
    def enable_audit(self) -> None:
        """
        Enable auditing.
        """
        pass
    
    @abstractmethod
    def disable_audit(self) -> None:
        """
        Disable auditing.
        """
        pass


# ============================================================================
# AUTHORIZATION INTERFACES
# ============================================================================

class IAuthorization(ABC):
    """
    Interface for authorization.
    
    Enforces consistent authorization behavior across XWSystem.
    """
    
    @abstractmethod
    def check_permission(self, user: str, resource: str, action: str) -> bool:
        """
        Check user permission for resource action.
        
        Args:
            user: User identifier
            resource: Resource identifier
            action: Action to check
            
        Returns:
            True if permitted
        """
        pass
    
    @abstractmethod
    def grant_permission(self, user: str, resource: str, action: str) -> bool:
        """
        Grant permission to user.
        
        Args:
            user: User identifier
            resource: Resource identifier
            action: Action to grant
            
        Returns:
            True if granted
        """
        pass
    
    @abstractmethod
    def revoke_permission(self, user: str, resource: str, action: str) -> bool:
        """
        Revoke permission from user.
        
        Args:
            user: User identifier
            resource: Resource identifier
            action: Action to revoke
            
        Returns:
            True if revoked
        """
        pass
    
    @abstractmethod
    def get_user_roles(self, user: str) -> list[str]:
        """
        Get user roles.
        
        Args:
            user: User identifier
            
        Returns:
            List of role names
        """
        pass
    
    @abstractmethod
    def assign_role(self, user: str, role: str) -> bool:
        """
        Assign role to user.
        
        Args:
            user: User identifier
            role: Role name
            
        Returns:
            True if assigned
        """
        pass
    
    @abstractmethod
    def remove_role(self, user: str, role: str) -> bool:
        """
        Remove role from user.
        
        Args:
            user: User identifier
            role: Role name
            
        Returns:
            True if removed
        """
        pass
    
    @abstractmethod
    def get_role_permissions(self, role: str) -> list[str]:
        """
        Get role permissions.
        
        Args:
            role: Role name
            
        Returns:
            List of permissions
        """
        pass
    
    @abstractmethod
    def set_role_permissions(self, role: str, permissions: list[str]) -> None:
        """
        Set role permissions.
        
        Args:
            role: Role name
            permissions: List of permissions
        """
        pass


# ============================================================================
# SECURITY VALIDATION INTERFACES
# ============================================================================

class ISecurityValidator(ABC):
    """
    Interface for security validation.
    
    Enforces consistent security validation across XWSystem.
    """
    
    @abstractmethod
    def validate_password(self, password: str) -> tuple[bool, list[str]]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: str, input_type: str) -> tuple[bool, list[str]]:
        """
        Validate input data.
        
        Args:
            input_data: Input data to validate
            input_type: Type of input (email, url, etc.)
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass
    
    @abstractmethod
    def sanitize_input(self, input_data: str) -> str:
        """
        Sanitize input data.
        
        Args:
            input_data: Input data to sanitize
            
        Returns:
            Sanitized data
        """
        pass
    
    @abstractmethod
    def detect_sql_injection(self, input_data: str) -> bool:
        """
        Detect SQL injection attempts.
        
        Args:
            input_data: Input data to check
            
        Returns:
            True if SQL injection detected
        """
        pass
    
    @abstractmethod
    def detect_xss(self, input_data: str) -> bool:
        """
        Detect XSS attempts.
        
        Args:
            input_data: Input data to check
            
        Returns:
            True if XSS detected
        """
        pass
    
    @abstractmethod
    def validate_certificate(self, certificate: bytes) -> tuple[bool, str]:
        """
        Validate certificate.
        
        Args:
            certificate: Certificate data
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def check_security_headers(self, headers: dict[str, str]) -> dict[str, bool]:
        """
        Check security headers.
        
        Args:
            headers: HTTP headers
            
        Returns:
            Dictionary of header validation results
        """
        pass


# ============================================================================
# SECURITY MONITORING INTERFACES
# ============================================================================

class ISecurityMonitor(ABC):
    """
    Interface for security monitoring.
    
    Enforces consistent security monitoring across XWSystem.
    """
    
    @abstractmethod
    def detect_intrusion(self, event_data: dict[str, Any]) -> bool:
        """
        Detect intrusion attempts.
        
        Args:
            event_data: Event data to analyze
            
        Returns:
            True if intrusion detected
        """
        pass
    
    @abstractmethod
    def monitor_failed_logins(self, user: str, max_attempts: int = 5) -> bool:
        """
        Monitor failed login attempts.
        
        Args:
            user: User identifier
            max_attempts: Maximum allowed attempts
            
        Returns:
            True if threshold exceeded
        """
        pass
    
    @abstractmethod
    def detect_anomaly(self, behavior_data: dict[str, Any]) -> bool:
        """
        Detect anomalous behavior.
        
        Args:
            behavior_data: Behavior data to analyze
            
        Returns:
            True if anomaly detected
        """
        pass
    
    @abstractmethod
    def get_security_alerts(self) -> list[dict[str, Any]]:
        """
        Get security alerts.
        
        Returns:
            List of security alerts
        """
        pass
    
    @abstractmethod
    def clear_security_alerts(self) -> None:
        """
        Clear security alerts.
        """
        pass
    
    @abstractmethod
    def get_threat_level(self) -> SecurityLevel:
        """
        Get current threat level.
        
        Returns:
            Current threat level
        """
        pass
    
    @abstractmethod
    def set_threat_level(self, level: SecurityLevel) -> None:
        """
        Set threat level.
        
        Args:
            level: Threat level to set
        """
        pass
    
    @abstractmethod
    def get_security_metrics(self) -> dict[str, Any]:
        """
        Get security metrics.
        
        Returns:
            Security metrics dictionary
        """
        pass


# ============================================================================
# SECURITY POLICY INTERFACES
# ============================================================================

class ISecurityPolicy(ABC):
    """
    Interface for security policies.
    
    Enforces consistent security policy behavior across XWSystem.
    """
    
    @abstractmethod
    def get_policy(self, policy_name: str) -> dict[str, Any]:
        """
        Get security policy.
        
        Args:
            policy_name: Policy name
            
        Returns:
            Policy dictionary
        """
        pass
    
    @abstractmethod
    def set_policy(self, policy_name: str, policy: dict[str, Any]) -> None:
        """
        Set security policy.
        
        Args:
            policy_name: Policy name
            policy: Policy dictionary
        """
        pass
    
    @abstractmethod
    def validate_policy(self, policy: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate security policy.
        
        Args:
            policy: Policy to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass
    
    @abstractmethod
    def apply_policy(self, policy_name: str, context: dict[str, Any]) -> bool:
        """
        Apply security policy.
        
        Args:
            policy_name: Policy name
            context: Context data
            
        Returns:
            True if policy applied successfully
        """
        pass
    
    @abstractmethod
    def list_policies(self) -> list[str]:
        """
        List all security policies.
        
        Returns:
            List of policy names
        """
        pass
    
    @abstractmethod
    def remove_policy(self, policy_name: str) -> bool:
        """
        Remove security policy.
        
        Args:
            policy_name: Policy name to remove
            
        Returns:
            True if removed
        """
        pass
    
    @abstractmethod
    def get_policy_violations(self) -> list[dict[str, Any]]:
        """
        Get policy violations.
        
        Returns:
            List of policy violations
        """
        pass
    
    @abstractmethod
    def clear_policy_violations(self) -> None:
        """
        Clear policy violations.
        """
        pass


# ============================================================================
# SECURITY TOKEN INTERFACES
# ============================================================================

class ISecurityToken(ABC):
    """
    Interface for security tokens.
    
    Enforces consistent security token behavior across XWSystem.
    """
    
    @abstractmethod
    def generate_token(self, payload: dict[str, Any], expires_in: int = 3600) -> str:
        """
        Generate security token.
        
        Args:
            payload: Token payload
            expires_in: Expiration time in seconds
            
        Returns:
            Generated token
        """
        pass
    
    @abstractmethod
    def validate_token(self, token: str) -> tuple[bool, dict[str, Any]]:
        """
        Validate security token.
        
        Args:
            token: Token to validate
            
        Returns:
            Tuple of (is_valid, payload)
        """
        pass
    
    @abstractmethod
    def refresh_token(self, token: str, expires_in: int = 3600) -> str:
        """
        Refresh security token.
        
        Args:
            token: Token to refresh
            expires_in: New expiration time
            
        Returns:
            Refreshed token
        """
        pass
    
    @abstractmethod
    def revoke_token(self, token: str) -> bool:
        """
        Revoke security token.
        
        Args:
            token: Token to revoke
            
        Returns:
            True if revoked
        """
        pass
    
    @abstractmethod
    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired.
        
        Args:
            token: Token to check
            
        Returns:
            True if expired
        """
        pass
    
    @abstractmethod
    def get_token_info(self, token: str) -> dict[str, Any]:
        """
        Get token information.
        
        Args:
            token: Token to get info for
            
        Returns:
            Token information dictionary
        """
        pass
    
    @abstractmethod
    def list_active_tokens(self, user: Optional[str] = None) -> list[str]:
        """
        List active tokens.
        
        Args:
            user: Filter by user
            
        Returns:
            List of active tokens
        """
        pass
    
    @abstractmethod
    def cleanup_expired_tokens(self) -> int:
        """
        Cleanup expired tokens.
        
        Returns:
            Number of tokens cleaned up
        """
        pass


# ============================================================================
# SECURITY PROTOCOLS
# ============================================================================

@runtime_checkable
class Hashable(Protocol):
    """Protocol for objects that can be hashed securely."""
    
    def hash(self, data: Union[str, bytes], **kwargs: Any) -> str:
        """Generate hash of data."""
        ...


@runtime_checkable
class Encryptable(Protocol):
    """Protocol for objects that support encryption/decryption."""
    
    def encrypt(self, data: Union[str, bytes], **kwargs: Any) -> bytes:
        """Encrypt data."""
        ...
    
    def decrypt(self, data: bytes, **kwargs: Any) -> Union[str, bytes]:
        """Decrypt data."""
        ...
