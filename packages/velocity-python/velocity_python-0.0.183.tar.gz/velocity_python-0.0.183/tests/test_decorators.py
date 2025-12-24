import unittest
from unittest.mock import patch

from velocity.db import exceptions
from velocity.db.core.decorators import reset_id_on_dup_key, retry_on_dup_key


class DummyTx:
    def __init__(self):
        self.savepoints = []

    def create_savepoint(self, cursor=None):
        savepoint = object()
        self.savepoints.append(("create", savepoint))
        return savepoint

    def release_savepoint(self, savepoint, cursor=None):
        self.savepoints.append(("release", savepoint))

    def rollback_savepoint(self, savepoint, cursor=None):
        self.savepoints.append(("rollback", savepoint))


class DummyTable:
    def __init__(self):
        self.tx = DummyTx()
        self._cursor = object()
        self.sequence_updates = []
        self.last_max_column = None
        self.max_value = 7

    def cursor(self):
        return self._cursor

    def set_sequence(self, value):
        self.sequence_updates.append(value)

    def max(self, column):
        self.last_max_column = column
        return self.max_value


class ResetIdOnDupKeyTests(unittest.TestCase):
    def setUp(self):
        self.table = DummyTable()

    def test_retries_when_sys_id_duplicate(self):
        attempts = {"count": 0}

        @reset_id_on_dup_key
        def insert(self, data):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise exceptions.DbDuplicateKeyError(
                    'duplicate key value violates unique constraint "table_pkey"\nDETAIL: Key (sys_id)=(1) already exists.'
                )
            return "ok"

        with patch("velocity.db.core.decorators.time.sleep", return_value=None):
            result = insert(self.table, data={})

        self.assertEqual(result, "ok")
        self.assertEqual(attempts["count"], 2)
        self.assertEqual(self.table.sequence_updates, [self.table.max_value + 1])
        self.assertEqual(self.table.last_max_column, "sys_id")

    def test_retries_when_primary_constraint_name_only(self):
        attempts = {"count": 0}

        @reset_id_on_dup_key
        def insert(self, data):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise exceptions.DbDuplicateKeyError(
                    "Duplicate entry '1' for key 'PRIMARY'"
                )
            return "ok"

        with patch("velocity.db.core.decorators.time.sleep", return_value=None):
            result = insert(self.table, data={})

        self.assertEqual(result, "ok")
        self.assertEqual(attempts["count"], 2)
        self.assertEqual(self.table.sequence_updates, [self.table.max_value + 1])

    def test_raises_when_non_primary_duplicate(self):
        attempts = {"count": 0}

        @reset_id_on_dup_key
        def insert(self, data):
            attempts["count"] += 1
            raise exceptions.DbDuplicateKeyError(
                'duplicate key value violates unique constraint "table_email_key"'
            )

        with patch("velocity.db.core.decorators.time.sleep", return_value=None):
            with self.assertRaises(exceptions.DbDuplicateKeyError):
                insert(self.table, data={})

        self.assertEqual(attempts["count"], 1)
        self.assertEqual(self.table.sequence_updates, [])


class RetryOnDupKeyTests(unittest.TestCase):
    def setUp(self):
        self.table = DummyTable()

    def test_retries_for_primary_key_duplicate(self):
        attempts = {"count": 0}

        @retry_on_dup_key
        def operation(self):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise exceptions.DbDuplicateKeyError(
                    "Key (sys_id)=(1) already exists."
                )
            return "done"

        with patch("velocity.db.core.decorators.time.sleep", return_value=None):
            result = operation(self.table)

        self.assertEqual(result, "done")
        self.assertEqual(attempts["count"], 2)

    def test_retries_for_primary_keyword_only(self):
        attempts = {"count": 0}

        @retry_on_dup_key
        def operation(self):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise exceptions.DbDuplicateKeyError(
                    "Violation of PRIMARY KEY constraint"
                )
            return "done"

        with patch("velocity.db.core.decorators.time.sleep", return_value=None):
            result = operation(self.table)

        self.assertEqual(result, "done")
        self.assertEqual(attempts["count"], 2)

    def test_raises_for_non_primary_duplicate(self):
        @retry_on_dup_key
        def operation(self):
            raise exceptions.DbDuplicateKeyError(
                'duplicate key value violates unique constraint "table_email_key"'
            )

        with patch("velocity.db.core.decorators.time.sleep", return_value=None):
            with self.assertRaises(exceptions.DbDuplicateKeyError):
                operation(self.table)


if __name__ == "__main__":
    unittest.main()
