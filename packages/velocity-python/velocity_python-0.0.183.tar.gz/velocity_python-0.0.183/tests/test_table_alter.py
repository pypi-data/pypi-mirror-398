import datetime
import unittest

from velocity.db.core.table import Table
from velocity.db.servers.postgres import types as postgres_types
from velocity.db.servers.mysql import types as mysql_types
from velocity.db.servers.sqlserver import types as sqlserver_types


class RecordingSQL:
    def __init__(self, server, types_module):
        self.server = server
        self.types = types_module.TYPES
        self.calls = []

    def alter_add(self, table, columns, null_allowed=True):
        self.calls.append(("alter_add", table, columns, null_allowed))
        return (f"ALTER_ADD {columns}", tuple())

    def alter_column_by_type(self, table, column, value, nullable=True):
        self.calls.append(("alter_column_by_type", table, column, value, nullable))
        return (f"ALTER_TYPE {column} {value}", tuple())

    def alter_column_by_sql(self, table, column, value):
        self.calls.append(("alter_column_by_sql", table, column, value))
        return (f"ALTER_SQL {column} {value}", tuple())


class FakeEngine:
    def __init__(self, sql):
        self.sql = sql
        self.schema_locked = False


class FakeTx:
    def __init__(self, engine):
        self.engine = engine
        self.executed = []
        self._cursor = object()
        self.savepoints = []

    def cursor(self):
        return self._cursor

    def execute(self, sql, vals, cursor=None):
        self.executed.append((sql, vals))
        return None

    def create_savepoint(self, cursor=None):
        token = object()
        self.savepoints.append(("create", token))
        return token

    def release_savepoint(self, token, cursor=None):
        self.savepoints.append(("release", token))

    def rollback_savepoint(self, token, cursor=None):
        self.savepoints.append(("rollback", token))


class FakeColumn:
    def __init__(self, sql_type, nullable):
        self._sql_type = sql_type
        self._nullable = nullable

    @property
    def sql_type(self):
        return self._sql_type

    @property
    def is_nullable(self):
        if isinstance(self._nullable, str):
            return self._nullable
        return "YES" if self._nullable else "NO"


class FakeTable(Table):
    def __init__(self, sql, columns_info):
        engine = FakeEngine(sql)
        tx = FakeTx(engine)
        normalized = {
            name.lower(): {
                "type": info.get("type", "TEXT"),
                "nullable": info.get("nullable", True),
            }
            for name, info in columns_info.items()
        }
        self._columns_info = normalized
        super().__init__(tx, "fake_table")

    def sys_columns(self, **kwds):
        return list(self._columns_info.keys())

    def column(self, name):
        info = self._columns_info[name]
        return FakeColumn(info["type"], info["nullable"])


class TableAlterTests(unittest.TestCase):
    def test_postgres_type_change_uses_python_type(self):
        sql = RecordingSQL("PostGreSQL", postgres_types)
        table = FakeTable(sql, {"campaign_end_date": {"type": "TEXT", "nullable": True}})

        table.alter({"campaign_end_date": datetime.datetime})

        self.assertEqual(len(sql.calls), 1)
        call = sql.calls[0]
        self.assertEqual(call[0], "alter_column_by_type")
        self.assertEqual(call[2], "campaign_end_date")
        self.assertIs(call[3], datetime.datetime)
        self.assertTrue(call[4])
        self.assertEqual(len(table.tx.executed), 1)

    def test_mysql_type_change_uses_concrete_sql_type(self):
        sql = RecordingSQL("MySQL", mysql_types)
        table = FakeTable(sql, {"campaign_end_date": {"type": "TEXT", "nullable": True}})

        table.alter({"campaign_end_date": datetime.datetime})

        self.assertEqual(len(sql.calls), 1)
        call = sql.calls[0]
        self.assertEqual(call[0], "alter_column_by_type")
        self.assertEqual(call[3], "DATETIME")
        self.assertTrue(call[4])

    def test_sqlserver_type_change_uses_concrete_sql_type(self):
        sql = RecordingSQL("SQLServer", sqlserver_types)
        table = FakeTable(sql, {"campaign_end_date": {"type": "TEXT", "nullable": True}})

        table.alter({"campaign_end_date": datetime.datetime})

        self.assertEqual(len(sql.calls), 1)
        call = sql.calls[0]
        self.assertEqual(call[0], "alter_column_by_type")
        self.assertTrue(call[3].startswith("DATETIME"))
        self.assertTrue(call[4])

    def test_add_new_column_enforces_not_null_override(self):
        sql = RecordingSQL("PostGreSQL", postgres_types)
        table = FakeTable(sql, {})

        table.alter({"new_col": {"type": int, "nullable": False}})

        self.assertEqual(len(sql.calls), 2)
        add_call = sql.calls[0]
        self.assertEqual(add_call[0], "alter_add")
        self.assertIn("new_col", add_call[2])
        self.assertEqual(sql.calls[1][0], "alter_column_by_sql")
        self.assertIn("SET NOT NULL", sql.calls[1][3])

    def test_alter_add_skips_existing_columns(self):
        sql = RecordingSQL("PostGreSQL", postgres_types)
        table = FakeTable(sql, {"name": {"type": "TEXT", "nullable": True}})

        table.alter_add({"name": str, "bonus": str})

        self.assertEqual(len(sql.calls), 1)
        call = sql.calls[0]
        self.assertEqual(call[0], "alter_add")
        self.assertEqual(set(call[2].keys()), {"bonus"})


if __name__ == "__main__":
    unittest.main()
