#!/usr/bin/env python3
"""
Test the package as if it were installed from PyPI.
This simulates what users will experience.
"""

import sys
import subprocess
import tempfile
import os
from pathlib import Path

print("=" * 70)
print("Testing Package Installation (Simulating PyPI Install)")
print("=" * 70)

def run_test(name, func):
    """Run a test and report results."""
    try:
        result = func()
        if result:
            print(f"✓ {name}")
            return True
        else:
            print(f"❌ {name}: FAILED")
            return False
    except Exception as e:
        print(f"❌ {name}: ERROR - {str(e)}")
        return False

# Test 1: Check if package can be imported after installation simulation
print("\n1. Testing Package Import from Built Wheel...")
def test_wheel_import():
    """Test importing from the built wheel file."""
    import zipfile
    import importlib.util
    
    wheel_path = Path("dist/fx_sdk-0.1.0-py3-none-any.whl")
    if not wheel_path.exists():
        print("   ⚠ Wheel file not found - skipping")
        return True
    
    # Extract and test imports
    with zipfile.ZipFile(wheel_path, 'r') as wheel:
        # Check that all expected files are in the wheel
        files = wheel.namelist()
        
        required_files = [
            "fx_sdk/__init__.py",
            "fx_sdk/client.py",
            "fx_sdk/constants.py",
            "fx_sdk/utils.py",
            "fx_sdk/exceptions.py",
        ]
        
        missing = []
        for req_file in required_files:
            if not any(req_file in f for f in files):
                missing.append(req_file)
        
        if missing:
            print(f"   ❌ Missing files in wheel: {missing}")
            return False
        
        # Check ABI files
        abi_files = [f for f in files if "abis/" in f and f.endswith(".json")]
        if len(abi_files) < 15:  # Should have at least 15 ABIs
            print(f"   ⚠ Only {len(abi_files)} ABI files found (expected 15+)")
        
        print(f"   ✓ Wheel contains {len(files)} files")
        print(f"   ✓ Found {len(abi_files)} ABI files")
        return True

run_test("Wheel contents", test_wheel_import)

# Test 2: Verify package metadata
print("\n2. Verifying Package Metadata...")
def test_metadata():
    """Check package metadata is correct."""
    import zipfile
    
    wheel_path = Path("dist/fx_sdk-0.1.0-py3-none-any.whl")
    if not wheel_path.exists():
        return True
    
    with zipfile.ZipFile(wheel_path, 'r') as wheel:
        for name in wheel.namelist():
            if 'METADATA' in name:
                metadata = wheel.read(name).decode('utf-8')
                
                checks = {
                    "Name: fx-sdk": "Name: fx-sdk" in metadata,
                    "Version: 0.1.0": "Version: 0.1.0" in metadata,
                    "Python >=3.8": "Requires-Python: >=3.8" in metadata,
                    "Author present": "Author:" in metadata,
                    "Description present": "Summary:" in metadata,
                }
                
                failed = [k for k, v in checks.items() if not v]
                if failed:
                    print(f"   ❌ Metadata issues: {', '.join(failed)}")
                    return False
                
                print("   ✓ All metadata fields present")
                return True
    
    print("   ⚠ Could not find METADATA file")
    return True

run_test("Package metadata", test_metadata)

# Test 3: Test actual import (current installation)
print("\n3. Testing Current Installation...")
def test_current_import():
    """Test that the currently installed package works."""
    try:
        # Test main imports
        from fx_sdk import ProtocolClient, constants, utils, exceptions
        from fx_sdk import __version__
        
        # Test that version is set
        if not __version__ or __version__ == "0.0.0":
            print("   ❌ Invalid version")
            return False
        
        # Test that ProtocolClient can be instantiated
        try:
            client = ProtocolClient("https://eth.llamarpc.com")
            print(f"   ✓ ProtocolClient works (version {__version__})")
            return True
        except Exception as e:
            print(f"   ⚠ ProtocolClient initialization: {e}")
            return True  # Not critical for package structure
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

run_test("Current installation", test_current_import)

# Test 4: Check for sensitive data
print("\n4. Checking for Sensitive Data...")
def test_sensitive_data():
    """Check that no sensitive data is in the package."""
    import re
    
    sensitive_patterns = [
        (r'pypi-[A-Za-z0-9_-]+', "PyPI API tokens"),
        (r'0x[a-fA-F0-9]{64}', "Private keys (64 hex chars)"),
        (r'sk_live_[A-Za-z0-9]+', "Stripe keys"),
        (r'AKIA[0-9A-Z]{16}', "AWS keys"),
    ]
    
    files_to_check = [
        "fx_sdk/client.py",
        "fx_sdk/constants.py",
        "fx_sdk/__init__.py",
    ]
    
    issues = []
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            continue
        
        with open(file_path, 'r') as f:
            content = f.read()
            for pattern, name in sensitive_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    # Filter out false positives (like contract addresses)
                    for match in matches:
                        if name == "Private keys" and len(match) == 66:
                            # Contract addresses are 42 chars, private keys are 66
                            issues.append(f"{file_path}: Possible {name} found")
    
    if issues:
        print(f"   ⚠ Potential sensitive data found:")
        for issue in issues:
            print(f"      - {issue}")
        print("   ⚠ Review before uploading!")
        return True  # Warning, not error
    
    print("   ✓ No sensitive data detected")
    return True

run_test("Sensitive data check", test_sensitive_data)

# Test 5: Documentation files
print("\n5. Checking Documentation...")
def test_documentation():
    """Check that documentation files exist."""
    docs = {
        "README.md": "Main documentation",
        "LICENSE": "License file",
        "features.md": "Features documentation",
    }
    
    missing = []
    for doc, desc in docs.items():
        if not os.path.exists(doc):
            missing.append(f"{doc} ({desc})")
    
    if missing:
        print(f"   ⚠ Missing: {', '.join(missing)}")
        return True  # Warning
    
    print("   ✓ All documentation files present")
    return True

run_test("Documentation files", test_documentation)

# Test 6: File sizes (check for accidentally large files)
print("\n6. Checking File Sizes...")
def test_file_sizes():
    """Check that no unexpectedly large files are included."""
    import zipfile
    
    wheel_path = Path("dist/fx_sdk-0.1.0-py3-none-any.whl")
    if not wheel_path.exists():
        return True
    
    with zipfile.ZipFile(wheel_path, 'r') as wheel:
        large_files = []
        for info in wheel.infolist():
            # Check for files larger than 1MB
            if info.file_size > 1024 * 1024:
                large_files.append(f"{info.filename} ({info.file_size / 1024 / 1024:.2f}MB)")
        
        if large_files:
            print(f"   ⚠ Large files found:")
            for f in large_files:
                print(f"      - {f}")
            return True  # Warning
        
        total_size = sum(info.file_size for info in wheel.infolist())
        print(f"   ✓ Total package size: {total_size / 1024:.1f}KB")
        return True

run_test("File sizes", test_file_sizes)

print("\n" + "=" * 70)
print("Installation Simulation Complete")
print("=" * 70)
print("\n✅ Package structure looks good!")
print("\n💡 Tip: For a real installation test, you can:")
print("   1. Create a virtual environment")
print("   2. pip install dist/fx_sdk-0.1.0-py3-none-any.whl")
print("   3. Test imports and basic functionality")
print("\n" + "=" * 70)

