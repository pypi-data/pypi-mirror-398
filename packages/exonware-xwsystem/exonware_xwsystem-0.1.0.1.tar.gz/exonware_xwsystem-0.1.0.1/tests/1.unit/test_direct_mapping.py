#!/usr/bin/env python3
"""
Direct test for dynamic mapping system without full xwsystem import
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import pytest

@pytest.mark.skip(reason="xwlazy has been removed from the codebase")
def test_direct_mapping():
    """Test the dynamic mapping system directly."""
    print("Testing dynamic mapping system directly...")
    
    try:
        # Import only the specific modules we need
        # from xwlazy.lazy import LazyDiscovery
        raise ImportError("xwlazy has been removed")
        print("✓ LazyDiscovery imported")
        
        discovery = LazyDiscovery()
        print("✓ Discovery instance created")
        
        # Test package mapping
        package_mapping = discovery.get_package_import_mapping()
        print(f"✓ Package mapping created with {len(package_mapping)} entries")
        
        # Test import mapping
        import_mapping = discovery.get_import_package_mapping()
        print(f"✓ Import mapping created with {len(import_mapping)} entries")
        
        # Show some examples
        print("\nSample package mappings:")
        for i, (package, imports) in enumerate(list(package_mapping.items())[:5]):
            print(f"  {package}: {imports}")
        
        print("\nSample import mappings:")
        for i, (import_name, package) in enumerate(list(import_mapping.items())[:5]):
            print(f"  {import_name}: {package}")
        
        # Test DependencyMapper
        from xwlazy.lazy import DependencyMapper
        mapper = DependencyMapper()
        print("\n✓ DependencyMapper created")
        
        # Test some mappings
        test_imports = ["fastavro", "cv2", "PIL", "yaml", "sklearn"]
        print("\nTesting mappings:")
        for import_name in test_imports:
            package_name = mapper.get_package_name(import_name)
            print(f"  {import_name} -> {package_name}")
        
        # Test the new mapping methods
        print("\nTesting new mapping methods:")
        
        # Test get_package_for_import
        for import_name in ["cv2", "PIL", "yaml"]:
            package = discovery.get_package_for_import(import_name)
            print(f"  get_package_for_import('{import_name}') = {package}")
        
        # Test get_imports_for_package
        for package in ["opencv-python", "Pillow", "PyYAML"]:
            imports = discovery.get_imports_for_package(package)
            print(f"  get_imports_for_package('{package}') = {imports}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_mapping()
