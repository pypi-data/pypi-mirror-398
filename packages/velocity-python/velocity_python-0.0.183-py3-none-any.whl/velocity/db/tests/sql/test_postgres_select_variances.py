import unittest
from velocity.db.servers import postgres, tablehelper
from velocity.db.core.table import Query
from common import TestSQLModule, engine

DO_ALL = True

print(f"DO_ALL: {DO_ALL}")


@engine.transaction
class TestLocal(TestSQLModule):

    def test_table_helper(self, tx):
        if not DO_ALL:
            return
        th = tablehelper.TableHelper(tx, "fk_child")

        expected_output = (
            "column_name IN (SELECT COLUMN_NAME\nFROM TABLE_NAME\nWHERE COLUMN_NAME = 1)",
            None,
        )
        t = th.make_predicate(
            "column_name",
            Query("select column_name from table_name where column_name = 1"),
        )
        self.assertEqual(t, expected_output)

        expected_output = ("column_name = %s", "value")
        t = th.make_predicate("column_name", "value")
        self.assertEqual(t, expected_output)

        expected_output = ("column_name > %s", "value")
        t = th.make_predicate(">column_name", "value")
        self.assertEqual(t, expected_output)

        expected_output = ("column_name <> %s", "value")
        t = th.make_predicate("<>column_name", "value")
        self.assertEqual(t, expected_output)

        expected_output = ("B.parent_name <> %s", "value")
        t = th.make_predicate("<>parent_id>parent_name", "value")
        self.assertEqual(t, expected_output)

        expected_output = ('B."table" <> %s', "value")
        t = th.make_predicate("<>parent_id>table", "value")
        self.assertEqual(t, expected_output)

        expected_output = ("B.parent_name IS NOT NULL", None)
        t = th.make_predicate("<>parent_id>parent_name", None)
        self.assertEqual(t, expected_output)

        columns = [
            ("parent_id", "parent_id"),
            ("parent_name", "parent_name"),
            ("parent_id>parent_name", "parent_id_parent_name"),
            ("quijibo", "quijibo"),
            ("doojibo", "doojibo"),
            ("symmetric", '"symmetric"'),
            ("table", '"table"'),
            ("parent_id>is_valid", "parent_id_is_valid"),
            ("sum_info", "sum_info"),
            ("max_hours", "max_hours"),
            ("parent_id>num_things", "parent_id_num_things"),
            ("parent_id>symmetric", "parent_id_symmetric"),
            ("parent_id>table", "parent_id_table"),
        ]
        for key, val in columns:
            column = th.resolve_references(key, options={"alias_only": True})
            self.assertEqual(column, val)
        columns = [
            ("parent_id", "parent_id"),
            ("parent_name", "parent_name"),
            ("parent_id>parent_name", "B.parent_name"),
            ("quijibo", "quijibo"),
            ("doojibo", "doojibo"),
            ("symmetric", '"symmetric"'),
            ("table", '"table"'),
            ("parent_id>is_valid", "B.is_valid"),
            ("sum_info", "sum_info"),
            ("max_hours", "max_hours"),
            ("parent_id>num_things", "B.num_things"),
            ("parent_id>symmetric", 'B."symmetric"'),
            ("parent_id>table", 'B."table"'),
        ]
        for key, val in columns:
            column = th.resolve_references(key, options={"alias_table": True})
            self.assertEqual(column, val)

        columns = [
            ("parent_id", "parent_id"),
            ("parent_name", "parent_name"),
            ("parent_id>parent_name", "B.parent_name as parent_id_parent_name"),
            ("quijibo", "quijibo"),
            ("doojibo", "doojibo"),
            ("symmetric", '"symmetric"'),
            ("table", '"table"'),
            ("parent_id>is_valid", "B.is_valid as parent_id_is_valid"),
            ("sum_info", "sum_info"),
            ("max_hours", "max_hours"),
            ("parent_id>num_things", "B.num_things as parent_id_num_things"),
            ("parent_id>symmetric", 'B."symmetric" as parent_id_symmetric'),
            ("parent_id>table", 'B."table" as parent_id_table'),
        ]
        for key, val in columns:
            column = th.resolve_references(
                key, options={"alias_table": True, "alias_column": True}
            )
            self.assertEqual(column, val)

        columns = [
            ("parent_id", "parent_id"),
            ("parent_name", "parent_name"),
            ("parent_id>parent_name", "fk_parent.parent_name as parent_id_parent_name"),
            ("quijibo", "quijibo"),
            ("doojibo", "doojibo"),
            ("symmetric", '"symmetric"'),
            ("table", '"table"'),
            ("parent_id>is_valid", "fk_parent.is_valid as parent_id_is_valid"),
            ("sum_info", "sum_info"),
            ("max_hours", "max_hours"),
            ("parent_id>num_things", "fk_parent.num_things as parent_id_num_things"),
            ("parent_id>symmetric", 'fk_parent."symmetric" as parent_id_symmetric'),
            ("parent_id>table", 'fk_parent."table" as parent_id_table'),
        ]
        for key, val in columns:
            column = th.resolve_references(
                key, options={"alias_table": False, "alias_column": True}
            )
            self.assertEqual(column, val)

    def test_select_snuffleupagus(self, tx):
        if not DO_ALL:
            return

        expected_sql = """SELECT parent_id,
       parent_name,
       B.parent_name AS parent_id_parent_name,
       quijibo,
       doojibo,
       "symmetric",
       "table",
       B.is_valid AS parent_id_is_valid,
       sum_info,
       max_hours,
       B.num_things AS parent_id_num_things,
       B."symmetric" AS parent_id_symmetric,
       B."table" AS parent_id_table
FROM fk_child AS A
LEFT JOIN fk_parent AS B ON A.parent_id = B.sys_id
WHERE B.parent_name = %s
  AND B.is_valid IS TRUE
  AND B.num_things = %s
  AND B."symmetric" IS TRUE
  AND sum_info = %s
  AND max_hours = %s
GROUP BY parent_id_num_things,
         parent_id_parent_name
HAVING B.num_things = %s
AND B."symmetric" IS TRUE
ORDER BY parent_id_num_things DESC,
         parent_id_parent_name
OFFSET 99 ROWS FETCH NEXT 100 ROWS ONLY
FOR
UPDATE SKIP LOCKED"""
        expected_vars = ("value", 1, "value", 1, 1)

        sql, vars = tx.table("fk_child").select(
            sql_only=True,
            columns=[
                "parent_id",
                "parent_name",
                "parent_id>parent_name",
                "quijibo",
                "doojibo",
                "symmetric",
                "table",
                "parent_id>is_valid",
                "sum_info",
                "max_hours",
                "parent_id>num_things",
                "parent_id>symmetric",
                "parent_id>table",
            ],
            where={
                "parent_id>parent_name": "value",
                "parent_id>is_valid": True,
                "parent_id>num_things": 1,
                "parent_id>symmetric": True,
                "sum_info": "value",
                "max_hours": 1,
            },
            having={"parent_id>num_things": 1, "parent_id>symmetric": True},
            orderby=["parent_id>num_things desc", "parent_id>parent_name"],
            groupby=["parent_id>num_things", "parent_id>parent_name"],
            lock=True,
            skip_locked=True,
            start=99,
            qty=100,
        )

        self.assertEqual(sql, expected_sql)
        self.assertEqual(vars, expected_vars)

    def test_create_index(self, tx):
        if not DO_ALL:
            return

        sql, vars = tx.table("weird_names_table").create_index(
            sql_only=True,
            unique=True,
            columns=[
                "sum_info",
                "max_hours",
                "order",
            ],
            where={
                "sum_info": "value",
                "max_hours": 1,
            },
        )
        expected_sql = """CREATE UNIQUE INDEX IDX__WEIRD_NAMES_TABLE__SUM_INFO_MAX_HOURS_ORDER ON weird_names_table (sum_info, max_hours, "order")
                          WHERE sum_info = %s
                          AND max_hours = %s
                          """
        expected_vars = ("value", 1)
        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)

    def test_delete(self, tx):
        if not DO_ALL:
            return

        sql, vars = tx.table("weird_names_table").delete(
            sql_only=True,
            where={
                "sum_info": "value",
                "max_hours": 1,
            },
        )
        expected_sql = """
        DELETE FROM weird_names_table WHERE sum_info = %s  AND  max_hours = %s
        """
        expected_vars = ("value", 1)
        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)

    def test_missing(self, tx):
        if not DO_ALL:
            return

        sql, vars = tx.table("weird_names_table").missing(
            sql_only=True,
            list_=["a", "b", "c"],
            where={
                "sum_info": "value",
                "max_hours": 1,
            },
        )
        expected_sql = """
        SELECT *
        FROM UNNEST('{a,b,c}'::int[]) id
        EXCEPT ALL
        SELECT sys_id
        FROM weird_names_table
        WHERE sum_info = %s
        AND max_hours = %s
        """
        expected_vars = ("value", 1)
        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)

    def test_insert(self, tx):
        if not DO_ALL:
            return

        sql, vars = tx.table("weird_names_table").insert(
            sql_only=True,
            data={
                "sum_info": "value",
                "max_hours": 1,
            },
        )
        expected_sql = """
        INSERT INTO weird_names_table (sum_info, max_hours)
        VALUES (%s,%s)
        """
        expected_vars = ("value", 1)
        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)

    def test_update(self, tx):
        if not DO_ALL:
            return

        sql, vars = tx.table("weird_names_table").update(
            sql_only=True,
            data={
                "sum_info": "value",
                "max_hours": 1,
                "order": None,
            },
            where={
                "peekaboo": "value",
            },
        )
        expected_sql = """
        UPDATE weird_names_table
        SET sum_info = %s,
            max_hours = %s,
            "order" = %s
        WHERE peekaboo = %s
        """
        expected_vars = ("value", 1, None, "value")

        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)

    def test_count(self, tx):
        if not DO_ALL:
            return

        sql, vars = tx.table("weird_names_table").count(
            sql_only=True,
            where={
                "peekaboo": "value",
            },
        )
        expected_sql = """
        SELECT count(*)
        FROM weird_names_table
        WHERE peekaboo = %s
        """
        expected_vars = ("value",)

        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)

    def test_extract_column_name(self, tx):
        if not DO_ALL:
            return

        th = tablehelper.TableHelper(tx, "fk_child")
        column = th.extract_column_name("parent_id>parent_name")
        self.assertEqual(column, "parent_id>parent_name")
        column = th.extract_column_name("count(parent_id>parent_name)")
        self.assertEqual(column, "parent_id>parent_name")
        column = th.extract_column_name("sum(count(parent_id>parent_name))")
        self.assertEqual(column, "parent_id>parent_name")
        column = th.extract_column_name("coalesce(parent_id>parent_name, 0)")
        self.assertEqual(column, "parent_id>parent_name")

        column = th.extract_column_name("count(pArent_id>pArent_nAme)")
        self.assertEqual(column, "pArent_id>pArent_nAme")

        column = th.extract_column_name('count("pArent_id>pArent_nAme")')
        self.assertEqual(column, "pArent_id>pArent_nAme")

        # Ensure balanced parentheses

        self.assertRaises(
            ValueError,
            th.extract_column_name,
            "sum(count(coalesce(parent_id>parent_name, 0)",
        )
        column = th.extract_column_name(
            "sum(count(coalesce(parent_id>parent_name, 0)))"
        )
        self.assertEqual(column, "parent_id>parent_name")

        column = th.extract_column_name("!=sum(parent_id>parent_name, 0)")
        self.assertEqual(column, "parent_id>parent_name")

        for op in th.operators:
            column = th.extract_column_name(f"{op}coalesce(parent_id>parent_name, 0)")
            self.assertEqual(column, "parent_id>parent_name")

    def test_resolve_references(self, tx):
        if not DO_ALL:
            return

        th = tablehelper.TableHelper(tx, "fk_child")
        column = th.resolve_references("parent_id>parent_name")
        self.assertEqual(column, "fk_parent.parent_name as parent_id_parent_name")

        column = th.resolve_references("sum(parent_id>parent_name)")
        self.assertEqual(column, "sum(fk_parent.parent_name) as parent_id_parent_name")

        column = th.resolve_references('coalesce(parent_id>parent_name, "account")')
        self.assertEqual(
            column,
            'coalesce(fk_parent.parent_name, "account") as parent_id_parent_name',
        )

        column = th.resolve_references('>coalesce(parent_id>parent_name, "account")')
        self.assertEqual(
            column,
            'coalesce(fk_parent.parent_name, "account") as parent_id_parent_name',
        )

        for op in th.operators:
            column = th.resolve_references(f"{op}coalesce(parent_id>parent_name, 0)")
            self.assertEqual(
                column, f"coalesce(fk_parent.parent_name, 0) as parent_id_parent_name"
            )

    def test_duplicate_rows(self, tx):
        if not DO_ALL:
            return

        sql, vars = tx.table("weird_names_table").duplicate_rows(
            sql_only=True, columns=["peekaboo"]
        )

        expected_sql = """
        SELECT t.*
        FROM weird_names_table t
        JOIN (SELECT peekaboo
            FROM weird_names_table
            GROUP BY peekaboo
            HAVING count(*) > %s) dup
        ON t.peekaboo = dup.peekaboo
        ORDER BY peekaboo
        """
        expected_vars = (1,)

        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)

    def test_select_strings(self, tx):
        if not DO_ALL:
            return

        sql, vars = tx.table("weird_names_table").select(
            sql_only=True,
            columns="distinct parent_id, child_id",
            where="where_value = 'value'",
            having="having_value = 'value'",
        )
        expected_sql = """
        SELECT DISTINCT parent_id, child_id
        FROM weird_names_table
        WHERE where_value = 'value'
        HAVING having_value = 'value'
        """
        expected_vars = ()

        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)

    def test_function_in_predicate(self, tx):
        if not DO_ALL:
            return
        th = tablehelper.TableHelper(tx, "fk_child")
        columns = [
            ('coalesce(parent_id,"")', 'coalesce(parent_id,"")'),
            ('coalesce(parent_name,"")', 'coalesce(parent_name,"")'),
            (
                'coalesce(parent_id>parent_name,"")',
                'coalesce(B.parent_name,"") as parent_id_parent_name',
            ),
            ('coalesce(quijibo,"")', 'coalesce(quijibo,"")'),
            ('coalesce(doojibo,"")', 'coalesce(doojibo,"")'),
            ('coalesce(symmetric,"")', 'coalesce("symmetric","")'),
            ('coalesce(table,"")', 'coalesce("table","")'),
            (
                'coalesce(parent_id>is_valid,"")',
                'coalesce(B.is_valid,"") as parent_id_is_valid',
            ),
            ('coalesce(sum_info,"")', 'coalesce(sum_info,"")'),
            ('coalesce(max_hours,"")', 'coalesce(max_hours,"")'),
            (
                'coalesce(parent_id>num_things,"")',
                'coalesce(B.num_things,"") as parent_id_num_things',
            ),
            (
                'coalesce(parent_id>symmetric,"")',
                'coalesce(B."symmetric","") as parent_id_symmetric',
            ),
            (
                'sum(parent_id>table,"")',
                'sum(B."table","") as parent_id_table',
            ),
        ]
        for key, val in columns:
            column = th.resolve_references(
                key, options={"alias_table": True, "alias_column": True}
            )
            self.assertEqual(column, val)


if __name__ == "__main__":
    unittest.main()
