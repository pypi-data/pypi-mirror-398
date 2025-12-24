import unittest
from velocity.db.servers import postgres
import random

test_db = "test_foreign_key_db"
engine = postgres.initialize(
    database=test_db,
)
print(engine)


@engine.transaction  # Decorator to run the test in a transaction
class TestSQLModule(unittest.TestCase):

    @classmethod
    def setUpClass(cls, tx):
        tx.switch_to_database("postgres")
        tx.execute(f"drop database if exists {test_db}", single=True)
        # Drop and recreate the test database to ensure a clean environment
        db = tx.database(test_db)
        if db.exists():
            # Possibly drop if needed, or just recreate if the environment ensures cleanliness
            pass
        else:
            db.create()
        db.switch()

        cls.create_tables(tx)
        cls.insert_data(tx)

    @classmethod
    def create_tables(cls, tx):
        # Table with normal columns
        tx.table("normal_table").create(
            columns={
                "name": str,
                "active": bool,
                "value": float,
            }
        )

        # Table with "aggregate-like" column names
        # and a reserved keyword as a column name (e.g. "order")
        tx.table("weird_names_table").create(
            columns={
                "Sum_info": str,  # Looks like SUM but isn't
                "MAX_hours": int,  # Starts with MAX but not necessarily aggregate
                "order": str,  # reserved keyword in SQL, test quoting
            }
        )

        # Parent and child tables to test foreign keys and multiple pointers
        tx.table("fk_parent").create(
            columns={
                "parent_name": str,
                "num_things": int,
                "is_valid": bool,
            }
        )
        tx.table("fk_middle").create(
            columns={
                "parent_id": int,
                "title": str,
            }
        )
        tx.table("fk_middle").create_foreign_key("parent_id", "fk_parent", "sys_id")

        tx.table("fk_child").create(
            columns={"parent_id": int, "middle_id": int, "description": str}
        )
        tx.table("fk_child").create_foreign_key("parent_id", "fk_parent", "sys_id")
        tx.table("fk_child").create_foreign_key("middle_id", "fk_middle", "sys_id")

        # Another table for testing multiple foreign references to the same table
        tx.table("fk_self_ref").create(
            columns={
                "ref_id": int,
                "info": str,
            }
        )
        # A self referencing foreign key (if supported by environment)
        tx.table("fk_self_ref").create_foreign_key("ref_id", "fk_self_ref", "sys_id")

        # Table to test special operators and placeholders
        tx.table("special_values_table").create(
            columns={
                "name": str,
                "status": str,
                "score": float,
            }
        )

    @classmethod
    def insert_data(cls, tx):
        normal_table = tx.table("normal_table")
        normal_table.upsert(
            {"sys_id": 1, "name": "Alpha", "active": True, "value": 10.5}
        )
        normal_table.upsert(
            {"sys_id": 2, "name": "Beta", "active": False, "value": None}
        )

        weird = tx.table("weird_names_table")
        weird.upsert(
            {
                "sys_id": 10,
                "Sum_info": "Not an Aggregate",
                "MAX_hours": 40,
                "order": "first",
            }
        )
        weird.upsert(
            {"sys_id": 20, "Sum_info": "Also Not", "MAX_hours": 50, "order": "second"}
        )

        parent = tx.table("fk_parent")
        parent.upsert({"sys_id": 100, "parent_name": "P1"})
        parent.upsert({"sys_id": 200, "parent_name": "P2"})

        middle = tx.table("fk_middle")
        middle.upsert({"sys_id": 300, "parent_id": 100, "title": "M1"})
        middle.upsert({"sys_id": 400, "parent_id": 200, "title": "M2"})

        child = tx.table("fk_child")
        child.upsert(
            {"sys_id": 500, "parent_id": 100, "middle_id": 300, "description": "C1"}
        )
        child.upsert(
            {"sys_id": 600, "parent_id": 200, "middle_id": 400, "description": "C2"}
        )

        self_ref = tx.table("fk_self_ref")
        self_ref.upsert({"sys_id": 700, "ref_id": None, "info": "root"})
        self_ref.upsert({"sys_id": 800, "ref_id": 700, "info": "child_of_700"})
        self_ref.upsert({"sys_id": 900, "ref_id": 800, "info": "child_of_800"})

        special = tx.table("special_values_table")
        special.upsert(
            {
                "sys_id": 1000,
                "name": "Infinite Score",
                "status": "open",
                "score": 9999.99,
            }
        )
        special.upsert(
            {"sys_id": 1100, "name": "Unknown Value", "status": None, "score": None}
        )
        special.upsert(
            {"sys_id": 1200, "name": "Regular Entry", "status": "closed", "score": 100}
        )

        emails = [
            "test.user1@example.com",
            "demo.account@domain.com", 
            "sample.email@test.com",
            "mock.data@company.com",
            "placeholder@example.com",
            "testcase@domain.com",
            "fakeuser@test.com",
            "demodata@company.com",
        ]
        for i in range(10):
            special.upsert(
                {
                    "sys_id": 1300 + i,
                    "name": f"Entry {i}",
                    "status": "open",
                    "score": i * 10,
                    "email": random.choice(emails),
                }
            )

    # @classmethod
    # def tearDownClass(cls, tx):
    #     tx.switch_to_database("postgres")
    #     tx.execute(f"drop database if exists {test_db}", single=True)
