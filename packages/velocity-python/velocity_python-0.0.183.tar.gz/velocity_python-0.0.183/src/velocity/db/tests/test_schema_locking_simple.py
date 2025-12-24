#!/usr/bin/env python3
"""
Simple test to verify schema locking parameters in initializers.
"""

import unittest
import os
from unittest.mock import patch

from velocity.db.servers.sqlite import SQLiteInitializer


class TestSchemaLockingSimple(unittest.TestCase):
    """Test schema locking with SQLite (no external dependencies)."""
    
    def test_sqlite_schema_locked_parameter(self):
        """Test SQLite initializer accepts schema_locked parameter."""
        config = {"database": ":memory:"}
        
        # Test with schema_locked=True
        engine = SQLiteInitializer.initialize(config, schema_locked=True)
        self.assertTrue(engine.schema_locked)
        
        # Test with schema_locked=False (default)
        engine = SQLiteInitializer.initialize(config, schema_locked=False)
        self.assertFalse(engine.schema_locked)
        
        # Test default behavior
        engine = SQLiteInitializer.initialize(config)
        self.assertFalse(engine.schema_locked)

    @patch.dict(os.environ, {"VELOCITY_SCHEMA_LOCKED": "true"})
    def test_sqlite_environment_variable_override(self):
        """Test SQLite respects VELOCITY_SCHEMA_LOCKED environment variable."""
        config = {"database": ":memory:"}
        
        # Environment variable should override default
        engine = SQLiteInitializer.initialize(config)
        self.assertTrue(engine.schema_locked)
        
        # Environment variable should override explicit False
        engine = SQLiteInitializer.initialize(config, schema_locked=False)
        self.assertTrue(engine.schema_locked)

    def test_environment_variable_various_true_values(self):
        """Test that various 'true' values in environment variable work."""
        config = {"database": ":memory:"}
        
        # Test "1"
        with patch.dict(os.environ, {"VELOCITY_SCHEMA_LOCKED": "1"}):
            engine = SQLiteInitializer.initialize(config)
            self.assertTrue(engine.schema_locked)
        
        # Test "yes"
        with patch.dict(os.environ, {"VELOCITY_SCHEMA_LOCKED": "yes"}):
            engine = SQLiteInitializer.initialize(config)
            self.assertTrue(engine.schema_locked)
        
        # Test "TRUE" (case insensitive)
        with patch.dict(os.environ, {"VELOCITY_SCHEMA_LOCKED": "TRUE"}):
            engine = SQLiteInitializer.initialize(config)
            self.assertTrue(engine.schema_locked)
        
        # Test "false" (should not lock)
        with patch.dict(os.environ, {"VELOCITY_SCHEMA_LOCKED": "false"}):
            engine = SQLiteInitializer.initialize(config)
            self.assertFalse(engine.schema_locked)

    def test_schema_locking_methods(self):
        """Test schema locking runtime methods work correctly."""
        config = {"database": ":memory:"}
        
        # Start unlocked
        engine = SQLiteInitializer.initialize(config, schema_locked=False)
        self.assertFalse(engine.schema_locked)
        
        # Lock at runtime
        engine.lock_schema()
        self.assertTrue(engine.schema_locked)
        
        # Unlock at runtime
        engine.unlock_schema()
        self.assertFalse(engine.schema_locked)
        
        # Test context manager
        engine.lock_schema()
        self.assertTrue(engine.schema_locked)
        
        with engine.unlocked_schema():
            self.assertFalse(engine.schema_locked)
        
        # Should be locked again after context
        self.assertTrue(engine.schema_locked)


if __name__ == "__main__":
    unittest.main()
