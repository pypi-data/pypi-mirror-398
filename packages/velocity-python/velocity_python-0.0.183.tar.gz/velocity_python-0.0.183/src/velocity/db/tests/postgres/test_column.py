import unittest
from velocity.db.core.column import Column
from velocity.db.exceptions import DbColumnMissingError
from .common import CommonPostgresTest, engine, test_db


@engine.transaction
@engine.transaction
class TestColumn(CommonPostgresTest):
    
    @classmethod
    def create_test_tables(cls, tx):
        """Create test tables for column tests."""
        tx.table("mock_table").create(
            columns={
                "column1": int,
                "column2": str,
                "column3": str,
            }
        )
    
    def test_init(self, tx):
        column = tx.table("mock_table").column("column1")
        self.assertIsInstance(column, Column)
        self.assertEqual(column.name, "column1")


if __name__ == "__main__":
    unittest.main()
