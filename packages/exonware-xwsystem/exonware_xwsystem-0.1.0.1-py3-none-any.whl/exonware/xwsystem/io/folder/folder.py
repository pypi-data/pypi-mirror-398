"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

XWFolder - Concrete implementation of folder operations.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Optional, Union

from ..base import AFolder
from ..contracts import OperationResult, IFolder
from ...config.logging_setup import get_logger
from ...security.path_validator import PathValidator
from ...monitoring.performance_monitor import performance_monitor

logger = get_logger(__name__)


class XWFolder(AFolder):
    """
    Concrete implementation of folder operations with both static and instance methods.
    
    This class provides a complete, production-ready implementation of folder
    operations with xwsystem integration for security, validation, and monitoring.
    
    Features:
    - Directory I/O operations (create, delete, list, walk)
    - Directory metadata operations (size, permissions, contents)
    - Directory validation and safety checks
    - Static utility methods for directory operations
    - xwsystem integration (security, validation, monitoring)
    """
    
    def __init__(self, dir_path: Union[str, Path], **config):
        """
        Initialize XWFolder with xwsystem integration.
        
        Args:
            dir_path: Path to directory
            **config: Configuration options for directory operations
        """
        super().__init__(dir_path)
        
        # Initialize xwsystem utilities
        self._path_validator = PathValidator()
        
        # Configuration
        self.validate_paths = config.get('validate_paths', True)
        self.enable_monitoring = config.get('enable_monitoring', True)
        self.auto_create_parents = config.get('auto_create_parents', True)
        self.safe_operations = config.get('safe_operations', True)
        
        logger.debug(f"Folder initialized for path: {dir_path}")
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    def create(self, parents: bool = True, exist_ok: bool = True) -> bool:
        """Create directory with validation."""
        if self.validate_paths:
            self._path_validator.validate_path(self.dir_path, for_writing=True, create_dirs=parents)
        
        with performance_monitor("directory_create"):
            try:
                self.dir_path.mkdir(parents=parents, exist_ok=exist_ok)
                logger.debug(f"Directory created: {self.dir_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to create directory {self.dir_path}: {e}")
                return False
    
    def delete(self, recursive: bool = False) -> bool:
        """Delete directory with validation."""
        if self.validate_paths:
            self._path_validator.validate_path(self.dir_path)
        
        with performance_monitor("directory_delete"):
            try:
                if recursive:
                    shutil.rmtree(self.dir_path)
                else:
                    self.dir_path.rmdir()
                logger.debug(f"Directory deleted: {self.dir_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete directory {self.dir_path}: {e}")
                return False
    
    def copy_to(self, destination: Union[str, Path]) -> bool:
        """Copy directory to destination."""
        dest_path = Path(destination)
        
        if self.validate_paths:
            self._path_validator.validate_path(self.dir_path)
            self._path_validator.validate_path(dest_path)
        
        with performance_monitor("directory_copy"):
            try:
                shutil.copytree(self.dir_path, dest_path, dirs_exist_ok=True)
                logger.debug(f"Directory copied from {self.dir_path} to {dest_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to copy directory from {self.dir_path} to {dest_path}: {e}")
                return False
    
    def move_to(self, destination: Union[str, Path]) -> bool:
        """Move directory to destination."""
        dest_path = Path(destination)
        
        if self.validate_paths:
            self._path_validator.validate_path(self.dir_path)
            self._path_validator.validate_path(dest_path)
        
        with performance_monitor("directory_move"):
            try:
                shutil.move(str(self.dir_path), str(dest_path))
                self.dir_path = dest_path  # Update path after move
                logger.debug(f"Directory moved from {self.dir_path} to {dest_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to move directory from {self.dir_path} to {dest_path}: {e}")
                return False
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def get_info(self) -> dict[str, Any]:
        """Get comprehensive directory information."""
        return {
            'dir_path': str(self.dir_path),
            'exists': self.dir_path.exists(),
            'size': self.get_size() if self.dir_path.exists() else 0,
            'is_empty': self.is_empty() if self.dir_path.exists() else True,
            'is_readable': self.is_readable(self.dir_path) if self.dir_path.exists() else False,
            'is_writable': self.is_writable(self.dir_path) if self.dir_path.exists() else False,
            'is_executable': self.is_executable(self.dir_path) if self.dir_path.exists() else False,
            'permissions': self.get_permissions(self.dir_path) if self.dir_path.exists() else 0,
            'file_count': len(self.list_files()) if self.dir_path.exists() else 0,
            'directory_count': len(self.list_directories()) if self.dir_path.exists() else 0,
            'validate_paths': self.validate_paths,
            'enable_monitoring': self.enable_monitoring,
            'auto_create_parents': self.auto_create_parents,
            'safe_operations': self.safe_operations
        }
    
    def get_file_count(self) -> int:
        """Get count of files in directory."""
        return len(self.list_files())
    
    def get_directory_count(self) -> int:
        """Get count of subdirectories."""
        return len(self.list_directories())
    
    def get_total_size(self) -> int:
        """Get total size of directory including subdirectories."""
        return self.get_size()
    
    def find_files(self, pattern: str, recursive: bool = True) -> list[Path]:
        """Find files matching pattern."""
        return self.list_files(pattern, recursive)
    
    def find_directories(self, pattern: str, recursive: bool = True) -> list[Path]:
        """Find directories matching pattern."""
        if not self.dir_path.exists():
            return []
        
        if recursive:
            return [p for p in self.dir_path.rglob(pattern) if p.is_dir()]
        else:
            return [p for p in self.dir_path.glob(pattern) if p.is_dir()]
    
    def cleanup_empty_directories(self, recursive: bool = True) -> int:
        """Remove empty directories."""
        removed_count = 0
        
        try:
            if recursive:
                # Walk from bottom up to remove empty directories
                for root, dirs, files in os.walk(self.dir_path, topdown=False):
                    for dir_name in dirs:
                        dir_path = Path(root) / dir_name
                        try:
                            if not any(dir_path.iterdir()):  # Directory is empty
                                dir_path.rmdir()
                                removed_count += 1
                        except OSError:
                            pass  # Directory not empty or permission error
            else:
                # Only check current directory
                if self.is_empty():
                    self.dir_path.rmdir()
                    removed_count = 1
            
            logger.debug(f"Removed {removed_count} empty directories")
            return removed_count
        except Exception as e:
            logger.error(f"Failed to cleanup empty directories: {e}")
            return 0
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass  # No cleanup needed for folder operations
