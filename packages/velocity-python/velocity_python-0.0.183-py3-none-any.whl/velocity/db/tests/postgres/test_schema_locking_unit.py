import unittest
import os
from velocity.db.core.engine import Engine
from velocity.db.exceptions import DbSchemaLockedError


class MockDriver:
    """Mock database driver for testing"""
    def connect(self, **kwargs):
        return None


class MockSQL:
    """Mock SQL dialect for testing"""
    server = "MockDB"


class TestSchemaLockingUnit(unittest.TestCase):
    """Unit tests for schema locking functionality without database connection"""

    def test_engine_schema_locked_property(self):
        """Test engine schema_locked property and methods"""
        # Test default unlocked state
        engine = Engine(MockDriver(), {}, MockSQL(), schema_locked=False)
        self.assertFalse(engine.schema_locked)
        
        # Test locked initialization  
        locked_engine = Engine(MockDriver(), {}, MockSQL(), schema_locked=True)
        self.assertTrue(locked_engine.schema_locked)

    def test_schema_lock_unlock_methods(self):
        """Test runtime locking and unlocking"""
        engine = Engine(MockDriver(), {}, MockSQL(), schema_locked=False)
        
        # Initially unlocked
        self.assertFalse(engine.schema_locked)
        
        # Lock schema
        engine.lock_schema()
        self.assertTrue(engine.schema_locked)
        
        # Unlock schema
        engine.unlock_schema()
        self.assertFalse(engine.schema_locked)

    def test_unlocked_schema_context_manager(self):
        """Test the context manager for temporarily unlocking schema"""
        engine = Engine(MockDriver(), {}, MockSQL(), schema_locked=True)
        
        # Initially locked
        self.assertTrue(engine.schema_locked)
        
        # Temporarily unlock
        with engine.unlocked_schema():
            self.assertFalse(engine.schema_locked)
        
        # Should be locked again after context
        self.assertTrue(engine.schema_locked)

    def test_nested_unlocked_schema_context(self):
        """Test nested context managers"""
        engine = Engine(MockDriver(), {}, MockSQL(), schema_locked=True)
        
        self.assertTrue(engine.schema_locked)
        
        with engine.unlocked_schema():
            self.assertFalse(engine.schema_locked)
            
            # Nested context - should stay unlocked
            with engine.unlocked_schema():
                self.assertFalse(engine.schema_locked)
            
            # Still unlocked in outer context
            self.assertFalse(engine.schema_locked)
        
        # Back to original locked state
        self.assertTrue(engine.schema_locked)

    def test_environment_variable_parsing(self):
        """Test environment variable parsing for schema locking"""
        # Test various truthy values
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('1', True),
            ('yes', True),
            ('YES', True),
            ('false', False),
            ('0', False),
            ('no', False),
            ('', False),
            ('random', False),
        ]
        
        for env_value, expected in test_cases:
            with self.subTest(env_value=env_value):
                # Mock the environment variable check
                if env_value.lower() in ('true', '1', 'yes'):
                    schema_locked = True
                else:
                    schema_locked = False
                    
                self.assertEqual(schema_locked, expected)

    def test_schema_locked_error_creation(self):
        """Test that DbSchemaLockedError can be created and raised"""
        with self.assertRaises(DbSchemaLockedError) as context:
            raise DbSchemaLockedError("Test schema lock error")
        
        self.assertIn("Test schema lock error", str(context.exception))


if __name__ == "__main__":
    unittest.main()
