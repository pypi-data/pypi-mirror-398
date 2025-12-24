#!/usr/bin/env python3
"""Integration test for sys_modified_count triggers against the demo PostgreSQL database."""

import sys
import unittest
import uuid
from pathlib import Path

# Ensure the shared secrets package (contains env.py) is on the path.
REPO_ROOT = Path(__file__).resolve().parents[1]
SECRETS_PATH = REPO_ROOT.parent / "caringcent" / "secrets"
if str(SECRETS_PATH) not in sys.path:
    sys.path.append(str(SECRETS_PATH))

import env
from velocity.db.servers import postgres

# Ensure we are pointed at the demo environment before opening any connections.
env.set("demo")

engine = postgres.initialize()


class TestSysModifiedCountDemo(unittest.TestCase):
    """Exercises the new sys_modified_count wiring against the demo PostgreSQL database."""

    @classmethod
    def setUpClass(cls):
        cls.table_name = f"tmp_sys_mod_{uuid.uuid4().hex[:12]}"

        @engine.transaction
        def setup(tx):
            table = tx.table(cls.table_name)
            table.drop()
            table.create(columns={"custom_value": "sample"})

        setup()

    @classmethod
    def tearDownClass(cls):
        @engine.transaction
        def cleanup(tx):
            tx.table(cls.table_name).drop()

        cleanup()

    def test_sys_modified_count_triggers_increment(self):
        table_name = self.table_name

        @engine.transaction
        def run(tx):
            table = tx.table(table_name)
            row = table.new({"custom_value": "initial"})

            row_data = row.to_dict()
            self.assertEqual(row_data["sys_modified_count"], 0, "insert should reset modified count")
            self.assertFalse(row_data["sys_dirty"], "insert should start clean")
            self.assertEqual(row_data["sys_table"], table_name)

            row["custom_value"] = "updated"
            updated = row.to_dict()
            self.assertEqual(updated["sys_modified_count"], 1)
            self.assertTrue(updated["sys_dirty"])

            # Ensure the helper no-ops when the system columns already exist.
            self.assertIsNone(table.ensure_system_columns())

            row["custom_value"] = "final"
            final = row.to_dict()
            self.assertEqual(final["sys_modified_count"], 2)
            self.assertTrue(final["sys_dirty"])

        run()


if __name__ == "__main__":
    unittest.main()
