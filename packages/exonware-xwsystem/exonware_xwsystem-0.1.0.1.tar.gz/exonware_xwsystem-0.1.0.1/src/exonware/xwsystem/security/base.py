#exonware/xwsystem/security/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Security module base classes - abstract classes for security functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from .defs import HashAlgorithm, EncryptionAlgorithm, SecurityLevel


class ACryptographicBase(ABC):
    """Abstract base class for cryptographic operations."""
    
    def __init__(self, algorithm: Union[HashAlgorithm, EncryptionAlgorithm]):
        """
        Initialize cryptographic base.
        
        Args:
            algorithm: Cryptographic algorithm
        """
        self.algorithm = algorithm
        self._key: Optional[bytes] = None
        self._iv: Optional[bytes] = None
    
    @abstractmethod
    def generate_key(self, key_size: int = 256) -> bytes:
        """Generate cryptographic key."""
        pass
    
    @abstractmethod
    def set_key(self, key: bytes) -> None:
        """Set cryptographic key."""
        pass
    
    @abstractmethod
    def get_key(self) -> Optional[bytes]:
        """Get cryptographic key."""
        pass
    
    @abstractmethod
    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """Encrypt data."""
        pass
    
    @abstractmethod
    def decrypt(self, encrypted_data: bytes) -> Union[str, bytes]:
        """Decrypt data."""
        pass
    
    @abstractmethod
    def hash(self, data: Union[str, bytes]) -> str:
        """Hash data."""
        pass
    
    @abstractmethod
    def verify_hash(self, data: Union[str, bytes], hash_value: str) -> bool:
        """Verify data hash."""
        pass
    
    @abstractmethod
    def sign(self, data: Union[str, bytes]) -> bytes:
        """Sign data."""
        pass
    
    @abstractmethod
    def verify_signature(self, data: Union[str, bytes], signature: bytes) -> bool:
        """Verify data signature."""
        pass


class AHashBase(ABC):
    """Abstract base class for hash operations."""
    
    def __init__(self, algorithm: HashAlgorithm = HashAlgorithm.SHA256):
        """
        Initialize hash base.
        
        Args:
            algorithm: Hash algorithm
        """
        self.algorithm = algorithm
        self._salt: Optional[bytes] = None
    
    @abstractmethod
    def hash(self, data: Union[str, bytes], salt: Optional[bytes] = None) -> str:
        """Hash data."""
        pass
    
    @abstractmethod
    def hash_file(self, file_path: Union[str, bytes]) -> str:
        """Hash file content."""
        pass
    
    @abstractmethod
    def verify_hash(self, data: Union[str, bytes], hash_value: str, salt: Optional[bytes] = None) -> bool:
        """Verify data hash."""
        pass
    
    @abstractmethod
    def generate_salt(self, length: int = 32) -> bytes:
        """Generate random salt."""
        pass
    
    @abstractmethod
    def set_salt(self, salt: bytes) -> None:
        """Set salt for hashing."""
        pass
    
    @abstractmethod
    def get_salt(self) -> Optional[bytes]:
        """Get current salt."""
        pass
    
    @abstractmethod
    def hash_with_salt(self, data: Union[str, bytes]) -> tuple[str, bytes]:
        """Hash data with generated salt."""
        pass


class AEncryptionBase(ABC):
    """Abstract base class for encryption operations."""
    
    def __init__(self, algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256):
        """
        Initialize encryption base.
        
        Args:
            algorithm: Encryption algorithm
        """
        self.algorithm = algorithm
        self._key: Optional[bytes] = None
        self._iv: Optional[bytes] = None
    
    @abstractmethod
    def generate_key(self, key_size: int = 256) -> bytes:
        """Generate encryption key."""
        pass
    
    @abstractmethod
    def generate_iv(self, iv_size: int = 16) -> bytes:
        """Generate initialization vector."""
        pass
    
    @abstractmethod
    def set_key(self, key: bytes) -> None:
        """Set encryption key."""
        pass
    
    @abstractmethod
    def set_iv(self, iv: bytes) -> None:
        """Set initialization vector."""
        pass
    
    @abstractmethod
    def encrypt(self, data: Union[str, bytes], key: Optional[bytes] = None, iv: Optional[bytes] = None) -> bytes:
        """Encrypt data."""
        pass
    
    @abstractmethod
    def decrypt(self, encrypted_data: bytes, key: Optional[bytes] = None, iv: Optional[bytes] = None) -> Union[str, bytes]:
        """Decrypt data."""
        pass
    
    @abstractmethod
    def encrypt_file(self, file_path: Union[str, bytes], output_path: Union[str, bytes]) -> bool:
        """Encrypt file."""
        pass
    
    @abstractmethod
    def decrypt_file(self, encrypted_file_path: Union[str, bytes], output_path: Union[str, bytes]) -> bool:
        """Decrypt file."""
        pass


class APathValidatorBase(ABC):
    """Abstract base class for path validation."""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.MEDIUM):
        """
        Initialize path validator.
        
        Args:
            security_level: Security level for validation
        """
        self.security_level = security_level
        self._allowed_paths: list[str] = []
        self._blocked_paths: list[str] = []
    
    @abstractmethod
    def validate_path(self, path: Union[str, bytes]) -> bool:
        """Validate file path."""
        pass
    
    @abstractmethod
    def sanitize_path(self, path: Union[str, bytes]) -> str:
        """Sanitize file path."""
        pass
    
    @abstractmethod
    def is_safe_path(self, path: Union[str, bytes]) -> bool:
        """Check if path is safe."""
        pass
    
    @abstractmethod
    def is_absolute_path(self, path: Union[str, bytes]) -> bool:
        """Check if path is absolute."""
        pass
    
    @abstractmethod
    def is_relative_path(self, path: Union[str, bytes]) -> bool:
        """Check if path is relative."""
        pass
    
    @abstractmethod
    def contains_path_traversal(self, path: Union[str, bytes]) -> bool:
        """Check if path contains traversal sequences."""
        pass
    
    @abstractmethod
    def normalize_path(self, path: Union[str, bytes]) -> str:
        """Normalize file path."""
        pass
    
    @abstractmethod
    def add_allowed_path(self, path: str) -> None:
        """Add allowed path."""
        pass
    
    @abstractmethod
    def add_blocked_path(self, path: str) -> None:
        """Add blocked path."""
        pass
    
    @abstractmethod
    def get_allowed_paths(self) -> list[str]:
        """Get allowed paths."""
        pass
    
    @abstractmethod
    def get_blocked_paths(self) -> list[str]:
        """Get blocked paths."""
        pass


class AResourceLimitsBase(ABC):
    """Abstract base class for resource limits."""
    
    def __init__(self):
        """Initialize resource limits."""
        self._limits: dict[str, int] = {}
        self._current_usage: dict[str, int] = {}
    
    @abstractmethod
    def set_limit(self, resource: str, limit: int) -> None:
        """Set resource limit."""
        pass
    
    @abstractmethod
    def get_limit(self, resource: str) -> Optional[int]:
        """Get resource limit."""
        pass
    
    @abstractmethod
    def check_limit(self, resource: str, usage: int) -> bool:
        """Check if usage exceeds limit."""
        pass
    
    @abstractmethod
    def increment_usage(self, resource: str, amount: int = 1) -> bool:
        """Increment resource usage."""
        pass
    
    @abstractmethod
    def decrement_usage(self, resource: str, amount: int = 1) -> None:
        """Decrement resource usage."""
        pass
    
    @abstractmethod
    def get_usage(self, resource: str) -> int:
        """Get current resource usage."""
        pass
    
    @abstractmethod
    def get_usage_percentage(self, resource: str) -> float:
        """Get resource usage percentage."""
        pass
    
    @abstractmethod
    def reset_usage(self, resource: str) -> None:
        """Reset resource usage."""
        pass
    
    @abstractmethod
    def get_all_limits(self) -> dict[str, int]:
        """Get all resource limits."""
        pass
    
    @abstractmethod
    def get_all_usage(self) -> dict[str, int]:
        """Get all resource usage."""
        pass
    
    @abstractmethod
    def is_limit_exceeded(self, resource: str) -> bool:
        """Check if resource limit is exceeded."""
        pass


class ASecurityValidatorBase(ABC):
    """Abstract base class for security validation."""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.MEDIUM):
        """
        Initialize security validator.
        
        Args:
            security_level: Security level for validation
        """
        self.security_level = security_level
        self._validation_rules: dict[str, callable] = {}
    
    @abstractmethod
    def validate_input(self, data: Any, input_type: str) -> bool:
        """Validate input data."""
        pass
    
    @abstractmethod
    def validate_output(self, data: Any, output_type: str) -> bool:
        """Validate output data."""
        pass
    
    @abstractmethod
    def validate_operation(self, operation: str, **kwargs) -> bool:
        """Validate operation."""
        pass
    
    @abstractmethod
    def add_validation_rule(self, rule_name: str, rule_func: callable) -> None:
        """Add validation rule."""
        pass
    
    @abstractmethod
    def remove_validation_rule(self, rule_name: str) -> None:
        """Remove validation rule."""
        pass
    
    @abstractmethod
    def get_validation_errors(self) -> list[str]:
        """Get validation errors."""
        pass
    
    @abstractmethod
    def clear_validation_errors(self) -> None:
        """Clear validation errors."""
        pass
    
    @abstractmethod
    def is_secure_operation(self, operation: str) -> bool:
        """Check if operation is secure."""
        pass
    
    @abstractmethod
    def get_security_score(self) -> float:
        """Get security score."""
        pass


# ============================================================================
# AUTHENTICATION BASE CLASSES (Moved from enterprise)
# ============================================================================

from dataclasses import dataclass, field


@dataclass
class ATokenInfo:
    """Token information structure."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


@dataclass
class AUserInfo:
    """User information structure."""
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    roles: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)


class AAuthProvider(ABC):
    """Abstract base class for authentication providers."""
    
    @abstractmethod
    async def authenticate(self, credentials: dict[str, Any]) -> ATokenInfo:
        """Authenticate user with credentials."""
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> AUserInfo:
        """Validate authentication token."""
        pass
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> ATokenInfo:
        """Refresh authentication token."""
        pass