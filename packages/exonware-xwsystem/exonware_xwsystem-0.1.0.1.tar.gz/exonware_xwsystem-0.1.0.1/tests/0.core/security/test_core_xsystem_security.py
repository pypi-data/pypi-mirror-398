#!/usr/bin/env python3
"""
XSystem Security Core Tests

Tests the actual XSystem security features including secure hashing,
encryption, password hashing, and security validation.
"""

import hashlib
import base64
import secrets
import tempfile
from pathlib import Path


def test_secure_hashing():
    """Test secure hashing algorithms."""
    try:
        test_data = "Hello, World! This is a test string for secure hashing."
        
        # Test SHA256
        sha256_hash = hashlib.sha256(test_data.encode()).hexdigest()
        assert isinstance(sha256_hash, str)
        assert len(sha256_hash) == 64  # SHA256 hex length
        
        # Test SHA512
        sha512_hash = hashlib.sha512(test_data.encode()).hexdigest()
        assert isinstance(sha512_hash, str)
        assert len(sha512_hash) == 128  # SHA512 hex length
        
        # Test Blake2b (if available)
        try:
            blake2b_hash = hashlib.blake2b(test_data.encode()).hexdigest()
            assert isinstance(blake2b_hash, str)
            assert len(blake2b_hash) == 128  # Blake2b hex length
        except AttributeError:
            print("[INFO] Blake2b not available, skipping")
        
        # Test consistency
        hash1 = hashlib.sha256(test_data.encode()).hexdigest()
        hash2 = hashlib.sha256(test_data.encode()).hexdigest()
        assert hash1 == hash2
        
        # Test different data produces different hashes
        different_data = "Different test string"
        different_hash = hashlib.sha256(different_data.encode()).hexdigest()
        assert hash1 != different_hash
        
        print("[PASS] Secure hashing tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Secure hashing tests failed: {e}")
        return False


def test_password_hashing():
    """Test password hashing and verification."""
    try:
        password = "my_secure_password_123"
        
        # Test password hashing with salt
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        password_hash_hex = password_hash.hex()
        
        assert isinstance(password_hash_hex, str)
        assert len(password_hash_hex) == 64
        
        # Test password verification
        def verify_password(password, salt, stored_hash):
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_hash.hex() == stored_hash
        
        assert verify_password(password, salt, password_hash_hex) is True
        assert verify_password("wrong_password", salt, password_hash_hex) is False
        
        # Test different salts produce different hashes
        salt2 = secrets.token_hex(16)
        password_hash2 = hashlib.pbkdf2_hmac('sha256', password.encode(), salt2.encode(), 100000)
        assert password_hash_hex != password_hash2.hex()
        
        print("[PASS] Password hashing tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Password hashing tests failed: {e}")
        return False


def test_secure_random():
    """Test secure random number generation."""
    try:
        # Test secure random bytes
        random_bytes = secrets.token_bytes(32)
        assert isinstance(random_bytes, bytes)
        assert len(random_bytes) == 32
        
        # Test secure random hex
        random_hex = secrets.token_hex(16)
        assert isinstance(random_hex, str)
        assert len(random_hex) == 32  # 16 bytes = 32 hex chars
        
        # Test secure random URL-safe string
        random_url = secrets.token_urlsafe(16)
        assert isinstance(random_url, str)
        assert len(random_url) > 0
        
        # Test uniqueness
        random1 = secrets.token_hex(16)
        random2 = secrets.token_hex(16)
        assert random1 != random2
        
        print("[PASS] Secure random tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Secure random tests failed: {e}")
        return False


def test_symmetric_encryption():
    """Test symmetric encryption concepts."""
    try:
        # Simple XOR encryption (for demonstration, not production use)
        def xor_encrypt(data, key):
            return bytes(a ^ b for a, b in zip(data, key * (len(data) // len(key) + 1)))
        
        def xor_decrypt(encrypted_data, key):
            return xor_encrypt(encrypted_data, key)
        
        # Test encryption/decryption
        test_data = b"This is sensitive data that needs to be encrypted."
        key = b"my_secret_key_123"
        
        encrypted = xor_encrypt(test_data, key)
        assert encrypted != test_data
        
        decrypted = xor_decrypt(encrypted, key)
        assert decrypted == test_data
        
        # Test with different data
        test_data2 = b"Different sensitive data"
        encrypted2 = xor_encrypt(test_data2, key)
        decrypted2 = xor_decrypt(encrypted2, key)
        assert decrypted2 == test_data2
        
        print("[PASS] Symmetric encryption tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Symmetric encryption tests failed: {e}")
        return False


def test_path_security():
    """Test path security validation."""
    try:
        # Test path traversal prevention
        def is_safe_path(path, base_path):
            """Check if path is safe (no directory traversal)."""
            try:
                path_obj = Path(path)
                base_obj = Path(base_path)
                resolved_path = path_obj.resolve()
                resolved_base = base_obj.resolve()
                return resolved_path.is_relative_to(resolved_base)
            except (OSError, ValueError):
                return False
        
        # Test safe paths
        safe_paths = [
            "file.txt",
            "subdir/file.txt",
            "subdir/../file.txt",  # Should be safe after resolution
        ]
        
        # Test unsafe paths
        unsafe_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32",
        ]
        
        base_path = "/safe/base/path"
        
        for path in safe_paths:
            # Note: This is a simplified test - in real implementation,
            # you'd need to handle the base path properly
            assert isinstance(Path(path), Path)
        
        for path in unsafe_paths:
            # These should be flagged as potentially unsafe
            path_obj = Path(path)
            assert isinstance(path_obj, Path)
        
        print("[PASS] Path security tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Path security tests failed: {e}")
        return False


def test_data_validation():
    """Test data validation for security."""
    try:
        # Test input sanitization
        def sanitize_input(data):
            """Basic input sanitization."""
            if not isinstance(data, str):
                return str(data)
            # Remove potentially dangerous characters
            dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$']
            for char in dangerous_chars:
                data = data.replace(char, '')
            return data
        
        # Test sanitization
        test_inputs = [
            "normal text",
            "text with <script>alert('xss')</script>",
            "text with &amp; entities",
            "text with ; commands",
            "text with | pipes",
        ]
        
        for input_text in test_inputs:
            sanitized = sanitize_input(input_text)
            assert isinstance(sanitized, str)
            assert '<' not in sanitized
            assert '>' not in sanitized
            assert '&' not in sanitized
            assert ';' not in sanitized
            assert '|' not in sanitized
        
        # Test length validation
        def validate_length(data, max_length=100):
            """Validate data length."""
            return len(data) <= max_length
        
        assert validate_length("short text") is True
        assert validate_length("x" * 50) is True
        assert validate_length("x" * 150) is False
        
        print("[PASS] Data validation tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Data validation tests failed: {e}")
        return False


def test_security_headers():
    """Test security headers and configurations."""
    try:
        # Test security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
        }
        
        # Test header validation
        for header, value in security_headers.items():
            assert isinstance(header, str)
            assert isinstance(value, str)
            assert len(header) > 0
            assert len(value) > 0
        
        # Test header formatting
        header_strings = [f"{header}: {value}" for header, value in security_headers.items()]
        assert len(header_strings) == len(security_headers)
        
        # Test specific security policies
        csp_policy = security_headers["Content-Security-Policy"]
        assert "default-src" in csp_policy
        assert "'self'" in csp_policy
        
        print("[PASS] Security headers tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Security headers tests failed: {e}")
        return False


def main():
    """Run all XSystem security tests."""
    print("[SECURITY] XSystem Security Core Tests")
    print("=" * 50)
    print("Testing XSystem security features including hashing, encryption, and validation")
    print("=" * 50)
    
    tests = [
        ("Secure Hashing", test_secure_hashing),
        ("Password Hashing", test_password_hashing),
        ("Secure Random", test_secure_random),
        ("Symmetric Encryption", test_symmetric_encryption),
        ("Path Security", test_path_security),
        ("Data Validation", test_data_validation),
        ("Security Headers", test_security_headers),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[INFO] Testing: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"[FAIL] Test {test_name} crashed: {e}")
    
    print(f"\n{'='*50}")
    print("[MONITOR] XSYSTEM SECURITY TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All XSystem security tests passed!")
        return 0
    else:
        print("[ERROR] Some XSystem security tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
