import unittest
import sys
import os
from .common import CommonPostgresTest, engine, test_db


@engine.transaction
@engine.transaction
class TestFeatures(CommonPostgresTest):
    
    @classmethod
    def create_test_tables(cls, tx):
        """Clean up any existing tables for general usage tests."""
        # Ensure clean state by dropping tables if they exist
        tx.table("names").drop()
        tx.table("addresses").drop()

    def test_foreign_key(self, tx):
        first = tx.table("names")
        second = tx.table("addresses")
        first.create(
            {
                "first_name": str,
                "last_name": str,
            }
        )
        second.create(
            {
                "address": str,
                "address2": str,
                "city": str,
                "state": str,
                "zipcode": str,
                "country": str,
                "name_id": int,
            }
        )
        tx.commit()
        second.create_foreign_key("name_id", "names", "sys_id")
        first.insert(
            {
                "first_name": "John",
                "last_name": "Doe",
            }
        )
        tx.commit()
        second.insert(
            {
                "address": "123 Main St",
                "address2": "Apt 123",
                "city": "New York",
                "state": "NY",
                "zipcode": "12345",
                "country": "USA",
                "name_id": 1001,
            }
        )
        second.insert(
            {
                "address": "123 Main St",
                "address2": "Apt 123",
                "city": "New York",
                "state": "NY",
                "zipcode": "12345",
                "country": "USA",
                "name_id": 1001,
            }
        )
        second.insert(
            {
                "address": "123 Main St",
                "address2": "Apt 123",
                "city": "New York",
                "state": "NY",
                "zipcode": "12345",
                "country": "USA",
                "name_id": 1001,
            }
        )
        addresses = second.select(where={"name_id": 1001})
        # for address in addresses:
        #     print(address)

        first.drop()


if __name__ == "__main__":
    unittest.main()
