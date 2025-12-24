import unittest
from .common import CommonPostgresTest, engine, test_db


@engine.transaction
@engine.transaction
class TestConnections(CommonPostgresTest):
    
    @classmethod
    def create_test_tables(cls, tx):
        """Create test tables for connection tests."""
        tx.table("mock_table").create(
            columns={
                "column1": int,
                "column2": str,
                "column3": str,
            }
        )
    def test_init(self, tx):
        # Test the initialization of the Database object
        assert tx.table("mock_table").exists()


if __name__ == "__main__":
    unittest.main()
