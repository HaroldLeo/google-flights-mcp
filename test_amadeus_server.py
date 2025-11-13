#!/usr/bin/env python
"""
Quick test to verify the Amadeus MCP server can be imported and initialized.
This doesn't test actual API calls (requires credentials).
"""

import sys
import os


def test_import():
    """Test that the module can be imported."""
    try:
        from mcp_server_amadeus import main
        print("✓ Module import successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_server_structure():
    """Test that the server has expected structure."""
    try:
        from mcp_server_amadeus import server

        # Check for key functions
        required_attrs = [
            'get_access_token',
            'amadeus_request',
            'search_flights',
            'get_hotel_offers',
            'search_activities',
            'main'
        ]

        for attr in required_attrs:
            if not hasattr(server, attr):
                print(f"✗ Missing required function: {attr}")
                return False

        print("✓ Server structure validated")
        return True
    except Exception as e:
        print(f"✗ Structure validation failed: {e}")
        return False


def test_configuration():
    """Test configuration handling."""
    try:
        from mcp_server_amadeus.server import (
            AMADEUS_CLIENT_ID,
            AMADEUS_CLIENT_SECRET,
            AMADEUS_ENV,
            BASE_URL
        )

        print(f"✓ Configuration loaded:")
        print(f"  - Environment: {AMADEUS_ENV}")
        print(f"  - Base URL: {BASE_URL}")
        print(f"  - Client ID configured: {AMADEUS_CLIENT_ID is not None}")
        print(f"  - Client Secret configured: {AMADEUS_CLIENT_SECRET is not None}")

        if not AMADEUS_CLIENT_ID or not AMADEUS_CLIENT_SECRET:
            print("\n⚠ Warning: Credentials not configured")
            print("  Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET to use the server")

        return True
    except Exception as e:
        print(f"✗ Configuration check failed: {e}")
        return False


def main():
    """Run all tests."""
    print("="*70)
    print("AMADEUS MCP SERVER - BASIC TESTS")
    print("="*70)
    print()

    tests = [
        ("Import Test", test_import),
        ("Structure Test", test_server_structure),
        ("Configuration Test", test_configuration),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{name}:")
        print("-" * 70)
        result = test_func()
        results.append(result)
        print()

    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("="*70)

    if passed == total:
        print("\n✓ All tests passed! Server is ready to use.")
        print("\nNext steps:")
        print("1. Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET environment variables")
        print("2. Run: mcp-server-amadeus")
        print("3. Or use with Claude Desktop (see AMADEUS_README.md)")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
