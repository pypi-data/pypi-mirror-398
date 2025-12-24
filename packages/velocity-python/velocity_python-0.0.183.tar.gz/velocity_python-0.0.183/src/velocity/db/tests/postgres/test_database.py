import unittest
from velocity.db.core.database import Database
from .common import CommonPostgresTest, engine, test_db


@engine.transaction
@engine.transaction
class TestDatabase(CommonPostgresTest):

    @classmethod
    def create_test_tables(cls, tx):
        """No special tables needed for database tests."""
        pass

    def test_init(self, tx):
        # Test the initialization of the Database object
        tx.database


if __name__ == "__main__":
    unittest.main()
