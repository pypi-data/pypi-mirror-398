import unittest
from velocity.db.core.row import Row
from .common import CommonPostgresTest, engine, test_db


@engine.transaction
@engine.transaction
class TestRow(CommonPostgresTest):
    
    @classmethod
    def create_test_tables(cls, tx):
        """Create test tables for row tests."""
        # Create a test table for row operations
        tx.table("test_users").create(
            columns={
                "name": str,
                "age": int,
                "email": str,
            }
        )
    def test_init(self, tx):
        pass

    # def test_repr(self):
    #     expected = "{'sys_id': 1, 'sys_name': 'John', 'sys_age': 30}"
    #     self.assertEqual(repr(self.row), expected)

    # def test_str(self):
    #     expected = "{'sys_id': 1, 'sys_name': 'John', 'sys_age': 30}"
    #     self.assertEqual(str(self.row), expected)

    # def test_len(self):
    #     self.assertEqual(len(self.row), 1)

    # def test_getitem(self):
    #     self.assertEqual(self.row['sys_name'], 'John')

    # def test_setitem(self):
    #     with self.assertRaises(Exception):
    #         self.row['sys_id'] = 2

    # def test_delitem(self):
    #     with self.assertRaises(Exception):
    #         del self.row['sys_id']

    # def test_contains(self):
    #     self.assertTrue('sys_name' in self.row)
    #     self.assertFalse('sys_email' in self.row)

    # def test_clear(self):
    #     self.row.clear()
    #     # Add assertions here to check if the row is cleared

    # def test_keys(self):
    #     expected = ['sys_id', 'sys_name', 'sys_age']
    #     self.assertEqual(self.row.keys(), expected)

    # def test_values(self):
    #     expected = [1, 'John', 30]
    #     self.assertEqual(self.row.values(), expected)

    # def test_items(self):
    #     expected = [('sys_id', 1), ('sys_name', 'John'), ('sys_age', 30)]
    #     self.assertEqual(self.row.items(), expected)

    # def test_get(self):
    #     self.assertEqual(self.row.get('sys_name'), 'John')
    #     self.assertEqual(self.row.get('sys_email'), None)

    # def test_setdefault(self):
    #     self.assertEqual(self.row.setdefault('sys_name'), 'John')
    #     self.assertEqual(self.row.setdefault('sys_email', 'john@example.com'), 'john@example.com')

    # def test_update(self):
    #     self.row.update({'sys_name': 'Jane', 'sys_age': 25})
    #     # Add assertions here to check if the row is updated

    # def test_iterkeys(self):
    #     expected = ['sys_id', 'sys_name', 'sys_age']
    #     self.assertEqual(list(self.row.iterkeys()), expected)

    # def test_itervalues(self):
    #     expected = [1, 'John', 30]
    #     self.assertEqual(list(self.row.itervalues()), expected)

    # def test_iteritems(self):
    #     expected = [('sys_id', 1), ('sys_name', 'John'), ('sys_age', 30)]
    #     self.assertEqual(list(self.row.iteritems()), expected)

    # def test_bool(self):
    #     self.assertTrue(bool(self.row))

    # def test_copy(self):
    #     copied_row = self.row.copy()
    #     # Add assertions here to check if the row is copied correctly

    # def test_to_dict(self):
    #     expected = {'sys_id': 1, 'sys_name': 'John', 'sys_age': 30}
    #     self.assertEqual(self.row.to_dict(), expected)

    # def test_extract(self):
    #     expected = {'sys_id': 1, 'sys_name': 'John'}
    #     self.assertEqual(self.row.extract('sys_id', 'sys_name'), expected)

    # def test_key_cols(self):
    #     expected = ['sys_id']
    #     self.assertEqual(self.row.key_cols, expected)

    # def test_split(self):
    #     data, pk = self.row.split()
    #     # Add assertions here to check if the row is split correctly

    # def test_data(self):
    #     data = self.row.data
    #     # Add assertions here to check if the data is extracted correctly

    # def test_row(self):
    #     row = self.row.row('sys_id')
    #     # Add assertions here to check if the row is fetched correctly

    # def test_match(self):
    #     other = {'sys_id': 1, 'sys_name': 'John', 'sys_age': 30}
    #     self.assertTrue(self.row.match(other))
    #     other = {'sys_id': 2, 'sys_name': 'Jane', 'sys_age': 25}
    #     self.assertFalse(self.row.match(other))

    # def test_touch(self):
    #     self.row.touch()
    #     # Add assertions here to check if the row is touched correctly

    # def test_delete(self):
    #     self.row.delete()
    #     # Add assertions here to check if the row is deleted correctly


if __name__ == "__main__":
    unittest.main()
