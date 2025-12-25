"""
Centralized version management for eXonware projects.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Generation Date: January 27, 2025

This module provides a centralized VersionManager class that can be used
across all eXonware projects to maintain consistent version management.
"""

from typing import Any, Optional
import re


class VersionManager:
    """
    Centralized version management for eXonware projects.
    
    This class provides a unified way to manage versions across all
    eXonware libraries, ensuring consistency and reducing code duplication.
    """
    
    def __init__(self, version: str, project_name: str = ""):
        """
        Initialize the version manager.
        
        Args:
            version: Version string in format "major.minor.patch" or "major.minor.patch.build"
            project_name: Optional project name for identification
        """
        self._version = version
        self._project_name = project_name
        self._version_components = self._parse_version(version)
        self._suffix = ""
    
    def _parse_version(self, version: str) -> tuple[int, int, int, Optional[str]]:
        """Parse version string into components."""
        parts = version.split('.')
        
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        build = parts[3] if len(parts) > 3 else None
        
        return major, minor, patch, build
    
    @property
    def version(self) -> str:
        """Get the full version string."""
        return self._version
    
    @property
    def version_string(self) -> str:
        """Get the version string with suffix."""
        return self._version + self._suffix
    
    @property
    def major(self) -> int:
        """Get the major version number."""
        return self._version_components[0]
    
    @property
    def minor(self) -> int:
        """Get the minor version number."""
        return self._version_components[1]
    
    @property
    def patch(self) -> int:
        """Get the patch version number."""
        return self._version_components[2]
    
    @property
    def build(self) -> Optional[str]:
        """Get the build version."""
        return self._version_components[3]
    
    @property
    def suffix(self) -> str:
        """Get the version suffix."""
        return self._suffix
    
    @suffix.setter
    def suffix(self, value: str):
        """Set the version suffix."""
        self._suffix = value
    
    def get_version_info(self) -> tuple[int, int, int, Optional[str]]:
        """Get version as a tuple (major, minor, patch, build)."""
        return self._version_components
    
    def get_version_dict(self) -> dict[str, Any]:
        """Get version information as a dictionary."""
        return {
            "version": self.version_string,
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "build": self.build,
            "suffix": self.suffix,
            "project": self._project_name
        }
    
    def is_dev_version(self) -> bool:
        """Check if this is a development version."""
        return self.suffix in ("dev", "alpha", "beta") or self.build is not None
    
    def is_release_version(self) -> bool:
        """Check if this is a release version."""
        return not self.is_dev_version()
    
    def bump_major(self) -> str:
        """Bump major version and return new version string."""
        new_version = f"{self.major + 1}.0.0"
        return new_version
    
    def bump_minor(self) -> str:
        """Bump minor version and return new version string."""
        new_version = f"{self.major}.{self.minor + 1}.0"
        return new_version
    
    def bump_patch(self) -> str:
        """Bump patch version and return new version string."""
        new_version = f"{self.major}.{self.minor}.{self.patch + 1}"
        return new_version
    
    def bump_build(self) -> str:
        """Bump build version and return new version string."""
        if self.build is None:
            new_version = f"{self.major}.{self.minor}.{self.patch}.1"
        else:
            try:
                build_num = int(self.build) + 1
                new_version = f"{self.major}.{self.minor}.{self.patch}.{build_num}"
            except ValueError:
                # If build is not a number, append .1
                new_version = f"{self.major}.{self.minor}.{self.patch}.{self.build}.1"
        return new_version
    
    def __str__(self) -> str:
        """String representation of the version."""
        return self.version_string
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"VersionManager(version='{self.version}', project='{self._project_name}')"


# Convenience function for creating version managers
def create_version_manager(version: str, project_name: str = "") -> VersionManager:
    """
    Create a VersionManager instance.
    
    Args:
        version: Version string
        project_name: Optional project name
        
    Returns:
        VersionManager instance
    """
    return VersionManager(version, project_name)
