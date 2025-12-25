#!/usr/bin/env python3
"""
Comprehensive pre-upload tests for fx-sdk.
Run this before uploading to PyPI to catch any issues.
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path

print("=" * 70)
print("Pre-Upload Test Suite for fx-sdk")
print("=" * 70)

errors = []
warnings = []

def test(name, func):
    """Run a test and track results."""
    try:
        result = func()
        if result is False:
            errors.append(f"❌ {name}: FAILED")
            return False
        elif result is True:
            print(f"✓ {name}")
            return True
        else:
            print(f"✓ {name}: {result}")
            return True
    except Exception as e:
        errors.append(f"❌ {name}: ERROR - {str(e)}")
        return False

def warn(name, message):
    """Add a warning."""
    warnings.append(f"⚠ {name}: {message}")

# Test 1: Package structure
print("\n1. Testing Package Structure...")
def test_package_structure():
    required_files = [
        "fx_sdk/__init__.py",
        "fx_sdk/client.py",
        "fx_sdk/constants.py",
        "fx_sdk/utils.py",
        "fx_sdk/exceptions.py",
    ]
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    if missing:
        return f"Missing files: {', '.join(missing)}"
    return True

test("Package structure", test_package_structure)

# Test 2: ABI files
print("\n2. Testing ABI Files...")
def test_abi_files():
    abi_dir = Path("fx_sdk/abis")
    if not abi_dir.exists():
        return "ABI directory not found"
    
    abi_files = list(abi_dir.glob("*.json"))
    if len(abi_files) == 0:
        return "No ABI files found"
    
    expected_abis = [
        "erc20.json",
        "fxusd.json",
        "fxusd_base_pool.json",
        "diamond.json",
        "market.json",
        "rebalance_pool.json",
        "rebalance_pool_registry.json",
        "steth_treasury.json",
        "fxn.json",
        "vefxn.json",
        "gauge_controller.json",
        "multipath_converter.json",
        "steth_gateway.json",
        "vesting.json",
        "liquidity_gauge.json",
        "pool_manager.json",
        "reserve_pool.json",
        "saving_fxusd.json",
    ]
    
    missing = []
    for abi in expected_abis:
        if not (abi_dir / abi).exists():
            missing.append(abi)
    
    if missing:
        warn("ABI files", f"Missing ABIs: {', '.join(missing)}")
    
    return f"Found {len(abi_files)} ABI files"
test("ABI files", test_abi_files)

# Test 3: Import tests
print("\n3. Testing Imports...")
def test_imports():
    try:
        import fx_sdk
        if not hasattr(fx_sdk, '__version__'):
            return "Missing __version__"
        if not hasattr(fx_sdk, 'ProtocolClient'):
            return "Missing ProtocolClient export"
        if not hasattr(fx_sdk, 'constants'):
            return "Missing constants export"
        if not hasattr(fx_sdk, 'utils'):
            return "Missing utils export"
        if not hasattr(fx_sdk, 'exceptions'):
            return "Missing exceptions export"
        return f"Version: {fx_sdk.__version__}"
    except ImportError as e:
        return f"Import error: {str(e)}"

test("Main package import", test_imports)

def test_submodule_imports():
    modules = [
        "fx_sdk.client",
        "fx_sdk.constants",
        "fx_sdk.utils",
        "fx_sdk.exceptions",
    ]
    failed = []
    for module in modules:
        try:
            importlib.import_module(module)
        except ImportError as e:
            failed.append(f"{module}: {str(e)}")
    if failed:
        return f"Failed imports: {', '.join(failed)}"
    return True

test("Submodule imports", test_submodule_imports)

# Test 4: Constants
print("\n4. Testing Constants...")
def test_constants():
    from fx_sdk import constants
    
    required_constants = [
        "FXUSD",
        "FETH",
        "RUSD",
        "FXN",
        "VEFXN",
        "XETH",
        "XCVX",
        "XWBTC",
    ]
    
    missing = []
    for const in required_constants:
        if not hasattr(constants, const):
            missing.append(const)
    
    if missing:
        return f"Missing constants: {', '.join(missing)}"
    
    # Check that addresses are valid (start with 0x and are 42 chars)
    for const in required_constants:
        addr = getattr(constants, const)
        if not isinstance(addr, str) or not addr.startswith("0x") or len(addr) != 42:
            return f"Invalid address format for {const}: {addr}"
    
    return f"All {len(required_constants)} required constants present"

test("Constants", test_constants)

# Test 5: Utils
print("\n5. Testing Utility Functions...")
def test_utils():
    from fx_sdk import utils
    from decimal import Decimal
    
    # Test wei_to_decimal
    wei = 1500000000000000000
    eth = utils.wei_to_decimal(wei)
    if eth != Decimal("1.5"):
        return f"wei_to_decimal failed: expected 1.5, got {eth}"
    
    # Test decimal_to_wei
    wei_result = utils.decimal_to_wei(Decimal("1.5"))
    if wei_result != wei:
        return f"decimal_to_wei failed: expected {wei}, got {wei_result}"
    
    # Test to_checksum_address
    addr = "0x742d35cc6634c0532925a3b844bc9e2385c6b0e0"
    checksum = utils.to_checksum_address(addr)
    if not checksum.startswith("0x") or len(checksum) != 42:
        return f"to_checksum_address failed: invalid format"
    
    return True

test("Utility functions", test_utils)

# Test 6: Client initialization
print("\n6. Testing Client Initialization...")
def test_client_init():
    from fx_sdk import ProtocolClient
    
    # Test read-only initialization
    try:
        client = ProtocolClient("https://eth.llamarpc.com")
        if not hasattr(client, 'w3'):
            return "Client missing w3 attribute"
        if not hasattr(client, 'contracts'):
            return "Client missing contracts attribute"
        return "Read-only client initialized"
    except Exception as e:
        return f"Client initialization failed: {str(e)}"

test("Client initialization (read-only)", test_client_init)

# Test 7: Package metadata
print("\n7. Testing Package Metadata...")
def test_package_metadata():
    try:
        from fx_sdk import __version__
        if not __version__ or __version__ == "0.0.0":
            return "Invalid version number"
        return f"Version: {__version__}"
    except:
        return "Could not read version"

test("Package version", test_package_metadata)

# Test 8: Check for common issues
print("\n8. Checking for Common Issues...")
def test_common_issues():
    issues = []
    
    # Check for hardcoded paths
    import re
    with open("fx_sdk/client.py", "r") as f:
        content = f.read()
        if "/Users/" in content or "/home/" in content:
            issues.append("Hardcoded user paths found")
    
    # Check for TODO/FIXME in production code
    with open("fx_sdk/client.py", "r") as f:
        for i, line in enumerate(f, 1):
            if "TODO" in line.upper() or "FIXME" in line.upper():
                if not line.strip().startswith("#"):
                    issues.append(f"TODO/FIXME in code at line {i}")
    
    if issues:
        return f"Issues found: {', '.join(issues)}"
    return True

test("Common issues check", test_common_issues)

# Test 9: Build verification
print("\n9. Verifying Build Files...")
def test_build_files():
    dist_dir = Path("dist")
    if not dist_dir.exists():
        return "dist/ directory not found - run 'python3 -m build' first"
    
    wheel_file = dist_dir / "fx_sdk-0.1.0-py3-none-any.whl"
    tar_file = dist_dir / "fx_sdk-0.1.0.tar.gz"
    
    if not wheel_file.exists():
        return "Wheel file not found"
    if not tar_file.exists():
        return "Source distribution not found"
    
    return f"Build files present (wheel: {wheel_file.stat().st_size/1024:.1f}KB, tar: {tar_file.stat().st_size/1024:.1f}KB)"

test("Build files", test_build_files)

# Test 10: Dependencies
print("\n10. Testing Dependencies...")
def test_dependencies():
    try:
        import web3
        import eth_account
        import eth_typing
        import eth_utils
        return f"All dependencies importable (web3 {web3.__version__})"
    except ImportError as e:
        return f"Missing dependency: {str(e)}"

test("Dependencies", test_dependencies)

# Test 11: Optional dependencies
print("\n11. Testing Optional Dependencies...")
def test_optional_deps():
    results = []
    
    try:
        import dotenv
        results.append("python-dotenv: available")
    except ImportError:
        results.append("python-dotenv: not installed (optional)")
    
    try:
        from google.colab import userdata
        results.append("google.colab: available")
    except ImportError:
        results.append("google.colab: not available (expected outside Colab)")
    
    return ", ".join(results)

test("Optional dependencies", test_optional_deps)

# Summary
print("\n" + "=" * 70)
print("Test Summary")
print("=" * 70)

if errors:
    print(f"\n❌ {len(errors)} ERROR(S) FOUND:")
    for error in errors:
        print(f"  {error}")
    print("\n⚠️  DO NOT UPLOAD TO PYPI UNTIL ERRORS ARE FIXED!")
    sys.exit(1)
else:
    print("\n✅ All critical tests passed!")

if warnings:
    print(f"\n⚠️  {len(warnings)} WARNING(S):")
    for warning in warnings:
        print(f"  {warning}")
    print("\n⚠️  Review warnings before uploading.")

print("\n" + "=" * 70)
print("✅ Package is ready for PyPI upload!")
print("=" * 70)
print("\nNext steps:")
print("1. Review any warnings above")
print("2. Run: python3 -m twine upload dist/*")
print("3. Verify on: https://pypi.org/project/fx-sdk/")

