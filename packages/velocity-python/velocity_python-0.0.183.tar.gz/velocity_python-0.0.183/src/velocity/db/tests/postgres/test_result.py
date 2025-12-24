import unittest
from velocity.db.core.result import Result
from .common import CommonPostgresTest, engine, test_db


@engine.transaction
@engine.transaction
class TestResult(CommonPostgresTest):
    
    @classmethod
    def create_test_tables(cls, tx):
        """No special tables needed for result tests."""
        pass
    def test_result_all(self, tx):
        result = tx.execute("SELECT current_timestamp")


if __name__ == "__main__":
    unittest.main()
