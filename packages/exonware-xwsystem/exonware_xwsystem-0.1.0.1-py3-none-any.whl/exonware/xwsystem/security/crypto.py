"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Cryptographic utilities for secure data handling and protection.
"""

import hashlib
import hmac
import secrets
import time
from base64 import b64decode, b64encode
from typing import Any, Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt

from ..config.logging_setup import get_logger
from .errors import CryptographicError

logger = get_logger("xwsystem.security.crypto")


class SecureHash:
    """Secure hashing utilities."""
    
    @staticmethod
    def sha256(data: Union[str, bytes]) -> str:
        """
        Compute SHA-256 hash.

        Args:
            data: Data to hash

        Returns:
            Hexadecimal hash string
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def sha512(data: Union[str, bytes]) -> str:
        """
        Compute SHA-512 hash.

        Args:
            data: Data to hash

        Returns:
            Hexadecimal hash string
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha512(data).hexdigest()

    @staticmethod
    def blake2b(data: Union[str, bytes], key: Optional[bytes] = None) -> str:
        """
        Compute BLAKE2b hash.

        Args:
            data: Data to hash
            key: Optional key for keyed hashing

        Returns:
            Hexadecimal hash string
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        if key is None:
            return hashlib.blake2b(data).hexdigest()
        else:
            return hashlib.blake2b(data, key=key).hexdigest()

    @staticmethod
    def hmac_sha256(data: Union[str, bytes], key: Union[str, bytes]) -> str:
        """
        Compute HMAC-SHA256.

        Args:
            data: Data to authenticate
            key: Secret key

        Returns:
            Hexadecimal HMAC string
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        if isinstance(key, str):
            key = key.encode('utf-8')
        return hmac.new(key, data, hashlib.sha256).hexdigest()

    @staticmethod
    def verify_hmac(data: Union[str, bytes], key: Union[str, bytes], expected_hmac: str) -> bool:
        """
        Verify HMAC-SHA256.

        Args:
            data: Data to verify
            key: Secret key
            expected_hmac: Expected HMAC value

        Returns:
            True if HMAC is valid
        """
        computed_hmac = SecureHash.hmac_sha256(data, key)
        return hmac.compare_digest(computed_hmac, expected_hmac)


class SecureRandom:
    """Cryptographically secure random number generation."""
    
    @staticmethod
    def token_bytes(length: int = 32) -> bytes:
        """
        Generate random bytes.

        Args:
            length: Number of bytes to generate

        Returns:
            Random bytes
        """
        return secrets.token_bytes(length)

    @staticmethod
    def token_hex(length: int = 32) -> str:
        """
        Generate random hex string.

        Args:
            length: Number of bytes to generate (hex will be 2x length)

        Returns:
            Random hex string
        """
        return secrets.token_hex(length)

    @staticmethod
    def token_urlsafe(length: int = 32) -> str:
        """
        Generate URL-safe random string.

        Args:
            length: Number of bytes to generate

        Returns:
            URL-safe random string
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def randint(min_val: int, max_val: int) -> int:
        """
        Generate random integer in range.

        Args:
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)

        Returns:
            Random integer
        """
        return secrets.randbelow(max_val - min_val + 1) + min_val

    @staticmethod
    def choice(sequence: list) -> Any:
        """
        Choose random element from sequence.

        Args:
            sequence: Sequence to choose from

        Returns:
            Random element
        """
        return secrets.choice(sequence)


class SymmetricEncryption:
    """Symmetric encryption using Fernet (AES-128 in CBC mode with HMAC)."""
    
    def __init__(self, key: Optional[bytes] = None) -> None:
        """
        Initialize symmetric encryption.

        Args:
            key: Encryption key (32 bytes) or None to generate new key
        """
            
        if key is None:
            key = Fernet.generate_key()
        
        self.key = key
        self._fernet = Fernet(key)

    @classmethod
    def generate_key(cls) -> bytes:
        """Generate new encryption key."""
        return Fernet.generate_key()

    @classmethod
    def derive_key_from_password(cls, password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """
        Derive encryption key from password using PBKDF2.

        Args:
            password: Password string
            salt: Salt bytes (16 bytes) or None to generate new salt

        Returns:
            Tuple of (key, salt)
        """
            
        if salt is None:
            salt = secrets.token_bytes(16)
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = b64encode(kdf.derive(password.encode('utf-8')))
        return key, salt

    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """
        Encrypt data.

        Args:
            data: Data to encrypt

        Returns:
            Encrypted data
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self._fernet.encrypt(data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data.

        Args:
            encrypted_data: Encrypted data

        Returns:
            Decrypted data
        """
        return self._fernet.decrypt(encrypted_data)

    def encrypt_string(self, text: str) -> str:
        """
        Encrypt string and return base64 encoded result.

        Args:
            text: Text to encrypt

        Returns:
            Base64 encoded encrypted text
        """
        encrypted = self.encrypt(text.encode('utf-8'))
        return b64encode(encrypted).decode('ascii')

    def decrypt_string(self, encrypted_text: str) -> str:
        """
        Decrypt base64 encoded encrypted string.

        Args:
            encrypted_text: Base64 encoded encrypted text

        Returns:
            Decrypted text
        """
        encrypted_data = b64decode(encrypted_text.encode('ascii'))
        decrypted = self.decrypt(encrypted_data)
        return decrypted.decode('utf-8')


class AsymmetricEncryption:
    """Asymmetric (RSA) encryption for secure key exchange and digital signatures."""
    
    def __init__(self, private_key: Optional[bytes] = None, public_key: Optional[bytes] = None) -> None:
        """
        Initialize asymmetric encryption.

        Args:
            private_key: Private key in PEM format
            public_key: Public key in PEM format
        """
            
        self.private_key = None
        self.public_key = None
        
        if private_key:
            self.private_key = serialization.load_pem_private_key(private_key, password=None)
            
        if public_key:
            self.public_key = serialization.load_pem_public_key(public_key)

    @classmethod
    def generate_key_pair(cls, key_size: int = 2048) -> tuple['AsymmetricEncryption', bytes, bytes]:
        """
        Generate new RSA key pair.

        Args:
            key_size: RSA key size in bits

        Returns:
            Tuple of (encryption instance, private_key_pem, public_key_pem)
        """
            
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        instance = cls(private_pem, public_pem)
        return instance, private_pem, public_pem

    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """
        Encrypt data with public key.

        Args:
            data: Data to encrypt

        Returns:
            Encrypted data
        """
        if not self.public_key:
            raise CryptographicError("Public key not available for encryption")
            
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        return self.public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data with private key.

        Args:
            encrypted_data: Encrypted data

        Returns:
            Decrypted data
        """
        if not self.private_key:
            raise CryptographicError("Private key not available for decryption")
            
        return self.private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def sign(self, data: Union[str, bytes]) -> bytes:
        """
        Sign data with private key.

        Args:
            data: Data to sign

        Returns:
            Digital signature
        """
        if not self.private_key:
            raise CryptographicError("Private key not available for signing")
            
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        return self.private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

    def verify(self, data: Union[str, bytes], signature: bytes) -> bool:
        """
        Verify signature with public key.

        Args:
            data: Original data
            signature: Digital signature

        Returns:
            True if signature is valid
        """
        if not self.public_key:
            raise CryptographicError("Public key not available for verification")
            
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        try:
            self.public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False


class SecureStorage:
    """Secure storage for sensitive data with encryption and integrity protection."""
    
    def __init__(self, key: Optional[bytes] = None) -> None:
        """
        Initialize secure storage.

        Args:
            key: Encryption key or None to generate new key
        """
        self.encryption = SymmetricEncryption(key)
        self._storage: dict[str, dict[str, Any]] = {}

    def store(self, key: str, value: Any, metadata: Optional[dict[str, Any]] = None) -> None:
        """
        Store value securely.

        Args:
            key: Storage key
            value: Value to store
            metadata: Optional metadata
        """
        # Serialize value
        import json
        value_json = json.dumps(value)
        
        # Encrypt value
        encrypted_value = self.encryption.encrypt_string(value_json)
        
        # Store with metadata
        self._storage[key] = {
            'value': encrypted_value,
            'metadata': metadata or {},
            'timestamp': time.time(),
        }

    def retrieve(self, key: str) -> Any:
        """
        Retrieve value securely.

        Args:
            key: Storage key

        Returns:
            Stored value

        Raises:
            KeyError: If key not found
        """
        if key not in self._storage:
            raise KeyError(f"Key not found: {key}")
            
        entry = self._storage[key]
        encrypted_value = entry['value']
        
        # Decrypt value
        value_json = self.encryption.decrypt_string(encrypted_value)
        
        # Deserialize value
        import json
        return json.loads(value_json)

    def exists(self, key: str) -> bool:
        """Check if key exists in storage."""
        return key in self._storage

    def delete(self, key: str) -> bool:
        """
        Delete key from storage.

        Args:
            key: Storage key

        Returns:
            True if key was deleted, False if not found
        """
        if key in self._storage:
            del self._storage[key]
            return True
        return False

    def list_keys(self) -> list[str]:
        """Get list of all storage keys."""
        return list(self._storage.keys())

    def get_metadata(self, key: str) -> dict[str, Any]:
        """
        Get metadata for a key.

        Args:
            key: Storage key

        Returns:
            Metadata dictionary

        Raises:
            KeyError: If key not found
        """
        if key not in self._storage:
            raise KeyError(f"Key not found: {key}")
            
        return self._storage[key]['metadata'].copy()

    def clear(self) -> None:
        """Clear all stored data."""
        self._storage.clear()


# Convenience functions
def hash_password(password: str, rounds: int = 12) -> str:
    """
    Hash password using bcrypt (secure, slow hashing).
    
    This replaces the previous insecure SHA-256 + salt implementation.
    Bcrypt is specifically designed for password hashing with:
    - Built-in salt generation
    - Configurable work factor (rounds)
    - Resistance to rainbow table attacks
    - Time-tested security

    Args:
        password: Password to hash
        rounds: Cost factor (4-31, default 12). Higher = more secure but slower

    Returns:
        Bcrypt hash string (includes salt and cost factor)
        
    Raises:
        CryptographicError: If bcrypt is not available
    """
    return _hash_password_pbkdf2(password)
    
    if not (4 <= rounds <= 31):
        raise CryptographicError("bcrypt rounds must be between 4 and 31")
    
    # Convert password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=rounds)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify password against bcrypt hash.

    Args:
        password: Password to verify
        hashed_password: Stored bcrypt hash

    Returns:
        True if password is correct
        
    Raises:
        CryptographicError: If bcrypt is not available and hash is not PBKDF2 format
    """
    # Check if it's a PBKDF2 hash (fallback format)
    if hashed_password.startswith('pbkdf2:'):
        return _verify_password_pbkdf2(password, hashed_password)
    
    try:
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError as e:
        logger.warning(f"Invalid bcrypt hash format: {e}")
        return False


def _hash_password_pbkdf2(password: str) -> str:
    """
    Fallback password hashing using PBKDF2 when bcrypt is not available.
    
    Args:
        password: Password to hash
        
    Returns:
        PBKDF2 hash string with format: pbkdf2:iterations:salt:hash
    """
    # cryptography is now required
    
    # Generate random salt
    salt = secrets.token_bytes(32)
    iterations = 100000  # OWASP recommended minimum
    
    # Derive key using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    key = kdf.derive(password.encode('utf-8'))
    
    # Format: pbkdf2:iterations:salt:hash (all base64 encoded)
    salt_b64 = b64encode(salt).decode('ascii')
    key_b64 = b64encode(key).decode('ascii')
    
    return f"pbkdf2:{iterations}:{salt_b64}:{key_b64}"


def _verify_password_pbkdf2(password: str, hashed_password: str) -> bool:
    """
    Verify password against PBKDF2 hash (fallback).
    
    Args:
        password: Password to verify
        hashed_password: PBKDF2 hash string
        
    Returns:
        True if password is correct
    """
    # cryptography is now required
    
    try:
        # Parse hash format: pbkdf2:iterations:salt:hash
        parts = hashed_password.split(':')
        if len(parts) != 4 or parts[0] != 'pbkdf2':
            return False
        
        iterations = int(parts[1])
        salt = b64decode(parts[2].encode('ascii'))
        expected_key = b64decode(parts[3].encode('ascii'))
        
        # Derive key using same parameters
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=len(expected_key),
            salt=salt,
            iterations=iterations,
        )
        derived_key = kdf.derive(password.encode('utf-8'))
        
        # Constant-time comparison
        return hmac.compare_digest(derived_key, expected_key)
        
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid PBKDF2 hash format: {e}")
        return False


def generate_api_key(length: int = 32) -> str:
    """Generate secure API key."""
    return SecureRandom.token_urlsafe(length)


def generate_session_token(length: int = 32) -> str:
    """Generate secure session token."""
    return SecureRandom.token_urlsafe(length)


# Async security operations
async def hash_password_async(password: str, rounds: int = 12) -> str:
    """
    Async version of hash_password using thread pool.
    
    Args:
        password: Password to hash
        rounds: Cost factor (4-31, default 12)
        
    Returns:
        Bcrypt hash string
    """
    import asyncio
    return await asyncio.to_thread(hash_password, password, rounds)


async def verify_password_async(password: str, hashed_password: str) -> bool:
    """
    Async version of verify_password using thread pool.
    
    Args:
        password: Password to verify
        hashed_password: Stored bcrypt hash
        
    Returns:
        True if password is correct
    """
    import asyncio
    return await asyncio.to_thread(verify_password, password, hashed_password)


class AsyncSecureStorage:
    """Async version of SecureStorage for non-blocking operations."""
    
    def __init__(self, key: Optional[bytes] = None) -> None:
        """Initialize async secure storage."""
        self._storage = SecureStorage(key)
    
    async def store(self, key: str, value: Any, metadata: Optional[dict[str, Any]] = None) -> None:
        """Store value securely (async)."""
        import asyncio
        await asyncio.to_thread(self._storage.store, key, value, metadata)
    
    async def retrieve(self, key: str) -> Any:
        """Retrieve value securely (async)."""
        import asyncio
        return await asyncio.to_thread(self._storage.retrieve, key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists (async)."""
        import asyncio
        return await asyncio.to_thread(self._storage.exists, key)
    
    async def delete(self, key: str) -> bool:
        """Delete key from storage (async)."""
        import asyncio
        return await asyncio.to_thread(self._storage.delete, key)
    
    async def list_keys(self) -> list[str]:
        """Get list of all storage keys (async)."""
        import asyncio
        return await asyncio.to_thread(self._storage.list_keys)
    
    async def get_metadata(self, key: str) -> dict[str, Any]:
        """Get metadata for a key (async)."""
        import asyncio
        return await asyncio.to_thread(self._storage.get_metadata, key)
    
    async def clear(self) -> None:
        """Clear all stored data (async)."""
        import asyncio
        await asyncio.to_thread(self._storage.clear)


class AsyncSymmetricEncryption:
    """Async version of SymmetricEncryption for non-blocking operations."""
    
    def __init__(self, key: Optional[bytes] = None) -> None:
        """Initialize async symmetric encryption."""
        self._encryption = SymmetricEncryption(key)
    
    @property
    def key(self) -> bytes:
        """Get the encryption key."""
        return self._encryption.key
    
    async def encrypt(self, data: Union[str, bytes]) -> bytes:
        """Encrypt data (async)."""
        import asyncio
        return await asyncio.to_thread(self._encryption.encrypt, data)
    
    async def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data (async)."""
        import asyncio
        return await asyncio.to_thread(self._encryption.decrypt, encrypted_data)
    
    async def encrypt_string(self, text: str) -> str:
        """Encrypt string and return base64 encoded result (async)."""
        import asyncio
        return await asyncio.to_thread(self._encryption.encrypt_string, text)
    
    async def decrypt_string(self, encrypted_text: str) -> str:
        """Decrypt base64 encoded encrypted string (async)."""
        import asyncio
        return await asyncio.to_thread(self._encryption.decrypt_string, encrypted_text)


class AsyncAsymmetricEncryption:
    """Async version of AsymmetricEncryption for non-blocking operations."""
    
    def __init__(self, private_key: Optional[bytes] = None, public_key: Optional[bytes] = None) -> None:
        """Initialize async asymmetric encryption."""
        self._encryption = AsymmetricEncryption(private_key, public_key)
    
    @classmethod
    async def generate_key_pair_async(cls, key_size: int = 2048) -> tuple['AsyncAsymmetricEncryption', bytes, bytes]:
        """Generate new RSA key pair (async)."""
        import asyncio
        encryption, private_pem, public_pem = await asyncio.to_thread(
            AsymmetricEncryption.generate_key_pair, key_size
        )
        async_encryption = cls(private_pem, public_pem)
        return async_encryption, private_pem, public_pem
    
    async def encrypt(self, data: Union[str, bytes]) -> bytes:
        """Encrypt data with public key (async)."""
        import asyncio
        return await asyncio.to_thread(self._encryption.encrypt, data)
    
    async def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data with private key (async)."""
        import asyncio
        return await asyncio.to_thread(self._encryption.decrypt, encrypted_data)
    
    async def sign(self, data: Union[str, bytes]) -> bytes:
        """Sign data with private key (async)."""
        import asyncio
        return await asyncio.to_thread(self._encryption.sign, data)
    
    async def verify(self, data: Union[str, bytes], signature: bytes) -> bool:
        """Verify signature with public key (async)."""
        import asyncio
        return await asyncio.to_thread(self._encryption.verify, data, signature)
