#!/usr/bin/env python3
"""
#exonware/xwdata/tests/verify_installation.py

Verify xwdata installation and basic functionality.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.3
Generation Date: 26-Oct-2025

Usage:
    python tests/verify_installation.py
"""

import sys
from pathlib import Path
import io

# Set UTF-8 encoding for Windows console to handle emojis
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass  # If already wrapped or not supported

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def verify_import():
    """Verify library can be imported."""
    try:
        import exonware.xwdata
        print("✅ Import successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def verify_basic_functionality():
    """Verify basic operations work."""
    try:
        from exonware.xwdata import XWData
        import asyncio
        
        # Create from native data (sync - don't use dict in async context)
        data = XWData.from_native({'name': 'Alice', 'age': 30})
        
        # Test access (async)
        async def test():
            return await data.get('name')
        
        name = asyncio.run(test())
        
        if name == 'Alice':
            print("✅ Basic functionality works")
            return True
        else:
            print(f"❌ Basic functionality failed: Expected 'Alice', got {name}")
            return False
    except Exception as e:
        print(f"❌ Basic functionality failed: {e}")
        return False


def verify_dependencies():
    """Verify critical dependencies are available."""
    try:
        import pytest
        import exonware.xwsystem
        import exonware.xwnode
        print("✅ Dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Dependency check failed: {e}")
        return False


def verify_async_support():
    """Verify async operations work."""
    try:
        from exonware.xwdata import XWData
        import asyncio
        
        async def test_async():
            # Use from_native in async context
            data = XWData.from_native({'test': 'async'})
            value = await data.get('test')
            return value == 'async'
        
        result = asyncio.run(test_async())
        if result:
            print("✅ Async operations work")
            return True
        else:
            print("❌ Async operations failed")
            return False
    except Exception as e:
        print(f"❌ Async verification failed: {e}")
        return False


def main():
    """Run all verification checks."""
    print("="*80)
    print("🔍 Verifying xwdata installation...")
    print("="*80)
    print()
    
    checks = [
        ("Import", verify_import),
        ("Basic Functionality", verify_basic_functionality),
        ("Dependencies", verify_dependencies),
        ("Async Support", verify_async_support),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"Testing {name}...")
        results.append(check_func())
        print()
    
    print("="*80)
    if all(results):
        print("🎉 SUCCESS! xwdata is ready to use!")
        print("="*80)
        sys.exit(0)
    else:
        print("💥 FAILED! Some checks did not pass.")
        print("="*80)
        sys.exit(1)


if __name__ == "__main__":
    main()
