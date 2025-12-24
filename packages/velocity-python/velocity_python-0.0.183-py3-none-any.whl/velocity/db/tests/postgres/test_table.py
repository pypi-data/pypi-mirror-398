import re
import unittest
import sys
import os
from .common import CommonPostgresTest, engine, test_db


@engine.transaction
class TestTable(CommonPostgresTest):

    @classmethod
    def create_test_tables(cls, tx):
        """No special tables needed for table tests."""
        pass

    def test_init(self, tx):
        t = tx.table("test_table")
        assert t.exists() == False
        assert tx.tables() == []
        assert (
            str(t)
            == """Table: test_table
(table exists) False
Columns: 0
Rows: 0
"""
        )
        self.assertTrue(re.match(r"PostGreSQL\.transaction\(.*:test_db_postgres\)", str(tx)))

    def test_rollback(self, tx):
        t = tx.table("test_table")
        for i in range(10):
            t.insert(
                {
                    "fname": "test",
                    "lname": "test",
                    "email": "test@test.com",
                    "age": 1,
                    "address": "test",
                    "city": "test",
                    "state": "test",
                    "zipcode": "test",
                    "country": "test",
                }
            )
        assert (
            str(t)
            == """Table: test_table
(table exists) True
Columns: 10
Rows: 10
"""
        )
        tx.rollback()
        assert (
            str(t)
            == """Table: test_table
(table exists) False
Columns: 0
Rows: 0
"""
        )
        tx.table("test_table").drop()

    def test_drop(self, tx):
        t = tx.table("test_table")
        for i in range(10):
            t.insert(
                {
                    "fname": "test",
                    "lname": "test",
                    "email": "test@test.com",
                    "age": 1,
                    "address": "test",
                    "city": "test",
                    "state": "test",
                    "zipcode": "test",
                    "country": "test",
                }
            )
        assert (
            str(t)
            == """Table: test_table
(table exists) True
Columns: 10
Rows: 10
"""
        )
        tx.table("test_table").drop()
        assert (
            str(t)
            == """Table: test_table
(table exists) False
Columns: 0
Rows: 0
"""
        )


if __name__ == "__main__":
    unittest.main()
