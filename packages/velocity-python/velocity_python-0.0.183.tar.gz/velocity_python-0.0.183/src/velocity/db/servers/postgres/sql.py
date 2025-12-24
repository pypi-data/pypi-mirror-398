import re
import hashlib
import sqlparse
from psycopg2 import sql as psycopg2_sql

from velocity.db import exceptions
from ..base.sql import BaseSQLDialect

from .reserved import reserved_words
from .types import TYPES
from .operators import OPERATORS, PostgreSQLOperators
from ..tablehelper import TableHelper
from collections.abc import Mapping, Sequence


# Configure TableHelper for PostgreSQL
TableHelper.reserved = reserved_words
TableHelper.operators = OPERATORS


system_fields = [
    "sys_id",
    "sys_created",
    "sys_modified",
    "sys_modified_by",
    "sys_modified_row",
    "sys_modified_count",
    "sys_dirty",
    "sys_table",
    "sys_keywords",
]


class SQL(BaseSQLDialect):
    server = "PostGreSQL"
    type_column_identifier = "data_type"
    is_nullable = "is_nullable"

    default_schema = "public"

    ApplicationErrorCodes = ["22P02", "42883", "42501", "42601", "25P01", "25P02", "42804"]  # Added 42804 for datatype mismatch

    DatabaseMissingErrorCodes = ["3D000"]
    TableMissingErrorCodes = ["42P01"]
    ColumnMissingErrorCodes = ["42703"]
    ForeignKeyMissingErrorCodes = ["42704"]

    ConnectionErrorCodes = [
        "08001",
        "08S01",
        "57P03",
        "08006",
        "53300",
        "08003",
        "08004",
        "08P01",
    ]
    DuplicateKeyErrorCodes = [
        "23505"
    ]  # unique_violation - no longer relying only on regex
    RetryTransactionCodes = ["40001", "40P01", "40002"]
    TruncationErrorCodes = ["22001"]
    LockTimeoutErrorCodes = ["55P03"]
    DatabaseObjectExistsErrorCodes = ["42710", "42P07", "42P04"]
    DataIntegrityErrorCodes = ["23503", "23502", "23514", "23P01", "22003"]

    @classmethod
    def get_error(cls, e):
        error_code = getattr(e, "pgcode", None)
        error_mesg = getattr(e, "pgerror", None)
        return error_code, error_mesg

    @staticmethod
    def _validate_where_string(where):
        """
        Validate string WHERE clauses to prevent malformed SQL.
        Raises ValueError for invalid inputs.
        """
        where_stripped = where.strip()
        if not where_stripped:
            raise ValueError("WHERE clause cannot be empty string.")
        # Check for boolean literals first (includes '1' and '0')
        if where_stripped in ('True', 'False', '1', '0'):
            raise ValueError(
                f"Invalid WHERE clause: '{where}'. "
                "Boolean literals alone are not valid WHERE clauses. "
                "Use complete SQL expressions like 'sys_active = true' instead."
            )
        # Then check for other numeric values (excluding '1' and '0' already handled above)
        elif where_stripped.isdigit():
            raise ValueError(
                f"Invalid WHERE clause: '{where}'. "
                "Bare integers are not valid WHERE clauses. "
                f"Use a dictionary like {{'sys_id': {where_stripped}}} or "
                f"a complete SQL expression like 'sys_id = {where_stripped}' instead."
            )

    @staticmethod
    def _validate_where_primitive(where):
        """
        Validate primitive type WHERE clauses (int, float, bool).
        Raises ValueError for invalid inputs.
        """
        suggested_fix = "{'sys_id': " + str(where) + "}" if isinstance(where, int) else "complete SQL expression"
        raise ValueError(
            f"Invalid WHERE clause: {where} (type: {type(where).__name__}). "
            f"Primitive values cannot be WHERE clauses directly. "
            f"Use a dictionary like {suggested_fix} or a complete SQL string instead. "
            f"This error prevents PostgreSQL 'argument of WHERE must be type boolean' errors."
        )

    @staticmethod
    def _process_predicates(predicates, target_list, vals_list):
        """
        Process predicate/value tuples and append to target list.
        Handles None values, tuple values, and scalar values.
        
        :param predicates: Iterable of (predicate, value) tuples
        :param target_list: List to append predicates to
        :param vals_list: List to append values to
        """
        for pred, val in predicates:
            target_list.append(pred)
            if val is None:
                pass
            elif isinstance(val, tuple):
                vals_list.extend(val)
            else:
                vals_list.append(val)

    @staticmethod
    def _is_special_value(val):
        """
        Check if a value is a special @@ prefixed value (e.g., @@CURRENT_TIMESTAMP).
        Returns tuple: (is_special, sql_expression)
        
        :param val: Value to check
        :return: (True, 'CURRENT_TIMESTAMP') if special, (False, None) otherwise
        """
        if isinstance(val, str) and len(val) > 2 and val.startswith("@@"):
            sql_expr = val[2:]
            if sql_expr:  # Ensure there's content after @@
                return True, sql_expr
        return False, None

    types = TYPES

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
        """
        Generate a PostgreSQL SELECT statement with proper table helper integration.
        """
        if not table:
            raise ValueError("Table name is required.")

        # Validate pagination parameters
        if start is not None and not isinstance(start, int):
            raise ValueError("Start (OFFSET) must be an integer.")
        if qty is not None and not isinstance(qty, int):
            raise ValueError("Qty (FETCH) must be an integer.")

        sql_parts = {
            "SELECT": [],
            "FROM": [],
            "WHERE": [],
            "GROUP BY": [],
            "HAVING": [],
            "ORDER BY": [],
        }

        sql = []
        vals = []

        # Create table helper instance
        th = TableHelper(tx, table)

        # Handle columns and DISTINCT before aliasing
        if columns is None:
            # No columns specified - select all
            columns = ["*"]
        elif isinstance(columns, str):
            columns = th.split_columns(columns)
        elif not isinstance(columns, Sequence):
            raise TypeError(
                f"Columns must be a string, sequence, or None, but {type(columns)} was found"
            )

        # Clean and validate columns
        columns = [c.strip() for c in columns if c.strip()]  # Remove empty columns
        if not columns:
            raise ValueError("No valid columns specified")

        distinct = False

        # Check for DISTINCT keyword in any column
        if any("distinct" in c.lower() for c in columns):
            distinct = True
            columns = [re.sub(r"(?i)\bdistinct\b", "", c).strip() for c in columns]

        # Process column references
        processed_columns = []
        for col in columns:
            try:
                processed_col = th.resolve_references(
                    col,
                    options={
                        "alias_column": True,
                        "alias_table": True,
                        "bypass_on_error": True,
                    },
                )
                processed_columns.append(processed_col)
            except Exception as e:
                raise ValueError(f"Error processing column '{col}': {e}")

        columns = processed_columns

        # Handle ORDER BY with improved validation
        new_orderby = []
        if isinstance(orderby, str):
            orderby = th.split_columns(orderby)

        # Handle orderby references
        if isinstance(orderby, Sequence):
            for column in orderby:
                try:
                    if " " in column:
                        parts = column.split(" ", 1)
                        if len(parts) == 2:
                            col_name, direction = parts
                            # Validate direction
                            direction = direction.upper()
                            if direction not in ("ASC", "DESC"):
                                raise ValueError(
                                    f"Invalid ORDER BY direction: {direction}"
                                )
                            col_name = th.resolve_references(
                                col_name.strip(), options={"alias_only": True}
                            )
                            new_orderby.append(f"{col_name} {direction}")
                        else:
                            raise ValueError(f"Invalid ORDER BY format: {column}")
                    else:
                        resolved_col = th.resolve_references(
                            column.strip(), options={"alias_only": True}
                        )
                        new_orderby.append(resolved_col)
                except Exception as e:
                    raise ValueError(
                        f"Error processing ORDER BY column '{column}': {e}"
                    )

        elif isinstance(orderby, Mapping):
            for key, val in orderby.items():
                try:
                    # Validate direction
                    direction = str(val).upper()
                    if direction not in ("ASC", "DESC"):
                        raise ValueError(f"Invalid ORDER BY direction: {direction}")
                    parsed_key = th.resolve_references(
                        key, options={"alias_only": True}
                    )
                    new_orderby.append(f"{parsed_key} {direction}")
                except Exception as e:
                    raise ValueError(f"Error processing ORDER BY key '{key}': {e}")

        orderby = new_orderby

        # Handle groupby
        if isinstance(groupby, str):
            groupby = th.split_columns(groupby)
        if isinstance(groupby, (Sequence)):
            new_groupby = []
            for gcol in groupby:
                new_groupby.append(
                    th.resolve_references(gcol, options={"alias_only": True})
                )
            groupby = new_groupby

        # Handle having
        if isinstance(having, Mapping):
            new_having = []
            for key, val in having.items():
                new_having.append(th.make_predicate(key, val))
            having = new_having

        # SELECT clause
        # columns is a list/tuple of already processed references
        sql_parts["SELECT"].extend(columns)
        alias = th.get_table_alias("current_table")
        if not alias:
            raise ValueError("Main table alias resolution failed.")

        # FROM clause
        if th.foreign_keys:
            sql_parts["FROM"].append(
                f"{TableHelper.quote(table)} AS {TableHelper.quote(alias)}"
            )
            # Handle joins
            done = []
            for key, ref_info in th.foreign_keys.items():
                ref_table = ref_info["ref_table"]
                if ref_table in done:
                    continue
                done.append(ref_table)
                if not all(
                    k in ref_info
                    for k in ("alias", "local_column", "ref_table", "ref_column")
                ):
                    raise ValueError(f"Invalid table alias info for {ref_table}.")
                sql_parts["FROM"].append(
                    f"LEFT JOIN {TableHelper.quote(ref_table)} AS {TableHelper.quote(ref_info['alias'])} "
                    f"ON {TableHelper.quote(alias)}.{TableHelper.quote(ref_info['local_column'])} = {TableHelper.quote(ref_info['alias'])}.{TableHelper.quote(ref_info['ref_column'])}"
                )
        else:
            sql_parts["FROM"].append(TableHelper.quote(table))

        # WHERE - Enhanced validation to prevent malformed SQL
        if where:
            if isinstance(where, str):
                cls._validate_where_string(where)
                sql_parts["WHERE"].append(where)
            elif isinstance(where, (int, float, bool)):
                cls._validate_where_primitive(where)
            elif isinstance(where, Mapping):
                # Convert dictionary to predicate list
                new_where = []
                for key, val in where.items():
                    try:
                        new_where.append(th.make_predicate(key, val))
                    except Exception as e:
                        raise ValueError(f"Error processing WHERE condition '{key}': {e}")
                where = new_where
                cls._process_predicates(where, sql_parts["WHERE"], vals)
            else:
                # Handle list of tuples or other iterable
                try:
                    cls._process_predicates(where, sql_parts["WHERE"], vals)
                except (TypeError, ValueError) as e:
                    raise ValueError(
                        f"Invalid WHERE clause format: {where}. "
                        "Expected dictionary, list of (predicate, value) tuples, or SQL string."
                    ) from e

        # GROUP BY
        if groupby:
            sql_parts["GROUP BY"].append(",".join(groupby))

        # HAVING
        if having:
            if isinstance(having, str):
                sql_parts["HAVING"].append(having)
            else:
                cls._process_predicates(having, sql_parts["HAVING"], vals)

        # ORDER BY
        if orderby:
            sql_parts["ORDER BY"].append(",".join(orderby))

        # Construct final SQL
        if sql_parts["SELECT"]:
            sql.append("SELECT")
            if distinct:
                sql.append("DISTINCT")
            sql.append(", ".join(sql_parts["SELECT"]))

        if sql_parts["FROM"]:
            sql.append("FROM")
            sql.append(" ".join(sql_parts["FROM"]))

        if sql_parts["WHERE"]:
            sql.append("WHERE " + " AND ".join(sql_parts["WHERE"]))

        if sql_parts["GROUP BY"]:
            sql.append("GROUP BY " + " ".join(sql_parts["GROUP BY"]))

        if sql_parts["HAVING"]:
            sql.append("HAVING " + " AND ".join(sql_parts["HAVING"]))

        if sql_parts["ORDER BY"]:
            sql.append("ORDER BY " + " ".join(sql_parts["ORDER BY"]))

        # OFFSET/FETCH
        if start is not None:
            if not isinstance(start, int):
                raise ValueError("Start (OFFSET) must be an integer.")
            sql.append(f"OFFSET {start} ROWS")

        if qty is not None:
            if not isinstance(qty, int):
                raise ValueError("Qty (FETCH) must be an integer.")
            sql.append(f"FETCH NEXT {qty} ROWS ONLY")

        # FOR UPDATE and SKIP LOCKED
        if lock or skip_locked:
            sql.append("FOR UPDATE")
        if skip_locked:
            sql.append("SKIP LOCKED")

        sql = sqlparse.format(" ".join(sql), reindent=True, keyword_case="upper")
        return sql, tuple(vals)

    @classmethod
    def update(cls, tx, table, data, where=None, pk=None, excluded=False):
        """
        Generate a Postgres UPDATE statement, handling the WHERE clause logic similar
        to how the SELECT statement does. If you want to do an ON CONFLICT ... DO UPDATE,
        that logic should generally live in `merge(...)` rather than here.

        :param tx: Database/transaction context object (used by TableHelper)
        :param table: Table name
        :param data: Dictionary of columns to update
        :param where: WHERE clause conditions (dict, list of tuples, or string)
        :param pk: Primary key dict to merge with `where`
        :param excluded: If True, creates `col = EXCLUDED.col` expressions (used in upsert)
        :return: (sql_string, params_tuple)
        """

        if not table:
            raise ValueError("Table name is required.")
        if not pk and not where:
            raise ValueError("Where clause (where) or primary key (pk) is required.")
        if not isinstance(data, Mapping) or not data:
            raise ValueError("data must be a non-empty mapping of column-value pairs.")

        th = TableHelper(tx, table)
        set_clauses = []
        vals = []

        # Merge pk into where if pk is provided
        if pk:
            if where:
                # If where is a dict, update it; otherwise raise error
                if isinstance(where, Mapping):
                    where = dict(where)  # copy to avoid mutation
                    where.update(pk)
                else:
                    raise ValueError(
                        "Cannot combine 'pk' with a non-dict 'where' clause."
                    )
            else:
                where = pk

        # Build SET clauses
        for col, val in data.items():
            col_quoted = th.resolve_references(
                col, options={"alias_column": False, "alias_table": False}
            )
            is_special, sql_expr = cls._is_special_value(val)
            if excluded:
                if is_special:
                    # Allow callers to force literal expressions like CURRENT_TIMESTAMP
                    set_clauses.append(f"{col_quoted} = {sql_expr}")
                else:
                    # For ON CONFLICT DO UPDATE statements, use the EXCLUDED value
                    set_clauses.append(f"{col_quoted} = EXCLUDED.{col_quoted}")
            else:
                if is_special:
                    set_clauses.append(f"{col_quoted} = {sql_expr}")
                else:
                    set_clauses.append(f"{col_quoted} = %s")
                    vals.append(val)

        # Build WHERE clauses for a normal update (ignored when excluded is True)
        where_clauses = []
        if not excluded:
            if where:
                if isinstance(where, Mapping):
                    new_where = []
                    for key, val in where.items():
                        new_where.append(th.make_predicate(key, val))
                    where = new_where
                elif isinstance(where, str):
                    cls._validate_where_string(where)
                    where_clauses.append(where)
                elif isinstance(where, (int, float, bool)):
                    cls._validate_where_primitive(where)
                
                # Process the where clause if it's a list of tuples
                if not isinstance(where, str):
                    try:
                        cls._process_predicates(where, where_clauses, vals)
                    except (TypeError, ValueError) as e:
                        raise ValueError(
                            f"Invalid WHERE clause format: {where}. "
                            "Expected dictionary, list of (predicate, value) tuples, or SQL string."
                        ) from e
            if not where_clauses:
                raise ValueError(
                    "No WHERE clause could be constructed. Update would affect all rows."
                )

        # Construct final SQL
        sql_parts = ["UPDATE"]
        if not excluded:
            sql_parts.append(TableHelper.quote(table))
        sql_parts.append("SET " + ", ".join(set_clauses))
        if not excluded and where_clauses:
            sql_parts.append("WHERE " + " AND ".join(where_clauses))
        
        final_sql = sqlparse.format(
            " ".join(sql_parts), reindent=True, keyword_case="upper"
        )
        return final_sql, tuple(vals)

    @classmethod
    def insert(cls, table, data):
        """
        Generate an INSERT statement.
        """
        # Create a temporary TableHelper instance for quoting
        # Note: We pass None for tx since we only need quoting functionality
        temp_helper = TableHelper(None, table)

        keys = []
        vals_placeholders = []
        args = []
        for key, val in data.items():
            keys.append(temp_helper.quote(key.lower()))
            is_special, sql_expr = cls._is_special_value(val)
            if is_special:
                vals_placeholders.append(sql_expr)
            else:
                vals_placeholders.append("%s")
                args.append(val)

        sql_parts = []
        sql_parts.append("INSERT INTO")
        sql_parts.append(temp_helper.quote(table))
        sql_parts.append("(")
        sql_parts.append(",".join(keys))
        sql_parts.append(")")
        sql_parts.append("VALUES")
        sql_parts.append("(")
        sql_parts.append(",".join(vals_placeholders))
        sql_parts.append(")")
        sql = sqlparse.format(" ".join(sql_parts), reindent=True, keyword_case="upper")
        return sql, tuple(args)

    @classmethod
    def merge(cls, tx, table, data, pk, on_conflict_do_nothing, on_conflict_update):
        if not isinstance(data, Mapping) or not data:
            raise ValueError("data must be a non-empty mapping of column-value pairs.")

        table_helper = TableHelper(tx, table)
        data = dict(data)  # work with a copy to avoid mutating the caller's dict

        if pk is None:
            pkeys = tx.table(table).primary_keys()
            if not pkeys:
                raise ValueError("Primary key required for merge.")
            missing = [key for key in pkeys if key not in data]
            if missing:
                missing_cols = ", ".join(missing)
                raise ValueError(
                    "Primary key values missing from data for merge: "
                    f"{missing_cols}. Provide pk=... or include the key values in data."
                )
            pk = {key: data[key] for key in pkeys}
        else:
            pk = dict(pk)
            for key, value in pk.items():
                if key in data and data[key] != value:
                    raise ValueError(
                        f"Conflicting values for primary key '{key}' between data and pk arguments."
                    )

        insert_data = dict(data)
        insert_data.update(pk)

        update_data = {k: v for k, v in data.items() if k not in pk}

        if not update_data and on_conflict_update:
            # Nothing to update, fall back to a no-op on conflict resolution.
            on_conflict_do_nothing = True
            on_conflict_update = False

        if on_conflict_do_nothing == on_conflict_update:
            raise Exception(
                "Update on conflict must have one and only one option to complete on conflict."
            )

        sql, vals = cls.insert(table, insert_data)
        sql = [sql]
        vals = list(vals)  # Convert to a mutable list

        sql.append("ON CONFLICT")
        conflict_columns = [TableHelper.quote(column) for column in pk.keys()]
        sql.append("(")
        sql.append(", ".join(conflict_columns))
        sql.append(")")
        sql.append("DO")
        if on_conflict_do_nothing:
            sql.append("NOTHING")
        elif on_conflict_update:
            sql_update, vals_update = cls.update(
                tx, table, update_data, pk, excluded=True
            )
            sql.append(sql_update)
            vals.extend(vals_update)

        import sqlparse

        final_sql = sqlparse.format(" ".join(sql), reindent=True, keyword_case="upper")
        return final_sql, tuple(vals)

    @classmethod
    def insnx(cls, tx, table, data, where=None):
        """Insert only when the supplied predicate finds no existing row."""
        if not table:
            raise ValueError("Table name is required.")
        if not isinstance(data, Mapping) or not data:
            raise ValueError("data must be a non-empty mapping of column-value pairs.")

        # Helper used for quoting and foreign key resolution
        th = TableHelper(tx, table)
        quote_helper = TableHelper(None, table)

        columns_sql = []
        select_parts = []
        vals = []

        for key, val in data.items():
            columns_sql.append(quote_helper.quote(key.lower()))
            is_special, sql_expr = cls._is_special_value(val)
            if is_special:
                select_parts.append(sql_expr)
            else:
                select_parts.append("%s")
                vals.append(val)

        if not select_parts:
            raise ValueError("At least one column is required for insert.")

        if where is None:
            if tx is None:
                raise ValueError(
                    "A transaction context is required when deriving WHERE from primary keys."
                )
            pk_cols = tx.table(table).primary_keys()
            if not pk_cols:
                raise ValueError("Primary key required to derive WHERE clause.")
            missing = [pk for pk in pk_cols if pk not in data]
            if missing:
                raise ValueError(
                    "Missing primary key value(s) for insert condition: " + ", ".join(missing)
                )
            where = {pk: data[pk] for pk in pk_cols}

        where_clauses = []
        where_vals = []

        if isinstance(where, Mapping):
            compiled = []
            for key, val in where.items():
                compiled.append(th.make_predicate(key, val))
            where = compiled

        if isinstance(where, str):
            where_clauses.append(where)
        else:
            try:
                for predicate, value in where:
                    where_clauses.append(predicate)
                    if value is None:
                        continue
                    if isinstance(value, tuple):
                        where_vals.extend(value)
                    else:
                        where_vals.append(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "Invalid WHERE clause format. Expected mapping, SQL string, or iterable of predicate/value pairs."
                ) from exc

        vals.extend(where_vals)

        exists_sql = [
            "SELECT 1 FROM",
            TableHelper.quote(table),
        ]
        if where_clauses:
            exists_sql.append("WHERE " + " AND ".join(where_clauses))

        sql_parts = [
            "INSERT INTO",
            TableHelper.quote(table),
            f"({','.join(columns_sql)})",
            "SELECT",
            ", ".join(select_parts),
            "WHERE NOT EXISTS (",
            " ".join(exists_sql),
            ")",
        ]

        final_sql = sqlparse.format(" ".join(sql_parts), reindent=True, keyword_case="upper")
        return final_sql, tuple(vals)

    insert_if_not_exists = insnx

    @classmethod
    def version(cls):
        return "select version()", tuple()

    @classmethod
    def timestamp(cls):
        return "select current_timestamp", tuple()

    @classmethod
    def user(cls):
        return "select current_user", tuple()

    @classmethod
    def databases(cls):
        return "select datname from pg_database where datistemplate = false", tuple()

    @classmethod
    def schemas(cls):
        return "select schema_name from information_schema.schemata", tuple()

    @classmethod
    def current_schema(cls):
        return "select current_schema", tuple()

    @classmethod
    def current_database(cls):
        return "select current_database()", tuple()

    @classmethod
    def tables(cls, system=False):
        if system:
            return (
                "select table_schema,table_name from information_schema.tables where table_type = 'BASE TABLE' order by table_schema,table_name",
                tuple(),
            )
        else:
            return (
                "select table_schema, table_name from information_schema.tables where table_type = 'BASE TABLE' and table_schema NOT IN ('pg_catalog', 'information_schema')",
                tuple(),
            )

    @classmethod
    def views(cls, system=False):
        if system:
            return (
                "select table_schema, table_name from information_schema.views order by table_schema,table_name",
                tuple(),
            )
        else:
            return (
                "select table_schema, table_name from information_schema.views where table_schema = any (current_schemas(false)) order by table_schema,table_name",
                tuple(),
            )

    @classmethod
    def create_database(cls, name):
        return f"create database {name}", tuple()

    @classmethod
    def last_id(cls, table):
        return "SELECT CURRVAL(PG_GET_SERIAL_SEQUENCE(%s, 'sys_id'))", tuple([table])

    @classmethod
    def current_id(cls, table):
        return (
            "SELECT pg_sequence_last_value(PG_GET_SERIAL_SEQUENCE(%s, 'sys_id'))",
            tuple([table]),
        )

    @classmethod
    def set_id(cls, table, start):
        return "SELECT SETVAL(PG_GET_SERIAL_SEQUENCE(%s, 'sys_id'), %s)", tuple(
            [table, start]
        )

    @classmethod
    def drop_database(cls, name):
        return f"drop database if exists {name}", tuple()

    @staticmethod
    def _sys_modified_function_sql(schema_identifier):
        return f"""
            CREATE OR REPLACE FUNCTION {schema_identifier}.on_sys_modified()
              RETURNS TRIGGER AS
            $BODY$
            BEGIN
                IF (TG_OP = 'INSERT') THEN
                    NEW.sys_table := TG_TABLE_NAME;
                    NEW.sys_created := transaction_timestamp();
                    NEW.sys_modified := transaction_timestamp();
                    NEW.sys_modified_row := clock_timestamp();
                    NEW.sys_modified_count := 0;
                ELSIF (TG_OP = 'UPDATE') THEN
                    NEW.sys_table := TG_TABLE_NAME;
                    NEW.sys_created := OLD.sys_created;
                    NEW.sys_modified_count := COALESCE(OLD.sys_modified_count, 0);
                    IF ROW(NEW.*) IS DISTINCT FROM ROW(OLD.*) THEN
                        IF OLD.sys_dirty IS TRUE AND NEW.sys_dirty IS FALSE THEN
                            NEW.sys_dirty := FALSE;
                        ELSE
                            NEW.sys_dirty := TRUE;
                        END IF;
                        NEW.sys_modified := transaction_timestamp();
                        NEW.sys_modified_row := clock_timestamp();
                        NEW.sys_modified_count := COALESCE(OLD.sys_modified_count, 0) + 1;
                    END IF;
                END IF;
                RETURN NEW;
            END;
            $BODY$
              LANGUAGE plpgsql VOLATILE
              COST 100;
        """

    @staticmethod
    def _sys_keywords_index_name(schema_unquoted, table_unquoted):
        base_index_name = f"idx_{schema_unquoted}_{table_unquoted}_sys_keywords_tsv"
        base_index_name = re.sub(r"[^0-9a-zA-Z_]+", "_", base_index_name)
        if len(base_index_name) > 60:
            digest = hashlib.sha256(base_index_name.encode("utf-8")).hexdigest()
            base_index_name = f"idx_{table_unquoted[:30]}_{digest[:8]}_sk"
            base_index_name = re.sub(r"[^0-9a-zA-Z_]+", "_", base_index_name)
        return base_index_name[:63]

    @classmethod
    def create_table(cls, name, columns={}, drop=False):
        if "." in name:
            fqtn = TableHelper.quote(name)
        else:
            fqtn = f"public.{TableHelper.quote(name)}"

        schema, table = fqtn.split(".")
        schema_unquoted = schema.replace('"', "")
        table_unquoted = table.replace('"', "")
        trigger_name = (
            f"on_update_row_{schema_unquoted}_{table_unquoted}".replace(".", "_")
        )
        trigger_identifier = TableHelper.quote(trigger_name)
        schema_identifier = TableHelper.quote(schema_unquoted)
        sql = []
        if drop:
            sql.append(cls.drop_table(fqtn)[0])
        sql.append(
            f"""
            CREATE TABLE {fqtn} (
              sys_id BIGSERIAL PRIMARY KEY,
              sys_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              sys_modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              sys_modified_by TEXT NOT NULL DEFAULT 'SYSTEM',
              sys_modified_row TIMESTAMP NOT NULL DEFAULT CLOCK_TIMESTAMP(),
              sys_modified_count INTEGER NOT NULL DEFAULT 0,
              sys_dirty BOOLEAN NOT NULL DEFAULT FALSE,
              sys_table TEXT NOT NULL,
              sys_keywords TEXT
            );

            SELECT SETVAL(PG_GET_SERIAL_SEQUENCE('{fqtn}', 'sys_id'),1000,TRUE);

            {cls._sys_modified_function_sql(schema_identifier)}

            DROP TRIGGER IF EXISTS {trigger_identifier} ON {fqtn};

            CREATE TRIGGER {trigger_identifier}
            BEFORE INSERT OR UPDATE ON {fqtn}
            FOR EACH ROW EXECUTE PROCEDURE {schema_identifier}.on_sys_modified();

        """
        )

        for key, val in columns.items():
            key = re.sub("<>!=%", "", key)
            if key in system_fields:
                continue
            sql.append(
                f"ALTER TABLE {TableHelper.quote(fqtn)} ADD COLUMN {TableHelper.quote(key)} {TYPES.get_type(val)};"
            )

        index_name = cls._sys_keywords_index_name(schema_unquoted, table_unquoted)
        index_identifier = TableHelper.quote(index_name)
        sql.append(
            f"CREATE INDEX {index_identifier} ON {fqtn} USING GIN (TO_TSVECTOR('simple', COALESCE(sys_keywords, '')));"
        )

        sql = sqlparse.format(" ".join(sql), reindent=True, keyword_case="upper")
        return sql, tuple()

    @classmethod
    def ensure_system_columns(
        cls,
        name,
        existing_columns=None,
        force=False,
        existing_indexes=None,
    ):
        """Ensure all Velocity system columns and triggers exist for the table."""
        existing_columns = {
            col.lower() for col in (existing_columns or [])
        }

        existing_indexes = {
            (idx or "").lower(): (definition or "")
            for idx, definition in (existing_indexes or {}).items()
        }

        required_columns = [
            "sys_id",
            "sys_created",
            "sys_modified",
            "sys_modified_by",
            "sys_modified_row",
            "sys_modified_count",
            "sys_dirty",
            "sys_table",
            "sys_keywords",
        ]

        missing_columns = [
            column for column in required_columns if column not in existing_columns
        ]

        if not missing_columns and not force:
            return None

        if "." in name:
            schema_name, table_name = name.split(".", 1)
        else:
            schema_name = cls.default_schema
            table_name = name

        schema_unquoted = schema_name.replace('"', "")
        table_unquoted = table_name.replace('"', "")

        schema_identifier = TableHelper.quote(schema_unquoted)
        table_identifier = TableHelper.quote(table_unquoted)
        fqtn = f"{schema_identifier}.{table_identifier}"

        trigger_name = (
            f"on_update_row_{schema_unquoted}_{table_unquoted}".replace(".", "_")
        )
        trigger_identifier = TableHelper.quote(trigger_name)

        statements = []
        added_columns = set()
        columns_after = set(existing_columns)

        if "sys_id" in missing_columns:
            statements.append(
                f"ALTER TABLE {fqtn} ADD COLUMN {TableHelper.quote('sys_id')} BIGSERIAL PRIMARY KEY;"
            )
            added_columns.add("sys_id")
            columns_after.add("sys_id")

        column_definitions = {
            "sys_created": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "sys_modified": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "sys_modified_by": "TEXT NOT NULL DEFAULT 'SYSTEM'",
            "sys_modified_row": "TIMESTAMP NOT NULL DEFAULT CLOCK_TIMESTAMP()",
            "sys_modified_count": "INTEGER NOT NULL DEFAULT 0",
            "sys_dirty": "BOOLEAN NOT NULL DEFAULT FALSE",
            "sys_table": "TEXT",
            "sys_keywords": "TEXT",
        }

        for column, definition in column_definitions.items():
            if column in missing_columns:
                statements.append(
                    f"ALTER TABLE {fqtn} ADD COLUMN {TableHelper.quote(column)} {definition};"
                )
                added_columns.add(column)
                columns_after.add(column)

        default_map = {
            "sys_created": "CURRENT_TIMESTAMP",
            "sys_modified": "CURRENT_TIMESTAMP",
            "sys_modified_by": "'SYSTEM'",
            "sys_modified_row": "CLOCK_TIMESTAMP()",
            "sys_modified_count": "0",
            "sys_dirty": "FALSE",
        }

        for column, default_sql in default_map.items():
            if column in columns_after and (force or column in added_columns):
                quoted_column = TableHelper.quote(column)
                statements.append(
                    f"UPDATE {fqtn} SET {quoted_column} = {default_sql} WHERE {quoted_column} IS NULL;"
                )
                statements.append(
                    f"ALTER TABLE {fqtn} ALTER COLUMN {quoted_column} SET DEFAULT {default_sql};"
                )

        if "sys_table" in columns_after and (force or "sys_table" in added_columns):
            quoted_column = TableHelper.quote("sys_table")
            table_literal = table_unquoted.replace("'", "''")
            statements.append(
                f"UPDATE {fqtn} SET {quoted_column} = COALESCE({quoted_column}, '{table_literal}') WHERE {quoted_column} IS NULL;"
            )

        not_null_columns = {
            "sys_created",
            "sys_modified",
            "sys_modified_by",
            "sys_modified_row",
            "sys_modified_count",
            "sys_dirty",
            "sys_table",
        }

        for column in not_null_columns:
            if column in columns_after and (force or column in added_columns):
                statements.append(
                    f"ALTER TABLE {fqtn} ALTER COLUMN {TableHelper.quote(column)} SET NOT NULL;"
                )

        reset_trigger = force or bool(added_columns)

        if reset_trigger:
            statements.append(
                f"DROP TRIGGER IF EXISTS {trigger_identifier} ON {fqtn};"
            )
            statements.append(cls._sys_modified_function_sql(schema_identifier))
            statements.append(
                f"""
                CREATE TRIGGER {trigger_identifier}
                BEFORE INSERT OR UPDATE ON {fqtn}
                FOR EACH ROW EXECUTE PROCEDURE {schema_identifier}.on_sys_modified();
            """
            )

        if "sys_keywords" in columns_after:
            index_name = cls._sys_keywords_index_name(schema_unquoted, table_unquoted)
            quoted_index_name = TableHelper.quote(index_name)

            current_definition = existing_indexes.get(index_name.lower(), "")
            current_definition_lower = current_definition.lower()
            has_target = (
                "to_tsvector" in current_definition_lower
                and "coalesce" in current_definition_lower
                and "sys_keywords" in current_definition_lower
            )
            needs_rebuild = force or not has_target

            if needs_rebuild:
                statements.append(
                    f"DROP INDEX IF EXISTS {quoted_index_name};"
                )
                statements.append(
                    f"CREATE INDEX {quoted_index_name} ON {fqtn} USING GIN (TO_TSVECTOR('simple', COALESCE(sys_keywords, '')));"
                )

        if not statements:
            return None

        sql = sqlparse.format(
            " ".join(statements), reindent=True, keyword_case="upper"
        )
        return sql, tuple()

    @classmethod
    def drop_table(cls, name):
        return f"drop table if exists {TableHelper.quote(name)} cascade;", tuple()

    @classmethod
    def drop_column(cls, table, name, cascade=True):
        if cascade:
            return (
                f"ALTER TABLE {TableHelper.quote(table)} DROP COLUMN {TableHelper.quote(name)} CASCADE",
                tuple(),
            )
        else:
            return (
                f"ALTER TABLE {TableHelper.quote(table)} DROP COLUMN {TableHelper.quote(name)}",
                tuple(),
            )

    @classmethod
    def columns(cls, name):
        if "." in name:
            return """
            select column_name
            from information_schema.columns
            where UPPER(table_schema) = UPPER(%s)
            and UPPER(table_name) = UPPER(%s)
            """, tuple(
                name.split(".")
            )
        else:
            return """
            select column_name
            from information_schema.columns
            where UPPER(table_name) = UPPER(%s)
            """, tuple(
                [
                    name,
                ]
            )

    @classmethod
    def column_info(cls, table, name):
        params = table.split(".")
        params.append(name)
        if "." in table:
            return """
            select *
            from information_schema.columns
            where UPPER(table_schema ) = UPPER(%s)
            and UPPER(table_name) = UPPER(%s)
            and UPPER(column_name) = UPPER(%s)
            """, tuple(
                params
            )
        else:
            return """
            select *
            from information_schema.columns
            where UPPER(table_name) = UPPER(%s)
            and UPPER(column_name) = UPPER(%s)
            """, tuple(
                params
            )

    @classmethod
    def primary_keys(cls, table):
        params = table.split(".")
        params.reverse()
        if "." in table:
            return """
            SELECT
              pg_attribute.attname
            FROM pg_index, pg_class, pg_attribute, pg_namespace
            WHERE
              pg_class.oid = %s::regclass AND
              indrelid = pg_class.oid AND
              nspname = %s AND
              pg_class.relnamespace = pg_namespace.oid AND
              pg_attribute.attrelid = pg_class.oid AND
              pg_attribute.attnum = any(pg_index.indkey)
             AND indisprimary
            """, tuple(
                params
            )
        else:
            return """
            SELECT
              pg_attribute.attname
            FROM pg_index, pg_class, pg_attribute, pg_namespace
            WHERE
              pg_class.oid = %s::regclass AND
              indrelid = pg_class.oid AND
              pg_class.relnamespace = pg_namespace.oid AND
              pg_attribute.attrelid = pg_class.oid AND
              pg_attribute.attnum = any(pg_index.indkey)
             AND indisprimary
            """, tuple(
                params
            )

    @classmethod
    def foreign_key_info(cls, table=None, column=None, schema=None):
        if "." in table:
            schema, table = table.split(".")

        sql = [
            """
        SELECT
             KCU1.CONSTRAINT_NAME AS "FK_CONSTRAINT_NAME"
           , KCU1.CONSTRAINT_SCHEMA AS "FK_CONSTRAINT_SCHEMA"
           , KCU1.CONSTRAINT_CATALOG AS "FK_CONSTRAINT_CATALOG"
           , KCU1.TABLE_NAME AS "FK_TABLE_NAME"
           , KCU1.COLUMN_NAME AS "FK_COLUMN_NAME"
           , KCU1.ORDINAL_POSITION AS "FK_ORDINAL_POSITION"
           , KCU2.CONSTRAINT_NAME AS "UQ_CONSTRAINT_NAME"
           , KCU2.CONSTRAINT_SCHEMA AS "UQ_CONSTRAINT_SCHEMA"
           , KCU2.CONSTRAINT_CATALOG AS "UQ_CONSTRAINT_CATALOG"
           , KCU2.TABLE_NAME AS "UQ_TABLE_NAME"
           , KCU2.COLUMN_NAME AS "UQ_COLUMN_NAME"
           , KCU2.ORDINAL_POSITION AS "UQ_ORDINAL_POSITION"
           , KCU1.CONSTRAINT_NAME AS "CONSTRAINT_NAME"
           , KCU2.CONSTRAINT_SCHEMA AS "REFERENCED_TABLE_SCHEMA"
           , KCU2.TABLE_NAME AS "REFERENCED_TABLE_NAME"
           , KCU2.COLUMN_NAME AS "REFERENCED_COLUMN_NAME"
        FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS RC
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE KCU1
        ON KCU1.CONSTRAINT_CATALOG = RC.CONSTRAINT_CATALOG
           AND KCU1.CONSTRAINT_SCHEMA = RC.CONSTRAINT_SCHEMA
           AND KCU1.CONSTRAINT_NAME = RC.CONSTRAINT_NAME
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE KCU2
        ON KCU2.CONSTRAINT_CATALOG = RC.UNIQUE_CONSTRAINT_CATALOG
           AND KCU2.CONSTRAINT_SCHEMA = RC.UNIQUE_CONSTRAINT_SCHEMA
           AND KCU2.CONSTRAINT_NAME = RC.UNIQUE_CONSTRAINT_NAME
           AND KCU2.ORDINAL_POSITION = KCU1.ORDINAL_POSITION
        """
        ]
        vals = []
        where = {}
        if schema:
            where["LOWER(KCU1.CONSTRAINT_SCHEMA)"] = schema.lower()
        if table:
            where["LOWER(KCU1.TABLE_NAME)"] = table.lower()
        if column:
            where["LOWER(KCU1.COLUMN_NAME)"] = column.lower()
        sql.append("WHERE")
        connect = ""
        for key, val in where.items():
            if connect:
                sql.append(connect)
            sql.append(f"{key} = %s")
            vals.append(val)
            connect = "AND"

        sql = sqlparse.format(" ".join(sql), reindent=True, keyword_case="upper")
        return sql, tuple(vals)

    @classmethod
    def create_foreign_key(
        cls, table, columns, key_to_table, key_to_columns, name=None, schema=None
    ):
        if "." not in table and schema:
            table = f"{schema}.{table}"
        if isinstance(key_to_columns, str):
            key_to_columns = [key_to_columns]
        if isinstance(columns, str):
            columns = [columns]
        if not name:
            m = hashlib.md5()
            m.update(table.encode("utf-8"))
            m.update(" ".join(columns).encode("utf-8"))
            m.update(key_to_table.encode("utf-8"))
            m.update(" ".join(key_to_columns).encode("utf-8"))
            name = f"FK_{m.hexdigest()}"
        sql = f"ALTER TABLE {table} ADD CONSTRAINT {name} FOREIGN KEY ({','.join(columns)}) REFERENCES {key_to_table} ({','.join(key_to_columns)});"
        sql = sqlparse.format(sql, reindent=True, keyword_case="upper")
        return sql, tuple()

    @classmethod
    def drop_foreign_key(
        cls,
        table,
        columns,
        key_to_table=None,
        key_to_columns=None,
        name=None,
        schema=None,
    ):
        if "." not in table and schema:
            table = f"{schema}.{table}"
        if isinstance(key_to_columns, str):
            key_to_columns = [key_to_columns]
        if isinstance(columns, str):
            columns = [columns]
        if not name:
            m = hashlib.md5()
            m.update(table.encode("utf-8"))
            m.update(" ".join(columns).encode("utf-8"))
            m.update(key_to_table.encode("utf-8"))
            m.update(" ".join(key_to_columns).encode("utf-8"))
            name = f"FK_{m.hexdigest()}"
        sql = f"ALTER TABLE {table} DROP CONSTRAINT {name};"
        return sql, tuple()

    @classmethod
    def create_index(
        cls,
        tx,
        table=None,
        columns=None,
        unique=False,
        direction=None,
        where=None,
        name=None,
        schema=None,
        trigram=None,
        lower=None,
    ):
        """
        The following statements must be executed on the database instance once to enable respective trigram features.
        CREATE EXTENSION pg_trgm; is required to use  gin.
        CREATE EXTENSION btree_gist; is required to use gist
        """
        if "." not in table and schema:
            table = f"{schema}.{table}"
        if isinstance(columns, (list, set)):
            columns = ",".join([TableHelper.quote(c) for c in columns])
        else:
            columns = TableHelper.quote(columns)
        sql = ["CREATE"]
        if unique:
            sql.append("UNIQUE")
        sql.append("INDEX")
        tablename = TableHelper.quote(table)
        if not name:
            name = re.sub(
                r"\([^)]*\)",
                "",
                columns.replace(" ", "").replace(",", "_").replace('"', ""),
            )
        if trigram:
            sql.append(f"IDX__TRGM_{table.replace('.', '_')}_{trigram}__{name}".upper())
        else:
            sql.append(f"IDX__{table.replace('.', '_')}__{name}".upper())
        sql.append("ON")
        sql.append(TableHelper.quote(tablename))

        if trigram:
            sql.append("USING")
            sql.append(trigram)
        sql.append("(")
        join = ""
        for column_name in columns.split(","):
            column_name = column_name.replace('"', "")
            if join:
                sql.append(join)
            column = tx.table(table).column(column_name)
            if not column.exists():
                raise Exception(
                    f"Column {column_name} does not exist in table {table}."
                )
            if column.py_type == str:
                if lower:
                    sql.append(f"lower({TableHelper.quote(column_name)})")
                else:
                    sql.append(TableHelper.quote(column_name))
            else:
                sql.append(TableHelper.quote(column_name))
            join = ","

        if trigram:
            sql.append(f"{trigram.lower()}_trgm_ops")
        sql.append(")")
        vals = []
        s, v = TableHelper(tx, table).make_where(where)
        sql.append(s)
        vals.extend(v)

        sql = sqlparse.format(" ".join(sql), reindent=True, keyword_case="upper")
        return sql, tuple(vals)

    @classmethod
    def drop_index(cls, table=None, columns=None, name=None, schema=None, trigram=None):
        if "." not in table and schema:
            table = f"{schema}.{table}"
        if isinstance(columns, (list, set)):
            columns = ",".join([TableHelper.quote(c) for c in columns])
        else:
            columns = TableHelper.quote(columns)
        sql = ["DROP"]
        sql.append("INDEX IF EXISTS")
        _tablename = TableHelper.quote(table)
        if not name:
            name = re.sub(
                r"\([^)]*\)",
                "",
                columns.replace(" ", "").replace(",", "_").replace('"', ""),
            )
        if trigram:
            sql.append(f"IDX__TRGM_{table.replace('.', '_')}_{trigram.upper()}__{name}")
        else:
            sql.append(f"IDX__{table.replace('.', '_')}__{name}")

        sql = sqlparse.format(" ".join(sql), reindent=True, keyword_case="upper")
        return sql, tuple()

    @classmethod
    def massage_data(cls, data):
        data = {key: val for key, val in data.items()}
        primaryKey = set(cls.GetPrimaryKeyColumnNames())
        if not primaryKey:
            if not cls.Exists():
                raise exceptions.DbTableMissingError
        dataKeys = set(data.keys()).intersection(primaryKey)
        dataColumns = set(data.keys()).difference(primaryKey)
        pk = {}
        pk.update([(k, data[k]) for k in dataKeys])
        d = {}
        d.update([(k, data[k]) for k in dataColumns])
        return d, pk

    @classmethod
    def alter_add(cls, table, columns, null_allowed=True):
        """
        Modify the table to add new columns. If the `value` is 'now()', treat it as a
        TIMESTAMP type (optionally with a DEFAULT now() clause).
        """
        sql = []
        null_clause = "NOT NULL" if not null_allowed else ""

        if isinstance(columns, dict):
            for col_name, val in columns.items():
                col_name_clean = re.sub("<>!=%", "", col_name)
                # If the user wants 'now()' to be recognized as a TIMESTAMP column:
                if isinstance(val, str) and val.strip().lower() == "@@now()":
                    # We assume the user wants the type to be TIMESTAMP
                    # Optionally we can also add `DEFAULT now()` if desired
                    # so that newly added rows use the current timestamp
                    col_type = "TIMESTAMP"
                    sql.append(
                        f"ALTER TABLE {TableHelper.quote(table)} "
                        f"ADD {TableHelper.quote(col_name_clean)} {col_type} {null_clause};"
                    )
                else:
                    # Normal code path: rely on your `TYPES.get_type(...)` logic
                    col_type = TYPES.get_type(val)
                    sql.append(
                        f"ALTER TABLE {TableHelper.quote(table)} "
                        f"ADD {TableHelper.quote(col_name_clean)} {col_type} {null_clause};"
                    )

        final_sql = sqlparse.format(" ".join(sql), reindent=True, keyword_case="upper")
        return final_sql, tuple()

    @classmethod
    def alter_drop(cls, table, columns):
        sql = [f"ALTER TABLE {TableHelper.quote(table)} DROP COLUMN"]
        if isinstance(columns, dict):
            for key, val in columns.items():
                key = re.sub("<>!=%", "", key)
                sql.append(f"{key},")
        if sql[-1][-1] == ",":
            sql[-1] = sql[-1][:-1]
        sql = sqlparse.format(" ".join(sql), reindent=True, keyword_case="upper")
        return sql, tuple()

    @classmethod
    def alter_column_by_type(cls, table, column, value, nullable=True):
        sql = [f"ALTER TABLE {TableHelper.quote(table)} ALTER COLUMN"]
        sql.append(f"{TableHelper.quote(column)} TYPE {TYPES.get_type(value)}")
        sql.append(f"USING {TableHelper.quote(column)}::{TYPES.get_conv(value)}")
        if not nullable:
            sql.append("NOT NULL")
        sql = sqlparse.format(" ".join(sql), reindent=True, keyword_case="upper")
        return sql, tuple()

    @classmethod
    def alter_column_by_sql(cls, table, column, value):
        sql = [f"ALTER TABLE {TableHelper.quote(table)} ALTER COLUMN"]
        sql.append(f"{TableHelper.quote(column)} {value}")
        sql = sqlparse.format(" ".join(sql), reindent=True, keyword_case="upper")
        return sql, tuple()

    @classmethod
    def rename_column(cls, table, orig, new):
        return (
            f"ALTER TABLE {TableHelper.quote(table)} RENAME COLUMN {TableHelper.quote(orig)} TO {TableHelper.quote(new)};",
            tuple(),
        )

    @classmethod
    def rename_table(cls, table, new):
        return (
            f"ALTER TABLE {TableHelper.quote(table)} RENAME TO {TableHelper.quote(new)};",
            tuple(),
        )

    @classmethod
    def create_savepoint(cls, sp):
        return f'SAVEPOINT "{sp}"', tuple()

    @classmethod
    def release_savepoint(cls, sp):
        return f'RELEASE SAVEPOINT "{sp}"', tuple()

    @classmethod
    def rollback_savepoint(cls, sp):
        return f'ROLLBACK TO SAVEPOINT "{sp}"', tuple()

    @classmethod
    def delete(cls, tx, table, where):
        sql = [f"DELETE FROM {TableHelper.quote(table)}"]
        vals = []
        if where:
            s, v = TableHelper(tx, table).make_where(where)
            sql.append(s)
            vals.extend(v)
        sql = sqlparse.format(" ".join(sql), reindent=True, keyword_case="upper")
        return sql, tuple(vals)

    @classmethod
    def truncate(cls, table):
        return f"truncate table {TableHelper.quote(table)}", tuple()

    @classmethod
    def create_view(cls, name, query, temp=False, silent=True):
        sql = ["CREATE"]
        if silent:
            sql.append("OR REPLACE")
        if temp:
            sql.append("TEMPORARY")
        sql.append("VIEW")
        sql.append(name)
        sql.append("AS")
        sql.append(query)
        sql = sqlparse.format(" ".join(sql), reindent=True, keyword_case="upper")
        return sql, tuple()

    @classmethod
    def drop_view(cls, name, silent=True):
        sql = ["DROP VIEW"]
        if silent:
            sql.append("IF EXISTS")
        sql.append(name)
        sql = sqlparse.format(" ".join(sql), reindent=True, keyword_case="upper")
        return sql, tuple()

    @classmethod
    def alter_trigger(cls, table, state="ENABLE", name="USER"):
        return f"ALTER TABLE {table} {state} TRIGGER {name}", tuple()

    @classmethod
    def set_sequence(cls, table, next_value):
        return (
            f"SELECT SETVAL(PG_GET_SERIAL_SEQUENCE('{table}', 'sys_id'),{next_value},FALSE)",
            tuple(),
        )

    @classmethod
    def missing(cls, tx, table, list, column="SYS_ID", where=None):
        sql = [
            "SELECT * FROM",
            f"UNNEST('{{{','.join([str(x) for x in list])}}}'::int[]) id",
            "EXCEPT ALL",
            f"SELECT {column} FROM {table}",
        ]
        vals = []
        if where:
            s, v = TableHelper(tx, table).make_where(where)
            sql.append(s)
            vals.extend(v)
        sql = sqlparse.format(" ".join(sql), reindent=True, keyword_case="upper")
        return sql, tuple(vals)

    @classmethod
    def indexes(cls, table):
        """
        Returns SQL for retrieving all indexes on a given table with detailed attributes.
        """
        if "." in table:
            schema, tbl = table.split(".", 1)
            schema = schema.replace('"', "")
            tbl = tbl.replace('"', "")
            return (
                """
                SELECT indexname, tablename, schemaname, indexdef
                FROM pg_indexes
                WHERE tablename = %s AND schemaname = %s
                """,
                (tbl, schema),
            )

        return (
            """
            SELECT indexname, tablename, schemaname, indexdef
            FROM pg_indexes
            WHERE tablename = %s
            """,
            (table,),
        )
