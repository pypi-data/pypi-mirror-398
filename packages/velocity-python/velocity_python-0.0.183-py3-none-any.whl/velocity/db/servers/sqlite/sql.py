import re
import hashlib
import decimal
import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from collections.abc import Mapping, Sequence

from velocity.db import exceptions
from ..base.sql import BaseSQLDialect
from .reserved import reserved_words
from .types import TYPES
from .operators import OPERATORS, SQLiteOperators
from ..tablehelper import TableHelper


# Configure TableHelper for SQLite
TableHelper.reserved = reserved_words
TableHelper.operators = OPERATORS


system_fields = [
    "sys_id",
    "sys_created",
    "sys_modified",
    "sys_modified_by",
    "sys_dirty",
    "sys_table",
    "sys_modified_count",
    "sys_keywords",
]


def quote(data):
    """Quote SQLite identifiers."""
    if isinstance(data, list):
        return [quote(item) for item in data]
    else:
        parts = data.split(".")
        new = []
        for part in parts:
            if '"' in part:
                new.append(part)
            elif part.upper() in reserved_words:
                new.append('"' + part + '"')
            elif re.findall("[/]", part):
                new.append('"' + part + '"')
            else:
                new.append(part)
        return ".".join(new)


class SQL(BaseSQLDialect):
    server = "SQLite3"
    type_column_identifier = "type"
    is_nullable = "notnull"

    default_schema = ""

    # SQLite error codes (numeric)
    ApplicationErrorCodes = []
    DatabaseMissingErrorCodes = []  # SQLite creates databases on demand
    TableMissingErrorCodes = []     # Detected by error message
    ColumnMissingErrorCodes = []    # Detected by error message  
    ForeignKeyMissingErrorCodes = []
    ConnectionErrorCodes = []
    DuplicateKeyErrorCodes = []     # Detected by error message
    RetryTransactionCodes = []      # SQLITE_BUSY
    TruncationErrorCodes = []
    LockTimeoutErrorCodes = []      # SQLITE_BUSY
    DatabaseObjectExistsErrorCodes = []
    DataIntegrityErrorCodes = []

    types = TYPES

    @classmethod
    def get_error(cls, e):
        """Extract error information from SQLite exception."""
        # SQLite exceptions don't have error codes like other databases
        return None, str(e)

    @classmethod
    def select(
        cls,
        tx,
        columns=None,
        table=None,
        where=None,
        orderby=None,
        groupby=None,
        having=None,
        start=None,
        qty=None,
        lock=None,
        skip_locked=None,
    ):
        """Generate a SQLite SELECT statement."""
        if not table:
            raise ValueError("Table name is required")

        sql_parts = []
        vals = []

        # SELECT clause
        if columns is None:
            columns = ["*"]
        elif isinstance(columns, str):
            columns = [columns]
        
        sql_parts.append("SELECT")
        sql_parts.append(", ".join(columns))

        # FROM clause
        sql_parts.append("FROM")
        sql_parts.append(quote(table))

        # WHERE clause
        if where:
            where_sql, where_vals = cls._build_where(where)
            sql_parts.append("WHERE")
            sql_parts.append(where_sql)
            vals.extend(where_vals)

        # GROUP BY clause
        if groupby:
            if isinstance(groupby, str):
                groupby = [groupby]
            sql_parts.append("GROUP BY")
            sql_parts.append(", ".join(quote(col) for col in groupby))

        # HAVING clause
        if having:
            having_sql, having_vals = cls._build_where(having)
            sql_parts.append("HAVING")
            sql_parts.append(having_sql)
            vals.extend(having_vals)

        # ORDER BY clause
        if orderby:
            if isinstance(orderby, str):
                orderby = [orderby]
            elif isinstance(orderby, dict):
                orderby_list = []
                for col, direction in orderby.items():
                    orderby_list.append(f"{quote(col)} {direction.upper()}")
                orderby = orderby_list
            sql_parts.append("ORDER BY")
            sql_parts.append(", ".join(orderby))

        # LIMIT and OFFSET (SQLite syntax)
        if qty is not None:
            sql_parts.append(f"LIMIT {qty}")
            if start is not None:
                sql_parts.append(f"OFFSET {start}")

        # Note: SQLite doesn't support row-level locking like FOR UPDATE
        if lock:
            pass  # Ignored for SQLite

        return " ".join(sql_parts), vals

    @classmethod
    def _build_where(cls, where):
        """Build WHERE clause for SQLite."""
        if isinstance(where, str):
            return where, []
        
        if isinstance(where, dict):
            where = list(where.items())

        if not isinstance(where, (list, tuple)):
            raise ValueError("WHERE clause must be string, dict, or list")

        conditions = []
        vals = []

        for key, val in where:
            if val is None:
                if "!" in key:
                    key = key.replace("!", "")
                    conditions.append(f"{quote(key)} IS NOT NULL")
                else:
                    conditions.append(f"{quote(key)} IS NULL")
            elif isinstance(val, (list, tuple)):
                if "!" in key:
                    key = key.replace("!", "")
                    conditions.append(f"{quote(key)} NOT IN ({', '.join(['?'] * len(val))})")
                else:
                    conditions.append(f"{quote(key)} IN ({', '.join(['?'] * len(val))})")
                vals.extend(val)
            else:
                # Handle operators
                op = "="
                if "<>" in key:
                    key = key.replace("<>", "")
                    op = "<>"
                elif "!=" in key:
                    key = key.replace("!=", "")
                    op = "<>"
                elif "%" in key:
                    key = key.replace("%", "")
                    op = "LIKE"
                elif "!" in key:
                    key = key.replace("!", "")
                    op = "<>"

                conditions.append(f"{quote(key)} {op} ?")
                vals.append(val)

        return " AND ".join(conditions), vals

    @classmethod
    def insert(cls, table, data):
        """Generate an INSERT statement for SQLite."""
        if not data:
            raise ValueError("Data cannot be empty")

        columns = list(data.keys())
        values = list(data.values())
        
        sql_parts = [
            "INSERT INTO",
            quote(table),
            f"({', '.join(quote(col) for col in columns)})",
            "VALUES",
            f"({', '.join(['?'] * len(values))})"  # SQLite uses ? placeholders
        ]

        return " ".join(sql_parts), values

    @classmethod
    def update(cls, tx, table, data, where=None, pk=None, excluded=False):
        """Generate an UPDATE statement for SQLite."""
        if not data:
            raise ValueError("Data cannot be empty")
        
        if not where and not pk:
            raise ValueError("Either WHERE clause or primary key must be provided")

        # Build SET clause
        set_clauses = []
        vals = []
        
        for col, val in data.items():
            set_clauses.append(f"{quote(col)} = ?")
            vals.append(val)

        # Build WHERE clause
        if pk:
            if where:
                # Merge pk into where
                if isinstance(where, dict):
                    where.update(pk)
                else:
                    # Convert to dict for merging
                    where_dict = dict(where) if isinstance(where, (list, tuple)) else {}
                    where_dict.update(pk)
                    where = where_dict
            else:
                where = pk

        where_sql, where_vals = cls._build_where(where) if where else ("", [])

        sql_parts = [
            "UPDATE",
            quote(table),
            "SET",
            ", ".join(set_clauses)
        ]

        if where_sql:
            sql_parts.extend(["WHERE", where_sql])
            vals.extend(where_vals)

        return " ".join(sql_parts), vals

    @classmethod
    def delete(cls, tx, table, where):
        """Generate a DELETE statement for SQLite."""
        if not where:
            raise ValueError("WHERE clause is required for DELETE")

        where_sql, where_vals = cls._build_where(where)
        
        sql_parts = [
            "DELETE FROM",
            quote(table),
            "WHERE",
            where_sql
        ]

        return " ".join(sql_parts), where_vals

    @classmethod
    def merge(cls, tx, table, data, pk, on_conflict_do_nothing, on_conflict_update):
        """Generate an INSERT OR REPLACE/INSERT OR IGNORE statement for SQLite."""
        if on_conflict_do_nothing:
            # SQLite: INSERT OR IGNORE
            insert_sql, insert_vals = cls.insert(table, data)
            insert_sql = insert_sql.replace("INSERT INTO", "INSERT OR IGNORE INTO")
            return insert_sql, insert_vals
        elif on_conflict_update:
            # SQLite: INSERT OR REPLACE (simple replacement)
            insert_sql, insert_vals = cls.insert(table, data)
            insert_sql = insert_sql.replace("INSERT INTO", "INSERT OR REPLACE INTO")
            return insert_sql, insert_vals
        else:
            return cls.insert(table, data)

    # Metadata queries
    @classmethod
    def version(cls):
        return "SELECT sqlite_version()"

    @classmethod
    def timestamp(cls):
        return "SELECT datetime('now')"

    @classmethod
    def user(cls):
        return "SELECT 'sqlite_user'"  # SQLite doesn't have users

    @classmethod
    def databases(cls):
        return "PRAGMA database_list"

    @classmethod
    def schemas(cls):
        return "PRAGMA database_list"

    @classmethod
    def current_schema(cls):
        return "SELECT 'main'"  # SQLite default schema

    @classmethod
    def current_database(cls):
        return "SELECT 'main'"

    @classmethod
    def tables(cls, system=False):
        if system:
            return "SELECT name FROM sqlite_master WHERE type='table'"
        else:
            return "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"

    @classmethod
    def views(cls, system=False):
        return "SELECT name FROM sqlite_master WHERE type='view'"

    @classmethod
    def create_database(cls, name):
        return f"-- SQLite databases are files: {name}"

    @classmethod
    def drop_database(cls, name):
        return f"-- SQLite databases are files: {name}"

    @classmethod
    def create_table(cls, name, columns=None, drop=False):
        if not name or not isinstance(name, str):
            raise ValueError("Table name must be a non-empty string")

        columns = columns or {}
        table_identifier = quote(name)
        base_name = name.split(".")[-1].replace('"', "")
        base_name_sql = base_name.replace("'", "''")
        trigger_prefix = re.sub(r"[^0-9A-Za-z_]+", "_", f"cc_sysmod_{base_name}")

        statements = []
        if drop:
            statements.append(f"DROP TABLE IF EXISTS {table_identifier};")

        statements.append(
            f"""
CREATE TABLE {table_identifier} (
  "sys_id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "sys_table" TEXT,
  "sys_created" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "sys_modified" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "sys_modified_by" TEXT,
  "sys_modified_count" INTEGER NOT NULL DEFAULT 0,
  "sys_dirty" INTEGER NOT NULL DEFAULT 0,
                            "sys_keywords" TEXT
);
""".strip()
        )

        for key, val in columns.items():
            clean_key = re.sub("<>!=%", "", key)
            if clean_key in system_fields:
                continue
            col_type = TYPES.get_type(val)
            statements.append(
                f"ALTER TABLE {table_identifier} ADD COLUMN {quote(clean_key)} {col_type};"
            )

        statements.extend(
            [
                f"DROP TRIGGER IF EXISTS {trigger_prefix}_ai;",
                f"DROP TRIGGER IF EXISTS {trigger_prefix}_au;",
                f"""
CREATE TRIGGER {trigger_prefix}_ai
AFTER INSERT ON {table_identifier}
FOR EACH ROW
BEGIN
    UPDATE {table_identifier}
    SET sys_created = COALESCE(NEW.sys_created, CURRENT_TIMESTAMP),
        sys_modified = CURRENT_TIMESTAMP,
        sys_modified_count = 0,
        sys_dirty = COALESCE(NEW.sys_dirty, 0),
        sys_table = '{base_name_sql}'
    WHERE rowid = NEW.rowid;
END;
""".strip(),
                f"""
CREATE TRIGGER {trigger_prefix}_au
AFTER UPDATE ON {table_identifier}
FOR EACH ROW
BEGIN
    UPDATE {table_identifier}
    SET sys_created = OLD.sys_created,
        sys_modified = CURRENT_TIMESTAMP,
        sys_table = '{base_name_sql}',
        sys_dirty = CASE WHEN OLD.sys_dirty = 1 AND NEW.sys_dirty = 0 THEN 0 ELSE 1 END,
        sys_modified_count = CASE WHEN OLD.sys_dirty = 1 AND NEW.sys_dirty = 0 THEN COALESCE(OLD.sys_modified_count, 0) ELSE COALESCE(OLD.sys_modified_count, 0) + 1 END
    WHERE rowid = NEW.rowid;
END;
""".strip(),
            ]
        )

        return "\n".join(statements), tuple()

    @classmethod
    def ensure_system_columns(
        cls,
        name,
        existing_columns=None,
        force=False,
        existing_indexes=None,
    ):
        """Ensure SQLite tables maintain the Velocity system triggers/columns."""
        existing_columns = {col.lower() for col in existing_columns or []}

        table_identifier = quote(name)
        base_name = name.split(".")[-1].replace('"', "")
        base_name_sql = base_name.replace("'", "''")
        trigger_prefix = re.sub(r"[^0-9A-Za-z_]+", "_", f"cc_sysmod_{base_name}")

        has_count = "sys_modified_count" in existing_columns

        add_column = not has_count
        recreate_triggers = force or add_column

        if not recreate_triggers and not force:
            return None

        statements = []

        if add_column:
            statements.append(
                f"ALTER TABLE {table_identifier} ADD COLUMN sys_modified_count INTEGER NOT NULL DEFAULT 0;"
            )

        statements.append(
            f"UPDATE {table_identifier} SET sys_modified_count = 0 WHERE sys_modified_count IS NULL;"
        )

        statements.append(f"DROP TRIGGER IF EXISTS {trigger_prefix}_ai;")
        statements.append(f"DROP TRIGGER IF EXISTS {trigger_prefix}_au;")

        statements.extend(
            [
                f"""
CREATE TRIGGER {trigger_prefix}_ai
AFTER INSERT ON {table_identifier}
FOR EACH ROW
BEGIN
    UPDATE {table_identifier}
    SET sys_created = COALESCE(NEW.sys_created, CURRENT_TIMESTAMP),
        sys_modified = CURRENT_TIMESTAMP,
        sys_modified_count = 0,
        sys_dirty = COALESCE(NEW.sys_dirty, 0),
        sys_table = '{base_name_sql}'
    WHERE rowid = NEW.rowid;
END;
""".strip(),
                f"""
CREATE TRIGGER {trigger_prefix}_au
AFTER UPDATE ON {table_identifier}
FOR EACH ROW
BEGIN
    UPDATE {table_identifier}
    SET sys_created = OLD.sys_created,
        sys_modified = CURRENT_TIMESTAMP,
        sys_table = '{base_name_sql}',
        sys_dirty = CASE WHEN OLD.sys_dirty = 1 AND NEW.sys_dirty = 0 THEN 0 ELSE 1 END,
        sys_modified_count = CASE WHEN OLD.sys_dirty = 1 AND NEW.sys_dirty = 0 THEN COALESCE(OLD.sys_modified_count, 0) ELSE COALESCE(OLD.sys_modified_count, 0) + 1 END
    WHERE rowid = NEW.rowid;
END;
""".strip(),
            ]
        )

        return "\n".join(statements), tuple()

    @classmethod
    def drop_table(cls, name):
        return f"DROP TABLE {quote(name)}"

    @classmethod
    def truncate(cls, table):
        return f"DELETE FROM {quote(table)}"  # SQLite doesn't have TRUNCATE

    @classmethod
    def columns(cls, name):
        return f"PRAGMA table_info({quote(name)})"

    @classmethod
    def column_info(cls, table, name):
        return f"PRAGMA table_info({quote(table)})"

    @classmethod
    def drop_column(cls, table, name, cascade=True):
        # SQLite doesn't support DROP COLUMN directly
        return f"-- SQLite doesn't support DROP COLUMN for {table}.{name}"

    @classmethod
    def alter_add(cls, table, columns, null_allowed=True):
        alter_parts = []
        for col, col_type in columns.items():
            null_clause = "" if null_allowed else " NOT NULL"
            alter_parts.append(f"ALTER TABLE {quote(table)} ADD COLUMN {quote(col)} {col_type}{null_clause}")
        
        return "; ".join(alter_parts)

    @classmethod
    def alter_drop(cls, table, columns):
        return f"-- SQLite doesn't support DROP COLUMN for {table}"

    @classmethod
    def alter_column_by_type(cls, table, column, value, nullable=True):
        return f"-- SQLite doesn't support ALTER COLUMN for {table}.{column}"

    @classmethod
    def alter_column_by_sql(cls, table, column, value):
        return f"-- SQLite doesn't support ALTER COLUMN for {table}.{column}"

    @classmethod
    def rename_column(cls, table, orig, new):
        return f"ALTER TABLE {quote(table)} RENAME COLUMN {quote(orig)} TO {quote(new)}"

    @classmethod
    def rename_table(cls, table, new):
        return f"ALTER TABLE {quote(table)} RENAME TO {quote(new)}"

    @classmethod
    def primary_keys(cls, table):
        return f"PRAGMA table_info({quote(table)})"

    @classmethod
    def foreign_key_info(cls, table=None, column=None, schema=None):
        if table:
            return f"PRAGMA foreign_key_list({quote(table)})"
        else:
            return "-- SQLite foreign key info requires table name"

    @classmethod
    def create_foreign_key(cls, table, columns, key_to_table, key_to_columns, name=None, schema=None):
        # SQLite foreign keys must be defined at table creation time
        return f"-- SQLite foreign keys must be defined at table creation"

    @classmethod
    def drop_foreign_key(cls, table, columns, key_to_table=None, key_to_columns=None, name=None, schema=None):
        return f"-- SQLite foreign keys must be dropped by recreating table"

    @classmethod
    def create_index(cls, tx, table=None, columns=None, unique=False, direction=None, where=None, name=None, schema=None, trigram=None, lower=None):
        if name is None:
            name = f"idx_{table}_{'_'.join(columns)}"
        
        index_type = "UNIQUE INDEX" if unique else "INDEX"
        col_list = ", ".join(quote(col) for col in columns)
        
        sql = f"CREATE {index_type} {quote(name)} ON {quote(table)} ({col_list})"
        
        if where:
            sql += f" WHERE {where}"
        
        return sql

    @classmethod
    def drop_index(cls, table=None, columns=None, name=None, schema=None, trigram=None):
        if name is None:
            name = f"idx_{table}_{'_'.join(columns)}"
        
        return f"DROP INDEX {quote(name)}"

    @classmethod
    def indexes(cls, table):
        return f"PRAGMA index_list({quote(table)})"

    @classmethod
    def create_savepoint(cls, sp):
        return f"SAVEPOINT {sp}"

    @classmethod
    def release_savepoint(cls, sp):
        return f"RELEASE SAVEPOINT {sp}"

    @classmethod
    def rollback_savepoint(cls, sp):
        return f"ROLLBACK TO SAVEPOINT {sp}"

    @classmethod
    def create_view(cls, name, query, temp=False, silent=True):
        temp_clause = "TEMPORARY " if temp else ""
        return f"CREATE {temp_clause}VIEW {quote(name)} AS {query}"

    @classmethod
    def drop_view(cls, name, silent=True):
        if silent:
            return f"DROP VIEW IF EXISTS {quote(name)}"
        else:
            return f"DROP VIEW {quote(name)}"

    @classmethod
    def last_id(cls, table):
        return "SELECT last_insert_rowid()"

    @classmethod
    def current_id(cls, table):
        return f"SELECT seq FROM sqlite_sequence WHERE name = '{table}'"

    @classmethod
    def set_id(cls, table, start):
        return f"UPDATE sqlite_sequence SET seq = {start} WHERE name = '{table}'"

    @classmethod
    def set_sequence(cls, table, next_value):
        return f"UPDATE sqlite_sequence SET seq = {next_value} WHERE name = '{table}'"

    @classmethod
    def massage_data(cls, data):
        """Massage data before insert/update operations."""
        # SQLite-specific data transformations
        massaged = {}
        for key, value in data.items():
            if isinstance(value, bool):
                # Convert boolean to integer for SQLite
                massaged[key] = 1 if value else 0
            else:
                massaged[key] = value
        return massaged

    @classmethod
    def alter_trigger(cls, table, state="ENABLE", name="USER"):
        return f"-- SQLite trigger management for {table}"

    @classmethod
    def missing(cls, tx, table, list_values, column="SYS_ID", where=None):
        """Generate query to find missing values from a list."""
        # SQLite version using WITH clause
        value_list = ", ".join([f"({i}, ?)" for i in range(len(list_values))])
        
        sql = f"""
        WITH input_values(pos, val) AS (
            VALUES {value_list}
        )
        SELECT val FROM input_values 
        WHERE val NOT IN (
            SELECT {quote(column)} FROM {quote(table)}
        """
        
        vals = list_values
        
        if where:
            where_sql, where_vals = cls._build_where(where)
            sql += f" WHERE {where_sql}"
            vals.extend(where_vals)
        
        sql += ") ORDER BY pos"
        
        return sql, vals
