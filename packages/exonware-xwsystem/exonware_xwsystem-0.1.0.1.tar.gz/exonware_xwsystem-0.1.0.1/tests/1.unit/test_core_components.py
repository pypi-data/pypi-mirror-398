"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.3
Generation Date: August 31, 2025

Unit tests for individual core components.
"""

import pytest
from pathlib import Path
import tempfile
import os

from exonware.xwsystem import (
    ThreadSafeFactory,
    PathValidator,
    PathSecurityError,
    AtomicFileWriter,
    CircularReferenceDetector,
    GenericHandlerFactory,
)


@pytest.mark.xwsystem_unit
class TestThreadSafeFactory:
    """Test ThreadSafeFactory functionality in isolation."""
    
    def test_register_and_get_handler(self):
        """Test handler registration and retrieval."""
        factory = ThreadSafeFactory()
        factory.register("test", str, ["txt"])
        
        assert factory.get_handler("test") == str
        assert "test" in factory.get_available_formats()
    
    def test_get_nonexistent_handler(self):
        """Test getting non-existent handler raises KeyError."""
        factory = ThreadSafeFactory()
        with pytest.raises(KeyError):
            factory.get_handler("nonexistent")


@pytest.mark.xwsystem_unit
class TestPathValidator:
    """Test PathValidator functionality in isolation."""
    
    def test_relative_path_validation(self):
        """Test relative path validation."""
        validator = PathValidator(check_existence=False)
        result = validator.validate_path("test/file.txt")
        assert isinstance(result, Path)
    
    def test_absolute_path_restriction(self):
        """Test absolute path restriction."""
        validator = PathValidator(allow_absolute=False, check_existence=False)
        
        with pytest.raises(PathSecurityError, match="Absolute paths not allowed"):
            validator.validate_path("/absolute/path")
    
    def test_base_path_restriction(self):
        """Test base path restriction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = PathValidator(base_path=temp_dir)
            
            # Valid path within base
            result = validator.validate_path("subdir/file.txt")
            assert str(result).startswith(temp_dir)
            
            # Invalid path outside base
            with pytest.raises(ValueError, match="Path outside base directory"):
                validator.validate_path("../../../etc/passwd")


@pytest.mark.xwsystem_unit
class TestAtomicFileWriter:
    """Test AtomicFileWriter functionality in isolation."""
    
    def test_atomic_write_success(self):
        """Test successful atomic write."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_file = Path(temp_dir) / "test.txt"
            content = "Hello, World!"
            
            writer = AtomicFileWriter(target_path=str(target_file))
            writer.write(content.encode('utf-8'))
            
            assert target_file.exists()
            assert target_file.read_text() == content
    
    def test_atomic_write_rollback(self):
        """Test atomic write rollback on failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_file = Path(temp_dir) / "test.txt"
            original_content = "Original content"
            target_file.write_text(original_content)
            
            # Test that original content is preserved on failure
            writer = AtomicFileWriter(target_path=str(target_file))
            try:
                writer.write("New content".encode('utf-8'))
                raise RuntimeError("Simulated failure")
            except RuntimeError:
                pass
            
            assert target_file.exists()
            assert target_file.read_text() == original_content


@pytest.mark.xwsystem_unit
class TestCircularReferenceDetector:
    """Test CircularReferenceDetector functionality in isolation."""
    
    def test_no_circular_references(self):
        """Test detection with no circular references."""
        detector = CircularReferenceDetector()
        data = {"a": 1, "b": 2, "c": {"d": 3}}
        
        assert not detector.has_circular_references(data)
    
    def test_circular_references_detected(self):
        """Test detection of circular references."""
        detector = CircularReferenceDetector()
        
        # Create circular reference
        data = {"a": 1}
        data["self"] = data
        
        assert detector.has_circular_references(data)
    
    def test_max_depth_exceeded(self):
        """Test max depth exceeded handling."""
        detector = CircularReferenceDetector(max_depth=2)
        
        # Create deeply nested structure
        data = {"level1": {"level2": {"level3": {"level4": "deep"}}}}
        
        # Should not raise exception, just return False
        result = detector.has_circular_references(data)
        assert isinstance(result, bool)


@pytest.mark.xwsystem_unit
class TestGenericHandlerFactory:
    """Test GenericHandlerFactory functionality in isolation."""
    
    def test_handler_registration(self):
        """Test handler registration and retrieval."""
        factory = GenericHandlerFactory()
        
        class TestHandler:
            def __init__(self, name):
                self.name = name
        
        factory.register("test", TestHandler)
        handler = factory.create("test", "test_instance")
        
        assert isinstance(handler, TestHandler)
        assert handler.name == "test_instance"
