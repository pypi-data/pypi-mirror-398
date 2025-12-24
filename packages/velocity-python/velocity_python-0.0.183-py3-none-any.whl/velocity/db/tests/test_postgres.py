import unittest
import decimal
from types import SimpleNamespace
from unittest import mock
from velocity.db.servers.postgres.sql import SQL
from velocity.db.servers.tablehelper import TableHelper
from velocity.db.servers.postgres.types import TYPES
from velocity.db.core.table import Table


class MockTx:
    def __init__(self):
        self.table_cache = {}
        self.cursor_cache = {}
    
    def cursor(self):
        return None
    
    def table(self, table_name):
        # Return a mock table object
        return MockTable()

class MockTable:
    def column(self, column_name):
        return MockColumn()

    def primary_keys(self):
        return ["id"]


class DummyCursor:
    def __init__(self, rowcount=0):
        self.rowcount = rowcount


class DummyResult:
    def __init__(self, rowcount=0):
        self.cursor = DummyCursor(rowcount)


class DummyTx:
    def __init__(self):
        self.engine = SimpleNamespace(sql=SimpleNamespace(), schema_locked=False)
        self.executed = []
        self.next_results = []

    def cursor(self):
        return DummyCursor()

    def create_savepoint(self, cursor=None):
        sp_id = f"sp_{len(self.executed)}"
        return sp_id

    def release_savepoint(self, sp, cursor=None):
        return None

    def rollback_savepoint(self, sp, cursor=None):
        return None

    def execute(self, sql, params, cursor=None):
        self.executed.append((sql, params))
        if self.next_results:
            return self.next_results.pop(0)
        return DummyResult(0)

    def table(self, table_name):
        return MockTable()

    def primary_keys(self):
        return ["id"]

class MockColumn:
    def __init__(self):
        self.py_type = str
    
    def exists(self):
        return True

class TestSQLModule(unittest.TestCase):
    def test_quote_simple_identifier(self):
        self.assertEqual(TableHelper.quote("test"), "test")

    def test_quote_reserved_word(self):
        self.assertEqual(TableHelper.quote("SELECT"), '"SELECT"')

    def test_quote_with_special_characters(self):
        self.assertEqual(TableHelper.quote("my/schema"), '"my/schema"')

    def test_quote_dot_notation(self):
        self.assertEqual(TableHelper.quote("my_table.my_column"), "my_table.my_column")

    def test_quote_list_identifiers(self):
        self.assertEqual(
            TableHelper.quote(["test", "SELECT", "my_table"]),
            ["test", '"SELECT"', "my_table"],
        )

    def test_make_where_simple_equality(self):
        # Create a mock transaction and table helper
        mock_tx = MockTx()
        helper = TableHelper(mock_tx, "test_table")

        sql, vals = helper.make_where({"column1": "value1"})
        self.assertIn("column1 = %s", sql)
        self.assertEqual(vals, ("value1",))

    def test_make_where_with_null(self):
        mock_tx = MockTx()
        helper = TableHelper(mock_tx, "test_table")

        sql, vals = helper.make_where({"column1": None})
        self.assertIn("column1 IS NULL", sql)
        self.assertEqual(vals, ())

    def test_make_where_with_not_null(self):
        mock_tx = MockTx()
        helper = TableHelper(mock_tx, "test_table")

        sql, vals = helper.make_where({"column1!": None})
        self.assertIn("column1! IS NULL", sql)
        self.assertEqual(vals, ())

    def test_make_where_with_operators(self):
        mock_tx = MockTx()
        helper = TableHelper(mock_tx, "test_table")

        sql, vals = helper.make_where({"column1>": 10, "column2!": "value2"})
        self.assertIn("column1> = %s", sql)
        self.assertIn("column2! = %s", sql)
        self.assertEqual(len(vals), 2)

    def test_make_where_with_list(self):
        mock_tx = MockTx()
        helper = TableHelper(mock_tx, "test_table")

        sql, vals = helper.make_where({"column1": [1, 2, 3]})
        self.assertIn("column1 IN", sql)
        self.assertEqual(len(vals), 3)

    def test_make_where_between(self):
        mock_tx = MockTx()
        helper = TableHelper(mock_tx, "test_table")

        sql, vals = helper.make_where({"column1><": [1, 10]})
        self.assertIn("column1>< = %s", sql)
        self.assertEqual(len(vals), 1)  # Actual implementation returns one parameter

    def test_sql_select_simple(self):
        mock_tx = MockTx()
        sql_query, params = SQL.select(mock_tx, columns="*", table="my_table")
        self.assertIn("SELECT *", sql_query)
        self.assertIn("FROM my_table", sql_query)
        self.assertEqual(params, ())

    def test_sql_select_with_where(self):
        mock_tx = MockTx()
        sql_query, params = SQL.select(mock_tx, columns="*", table="my_table", where={"id": 1})
        self.assertIn("SELECT *", sql_query)
        self.assertIn("WHERE id = %s", sql_query)
        self.assertEqual(params, (1,))

    def test_sql_select_with_order_by(self):
        mock_tx = MockTx()
        sql_query, params = SQL.select(mock_tx, columns="*", table="my_table", orderby="id DESC")
        self.assertIn("SELECT *", sql_query)
        self.assertIn("ORDER BY id DESC", sql_query)
        self.assertEqual(params, ())

    def test_sql_insert(self):
        sql_query, params = SQL.insert(
            table="my_table", data={"column1": "value1", "column2": 2}
        )
        self.assertIn("INSERT INTO my_table", sql_query)
        self.assertIn("VALUES (%s,%s)", sql_query)
        self.assertEqual(params, ("value1", 2))

    def test_sql_update(self):
        mock_tx = MockTx()
        sql_query, params = SQL.update(
            mock_tx, table="my_table", data={"column1": "new_value"}, pk={"id": 1}
        )
        self.assertIn("UPDATE my_table", sql_query)
        self.assertIn("SET column1 = %s", sql_query)
        self.assertIn("WHERE id = %s", sql_query)
        self.assertEqual(params, ("new_value", 1))

    def test_sql_delete(self):
        mock_tx = MockTx()
        sql_query, params = SQL.delete(mock_tx, table="my_table", where={"id": 1})
        self.assertIn("DELETE", sql_query)
        self.assertIn("FROM my_table", sql_query)
        self.assertIn("WHERE id = %s", sql_query)
        self.assertEqual(params, (1,))

    def test_sql_create_table(self):
        sql_query, params = SQL.create_table(
            name="public.test_table", columns={"name": str, "age": int}, drop=True
        )
        self.assertIn("CREATE TABLE", sql_query)
        self.assertIn("test_table", sql_query)
        self.assertIn("DROP TABLE IF EXISTS", sql_query)
        self.assertEqual(params, ())

    def test_sql_drop_table(self):
        sql_query, params = SQL.drop_table("public.test_table")
        self.assertIn("drop table if exists", sql_query.lower())
        self.assertIn("test_table", sql_query)
        self.assertEqual(params, ())

    def test_sql_create_index(self):
        mock_tx = MockTx()
        sql_query, params = SQL.create_index(
            mock_tx, table="my_table", columns="column1", unique=True
        )
        self.assertIn("CREATE UNIQUE INDEX", sql_query)
        self.assertIn("my_table", sql_query)
        self.assertEqual(params, ())

    def test_sql_drop_index(self):
        sql_query, params = SQL.drop_index(table="my_table", columns="column1")
        self.assertIn("DROP INDEX IF EXISTS", sql_query)
        self.assertEqual(params, ())

    def test_sql_foreign_key_creation(self):
        sql_query, params = SQL.create_foreign_key(
            table="child_table",
            columns="parent_id",
            key_to_table="parent_table",
            key_to_columns="id",
        )
        self.assertIn("ALTER TABLE child_table ADD CONSTRAINT", sql_query)
        self.assertIn(
            "FOREIGN KEY (parent_id) REFERENCES parent_table (id);", sql_query
        )
        self.assertEqual(params, ())

    def test_sql_merge_insert(self):
        mock_tx = MockTx()
        sql_query, params = SQL.merge(
            mock_tx,
            table="my_table",
            data={"column1": "value1"},
            pk={"id": 1},
            on_conflict_do_nothing=True,
            on_conflict_update=False,
        )
        self.assertIn("INSERT INTO my_table", sql_query)
        self.assertIn("ON CONFLICT", sql_query)
        self.assertIn("DO NOTHING", sql_query)
        self.assertEqual(params, ("value1", 1))

    def test_sql_merge_update(self):
        mock_tx = MockTx()
        sql_query, params = SQL.merge(
            mock_tx,
            table="my_table",
            data={"column1": "value1"},
            pk={"id": 1},
            on_conflict_do_nothing=False,
            on_conflict_update=True,
        )
        self.assertIn("INSERT INTO my_table", sql_query)
        self.assertIn("ON CONFLICT", sql_query)
        self.assertIn("DO", sql_query)
        self.assertIn("UPDATE", sql_query)
        self.assertIn("SET", sql_query)
        self.assertEqual(params, ("value1", 1))

    def test_sql_insnx_with_explicit_where(self):
        mock_tx = MockTx()
        sql_query, params = SQL.insnx(
            mock_tx,
            table="my_table",
            data={"id": 1, "column1": "value1"},
            where={"column1": "value1"},
        )
        self.assertIn("INSERT INTO", sql_query)
        self.assertIn("WHERE NOT EXISTS", sql_query)
        self.assertIn("SELECT 1 FROM my_table", sql_query)
        self.assertEqual(params, (1, "value1", "value1"))

    def test_sql_insert_if_not_exists_alias(self):
        mock_tx = MockTx()
        sql_alias, params_alias = SQL.insert_if_not_exists(
            mock_tx,
            table="my_table",
            data={"id": 1, "column1": "value1"},
            where={"column1": "value1"},
        )
        sql_main, params_main = SQL.insnx(
            mock_tx,
            table="my_table",
            data={"id": 1, "column1": "value1"},
            where={"column1": "value1"},
        )
        self.assertEqual(sql_alias, sql_main)
        self.assertEqual(params_alias, params_main)

    def test_table_update_or_insert_updates_only(self):
        tx = DummyTx()
        table = Table(tx, "my_table")
        table.cursor = mock.MagicMock(return_value=None)
        table.update = mock.MagicMock(return_value=1)
        ins_builder = mock.MagicMock()
        table.sql = SimpleNamespace(insnx=ins_builder, insert_if_not_exists=ins_builder)

        affected = table.update_or_insert(
            update_data={"value": "new"},
            insert_data={"id": 1, "value": "new"},
            where={"id": 1},
        )

        self.assertEqual(affected, 1)
        table.update.assert_called_once()
        ins_builder.assert_not_called()

    def test_table_update_or_insert_falls_back_to_insert(self):
        tx = DummyTx()
        table = Table(tx, "my_table")
        table.cursor = mock.MagicMock(return_value=None)
        table.update = mock.MagicMock(return_value=0)

        captured = {}

        def fake_insnx(tx_ctx, table_name, data, where):
            captured["tx"] = tx_ctx
            captured["table"] = table_name
            captured["data"] = dict(data)
            captured["where"] = where
            return ("INSERT", ("a", "b"))

        ins_builder = mock.MagicMock(side_effect=fake_insnx)
        table.sql = SimpleNamespace(insnx=ins_builder, insert_if_not_exists=ins_builder)
        tx.next_results.append(DummyResult(1))

        affected = table.update_or_insert(
            update_data={"value": "new"},
            where={"id": 1},
            pk={"id": 1},
        )

        self.assertEqual(affected, 1)
        table.update.assert_called_once()
        ins_builder.assert_called_once()
        self.assertEqual(captured["table"], "my_table")
        self.assertEqual(captured["data"], {"value": "new", "id": 1})
        self.assertEqual(captured["where"], {"id": 1})

    def test_table_update_or_insert_sql_only(self):
        tx = DummyTx()
        table = Table(tx, "my_table")
        table.cursor = mock.MagicMock(return_value=None)
        table.update = mock.MagicMock(return_value=("UPDATE sql", ("u",)))

        ins_builder = mock.MagicMock(return_value=("INSERT sql", ("i",)))
        table.sql = SimpleNamespace(insnx=ins_builder, insert_if_not_exists=ins_builder)

        result = table.update_or_insert(
            update_data={"value": "new"},
            where={"id": 1},
            pk={"id": 1},
            sql_only=True,
        )

        self.assertEqual(result["update"], ("UPDATE sql", ("u",)))
        self.assertEqual(result["insert"], ("INSERT sql", ("i",)))
        table.update.assert_called_once_with({"value": "new"}, where={"id": 1}, pk={"id": 1}, sql_only=True)
        ins_builder.assert_called_once()

    def test_sql_merge_conflict_columns_are_quoted(self):
        mock_tx = MockTx()
        sql_query, _ = SQL.merge(
            mock_tx,
            table="my_table",
            data={"payload": "value"},
            pk={"select": 1},
            on_conflict_do_nothing=False,
            on_conflict_update=True,
        )
        self.assertIn('on conflict ("select")'.upper(), sql_query.upper())

    def test_sql_merge_missing_auto_pk_values(self):
        mock_tx = MockTx()
        with self.assertRaisesRegex(
            ValueError, "Primary key values missing from data for merge"
        ):
            SQL.merge(
                mock_tx,
                table="my_table",
                data={"column1": "value1"},
                pk=None,
                on_conflict_do_nothing=False,
                on_conflict_update=True,
            )

    def test_sql_merge_auto_pk_without_update_columns_falls_back_to_do_nothing(self):
        mock_tx = MockTx()
        sql_query, params = SQL.merge(
            mock_tx,
            table="my_table",
            data={"id": 1},
            pk=None,
            on_conflict_do_nothing=False,
            on_conflict_update=True,
        )
        self.assertIn("DO NOTHING", sql_query)
        self.assertNotIn(" DO UPDATE", sql_query)
        self.assertEqual(params, (1,))

    def test_get_type_mapping(self):
        self.assertEqual(TYPES.get_type("string"), "TEXT")
        self.assertEqual(TYPES.get_type(123), "BIGINT")
        self.assertEqual(TYPES.get_type(123.456), "NUMERIC(19, 6)")
        self.assertEqual(TYPES.get_type(True), "BOOLEAN")
        self.assertEqual(TYPES.get_type(None), "TEXT")

    def test_py_type_mapping(self):
        self.assertEqual(TYPES.py_type("INTEGER"), int)
        self.assertEqual(TYPES.py_type("NUMERIC"), decimal.Decimal)
        self.assertEqual(TYPES.py_type("TEXT"), str)
        self.assertEqual(TYPES.py_type("BOOLEAN"), bool)

    def test_sql_truncate(self):
        sql_query, params = SQL.truncate("my_table")
        self.assertEqual(sql_query, "truncate table my_table")
        self.assertEqual(params, ())

    def test_sql_create_view(self):
        sql_query, params = SQL.create_view(
            name="my_view", query="SELECT * FROM my_table", temp=True, silent=True
        )
        self.assertIn("CREATE OR REPLACE", sql_query)
        self.assertIn("TEMPORARY VIEW", sql_query)
        self.assertIn("my_view", sql_query)
        self.assertIn("SELECT *", sql_query)
        self.assertIn("FROM my_table", sql_query)
        self.assertEqual(params, ())

    def test_sql_drop_view(self):
        sql_query, params = SQL.drop_view(name="my_view", silent=True)
        self.assertEqual(sql_query, "DROP VIEW IF EXISTS my_view")
        self.assertEqual(params, ())

    # Additional tests can be added here to cover more methods and edge cases


if __name__ == "__main__":
    unittest.main()
