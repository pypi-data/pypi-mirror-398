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
from .operators import OPERATORS, MySQLOperators
from ..tablehelper import TableHelper


# Configure TableHelper for MySQL
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
    """Quote MySQL identifiers."""
    if isinstance(data, list):
        return [quote(item) for item in data]
    else:
        parts = data.split(".")
        new = []
        for part in parts:
            if "`" in part:
                new.append(part)
            elif part.upper() in reserved_words:
                new.append("`" + part + "`")
            elif re.findall("[/]", part):
                new.append("`" + part + "`")
            else:
                new.append(part)
        return ".".join(new)


class SQL(BaseSQLDialect):
    server = "MySQL"
    type_column_identifier = "DATA_TYPE"
    is_nullable = "IS_NULLABLE"

    default_schema = ""

    ApplicationErrorCodes = []
    DatabaseMissingErrorCodes = ["1049"]  # ER_BAD_DB_ERROR
    TableMissingErrorCodes = ["1146"]     # ER_NO_SUCH_TABLE
    ColumnMissingErrorCodes = ["1054"]    # ER_BAD_FIELD_ERROR
    ForeignKeyMissingErrorCodes = ["1005"] # ER_CANT_CREATE_TABLE
    ConnectionErrorCodes = ["2002", "2003", "2006"] # Connection errors
    DuplicateKeyErrorCodes = ["1062"]     # ER_DUP_ENTRY
    RetryTransactionCodes = ["1213"]      # ER_LOCK_DEADLOCK
    TruncationErrorCodes = ["1406"]       # ER_DATA_TOO_LONG
    LockTimeoutErrorCodes = ["1205"]      # ER_LOCK_WAIT_TIMEOUT
    DatabaseObjectExistsErrorCodes = ["1050"] # ER_TABLE_EXISTS_ERROR
    DataIntegrityErrorCodes = ["1452", "1048", "1364"] # Foreign key, null, no default

    types = TYPES

    @classmethod
    def get_error(cls, e):
        """Extract error information from MySQL exception."""
        error_code = getattr(e, "errno", None)
        error_msg = getattr(e, "msg", None)
        return error_code, error_msg

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
        """Generate a MySQL SELECT statement."""
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

        # LIMIT clause (MySQL uses LIMIT instead of OFFSET/FETCH)
        if start is not None and qty is not None:
            sql_parts.append(f"LIMIT {start}, {qty}")
        elif qty is not None:
            sql_parts.append(f"LIMIT {qty}")

        # FOR UPDATE (lock)
        if lock:
            sql_parts.append("FOR UPDATE")
            if skip_locked:
                sql_parts.append("SKIP LOCKED")

        return " ".join(sql_parts), vals

    @classmethod
    def _build_where(cls, where):
        """Build WHERE clause for MySQL."""
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
                    conditions.append(f"{quote(key)} NOT IN ({', '.join(['%s'] * len(val))})")
                else:
                    conditions.append(f"{quote(key)} IN ({', '.join(['%s'] * len(val))})")
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
                elif "%%" in key:
                    key = key.replace("%%", "")
                    op = "LIKE"
                elif "%" in key:
                    key = key.replace("%", "")
                    op = "LIKE"
                elif "!" in key:
                    key = key.replace("!", "")
                    op = "<>"

                conditions.append(f"{quote(key)} {op} %s")
                vals.append(val)

        return " AND ".join(conditions), vals

    @classmethod
    def insert(cls, table, data):
        """Generate an INSERT statement for MySQL."""
        if not data:
            raise ValueError("Data cannot be empty")

        columns = list(data.keys())
        values = list(data.values())
        
        sql_parts = [
            "INSERT INTO",
            quote(table),
            f"({', '.join(quote(col) for col in columns)})",
            "VALUES",
            f"({', '.join(['%s'] * len(values))})"
        ]

        return " ".join(sql_parts), values

    @classmethod
    def update(cls, tx, table, data, where=None, pk=None, excluded=False):
        """Generate an UPDATE statement for MySQL."""
        if not data:
            raise ValueError("Data cannot be empty")
        
        if not where and not pk:
            raise ValueError("Either WHERE clause or primary key must be provided")

        # Build SET clause
        set_clauses = []
        vals = []
        
        for col, val in data.items():
            if excluded:
                # For ON DUPLICATE KEY UPDATE
                set_clauses.append(f"{quote(col)} = VALUES({quote(col)})")
            else:
                set_clauses.append(f"{quote(col)} = %s")
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
        """Generate a DELETE statement for MySQL."""
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
        """Generate an INSERT ... ON DUPLICATE KEY UPDATE statement for MySQL."""
        # First, create the INSERT part
        insert_sql, insert_vals = cls.insert(table, data)
        
        if on_conflict_do_nothing:
            # MySQL: INSERT IGNORE
            insert_sql = insert_sql.replace("INSERT INTO", "INSERT IGNORE INTO")
            return insert_sql, insert_vals
        elif on_conflict_update:
            # MySQL: INSERT ... ON DUPLICATE KEY UPDATE
            update_clauses = []
            for col in data.keys():
                if col not in pk:  # Don't update primary key columns
                    update_clauses.append(f"{quote(col)} = VALUES({quote(col)})")
            
            if update_clauses:
                insert_sql += f" ON DUPLICATE KEY UPDATE {', '.join(update_clauses)}"
            
            return insert_sql, insert_vals
        else:
            return insert_sql, insert_vals

    # Metadata queries
    @classmethod
    def version(cls):
        return "SELECT VERSION()"

    @classmethod
    def timestamp(cls):
        return "SELECT NOW()"

    @classmethod
    def user(cls):
        return "SELECT USER()"

    @classmethod
    def databases(cls):
        return "SHOW DATABASES"

    @classmethod
    def schemas(cls):
        return "SHOW DATABASES"  # MySQL databases are schemas

    @classmethod
    def current_schema(cls):
        return "SELECT DATABASE()"

    @classmethod
    def current_database(cls):
        return "SELECT DATABASE()"

    @classmethod
    def tables(cls, system=False):
        if system:
            return "SHOW TABLES"
        else:
            return "SHOW TABLES"

    @classmethod
    def views(cls, system=False):
        return "SHOW FULL TABLES WHERE Table_type = 'VIEW'"

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
        table_identifier = quote(name)
        base_name = name.split(".")[-1].replace("`", "")
        base_name_sql = base_name.replace("'", "''")
        trigger_prefix = re.sub(r"[^0-9A-Za-z_]+", "_", f"cc_sysmod_{base_name}")

        statements = []
        if drop:
            statements.append(f"DROP TABLE IF EXISTS {table_identifier};")

        statements.append(
            f"""
CREATE TABLE {table_identifier} (
  `sys_id` BIGINT NOT NULL AUTO_INCREMENT,
  `sys_table` TEXT,
  `sys_created` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `sys_modified` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `sys_modified_by` TEXT,
  `sys_modified_count` INT NOT NULL DEFAULT 0,
  `sys_dirty` TINYINT(1) NOT NULL DEFAULT 0,
    `sys_keywords` TEXT,
  PRIMARY KEY (`sys_id`)
) ENGINE=InnoDB;
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
                f"DROP TRIGGER IF EXISTS {trigger_prefix}_bi;",
                f"DROP TRIGGER IF EXISTS {trigger_prefix}_bu;",
                f"""
CREATE TRIGGER {trigger_prefix}_bi
BEFORE INSERT ON {table_identifier}
FOR EACH ROW
BEGIN
    SET NEW.sys_created = COALESCE(NEW.sys_created, NOW());
    SET NEW.sys_modified = NOW();
    SET NEW.sys_modified_count = 0;
    SET NEW.sys_dirty = IFNULL(NEW.sys_dirty, 0);
    SET NEW.sys_table = '{base_name_sql}';
END;
""".strip(),
                f"""
CREATE TRIGGER {trigger_prefix}_bu
BEFORE UPDATE ON {table_identifier}
FOR EACH ROW
BEGIN
    IF OLD.sys_dirty = TRUE AND NEW.sys_dirty = FALSE THEN
        SET NEW.sys_dirty = 0;
        SET NEW.sys_modified_count = IFNULL(OLD.sys_modified_count, 0);
    ELSE
        SET NEW.sys_dirty = 1;
        SET NEW.sys_modified_count = IFNULL(OLD.sys_modified_count, 0) + 1;
    END IF;
    SET NEW.sys_created = OLD.sys_created;
    SET NEW.sys_modified = NOW();
    SET NEW.sys_table = '{base_name_sql}';
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
        """Ensure MySQL tables maintain the Velocity system metadata."""
        existing_columns = {col.lower() for col in existing_columns or []}

        table_identifier = quote(name)
        base_name = name.split(".")[-1].replace("`", "")
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
                f"ALTER TABLE {table_identifier} ADD COLUMN IF NOT EXISTS `sys_modified_count` INT NOT NULL DEFAULT 0;"
            )

        statements.append(
            f"UPDATE {table_identifier} SET `sys_modified_count` = 0 WHERE `sys_modified_count` IS NULL;"
        )

        statements.append(f"DROP TRIGGER IF EXISTS {trigger_prefix}_bi;")
        statements.append(f"DROP TRIGGER IF EXISTS {trigger_prefix}_bu;")

        statements.extend(
            [
                f"""
CREATE TRIGGER {trigger_prefix}_bi
BEFORE INSERT ON {table_identifier}
FOR EACH ROW
BEGIN
    SET NEW.sys_created = COALESCE(NEW.sys_created, NOW());
    SET NEW.sys_modified = NOW();
    SET NEW.sys_modified_count = 0;
    SET NEW.sys_dirty = IFNULL(NEW.sys_dirty, 0);
    SET NEW.sys_table = '{base_name_sql}';
END;
""".strip(),
                f"""
CREATE TRIGGER {trigger_prefix}_bu
BEFORE UPDATE ON {table_identifier}
FOR EACH ROW
BEGIN
    IF OLD.sys_dirty = TRUE AND NEW.sys_dirty = FALSE THEN
        SET NEW.sys_dirty = 0;
        SET NEW.sys_modified_count = IFNULL(OLD.sys_modified_count, 0);
    ELSE
        SET NEW.sys_dirty = 1;
        SET NEW.sys_modified_count = IFNULL(OLD.sys_modified_count, 0) + 1;
    END IF;
    SET NEW.sys_created = OLD.sys_created;
    SET NEW.sys_modified = NOW();
    SET NEW.sys_table = '{base_name_sql}';
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
        return f"SHOW COLUMNS FROM {quote(name)}"

    @classmethod
    def column_info(cls, table, name):
        return f"SHOW COLUMNS FROM {quote(table)} LIKE '{name}'"

    @classmethod
    def drop_column(cls, table, name, cascade=True):
        return f"ALTER TABLE {quote(table)} DROP COLUMN {quote(name)}"

    @classmethod
    def alter_add(cls, table, columns, null_allowed=True):
        alter_parts = []
        for col, col_type in columns.items():
            null_clause = "NULL" if null_allowed else "NOT NULL"
            alter_parts.append(f"ADD COLUMN {quote(col)} {col_type} {null_clause}")
        
        return f"ALTER TABLE {quote(table)} {', '.join(alter_parts)}"

    @classmethod
    def alter_drop(cls, table, columns):
        drop_parts = [f"DROP COLUMN {quote(col)}" for col in columns]
        return f"ALTER TABLE {quote(table)} {', '.join(drop_parts)}"

    @classmethod
    def alter_column_by_type(cls, table, column, value, nullable=True):
        null_clause = "NULL" if nullable else "NOT NULL"
        return f"ALTER TABLE {quote(table)} MODIFY COLUMN {quote(column)} {value} {null_clause}"

    @classmethod
    def alter_column_by_sql(cls, table, column, value):
        return f"ALTER TABLE {quote(table)} MODIFY COLUMN {quote(column)} {value}"

    @classmethod
    def rename_column(cls, table, orig, new):
        # MySQL requires the full column definition for CHANGE
        return f"ALTER TABLE {quote(table)} CHANGE {quote(orig)} {quote(new)} /* TYPE_NEEDED */"

    @classmethod
    def rename_table(cls, table, new):
        return f"RENAME TABLE {quote(table)} TO {quote(new)}"

    @classmethod
    def primary_keys(cls, table):
        return f"SHOW KEYS FROM {quote(table)} WHERE Key_name = 'PRIMARY'"

    @classmethod
    def foreign_key_info(cls, table=None, column=None, schema=None):
        sql = """
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            CONSTRAINT_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE REFERENCED_TABLE_NAME IS NOT NULL
        """
        if table:
            sql += f" AND TABLE_NAME = '{table}'"
        if column:
            sql += f" AND COLUMN_NAME = '{column}'"
        return sql

    @classmethod
    def create_foreign_key(cls, table, columns, key_to_table, key_to_columns, name=None, schema=None):
        if name is None:
            name = f"fk_{table}_{'_'.join(columns)}"
        
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
            name = f"fk_{table}_{'_'.join(columns)}"
        
        return f"ALTER TABLE {quote(table)} DROP FOREIGN KEY {quote(name)}"

    @classmethod
    def create_index(cls, tx, table=None, columns=None, unique=False, direction=None, where=None, name=None, schema=None, trigram=None, lower=None):
        if name is None:
            name = f"idx_{table}_{'_'.join(columns)}"
        
        index_type = "UNIQUE INDEX" if unique else "INDEX"
        col_list = ", ".join(quote(col) for col in columns)
        
        return f"CREATE {index_type} {quote(name)} ON {quote(table)} ({col_list})"

    @classmethod
    def drop_index(cls, table=None, columns=None, name=None, schema=None, trigram=None):
        if name is None:
            name = f"idx_{table}_{'_'.join(columns)}"
        
        return f"DROP INDEX {quote(name)} ON {quote(table)}"

    @classmethod
    def indexes(cls, table):
        return f"SHOW INDEX FROM {quote(table)}"

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
        if temp:
            # MySQL doesn't support temporary views
            temp_clause = ""
        else:
            temp_clause = ""
        
        if silent:
            return f"CREATE OR REPLACE VIEW {quote(name)} AS {query}"
        else:
            return f"CREATE VIEW {quote(name)} AS {query}"

    @classmethod
    def drop_view(cls, name, silent=True):
        if silent:
            return f"DROP VIEW IF EXISTS {quote(name)}"
        else:
            return f"DROP VIEW {quote(name)}"

    @classmethod
    def last_id(cls, table):
        return "SELECT LAST_INSERT_ID()"

    @classmethod
    def current_id(cls, table):
        return f"SELECT AUTO_INCREMENT FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table}'"

    @classmethod
    def set_id(cls, table, start):
        return f"ALTER TABLE {quote(table)} AUTO_INCREMENT = {start}"

    @classmethod
    def set_sequence(cls, table, next_value):
        return f"ALTER TABLE {quote(table)} AUTO_INCREMENT = {next_value}"

    @classmethod
    def massage_data(cls, data):
        """Massage data before insert/update operations."""
        # MySQL-specific data transformations
        return data

    @classmethod
    def alter_trigger(cls, table, state="ENABLE", name="USER"):
        # MySQL has different trigger syntax
        return f"-- MySQL trigger management for {table}"

    @classmethod
    def missing(cls, tx, table, list_values, column="SYS_ID", where=None):
        """Generate query to find missing values from a list."""
        placeholders = ", ".join(["%s"] * len(list_values))
        sql = f"""
        SELECT missing_val FROM (
            SELECT %s AS missing_val
            {f"UNION ALL SELECT %s " * (len(list_values) - 1) if len(list_values) > 1 else ""}
        ) AS vals
        WHERE missing_val NOT IN (
            SELECT {quote(column)} FROM {quote(table)}
        """
        
        vals = list_values + list_values  # Values appear twice in this query structure
        
        if where:
            where_sql, where_vals = cls._build_where(where)
            sql += f" WHERE {where_sql}"
            vals.extend(where_vals)
        
        sql += ")"
        
        return sql, vals
