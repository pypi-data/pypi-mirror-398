import unittest
import sys
import os
from velocity.db.servers import postgres
from velocity.db.exceptions import DbSchemaLockedError, DbTableMissingError
import env
env.set()

test_db = "test_db_schema_locking"


class TestSchemaLocking(unittest.TestCase):
    """Test schema locking functionality with real database connections"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment before all tests"""
        # Create test database with unlocked schema for setup
        setup_engine = postgres.initialize(database="postgres", schema_locked=False)
        
        @setup_engine.transaction
        def create_test_db(tx):
            tx.execute(f"drop database if exists {test_db}", single=True)
            tx.database(test_db).create()
        
        create_test_db()

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment after all tests"""
        # Remove test database
        cleanup_engine = postgres.initialize(database="postgres", schema_locked=False)
        
        @cleanup_engine.transaction
        def cleanup_test_db(tx):
            tx.execute(f"drop database if exists {test_db}", single=True)
        
        cleanup_test_db()

    def setUp(self):
        """Set up test environment before each test"""
        # Clean up any test tables that might exist from previous runs
        cleanup_engine = postgres.initialize(database=test_db, schema_locked=False)
        
        @cleanup_engine.transaction
        def cleanup(tx):
            test_tables = [
                'auto_created_table',
                'definitely_nonexistent_table', 
                'runtime_test_table',
                'context_test_table',
                'env_test_table'
            ]
            for table_name in test_tables:
                table = tx.table(table_name)
                if table.exists():
                    table.drop()
        
        cleanup()

    def test_unlocked_schema_allows_creation(self):
        """Test that unlocked schema allows automatic table/column creation"""
        unlocked_engine = postgres.initialize(database=test_db, schema_locked=False)
        
        @unlocked_engine.transaction
        def test_auto_creation(tx):
            # This should automatically create the table and columns
            new_table = tx.table('auto_created_table')
            
            new_table.insert({
                'name': 'Test User',
                'email': 'test@example.com',
                'age': 25
            })
            
            # Verify the table was created and record inserted
            self.assertTrue(new_table.exists())
            result = new_table.select().one()
            self.assertEqual(result['name'], 'Test User')
            self.assertEqual(result['email'], 'test@example.com')
            self.assertEqual(result['age'], 25)
            
            # Test adding a new column to existing table
            new_table.insert({
                'name': 'Test User 2',
                'email': 'test2@example.com', 
                'age': 30,
                'city': 'New York'  # This should create a new column
            })
            
            # Verify new column was added
            result2 = new_table.select(where={'name': 'Test User 2'}).one()
            self.assertEqual(result2['city'], 'New York')
        
        test_auto_creation()

    def test_locked_schema_prevents_creation(self):
        """Test that locked schema prevents automatic table/column creation"""
        engine = postgres.initialize(database=test_db, schema_locked=True)
        
        @engine.transaction
        def test_blocked_creation(tx):
            # This should raise DbSchemaLockedError when trying to create the table
            nonexistent_table = tx.table('definitely_nonexistent_table')
            
            with self.assertRaises(DbSchemaLockedError) as context:
                nonexistent_table.insert({
                    'name': 'Test User',
                    'email': 'test@example.com'
                })
            
            # Check that the error message mentions schema locking
            self.assertIn("schema is locked", str(context.exception))
            
            # Verify the table was not created
            self.assertFalse(nonexistent_table.exists())
        
        test_blocked_creation()

    def test_locked_schema_prevents_column_creation(self):
        """Test that locked schema prevents automatic column creation on existing tables"""
        # First create a table with unlocked schema
        setup_engine = postgres.initialize(database=test_db, schema_locked=False)
        
        @setup_engine.transaction  
        def setup_table(tx):
            table = tx.table('runtime_test_table')
            table.insert({'name': 'Initial User', 'age': 25})
        
        setup_table()
        
        # Now try to add a column with locked schema
        locked_engine = postgres.initialize(database=test_db, schema_locked=True)
        
        @locked_engine.transaction
        def test_blocked_column(tx):
            table = tx.table('runtime_test_table')
            
            with self.assertRaises(DbSchemaLockedError) as context:
                # This should fail because 'email' column doesn't exist
                table.insert({
                    'name': 'New User',
                    'age': 30,
                    'email': 'new@example.com'  # This column doesn't exist yet
                })
            
            # Check that the error message mentions schema locking
            self.assertIn("schema is locked", str(context.exception))
        
        test_blocked_column()

    def test_runtime_schema_locking(self):
        """Test locking and unlocking schema at runtime"""
        engine = postgres.initialize(database=test_db, schema_locked=False)
        
        @engine.transaction
        def test_runtime_control(tx):
            # Should work initially (unlocked)
            table = tx.table('runtime_test_table_2')
            
            table.insert({'name': 'Test 1', 'status': 'active'})
            self.assertTrue(table.exists())
            
            # Verify record exists
            result = table.select().one()
            self.assertEqual(result['name'], 'Test 1')
            
        test_runtime_control()
        
        # Lock schema at runtime
        engine.lock_schema()
        self.assertTrue(engine.schema_locked)
        
        @engine.transaction
        def test_locked_state(tx):
            table = tx.table('runtime_test_table_2')
            
            # Should still be able to insert into existing table with existing columns
            table.insert({'name': 'Test 2', 'status': 'active'})
            
            # But should fail when trying to add new column
            with self.assertRaises(DbSchemaLockedError):
                table.insert({'name': 'Test 3', 'status': 'active', 'new_column': 'value'})
        
        test_locked_state()
        
        # Unlock schema
        engine.unlock_schema()
        self.assertFalse(engine.schema_locked)
        
        @engine.transaction
        def test_unlocked_again(tx):
            table = tx.table('runtime_test_table_2')
            
            # Should work again (unlocked) - can add new column
            table.insert({'name': 'Test 4', 'status': 'active', 'new_column': 'success'})
            
            result = table.select(where={'name': 'Test 4'}).one()
            self.assertEqual(result['new_column'], 'success')
        
        test_unlocked_again()

    def test_temporary_unlock_context_manager(self):
        """Test temporarily unlocking schema with context manager"""
        engine = postgres.initialize(database=test_db, schema_locked=True)
        
        @engine.transaction
        def test_context_unlock(tx):
            # Should be locked initially
            table = tx.table('context_test_table')
            table.drop()  # Clean up first if exists
            
            with self.assertRaises(DbSchemaLockedError):
                table.insert({'name': 'Test 1'})
            
            # Temporarily unlock
            with engine.unlocked_schema():
                # Should work inside context
                table.insert({'name': 'Test 2'})
                self.assertTrue(table.exists())
                
                # Schema should be unlocked inside context
                self.assertFalse(engine.schema_locked)
            
            # Should be locked again after context
            self.assertTrue(engine.schema_locked)
            
            # Verify we can still use the table (just can't create new ones)
            result = table.select().one()
            self.assertEqual(result['name'], 'Test 2')
            
            # Clean up
            table.drop()
        
        test_context_unlock()

    def test_environment_variable_override(self):
        """Test that VELOCITY_SCHEMA_LOCKED environment variable works"""
        # Set environment variable
        os.environ['VELOCITY_SCHEMA_LOCKED'] = 'true'
        
        try:
            # Even though we specify schema_locked=False, env var should override
            engine = postgres.initialize(database=test_db, schema_locked=False)
            self.assertTrue(engine.schema_locked)
            
            # Test that it actually blocks operations
            @engine.transaction
            def test_env_override(tx):
                table = tx.table('env_test_table')
                
                with self.assertRaises(DbSchemaLockedError):
                    table.insert({'name': 'Test', 'env_test': 'should_fail'})
            
            test_env_override()
            
        finally:
            # Clean up environment variable
            if 'VELOCITY_SCHEMA_LOCKED' in os.environ:
                del os.environ['VELOCITY_SCHEMA_LOCKED']

    def test_existing_table_operations_still_work(self):
        """Test that existing table operations work even with locked schema"""
        # First, create a table with unlocked schema
        setup_engine = postgres.initialize(database=test_db, schema_locked=False)
        
        @setup_engine.transaction
        def create_test_table(tx):
            table = tx.table('existing_table_test')
            table.insert({'name': 'User 1', 'email': 'user1@test.com', 'active': True})
            table.insert({'name': 'User 2', 'email': 'user2@test.com', 'active': False})
        
        create_test_table()
        
        # Now use locked schema and verify existing operations work
        locked_engine = postgres.initialize(database=test_db, schema_locked=True)
        
        @locked_engine.transaction
        def test_existing_operations(tx):
            table = tx.table('existing_table_test')
            
            # Reading should work
            all_users = table.select().all()
            self.assertEqual(len(all_users), 2)
            
            # Inserting with existing columns should work
            table.insert({'name': 'User 3', 'email': 'user3@test.com', 'active': True})
            
            # Updating should work
            table.update({'active': False}, where={'name': 'User 1'})
            
            # Verify updates
            user1 = table.select(where={'name': 'User 1'}).one()
            self.assertFalse(user1['active'])
            
            # Count should be 3 now
            count = table.count()
            self.assertEqual(count, 3)
            
            # But adding new columns should still fail
            with self.assertRaises(DbSchemaLockedError):
                table.insert({'name': 'User 4', 'email': 'user4@test.com', 'active': True, 'new_field': 'fail'})
        
        test_existing_operations()

    def tearDown(self):
        """Clean up after each test"""
        # Clean up test tables
        engine = postgres.initialize(database=test_db, schema_locked=False)
        
        @engine.transaction
        def cleanup(tx):
            test_tables = [
                'auto_created_table',
                'definitely_nonexistent_table', 
                'runtime_test_table',
                'runtime_test_table_2',
                'context_test_table',
                'env_test_table',
                'existing_table_test'
            ]
            for table_name in test_tables:
                table = tx.table(table_name)
                if table.exists():
                    table.drop()
        
        try:
            cleanup()
        except Exception:
            # Ignore cleanup errors
            pass


if __name__ == "__main__":
    unittest.main()
