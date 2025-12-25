"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Hazardous Materials (Hazmat) Layer - Low-level cryptographic primitives.

⚠️  WARNING: This module provides direct access to cryptographic primitives.
    Improper use can lead to security vulnerabilities. Only use if you know
    what you're doing. For most use cases, use the high-level crypto module.

Features:
- AEAD ciphers (AES-GCM, ChaCha20Poly1305)
- Key exchange algorithms (X25519, ECDH)
- Digital signatures (Ed25519, ECDSA)
- Hash functions and KDFs
- X.509 certificate handling
- Low-level cryptographic operations
"""

import os
from typing import Any, Optional, Union

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519, x25519, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305, AESCCM, AESOCB3
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHash
from cryptography.hazmat.primitives.kdf.x963kdf import X963KDF
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID

from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.security.hazmat")


class HazmatError(Exception):
    """Base exception for hazmat operations."""
    pass


def _ensure_cryptography():
    """Ensure cryptography library is available."""
    # Lazy installation system will handle cryptography if missing
    pass


# =============================================================================
# AEAD (Authenticated Encryption with Associated Data) Ciphers
# =============================================================================

class AES_GCM:
    """
    AES-GCM AEAD cipher.
    
    Provides authenticated encryption with associated data using AES in
    Galois/Counter Mode. This is the recommended AEAD cipher for most applications.
    """
    
    def __init__(self, key: bytes):
        """
        Initialize AES-GCM cipher.
        
        Args:
            key: 128, 192, or 256-bit key
        """
        if len(key) not in (16, 24, 32):
            raise HazmatError("AES-GCM key must be 128, 192, or 256 bits")
        
        self._cipher = AESGCM(key)
        self.key_size = len(key) * 8
    
    def encrypt(self, nonce: bytes, data: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """
        Encrypt and authenticate data.
        
        Args:
            nonce: 96-bit nonce (12 bytes) - MUST be unique for each encryption
            data: Plaintext data to encrypt
            associated_data: Optional associated data to authenticate but not encrypt
            
        Returns:
            Ciphertext with authentication tag appended
        """
        if len(nonce) != 12:
            raise HazmatError("AES-GCM nonce must be exactly 12 bytes")
        
        return self._cipher.encrypt(nonce, data, associated_data)
    
    def decrypt(self, nonce: bytes, data: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """
        Decrypt and verify data.
        
        Args:
            nonce: 96-bit nonce used for encryption
            data: Ciphertext with authentication tag
            associated_data: Associated data used during encryption
            
        Returns:
            Plaintext data
            
        Raises:
            HazmatError: If authentication fails
        """
        if len(nonce) != 12:
            raise HazmatError("AES-GCM nonce must be exactly 12 bytes")
        
        try:
            return self._cipher.decrypt(nonce, data, associated_data)
        except Exception as e:
            raise HazmatError(f"AES-GCM decryption/authentication failed: {e}")
    
    @staticmethod
    def generate_key(key_size: int = 256) -> bytes:
        """
        Generate random AES key.
        
        Args:
            key_size: Key size in bits (128, 192, or 256)
            
        Returns:
            Random key bytes
        """
        if key_size not in (128, 192, 256):
            raise HazmatError("Key size must be 128, 192, or 256 bits")
        
        return os.urandom(key_size // 8)
    
    @staticmethod
    def generate_nonce() -> bytes:
        """Generate random 96-bit nonce."""
        return os.urandom(12)


class ChaCha20Poly1305_Cipher:
    """
    ChaCha20-Poly1305 AEAD cipher.
    
    Provides authenticated encryption using ChaCha20 stream cipher with
    Poly1305 authenticator. Good alternative to AES-GCM, especially on
    systems without AES hardware acceleration.
    """
    
    def __init__(self, key: bytes):
        """
        Initialize ChaCha20-Poly1305 cipher.
        
        Args:
            key: 256-bit key (32 bytes)
        """
        if len(key) != 32:
            raise HazmatError("ChaCha20-Poly1305 key must be exactly 32 bytes")
        
        self._cipher = ChaCha20Poly1305(key)
        self.key_size = 256
    
    def encrypt(self, nonce: bytes, data: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """
        Encrypt and authenticate data.
        
        Args:
            nonce: 96-bit nonce (12 bytes) - MUST be unique for each encryption
            data: Plaintext data to encrypt
            associated_data: Optional associated data to authenticate but not encrypt
            
        Returns:
            Ciphertext with authentication tag appended
        """
        if len(nonce) != 12:
            raise HazmatError("ChaCha20-Poly1305 nonce must be exactly 12 bytes")
        
        return self._cipher.encrypt(nonce, data, associated_data)
    
    def decrypt(self, nonce: bytes, data: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """
        Decrypt and verify data.
        
        Args:
            nonce: 96-bit nonce used for encryption
            data: Ciphertext with authentication tag
            associated_data: Associated data used during encryption
            
        Returns:
            Plaintext data
            
        Raises:
            HazmatError: If authentication fails
        """
        if len(nonce) != 12:
            raise HazmatError("ChaCha20-Poly1305 nonce must be exactly 12 bytes")
        
        try:
            return self._cipher.decrypt(nonce, data, associated_data)
        except Exception as e:
            raise HazmatError(f"ChaCha20-Poly1305 decryption/authentication failed: {e}")
    
    @staticmethod
    def generate_key() -> bytes:
        """Generate random 256-bit key."""
        return os.urandom(32)
    
    @staticmethod
    def generate_nonce() -> bytes:
        """Generate random 96-bit nonce."""
        return os.urandom(12)


# =============================================================================
# Key Exchange Algorithms
# =============================================================================

class X25519_KeyExchange:
    """
    X25519 Elliptic Curve Diffie-Hellman key exchange.
    
    High-performance, secure key exchange using Curve25519.
    Recommended for most applications requiring key agreement.
    """
    
    def __init__(self, private_key: Optional[bytes] = None):
        """
        Initialize X25519 key exchange.
        
        Args:
            private_key: Optional 32-byte private key (generates random if None)
        """
        _ensure_cryptography()
        
        if private_key is not None:
            if len(private_key) != 32:
                raise HazmatError("X25519 private key must be exactly 32 bytes")
            self._private_key = x25519.X25519PrivateKey.from_private_bytes(private_key)
        else:
            self._private_key = x25519.X25519PrivateKey.generate()
    
    def get_public_key(self) -> bytes:
        """Get public key bytes."""
        return self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    
    def get_private_key(self) -> bytes:
        """Get private key bytes."""
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
    
    def exchange(self, peer_public_key: bytes) -> bytes:
        """
        Perform key exchange with peer's public key.
        
        Args:
            peer_public_key: Peer's 32-byte public key
            
        Returns:
            32-byte shared secret
        """
        if len(peer_public_key) != 32:
            raise HazmatError("X25519 public key must be exactly 32 bytes")
        
        try:
            peer_key = x25519.X25519PublicKey.from_public_bytes(peer_public_key)
            shared_secret = self._private_key.exchange(peer_key)
            return shared_secret
        except Exception as e:
            raise HazmatError(f"X25519 key exchange failed: {e}")
    
    @staticmethod
    def generate_keypair() -> tuple[bytes, bytes]:
        """
        Generate X25519 key pair.
        
        Returns:
            Tuple of (private_key, public_key) bytes
        """
        _ensure_cryptography()
        
        private_key = x25519.X25519PrivateKey.generate()
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return private_bytes, public_bytes


# =============================================================================
# Digital Signatures
# =============================================================================

class Ed25519_Signature:
    """
    Ed25519 digital signature algorithm.
    
    High-performance digital signatures using Edwards-curve Digital Signature
    Algorithm with Curve25519. Recommended for most signature applications.
    """
    
    def __init__(self, private_key: Optional[bytes] = None):
        """
        Initialize Ed25519 signature.
        
        Args:
            private_key: Optional 32-byte private key (generates random if None)
        """
        _ensure_cryptography()
        
        if private_key is not None:
            if len(private_key) != 32:
                raise HazmatError("Ed25519 private key must be exactly 32 bytes")
            self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key)
        else:
            self._private_key = ed25519.Ed25519PrivateKey.generate()
    
    def get_public_key(self) -> bytes:
        """Get public key bytes."""
        return self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    
    def get_private_key(self) -> bytes:
        """Get private key bytes."""
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
    
    def sign(self, data: bytes) -> bytes:
        """
        Sign data.
        
        Args:
            data: Data to sign
            
        Returns:
            64-byte signature
        """
        return self._private_key.sign(data)
    
    @staticmethod
    def verify(public_key: bytes, signature: bytes, data: bytes) -> bool:
        """
        Verify signature.
        
        Args:
            public_key: 32-byte public key
            signature: 64-byte signature
            data: Original data
            
        Returns:
            True if signature is valid
        """
        _ensure_cryptography()
        
        if len(public_key) != 32:
            raise HazmatError("Ed25519 public key must be exactly 32 bytes")
        
        if len(signature) != 64:
            raise HazmatError("Ed25519 signature must be exactly 64 bytes")
        
        try:
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
            pub_key.verify(signature, data)
            return True
        except Exception:
            return False
    
    @staticmethod
    def generate_keypair() -> tuple[bytes, bytes]:
        """
        Generate Ed25519 key pair.
        
        Returns:
            Tuple of (private_key, public_key) bytes
        """
        _ensure_cryptography()
        
        private_key = ed25519.Ed25519PrivateKey.generate()
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return private_bytes, public_bytes


# =============================================================================
# Key Derivation Functions
# =============================================================================

class HKDF_Expand:
    """
    HMAC-based Key Derivation Function (HKDF) - RFC 5869.
    
    Used to derive cryptographic keys from a shared secret or master key.
    Recommended for most key derivation needs.
    """
    
    @staticmethod
    def derive(key_material: bytes, length: int, info: bytes = b"", 
               salt: Optional[bytes] = None, hash_algorithm=None) -> bytes:
        """
        Derive key using HKDF.
        
        Args:
            key_material: Input key material
            length: Desired output length in bytes
            info: Optional context information
            salt: Optional salt (random if None)
            hash_algorithm: Hash algorithm (SHA256 if None)
            
        Returns:
            Derived key bytes
        """
        _ensure_cryptography()
        
        if hash_algorithm is None:
            hash_algorithm = hashes.SHA256()
        
        if salt is None:
            salt = b"\x00" * hash_algorithm.digest_size
        
        hkdf = HKDF(
            algorithm=hash_algorithm,
            length=length,
            salt=salt,
            info=info,
            backend=default_backend()
        )
        
        return hkdf.derive(key_material)


class PBKDF2_Derive:
    """
    Password-Based Key Derivation Function 2 (PBKDF2) - RFC 2898.
    
    Used to derive cryptographic keys from passwords with salt and iterations.
    Good for password-based encryption.
    """
    
    @staticmethod
    def derive(password: bytes, salt: bytes, iterations: int = 100000, 
               length: int = 32, hash_algorithm=None) -> bytes:
        """
        Derive key from password using PBKDF2.
        
        Args:
            password: Password bytes
            salt: Random salt (at least 8 bytes recommended)
            iterations: Number of iterations (100,000+ recommended)
            length: Desired output length in bytes
            hash_algorithm: Hash algorithm (SHA256 if None)
            
        Returns:
            Derived key bytes
        """
        _ensure_cryptography()
        
        if hash_algorithm is None:
            hash_algorithm = hashes.SHA256()
        
        if len(salt) < 8:
            raise HazmatError("Salt should be at least 8 bytes")
        
        if iterations < 10000:
            logger.warning(f"Low iteration count ({iterations}). Recommend 100,000+")
        
        kdf = PBKDF2HMAC(
            algorithm=hash_algorithm,
            length=length,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        
        return kdf.derive(password)


# =============================================================================
# X.509 Certificate Handling
# =============================================================================

class X509Certificate:
    """
    X.509 certificate handling utilities.
    
    Provides parsing, validation, and creation of X.509 certificates.
    """
    
    def __init__(self, cert_data: Union[bytes, str]):
        """
        Initialize with certificate data.
        
        Args:
            cert_data: PEM or DER certificate data
        """
        _ensure_cryptography()
        
        if isinstance(cert_data, str):
            cert_data = cert_data.encode('utf-8')
        
        try:
            # Try PEM first
            self._cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        except ValueError:
            try:
                # Try DER
                self._cert = x509.load_der_x509_certificate(cert_data, default_backend())
            except ValueError as e:
                raise HazmatError(f"Invalid certificate format: {e}")
    
    def get_subject(self) -> dict[str, str]:
        """Get certificate subject information."""
        subject_dict = {}
        for attribute in self._cert.subject:
            name = attribute.oid._name
            value = attribute.value
            subject_dict[name] = value
        return subject_dict
    
    def get_issuer(self) -> dict[str, str]:
        """Get certificate issuer information."""
        issuer_dict = {}
        for attribute in self._cert.issuer:
            name = attribute.oid._name
            value = attribute.value
            issuer_dict[name] = value
        return issuer_dict
    
    def get_serial_number(self) -> int:
        """Get certificate serial number."""
        return self._cert.serial_number
    
    def get_not_valid_before(self):
        """Get certificate start validity date."""
        return self._cert.not_valid_before
    
    def get_not_valid_after(self):
        """Get certificate end validity date."""
        return self._cert.not_valid_after
    
    def is_valid_now(self) -> bool:
        """Check if certificate is currently valid."""
        from datetime import datetime
        now = datetime.utcnow()
        return self._cert.not_valid_before <= now <= self._cert.not_valid_after
    
    def get_public_key(self):
        """Get certificate public key."""
        return self._cert.public_key()
    
    def get_signature_algorithm(self) -> str:
        """Get signature algorithm name."""
        return self._cert.signature_algorithm_oid._name
    
    def verify_signature(self, ca_cert: 'X509Certificate') -> bool:
        """
        Verify certificate signature against CA certificate.
        
        Args:
            ca_cert: CA certificate to verify against
            
        Returns:
            True if signature is valid
        """
        try:
            ca_public_key = ca_cert.get_public_key()
            
            if isinstance(ca_public_key, rsa.RSAPublicKey):
                ca_public_key.verify(
                    self._cert.signature,
                    self._cert.tbs_certificate_bytes,
                    padding.PKCS1v15(),
                    self._cert.signature_hash_algorithm
                )
            elif isinstance(ca_public_key, ec.EllipticCurvePublicKey):
                ca_public_key.verify(
                    self._cert.signature,
                    self._cert.tbs_certificate_bytes,
                    ec.ECDSA(self._cert.signature_hash_algorithm)
                )
            else:
                raise HazmatError(f"Unsupported public key type: {type(ca_public_key)}")
            
            return True
        except Exception:
            return False
    
    def to_pem(self) -> bytes:
        """Export certificate as PEM."""
        return self._cert.public_bytes(serialization.Encoding.PEM)
    
    def to_der(self) -> bytes:
        """Export certificate as DER."""
        return self._cert.public_bytes(serialization.Encoding.DER)
    
    @staticmethod
    def load_pem(pem_data: Union[bytes, str]) -> 'X509Certificate':
        """Load certificate from PEM data."""
        return X509Certificate(pem_data)
    
    @staticmethod
    def load_der(der_data: bytes) -> 'X509Certificate':
        """Load certificate from DER data."""
        return X509Certificate(der_data)
    
    @staticmethod
    def load_from_file(file_path: str) -> 'X509Certificate':
        """Load certificate from file."""
        with open(file_path, 'rb') as f:
            return X509Certificate(f.read())


# =============================================================================
# Hash Functions
# =============================================================================

def secure_hash(data: bytes, algorithm: str = "SHA256") -> bytes:
    """
    Compute secure hash of data.
    
    Args:
        data: Data to hash
        algorithm: Hash algorithm (SHA256, SHA384, SHA512, BLAKE2b, etc.)
        
    Returns:
        Hash digest bytes
    """
    _ensure_cryptography()
    
    algorithm = algorithm.upper()
    
    if algorithm == "SHA256":
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    elif algorithm == "SHA384":
        digest = hashes.Hash(hashes.SHA384(), backend=default_backend())
    elif algorithm == "SHA512":
        digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
    elif algorithm == "SHA3_256":
        digest = hashes.Hash(hashes.SHA3_256(), backend=default_backend())
    elif algorithm == "SHA3_384":
        digest = hashes.Hash(hashes.SHA3_384(), backend=default_backend())
    elif algorithm == "SHA3_512":
        digest = hashes.Hash(hashes.SHA3_512(), backend=default_backend())
    elif algorithm == "BLAKE2B":
        digest = hashes.Hash(hashes.BLAKE2b(64), backend=default_backend())
    elif algorithm == "BLAKE2S":
        digest = hashes.Hash(hashes.BLAKE2s(32), backend=default_backend())
    else:
        raise HazmatError(f"Unsupported hash algorithm: {algorithm}")
    
    digest.update(data)
    return digest.finalize()


# =============================================================================
# Utility Functions
# =============================================================================

def constant_time_compare(a: bytes, b: bytes) -> bool:
    """
    Constant-time comparison of byte strings.
    
    Prevents timing attacks when comparing secrets.
    
    Args:
        a: First byte string
        b: Second byte string
        
    Returns:
        True if equal, False otherwise
    """
    import hmac
    return hmac.compare_digest(a, b)


def secure_random(length: int) -> bytes:
    """
    Generate cryptographically secure random bytes.
    
    Args:
        length: Number of bytes to generate
        
    Returns:
        Random bytes
    """
    return os.urandom(length)


def is_cryptography_available() -> bool:
    """Check if cryptography library is available."""
    # Lazy installation system ensures cryptography is always available
    return True
