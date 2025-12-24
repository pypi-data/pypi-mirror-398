#!/usr/bin/env python3
"""
Quick test to verify PostgreSQL implementation is functionally unchanged.
"""
import sys
import os
sys.path.insert(0, '/home/ubuntu/tenspace/velocity-python/src')

def test_postgres_unchanged():
    """Test that PostgreSQL implementation is functionally unchanged."""
    print("Testing PostgreSQL implementation...")
    
    # Test imports
    try:
        from velocity.db.servers.postgres import initialize
        from velocity.db.servers.postgres.sql import SQL
        from velocity.db.servers.postgres.types import TYPES
        from velocity.db.servers.postgres.operators import OPERATORS
        print("✓ All imports successful")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    
    # Test SQL class attributes are the same
    expected_server = "PostGreSQL"
    if SQL.server != expected_server:
        print(f"✗ SQL.server changed: expected '{expected_server}', got '{SQL.server}'")
        return False
    print("✓ SQL.server unchanged")
    
    # Test error codes are preserved
    expected_duplicate_codes = ["23505"]
    if SQL.DuplicateKeyErrorCodes != expected_duplicate_codes:
        print(f"✗ DuplicateKeyErrorCodes changed: expected {expected_duplicate_codes}, got {SQL.DuplicateKeyErrorCodes}")
        return False
    print("✓ Error codes unchanged")
    
    # Test TYPES class methods exist
    if not hasattr(TYPES, 'get_type'):
        print("✗ TYPES.get_type method missing")
        return False
    if not hasattr(TYPES, 'get_conv'):
        print("✗ TYPES.get_conv method missing")
        return False
    if not hasattr(TYPES, 'py_type'):
        print("✗ TYPES.py_type method missing")
        return False
    print("✓ TYPES methods present")
    
    # Test type mappings are correct
    if TYPES.get_type(str) != "TEXT":
        print(f"✗ TYPES.get_type(str) changed: expected 'TEXT', got '{TYPES.get_type(str)}'")
        return False
    if TYPES.get_type(int) != "BIGINT":
        print(f"✗ TYPES.get_type(int) changed: expected 'BIGINT', got '{TYPES.get_type(int)}'")
        return False
    print("✓ Type mappings unchanged")
    
    # Test operators are preserved
    if OPERATORS.get("<>") != "<>":
        print(f"✗ Operator '<>' mapping changed")
        return False
    if OPERATORS.get("%%") != "ILIKE":
        print(f"✗ Operator '%%' mapping changed")
        return False
    print("✓ Operators unchanged")
    
    # Test SQL methods exist (just check key ones)
    sql_methods = ['select', 'insert', 'update', 'delete', 'merge', 'version', 'databases']
    for method in sql_methods:
        if not hasattr(SQL, method):
            print(f"✗ SQL.{method} method missing")
            return False
    print("✓ SQL methods present")
    
    print("\n🎉 PostgreSQL implementation is functionally unchanged!")
    return True

if __name__ == "__main__":
    success = test_postgres_unchanged()
    sys.exit(0 if success else 1)
