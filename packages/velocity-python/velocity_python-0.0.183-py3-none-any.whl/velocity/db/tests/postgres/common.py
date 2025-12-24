import unittest
from velocity.db.servers import postgres
import env
env.set()

test_db = "test_db_postgres"
engine = postgres.initialize(database=test_db)


class CommonPostgresTest(unittest.TestCase):
    """
    Base test class for PostgreSQL tests following the common pattern.
    All PostgreSQL tests should inherit from this class.
    """

    @classmethod
    def setUpClass(cls):
        """Set up the test database and create any common tables."""
        @engine.transaction
        def setup(tx):
            tx.switch_to_database("postgres")
            tx.execute(f"drop database if exists {test_db}", single=True)
            
            # Create the test database
            db = tx.database(test_db)
            if not db.exists():
                db.create()
            db.switch()

            # Call subclass-specific table creation with commit
            if hasattr(cls, 'create_test_tables'):
                cls.create_test_tables(tx)
        
        setup()

    @classmethod
    def tearDownClass(cls):
        """Clean up the test database."""
        @engine.transaction
        def cleanup(tx):
            tx.switch_to_database("postgres")
            tx.execute(f"drop database if exists {test_db}", single=True)
        
        cleanup()

    @classmethod
    def create_test_tables(cls, tx):
        """Override this method in subclasses to create test-specific tables."""
        pass
