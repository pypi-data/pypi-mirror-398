import unittest
import velocity.db.exceptions
from common import TestSQLModule, engine
import time

DO_ALL = True

print(f"DO_ALL: {DO_ALL}")


@engine.transaction
class TestLocal(TestSQLModule):

    def test_select_self_refer_wildcard(self, tx):
        if not DO_ALL:
            return

        sql, vars = tx.table("fk_child").select(
            sql_only=True, columns=["A.*", "parent_id>parent_name"]
        )
        expected_sql = """
        SELECT A.*,
        B.parent_name AS parent_id_parent_name
        FROM fk_child AS A
        LEFT JOIN fk_parent AS B ON A.parent_id = B.sys_id
        """
        expected_vars = ()
        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)

        # for row in tx.table("fk_child").select(
        #     columns=["A.*", "parent_id>parent_name"]
        # ):
        #     print(row)

        sql, vars = tx.table("fk_self_ref").select(
            sql_only=True, columns=["A.*", "ref_id>info"]
        )
        expected_sql = """
        SELECT A.*,
        B.info AS ref_id_info
        FROM fk_self_ref AS A
        LEFT JOIN fk_self_ref AS B ON A.ref_id = B.sys_id
        """
        expected_vars = ()
        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)
        # for row in tx.table("fk_self_ref").select(columns=["A.*", "ref_id>info"]):
        #     print(row)

        sql, vars = tx.table("fk_self_ref").select(
            sql_only=True, columns=["A.*", "ref_id>info", "ref_id>ref_id"]
        )
        expected_sql = """
        SELECT A.*,
        B.info AS ref_id_info,
        B.ref_id AS ref_id_ref_id
        FROM fk_self_ref AS A
        LEFT JOIN fk_self_ref AS B ON A.ref_id = B.sys_id
        """
        expected_vars = ()
        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)
        # for row in tx.table("fk_self_ref").select(
        #     columns=["A.*", "ref_id>info", "ref_id>ref_id"]
        # ):
        #     print(row)

    def test_complex_update(self, tx):
        if not DO_ALL:
            return
        sql, vars = tx.table("fk_child").update(
            sql_only=True,
            data={
                "name": "@parent_id>parent_name",
                "value": "@parent_id>num_things",
                "active": "@parent_id>is_valid",
            },
            where={
                ">parent_id>num_things": "10",
                "<num_things": "10",
            },
        )

        expected_sql = """
        UPDATE fk_child AS A
        SET name = %s,
            "value" = %s,
            active = %s
        LEFT JOIN fk_parent AS B
        WHERE B.num_things > %s
        AND num_things < %s
        AND A.parent_id = B.sys_id
        """
        expected_vars = (
            "@parent_id>parent_name",
            "@parent_id>num_things",
            "@parent_id>is_valid",
            "10",
            "10",
        )
        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)

        sql, vars = tx.table("fk_child").update(
            sql_only=True,
            data={
                "a": "a",
                "b": "a",
                "c": "a",
                "d": "a",
                "e": "a",
            },
            where={
                "sys_id": "700",
            },
        )

        expected_sql = """
        UPDATE fk_child
        SET a = %s,
            b = %s,
            c = %s,
            d = %s,
            e = %s
        WHERE sys_id = %s
        """
        expected_vars = ("a", "a", "a", "a", "a", "700")
        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)

    def test_complex_merge(self, tx):
        if not DO_ALL:
            return
        for i in range(10):
            tx.table("fk_you").insert(
                data={
                    "sys_id": i + 1000,
                    "parent_id": 1,
                    "name": f"Child {i}",
                    "value": i,
                    "active": True,
                },
            )
            self.assertRaises(
                velocity.db.exceptions.DbDuplicateKeyError,
                tx.table("fk_you").insert,
                data={
                    "sys_id": i + 1000,
                    "parent_id": 2,
                    "name": f"Child {i}-2",
                    "value": i,
                    "active": False,
                },
            )
        for i in range(10):
            tx.table("fk_you").insert(
                data={
                    "parent_id": 3,
                    "name": f"Child {i}-3",
                    "value": i,
                    "active": True,
                },
            )

        for i in range(10):
            tx.table("fk_you").merge(
                data={
                    "sys_id": i + 1000,
                    "parent_id": 4,
                    "name": f"Child {i}4",
                    "value": i,
                    "active": False,
                },
            )
        for i in range(10):
            tx.table("fk_you").merge(
                data={
                    "sys_id": i + 1100,
                    "parent_id": 4,
                    "name": f"Child {i}4",
                    "value": i,
                    "active": False,
                },
            )
        tx.commit()

    def test_duplicate_rows(self, tx):
        sql, vars = tx.table("special_values_table").duplicate_rows(
            sql_only=True,
            columns=["email", "status"],
        )
        expected_sql = """
         SELECT t.*
        FROM special_values_table t
        JOIN (SELECT email,
        status
        FROM special_values_table
        GROUP BY email,
                status
        HAVING count(*) > %s) dup
        ON t.email = dup.email AND t.status = dup.status
        ORDER BY email, status
        """
        expected_vars = (1,)

        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)

        # for row in tx.table("special_values_table").duplicate_rows(
        #     columns=["email", "status"],
        # ):
        #     print(row)

        sql, vars = tx.table("special_values_table").has_duplicates(
            sql_only=True,
            columns=["email", "status"],
        )
        expected_sql = """
        SELECT 1
        FROM special_values_table
        GROUP BY email,
                status
        HAVING count(*) > %s FETCH NEXT 1 ROWS ONLY
        """
        expected_vars = (1,)
        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)

        self.assertEqual(
            tx.table("special_values_table").has_duplicates(
                columns=["email", "status"],
            ),
            True,
        )

        expected_sql = """
        SELECT 1
        FROM special_values_table
        GROUP BY email,
                status
        HAVING count(*) > %s FETCH NEXT 1 ROWS ONLY
        """
        expected_vars = (1,)

        self.assertEqual(
            sql.split(),
            expected_sql.split(),
        )
        self.assertEqual(vars, expected_vars)
        self.assertEqual(
            tx.table("special_values_table").has_duplicates(
                columns=["sys_id", "status"],
            ),
            False,
        )
        for row in tx.table("special_values_table").duplicate_rows(
            columns=["sys_id", "status"],
        ):
            print(row)


if __name__ == "__main__":
    unittest.main()
