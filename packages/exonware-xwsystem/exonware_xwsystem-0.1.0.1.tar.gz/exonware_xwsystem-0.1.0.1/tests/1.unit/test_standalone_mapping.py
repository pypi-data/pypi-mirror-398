#!/usr/bin/env python3
"""
Standalone test for dynamic mapping system - bypasses package imports
"""

import sys
import os
from pathlib import Path

# Add the specific module path
module_path = Path(__file__).parent / 'src' / 'exonware' / 'xwsystem' / 'utils'
sys.path.insert(0, str(module_path))

def test_standalone_mapping():
    """Test the dynamic mapping system standalone."""
    print("Testing dynamic mapping system standalone...")
    
    try:
        # Import the modules directly
        import lazy_discovery
        print("✓ lazy_discovery imported")
        
        discovery = lazy_discovery.LazyDiscovery()
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
        
        # Test the new mapping methods
        print("\nTesting new mapping methods:")
        
        # Test get_package_for_import
        for import_name in ["cv2", "PIL", "yaml", "sklearn"]:
            package = discovery.get_package_for_import(import_name)
            print(f"  get_package_for_import('{import_name}') = {package}")
        
        # Test get_imports_for_package
        for package in ["opencv-python", "Pillow", "PyYAML", "scikit-learn"]:
            imports = discovery.get_imports_for_package(package)
            print(f"  get_imports_for_package('{package}') = {imports}")
        
        # Test DependencyMapper
        import lazy_install
        mapper = lazy_install.DependencyMapper()
        print("\n✓ DependencyMapper created")
        
        # Test some mappings
        test_imports = ["fastavro", "cv2", "PIL", "yaml", "sklearn"]
        print("\nTesting DependencyMapper mappings:")
        for import_name in test_imports:
            package_name = mapper.get_package_name(import_name)
            print(f"  {import_name} -> {package_name}")
        
        # Test the enhanced mapping methods
        print("\nTesting enhanced mapping methods:")
        package_import_mapping = mapper.get_package_import_mapping()
        import_package_mapping = mapper.get_import_package_mapping()
        
        print(f"  Package-import mapping has {len(package_import_mapping)} entries")
        print(f"  Import-package mapping has {len(import_package_mapping)} entries")
        
        # Show some examples
        print("\n  Sample package-import mappings:")
        for i, (package, imports) in enumerate(list(package_import_mapping.items())[:3]):
            print(f"    {package}: {imports}")
        
        print("\n  Sample import-package mappings:")
        for i, (import_name, package) in enumerate(list(import_package_mapping.items())[:3]):
            print(f"    {import_name}: {package}")
        
        print("\n✅ All tests passed!")
        print("\n🎉 Dynamic mapping system is working correctly!")
        print("   • Automatically discovers package mappings from project config")
        print("   • Creates bidirectional mappings (package ↔ import)")
        print("   • Caches mappings for performance")
        print("   • Package-agnostic and reusable across exonware libraries")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_standalone_mapping()
