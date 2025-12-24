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
from .operators import OPERATORS, SQLServerOperators
from ..tablehelper import TableHelper


# Configure TableHelper for SQL Server
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
    """Quote SQL Server identifiers."""
    if isinstance(data, list):
        return [quote(item) for item in data]
    else:
        parts = data.split(".")
        new = []
        for part in parts:
            if "[" in part:
                new.append(part)
            elif part.upper() in reserved_words:
                new.append("[" + part + "]")
            elif re.findall("[/]", part):
                new.append("[" + part + "]")
            else:
                new.append(part)
        return ".".join(new)


class SQL(BaseSQLDialect):
    server = "SQL Server"
    type_column_identifier = "DATA_TYPE"
    is_nullable = "IS_NULLABLE"

    default_schema = "dbo"

    # SQL Server error numbers
    ApplicationErrorCodes = []
    DatabaseMissingErrorCodes = ["911"]  # Database not found
    TableMissingErrorCodes = ["208"]     # Invalid object name
    ColumnMissingErrorCodes = ["207"]    # Invalid column name
    ForeignKeyMissingErrorCodes = ["1759"] # Foreign key error
    ConnectionErrorCodes = ["2", "53", "1326"] # Connection errors
    DuplicateKeyErrorCodes = ["2627", "2601"]  # Primary key / unique constraint
    RetryTransactionCodes = ["1205"]     # Deadlock
    TruncationErrorCodes = ["8152"]      # String truncation
    LockTimeoutErrorCodes = ["1222"]     # Lock request timeout
    DatabaseObjectExistsErrorCodes = ["2714"] # Object already exists
    DataIntegrityErrorCodes = ["547", "515"] # Foreign key, null constraint

    types = TYPES

    @classmethod
    def get_error(cls, e):
        """Extract error information from SQL Server exception."""
        # pytds exceptions have different attributes
        error_number = getattr(e, "number", None) or getattr(e, "msgno", None)
        error_message = getattr(e, "message", None) or str(e)
        return error_number, error_message

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
        """Generate a SQL Server SELECT statement."""
        if not table:
            raise ValueError("Table name is required")

        sql_parts = []
        vals = []

        # SELECT clause with TOP (SQL Server pagination)
        sql_parts.append("SELECT")
        
        # Handle TOP clause for SQL Server pagination
        if qty is not None and start is None:
            sql_parts.append(f"TOP {qty}")

        # Column selection
        if columns is None:
            columns = ["*"]
        elif isinstance(columns, str):
            columns = [columns]
        
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

        # ORDER BY clause (required for OFFSET/FETCH)
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
        elif start is not None:
            # ORDER BY is required for OFFSET/FETCH in SQL Server
            sql_parts.append("ORDER BY")
            sql_parts.append("(SELECT NULL)")

        # OFFSET and FETCH (SQL Server 2012+)
        if start is not None:
            sql_parts.append(f"OFFSET {start} ROWS")
            if qty is not None:
                sql_parts.append(f"FETCH NEXT {qty} ROWS ONLY")

        # Locking hints
        if lock:
            sql_parts.append("WITH (UPDLOCK)")
            if skip_locked:
                sql_parts.append("WITH (READPAST)")

        return " ".join(sql_parts), vals

    @classmethod
    def _build_where(cls, where):
        """Build WHERE clause for SQL Server."""
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
        """Generate an INSERT statement for SQL Server."""
        if not data:
            raise ValueError("Data cannot be empty")

        columns = list(data.keys())
        values = list(data.values())
        
        sql_parts = [
            "INSERT INTO",
            quote(table),
            f"({', '.join(quote(col) for col in columns)})",
            "VALUES",
            f"({', '.join(['?'] * len(values))})"  # SQL Server uses ? placeholders
        ]

        return " ".join(sql_parts), values

    @classmethod
    def update(cls, tx, table, data, where=None, pk=None, excluded=False):
        """Generate an UPDATE statement for SQL Server."""
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
        """Generate a DELETE statement for SQL Server."""
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
        """Generate a MERGE statement for SQL Server."""
        # SQL Server MERGE is complex - simplified version
        if on_conflict_do_nothing:
            # Use IF NOT EXISTS pattern
            pk_conditions = " AND ".join([f"{quote(k)} = ?" for k in pk.keys()])
            pk_values = list(pk.values())
            
            insert_sql, insert_vals = cls.insert(table, data)
            wrapped_sql = f"""
            IF NOT EXISTS (SELECT 1 FROM {quote(table)} WHERE {pk_conditions})
            BEGIN
                {insert_sql}
            END
            """
            return wrapped_sql, pk_values + insert_vals
        elif on_conflict_update:
            # Use actual MERGE statement
            pk_columns = list(pk.keys())
            data_columns = [k for k in data.keys() if k not in pk_columns]
            
            # Build MERGE statement
            merge_parts = [
                f"MERGE {quote(table)} AS target",
                f"USING (SELECT {', '.join(['?' for _ in data])} AS ({', '.join(quote(k) for k in data.keys())})) AS source",
                f"ON ({' AND '.join([f'target.{quote(k)} = source.{quote(k)}' for k in pk_columns])})",
                "WHEN MATCHED THEN",
                f"UPDATE SET {', '.join([f'{quote(k)} = source.{quote(k)}' for k in data_columns])}",
                "WHEN NOT MATCHED THEN",
                f"INSERT ({', '.join(quote(k) for k in data.keys())})",
                f"VALUES ({', '.join([f'source.{quote(k)}' for k in data.keys()])});",
            ]
            
            return " ".join(merge_parts), list(data.values())
        else:
            return cls.insert(table, data)

    # Metadata queries
    @classmethod
    def version(cls):
        return "SELECT @@VERSION"

    @classmethod
    def timestamp(cls):
        return "SELECT GETDATE()"

    @classmethod
    def user(cls):
        return "SELECT SYSTEM_USER"

    @classmethod
    def databases(cls):
        return "SELECT name FROM sys.databases WHERE database_id > 4"

    @classmethod
    def schemas(cls):
        return "SELECT name FROM sys.schemas"

    @classmethod
    def current_schema(cls):
        return "SELECT SCHEMA_NAME()"

    @classmethod
    def current_database(cls):
        return "SELECT DB_NAME()"

    @classmethod
    def tables(cls, system=False):
        if system:
            return "SELECT name FROM sys.tables"
        else:
            return "SELECT name FROM sys.tables WHERE is_ms_shipped = 0"

    @classmethod
    def views(cls, system=False):
        if system:
            return "SELECT name FROM sys.views"
        else:
            return "SELECT name FROM sys.views WHERE is_ms_shipped = 0"

    @classmethod
    def create_database(cls, name):
        return f"CREATE DATABASE {quote(name)}"

    @classmethod
    def drop_database(cls, name):
        return f"DROP DATABASE {quote(name)}"

    @classmethod
    def create_table(cls, name, columns=None, drop=False):
        if not name or not isinstance(name, str):
            raise ValueError("Table name must be a non-empty string")

        columns = columns or {}

        if "." in name:
            schema_part, table_part = name.split(".", 1)
        else:
            schema_part = cls.default_schema or "dbo"
            table_part = name

        schema_identifier = quote(schema_part)
        table_identifier = quote(name if "." in name else f"{schema_part}.{table_part}")
        base_name = table_part.replace("[", "").replace("]", "")
        base_name_sql = base_name.replace("'", "''")
        trigger_prefix = re.sub(r"[^0-9A-Za-z_]+", "_", f"CC_SYS_MOD_{base_name}")

        statements = []
        if drop:
            statements.append(f"IF OBJECT_ID(N'{table_identifier}', N'U') IS NOT NULL DROP TABLE {table_identifier};")

        statements.append(
            f"""
CREATE TABLE {table_identifier} (
  [sys_id] BIGINT IDENTITY(1,1) PRIMARY KEY,
  [sys_table] NVARCHAR(255),
  [sys_created] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
  [sys_modified] DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
  [sys_modified_by] NVARCHAR(255),
  [sys_modified_count] INT NOT NULL DEFAULT 0,
  [sys_dirty] BIT NOT NULL DEFAULT 0,
    [sys_keywords] NVARCHAR(MAX)
);
""".strip()
        )

        for key, val in columns.items():
            clean_key = re.sub("<>!=%", "", key)
            if clean_key in system_fields:
                continue
            col_type = TYPES.get_type(val)
            statements.append(
                f"ALTER TABLE {table_identifier} ADD {quote(clean_key)} {col_type};"
            )

        statements.extend(
            [
                f"IF OBJECT_ID(N'{schema_identifier}.{trigger_prefix}_insert', N'TR') IS NOT NULL DROP TRIGGER {schema_identifier}.{trigger_prefix}_insert;",
                f"IF OBJECT_ID(N'{schema_identifier}.{trigger_prefix}_update', N'TR') IS NOT NULL DROP TRIGGER {schema_identifier}.{trigger_prefix}_update;",
                f"""
CREATE TRIGGER {schema_identifier}.{trigger_prefix}_insert
ON {table_identifier}
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE t
    SET sys_created = ISNULL(i.sys_created, SYSDATETIME()),
        sys_modified = SYSDATETIME(),
        sys_modified_count = 0,
        sys_dirty = ISNULL(i.sys_dirty, 0),
        sys_table = '{base_name_sql}'
    FROM {table_identifier} AS t
    INNER JOIN inserted AS i ON t.sys_id = i.sys_id;
END;
""".strip(),
                f"""
CREATE TRIGGER {schema_identifier}.{trigger_prefix}_update
ON {table_identifier}
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE t
    SET sys_created = d.sys_created,
        sys_modified = SYSDATETIME(),
        sys_table = '{base_name_sql}',
        sys_dirty = CASE WHEN d.sys_dirty = 1 AND i.sys_dirty = 0 THEN 0 ELSE 1 END,
        sys_modified_count = CASE WHEN d.sys_dirty = 1 AND i.sys_dirty = 0 THEN ISNULL(d.sys_modified_count, 0) ELSE ISNULL(d.sys_modified_count, 0) + 1 END
    FROM {table_identifier} AS t
    INNER JOIN inserted AS i ON t.sys_id = i.sys_id
    INNER JOIN deleted AS d ON d.sys_id = i.sys_id;
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
        """Ensure SQL Server tables maintain Velocity system metadata."""
        existing_columns = {col.lower() for col in existing_columns or []}

        if "." in name:
            schema, table_name = name.split(".", 1)
        else:
            schema = cls.default_schema or "dbo"
            table_name = name

        schema_identifier = quote(schema)
        table_identifier = quote(name if "." in name else f"{schema}.{table_name}")
        object_name = f"[{schema}].[{table_name}]"
        table_name_sql = table_name.replace("'", "''")
        trigger_prefix = re.sub(r"[^0-9A-Za-z_]+", "_", f"CC_SYS_MOD_{table_name}")

        has_count = "sys_modified_count" in existing_columns

        add_column = not has_count
        recreate_triggers = force or add_column

        if not recreate_triggers and not force:
            return None

        statements = []

        if add_column:
            statements.append(
                f"IF COL_LENGTH(N'{object_name}', 'sys_modified_count') IS NULL BEGIN ALTER TABLE {table_identifier} ADD sys_modified_count INT NOT NULL CONSTRAINT DF_{trigger_prefix}_COUNT DEFAULT (0); END;"
            )

        statements.append(
            f"UPDATE {table_identifier} SET sys_modified_count = 0 WHERE sys_modified_count IS NULL;"
        )

        statements.append(
            f"IF OBJECT_ID(N'{schema_identifier}.{trigger_prefix}_insert', N'TR') IS NOT NULL DROP TRIGGER {schema_identifier}.{trigger_prefix}_insert;"
        )
        statements.append(
            f"IF OBJECT_ID(N'{schema_identifier}.{trigger_prefix}_update', N'TR') IS NOT NULL DROP TRIGGER {schema_identifier}.{trigger_prefix}_update;"
        )

        statements.extend(
            [
                f"""
CREATE TRIGGER {schema_identifier}.{trigger_prefix}_insert
ON {table_identifier}
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE t
    SET sys_created = ISNULL(i.sys_created, SYSDATETIME()),
        sys_modified = SYSDATETIME(),
        sys_modified_count = 0,
        sys_dirty = ISNULL(i.sys_dirty, 0),
        sys_table = '{table_name_sql}'
    FROM {table_identifier} AS t
    INNER JOIN inserted AS i ON t.sys_id = i.sys_id;
END;
""".strip(),
                f"""
CREATE TRIGGER {schema_identifier}.{trigger_prefix}_update
ON {table_identifier}
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE t
    SET sys_created = d.sys_created,
        sys_modified = SYSDATETIME(),
        sys_table = '{table_name_sql}',
        sys_dirty = CASE WHEN d.sys_dirty = 1 AND i.sys_dirty = 0 THEN 0 ELSE 1 END,
        sys_modified_count = CASE WHEN d.sys_dirty = 1 AND i.sys_dirty = 0 THEN ISNULL(d.sys_modified_count, 0) ELSE ISNULL(d.sys_modified_count, 0) + 1 END
    FROM {table_identifier} AS t
    INNER JOIN inserted AS i ON t.sys_id = i.sys_id
    INNER JOIN deleted AS d ON d.sys_id = i.sys_id;
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
        return f"TRUNCATE TABLE {quote(table)}"

    @classmethod
    def columns(cls, name):
        return f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{name}'
        ORDER BY ORDINAL_POSITION
        """

    @classmethod
    def column_info(cls, table, name):
        return f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{table}' AND COLUMN_NAME = '{name}'
        """

    @classmethod
    def drop_column(cls, table, name, cascade=True):
        return f"ALTER TABLE {quote(table)} DROP COLUMN {quote(name)}"

    @classmethod
    def alter_add(cls, table, columns, null_allowed=True):
        alter_parts = []
        for col, col_type in columns.items():
            null_clause = "NULL" if null_allowed else "NOT NULL"
            alter_parts.append(f"ADD {quote(col)} {col_type} {null_clause}")
        
        return f"ALTER TABLE {quote(table)} {', '.join(alter_parts)}"

    @classmethod
    def alter_drop(cls, table, columns):
        drop_parts = [f"DROP COLUMN {quote(col)}" for col in columns]
        return f"ALTER TABLE {quote(table)} {', '.join(drop_parts)}"

    @classmethod
    def alter_column_by_type(cls, table, column, value, nullable=True):
        null_clause = "NULL" if nullable else "NOT NULL"
        return f"ALTER TABLE {quote(table)} ALTER COLUMN {quote(column)} {value} {null_clause}"

    @classmethod
    def alter_column_by_sql(cls, table, column, value):
        return f"ALTER TABLE {quote(table)} ALTER COLUMN {quote(column)} {value}"

    @classmethod
    def rename_column(cls, table, orig, new):
        return f"EXEC sp_rename '{table}.{orig}', '{new}', 'COLUMN'"

    @classmethod
    def rename_table(cls, table, new):
        return f"EXEC sp_rename '{table}', '{new}'"

    @classmethod
    def primary_keys(cls, table):
        return f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
        AND TABLE_NAME = '{table}'
        """

    @classmethod
    def foreign_key_info(cls, table=None, column=None, schema=None):
        sql = """
        SELECT 
            FK.TABLE_NAME,
            CU.COLUMN_NAME,
            PK.TABLE_NAME AS REFERENCED_TABLE_NAME,
            PT.COLUMN_NAME AS REFERENCED_COLUMN_NAME,
            C.CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS C
        INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS FK ON C.CONSTRAINT_NAME = FK.CONSTRAINT_NAME
        INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS PK ON C.UNIQUE_CONSTRAINT_NAME = PK.CONSTRAINT_NAME
        INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE CU ON C.CONSTRAINT_NAME = CU.CONSTRAINT_NAME
        INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE PT ON PK.CONSTRAINT_NAME = PT.CONSTRAINT_NAME
        """
        if table:
            sql += f" WHERE FK.TABLE_NAME = '{table}'"
        if column:
            conjunction = " AND" if table else " WHERE"
            sql += f"{conjunction} CU.COLUMN_NAME = '{column}'"
        return sql

    @classmethod
    def create_foreign_key(cls, table, columns, key_to_table, key_to_columns, name=None, schema=None):
        if name is None:
            name = f"FK_{table}_{'_'.join(columns)}"
        
        col_list = ", ".join(quote(col) for col in columns)
        ref_col_list = ", ".join(quote(col) for col in key_to_columns)
        
        return f"""
        ALTER TABLE {quote(table)} 
        ADD CONSTRAINT {quote(name)} 
        FOREIGN KEY ({col_list}) 
        REFERENCES {quote(key_to_table)} ({ref_col_list})
        """

    @classmethod
    def drop_foreign_key(cls, table, columns, key_to_table=None, key_to_columns=None, name=None, schema=None):
        if name is None:
            name = f"FK_{table}_{'_'.join(columns)}"
        
        return f"ALTER TABLE {quote(table)} DROP CONSTRAINT {quote(name)}"

    @classmethod
    def create_index(cls, tx, table=None, columns=None, unique=False, direction=None, where=None, name=None, schema=None, trigram=None, lower=None):
        if name is None:
            name = f"IX_{table}_{'_'.join(columns)}"
        
        index_type = "UNIQUE INDEX" if unique else "INDEX"
        col_list = ", ".join(quote(col) for col in columns)
        
        sql = f"CREATE {index_type} {quote(name)} ON {quote(table)} ({col_list})"
        
        if where:
            sql += f" WHERE {where}"
        
        return sql

    @classmethod
    def drop_index(cls, table=None, columns=None, name=None, schema=None, trigram=None):
        if name is None:
            name = f"IX_{table}_{'_'.join(columns)}"
        
        return f"DROP INDEX {quote(name)} ON {quote(table)}"

    @classmethod
    def indexes(cls, table):
        return f"""
        SELECT 
            i.name AS index_name,
            c.name AS column_name,
            i.is_unique
        FROM sys.indexes i
        INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE i.object_id = OBJECT_ID('{table}')
        ORDER BY i.name, ic.key_ordinal
        """

    @classmethod
    def create_savepoint(cls, sp):
        return f"SAVE TRANSACTION {sp}"

    @classmethod
    def release_savepoint(cls, sp):
        return f"-- SQL Server doesn't support RELEASE SAVEPOINT {sp}"

    @classmethod
    def rollback_savepoint(cls, sp):
        return f"ROLLBACK TRANSACTION {sp}"

    @classmethod
    def create_view(cls, name, query, temp=False, silent=True):
        # SQL Server doesn't support temporary views in the same way
        return f"CREATE VIEW {quote(name)} AS {query}"

    @classmethod
    def drop_view(cls, name, silent=True):
        if silent:
            return f"DROP VIEW IF EXISTS {quote(name)}"
        else:
            return f"DROP VIEW {quote(name)}"

    @classmethod
    def last_id(cls, table):
        return "SELECT @@IDENTITY"

    @classmethod
    def current_id(cls, table):
        return f"SELECT IDENT_CURRENT('{table}')"

    @classmethod
    def set_id(cls, table, start):
        return f"DBCC CHECKIDENT('{table}', RESEED, {start})"

    @classmethod
    def set_sequence(cls, table, next_value):
        return f"DBCC CHECKIDENT('{table}', RESEED, {next_value})"

    @classmethod
    def massage_data(cls, data):
        """Massage data before insert/update operations."""
        # SQL Server-specific data transformations
        return data

    @classmethod
    def alter_trigger(cls, table, state="ENABLE", name="USER"):
        state_cmd = "ENABLE" if state.upper() == "ENABLE" else "DISABLE"
        return f"ALTER TABLE {quote(table)} {state_cmd} TRIGGER ALL"

    @classmethod
    def missing(cls, tx, table, list_values, column="SYS_ID", where=None):
        """Generate query to find missing values from a list."""
        # SQL Server version using VALUES clause
        value_rows = ", ".join([f"(?)" for _ in list_values])
        
        sql = f"""
        SELECT value_column FROM (
            VALUES {value_rows}
        ) AS input_values(value_column)
        WHERE value_column NOT IN (
            SELECT {quote(column)} FROM {quote(table)}
        """
        
        vals = list_values
        
        if where:
            where_sql, where_vals = cls._build_where(where)
            sql += f" WHERE {where_sql}"
            vals.extend(where_vals)
        
        sql += ")"
        
        return sql, vals
