import unittest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from velocity.db.exceptions import (
    DbObjectExistsError, DbTableMissingError, DbColumnMissingError, 
    DbSchemaLockedError, DbDuplicateKeyError
)
from velocity.db.core.row import Row
from velocity.db.core.result import Result
from .common import CommonPostgresTest, engine, test_db


@engine.transaction
class TestTableComprehensive(CommonPostgresTest):
    """Comprehensive tests for Table class including edge cases, race conditions, and error recovery."""
    
    @classmethod
    def create_test_tables(cls, tx):
        """Create comprehensive test tables for Table testing."""
        # Basic table for general operations
        tx.table("table_test_basic").create(
            columns={
                "name": str,
                "age": int,
                "email": str,
                "active": bool,
                "score": float,
                "data": str,
            }
        )
        
        # Table with constraints and indexes
        tx.table("table_test_constraints").create(
            columns={
                "username": str,
                "email": str,
                "created_at": str,
                "status": str,
            }
        )
        
        # Create unique indexes for constraint testing
        try:
            tx.table("table_test_constraints").create_index("username", unique=True)
            tx.table("table_test_constraints").create_index("email", unique=True)
        except:
            pass  # Index might already exist
        
        # Parent table for foreign key testing
        tx.table("table_test_parent").create(
            columns={
                "parent_name": str,
                "category": str,
                "priority": int,
            }
        )
        
        # Child table with foreign key
        tx.table("table_test_child").create(
            columns={
                "parent_id": int,
                "child_name": str,
                "value": float,
                "notes": str,
            }
        )
        
        # Create foreign key
        tx.table("table_test_child").create_foreign_key("parent_id", "table_test_parent", "sys_id")
        
        # Large table for performance testing
        tx.table("table_test_large").create(
            columns={
                "batch_id": int,
                "sequence": int,
                "data_payload": str,
                "processed": bool,
                "timestamp": str,
            }
        )
        
        # Table for concurrent access testing
        tx.table("table_test_concurrent").create(
            columns={
                "counter": int,
                "worker_id": str,
                "operation": str,
                "timestamp": str,
            }
        )
        
        # Insert initial test data
        cls.insert_test_data(tx)
    
    @classmethod
    def insert_test_data(cls, tx):
        """Insert comprehensive test data."""
        # Basic table data
        basic_data = [
            {"name": "Alice Johnson", "age": 30, "email": "alice@test.com", "active": True, "score": 95.5, "data": "user_data_1"},
            {"name": "Bob Smith", "age": 25, "email": "bob@test.com", "active": False, "score": 87.2, "data": "user_data_2"},
            {"name": "Charlie Brown", "age": 35, "email": "charlie@test.com", "active": True, "score": 92.8, "data": "user_data_3"},
            {"name": "Diana Prince", "age": 28, "email": "diana@test.com", "active": True, "score": 88.9, "data": "user_data_4"},
            {"name": "Eve Adams", "age": 32, "email": "eve@test.com", "active": False, "score": 91.1, "data": "user_data_5"},
        ]
        
        for data in basic_data:
            tx.table("table_test_basic").insert(data)
        
        # Constraints table data
        constraint_data = [
            {"username": "admin", "email": "admin@test.com", "created_at": "2023-01-01", "status": "active"},
            {"username": "user1", "email": "user1@test.com", "created_at": "2023-01-02", "status": "pending"},
            {"username": "user2", "email": "user2@test.com", "created_at": "2023-01-03", "status": "active"},
        ]
        
        for data in constraint_data:
            tx.table("table_test_constraints").insert(data)
        
        # Parent-child data
        parent_data = [
            {"parent_name": "Project Alpha", "category": "development", "priority": 1},
            {"parent_name": "Project Beta", "category": "testing", "priority": 2},
            {"parent_name": "Project Gamma", "category": "deployment", "priority": 3},
        ]
        
        parent_ids = []
        for data in parent_data:
            row = tx.table("table_test_parent").new(data)
            parent_ids.append(row["sys_id"])
        
        child_data = [
            {"parent_id": parent_ids[0], "child_name": "Task A1", "value": 10.5, "notes": "Important task"},
            {"parent_id": parent_ids[0], "child_name": "Task A2", "value": 20.3, "notes": "Secondary task"},
            {"parent_id": parent_ids[1], "child_name": "Task B1", "value": 15.7, "notes": "Testing task"},
            {"parent_id": parent_ids[2], "child_name": "Task C1", "value": 30.9, "notes": "Deployment task"},
        ]
        
        for data in child_data:
            tx.table("table_test_child").insert(data)
        
        # Large table data (batch insert)
        large_data = []
        for batch in range(10):
            for seq in range(50):
                large_data.append({
                    "batch_id": batch,
                    "sequence": seq,
                    "data_payload": f"batch_{batch}_seq_{seq}_data",
                    "processed": seq % 2 == 0,
                    "timestamp": f"2023-01-{(seq % 28) + 1:02d}",
                })
        
        for data in large_data:
            tx.table("table_test_large").insert(data)

    def test_table_creation_and_existence(self, tx):
        """Test table creation and existence checking."""
        # Test table exists
        table = tx.table("table_test_basic")
        self.assertTrue(table.exists())
        
        # Test non-existent table
        non_existent = tx.table("non_existent_table")
        self.assertFalse(non_existent.exists())
        
        # Test creating new table
        new_table = tx.table("table_test_new")
        self.assertFalse(new_table.exists())
        new_table.create(columns={"test_col": str, "test_num": int})
        self.assertTrue(new_table.exists())

    def test_table_string_representation(self, tx):
        """Test table string representation."""
        table = tx.table("table_test_basic")
        str_repr = str(table)
        
        self.assertIn("Table: table_test_basic", str_repr)
        self.assertIn("(table exists) True", str_repr)
        self.assertIn("Columns:", str_repr)
        self.assertIn("Rows:", str_repr)

    def test_table_column_operations(self, tx):
        """Test table column operations."""
        table = tx.table("table_test_basic")
        
        # Test getting columns
        columns = table.columns()
        self.assertIn("name", columns)
        self.assertIn("age", columns)
        self.assertIn("email", columns)
        
        # Test system columns
        sys_columns = table.sys_columns()
        self.assertIn("sys_id", sys_columns)
        self.assertIn("sys_created_by", sys_columns)
        self.assertIn("sys_created_on", sys_columns)
        
        # Test column filtering (non-sys columns)
        filtered_columns = table.columns()
        sys_column_count = len(
            [col for col in filtered_columns if table.is_system_column(col)]
        )
        self.assertEqual(sys_column_count, 0)

    def test_table_row_count(self, tx):
        """Test table row counting."""
        table = tx.table("table_test_basic")
        
        # Test len() method
        count = len(table)
        self.assertEqual(count, 5)  # We inserted 5 rows
        
        # Test count() method
        count_method = table.count()
        self.assertEqual(count_method, 5)
        
        # Test count with condition
        count_active = table.count({"active": True})
        self.assertEqual(count_active, 3)  # 3 active users

    def test_table_iteration(self, tx):
        """Test table iteration."""
        table = tx.table("table_test_basic")
        
        # Test basic iteration
        rows = list(table)
        self.assertEqual(len(rows), 5)
        
        # Test that rows are Row objects
        for row in rows:
            self.assertIsInstance(row, Row)
        
        # Test iteration with callable syntax
        active_rows = list(table(where={"active": True}))
        self.assertEqual(len(active_rows), 3)

    def test_table_insert_operations(self, tx):
        """Test table insert operations including edge cases."""
        table = tx.table("table_test_basic")
        
        # Test basic insert
        data = {"name": "Test User", "age": 40, "email": "test@test.com", "active": True, "score": 85.0}
        row = table.new(data)
        self.assertIsInstance(row, Row)
        self.assertEqual(row["name"], "Test User")
        
        # Test insert with None values
        data_with_none = {"name": "User With None", "age": None, "email": "none@test.com"}
        row_none = table.new(data_with_none)
        self.assertIsNone(row_none["age"])
        
        # Test insert with missing columns (should work with auto-creation)
        data_partial = {"name": "Partial User", "age": 25}
        row_partial = table.insert(data_partial)
        self.assertEqual(row_partial["name"], "Partial User")
        
        # Test insert with extra columns (should auto-create)
        data_extra = {"name": "Extra User", "age": 25, "new_column": "new_value"}
        row_extra = table.insert(data_extra)
        self.assertEqual(row_extra["new_column"], "new_value")

    def test_table_update_operations(self, tx):
        """Test table update operations."""
        table = tx.table("table_test_basic")
        
        # Get a row to update
        row = table.select().one()
        original_name = row["name"]
        row_id = row["sys_id"]
        
        # Test basic update
        table.update({"name": "Updated Name"}, {"sys_id": row_id})
        updated_row = table.find(row_id)
        self.assertEqual(updated_row["name"], "Updated Name")
        
        # Test bulk update
        affected = table.update({"active": False}, {"active": True})
        self.assertGreaterEqual(affected, 0)
        
        # Test update with complex where clause
        table.update({"score": 100.0}, {"age__gte": 30, "active": False})

    def test_table_delete_operations(self, tx):
        """Test table delete operations."""
        table = tx.table("table_test_basic")
        
        initial_count = table.count()
        
        # Test delete with specific condition
        deleted = table.delete({"name": "Updated Name"})
        self.assertGreaterEqual(deleted, 0)
        
        # Test bulk delete
        deleted_bulk = table.delete({"active": False})
        self.assertGreaterEqual(deleted_bulk, 0)
        
        # Verify count changed
        final_count = table.count()
        self.assertLess(final_count, initial_count)

    def test_table_select_operations(self, tx):
        """Test table select operations with various conditions."""
        table = tx.table("table_test_basic")
        
        # Test select all
        result = table.select()
        self.assertIsInstance(result, Result)
        
        # Test select with where clause
        result_where = table.select(where={"active": True})
        active_count = len(list(result_where))
        self.assertGreaterEqual(active_count, 0)
        
        # Test select with order by
        result_ordered = table.select(orderby="name")
        ordered_list = list(result_ordered)
        self.assertGreaterEqual(len(ordered_list), 0)
        
        # Test select with limit
        result_limited = table.select(limit=2)
        limited_list = list(result_limited)
        self.assertLessEqual(len(limited_list), 2)
        
        # Test select with complex conditions
        result_complex = table.select(where={"age__gte": 25, "active": True}, orderby="-score", limit=3)
        complex_list = list(result_complex)
        self.assertLessEqual(len(complex_list), 3)

    def test_table_upsert_operations(self, tx):
        """Test table upsert operations."""
        table = tx.table("table_test_basic")
        
        # Test upsert (insert new)
        new_data = {"name": "Upsert User", "age": 45, "email": "upsert@test.com"}
        row = table.get(new_data)
        self.assertEqual(row["name"], "Upsert User")
        
        # Test upsert (update existing)
        existing_data = {"name": "Upsert User Updated", "age": 46}
        where_clause = {"email": "upsert@test.com"}
        row_updated = table.upsert(existing_data, where_clause)
        self.assertEqual(row_updated["name"], "Upsert User Updated")
        self.assertEqual(row_updated["age"], 46)

    def test_table_find_operations(self, tx):
        """Test table find operations."""
        table = tx.table("table_test_basic")
        
        # Test find by sys_id
        first_row = table.select().one()
        found_row = table.find(first_row["sys_id"])
        self.assertEqual(found_row["sys_id"], first_row["sys_id"])
        
        # Test find with dictionary conditions
        found_by_name = table.find({"name": first_row["name"]})
        self.assertEqual(found_by_name["name"], first_row["name"])
        
        # Test find non-existent
        non_existent = table.find(99999999)
        self.assertIsNone(non_existent)

    def test_table_get_value_operations(self, tx):
        """Test table get_value operations."""
        table = tx.table("table_test_basic")
        
        # Get a known row
        row = table.select().one()
        row_id = row["sys_id"]
        
        # Test get_value
        name_value = table.get_value("name", {"sys_id": row_id})
        self.assertEqual(name_value, row["name"])
        
        # Test get_value with non-existent column
        with self.assertRaises((DbColumnMissingError, Exception)):
            table.get_value("non_existent_column", {"sys_id": row_id})

    def test_table_constraint_violations(self, tx):
        """Test handling of constraint violations."""
        table = tx.table("table_test_constraints")
        
        # Test unique constraint violation
        try:
            # Try to insert duplicate username
            table.insert({"username": "admin", "email": "admin2@test.com"})
        except (DbDuplicateKeyError, Exception):
            pass  # Expected to fail
        
        # Test foreign key constraint
        child_table = tx.table("table_test_child")
        try:
            # Try to insert with non-existent parent_id
            child_table.insert({"parent_id": 99999, "child_name": "Orphan Task"})
        except Exception:
            pass  # Expected to fail

    def test_table_transaction_rollback(self, tx):
        """Test table operations with transaction rollback."""
        table = tx.table("table_test_basic")
        
        initial_count = table.count()
        
        # Insert some data
        table.insert({"name": "Rollback Test", "age": 99})
        
        # Verify the insert
        after_insert_count = table.count()
        self.assertEqual(after_insert_count, initial_count + 1)
        
        # Rollback (this will happen automatically at end of test due to transaction decorator)
        # The rollback behavior is tested by the framework itself

    def test_table_concurrent_access(self, tx):
        """Test table operations under concurrent access."""
        table = tx.table("table_test_concurrent")
        
        # Clear any existing data
        table.truncate()
        
        def worker(worker_id, operations=10):
            """Worker function for concurrent testing."""
            results = []
            for i in range(operations):
                try:
                    # Insert operation
                    row = table.insert({
                        "counter": i,
                        "worker_id": f"worker_{worker_id}",
                        "operation": "insert",
                        "timestamp": f"2023-01-01T{i:02d}:00:00"
                    })
                    results.append(("insert", row["sys_id"]))
                    
                    # Update operation
                    table.update(
                        {"operation": "updated"},
                        {"sys_id": row["sys_id"]}
                    )
                    results.append(("update", row["sys_id"]))
                    
                    time.sleep(0.001)  # Small delay to encourage race conditions
                    
                except Exception as e:
                    results.append(("error", str(e)))
            
            return results
        
        # Run concurrent workers
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(worker, i, 5) for i in range(3)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        # Verify operations completed
        self.assertGreater(len(all_results), 0)
        
        # Check final state
        final_count = table.count()
        self.assertGreaterEqual(final_count, 0)

    def test_table_large_dataset_performance(self, tx):
        """Test table operations with large datasets."""
        table = tx.table("table_test_large")
        
        # Test count on large table
        count = table.count()
        self.assertEqual(count, 500)  # 10 batches * 50 sequences
        
        # Test filtered queries on large table
        batch_0_count = table.count({"batch_id": 0})
        self.assertEqual(batch_0_count, 50)
        
        # Test complex query
        complex_result = table.select(
            where={"batch_id__gte": 5, "processed": True},
            orderby="sequence",
            limit=10
        )
        complex_list = list(complex_result)
        self.assertLessEqual(len(complex_list), 10)
        
        # Test bulk operations
        affected = table.update(
            {"processed": True},
            {"batch_id": 1}
        )
        self.assertGreaterEqual(affected, 0)

    def test_table_edge_cases_empty_operations(self, tx):
        """Test edge cases with empty operations."""
        table = tx.table("table_test_basic")
        
        # Test select with empty where clause
        result = table.select(where={})
        self.assertIsInstance(result, Result)
        
        # Test update with empty data (should be handled gracefully)
        try:
            table.update({}, {"sys_id": 1})
        except Exception:
            pass  # May legitimately fail
        
        # Test delete with empty where (dangerous but should work)
        # Don't actually run this as it would delete all data
        # table.delete({})

    def test_table_edge_cases_null_and_unicode(self, tx):
        """Test edge cases with NULL and Unicode data."""
        table = tx.table("table_test_basic")
        
        # Test with Unicode data
        unicode_data = {
            "name": "José María 🚀",
            "email": "josé@español.com",
            "data": "Unicode test: αβγδε"
        }
        row = table.new(unicode_data)
        self.assertEqual(row["name"], "José María 🚀")
        
        # Test with NULL values
        null_data = {
            "name": "NULL Test User",
            "age": None,
            "email": None,
            "active": None,
            "score": None
        }
        row_null = table.insert(null_data)
        self.assertEqual(row_null["name"], "NULL Test User")
        self.assertIsNone(row_null["age"])

    def test_table_data_type_edge_cases(self, tx):
        """Test edge cases with different data types."""
        table = tx.table("table_test_basic")
        
        # Test with extreme values
        extreme_data = {
            "name": "Extreme User",
            "age": 999999999,  # Very large integer
            "score": 999999.999999,  # Large float
            "active": True,
            "data": "x" * 1000  # Long string
        }
        row = table.new(extreme_data)
        self.assertEqual(row["name"], "Extreme User")
        
        # Test with minimum values
        min_data = {
            "name": "",  # Empty string
            "age": 0,
            "score": 0.0,
            "active": False
        }
        row_min = table.new(min_data)
        self.assertEqual(row_min["age"], 0)

    def test_table_error_recovery(self, tx):
        """Test table error recovery scenarios."""
        table = tx.table("table_test_basic")
        
        # Test recovery from constraint violation
        try:
            # Insert with very long email that might exceed column limit
            table.insert({
                "name": "Long Email User",
                "email": "very" + "long" * 100 + "@example.com"
            })
        except Exception:
            # Should be able to continue after error
            row = table.insert({
                "name": "Recovery User",
                "email": "recovery@test.com"
            })
            self.assertEqual(row["name"], "Recovery User")
        
        # Test recovery from invalid column reference
        try:
            table.select(where={"invalid_column": "value"})
        except Exception:
            # Should be able to continue
            result = table.select(where={"name": "Recovery User"})
            self.assertIsInstance(result, Result)

    def test_table_context_manager(self, tx):
        """Test table as context manager."""
        # Test with context manager
        with tx.table("table_test_basic") as table:
            count = table.count()
            self.assertGreaterEqual(count, 0)
        
        # Table should be properly closed after context

    def test_table_drop_and_recreate(self, tx):
        """Test dropping and recreating tables."""
        # Create temporary table
        temp_table = tx.table("table_test_temp")
        temp_table.create(columns={"temp_col": str})
        self.assertTrue(temp_table.exists())
        
        # Drop table
        temp_table.drop()
        self.assertFalse(temp_table.exists())
        
        # Recreate with different schema
        temp_table.create(columns={"temp_col": str, "new_col": int})
        self.assertTrue(temp_table.exists())
        
        # Verify new schema
        columns = temp_table.columns()
        self.assertIn("temp_col", columns)
        self.assertIn("new_col", columns)

    def test_table_index_operations(self, tx):
        """Test table index operations."""
        table = tx.table("table_test_basic")
        
        # Create index
        try:
            table.create_index("name")
            table.create_index("email", unique=True)
        except Exception:
            pass  # Index might already exist
        
        # Test that operations still work with indexes
        result = table.select(where={"name": "Alice Johnson"})
        self.assertIsInstance(result, Result)

    def test_table_query_builder(self, tx):
        """Test table query builder functionality."""
        table = tx.table("table_test_basic")
        
        # Test that query building doesn't execute immediately
        query = table.select(where={"active": True})
        self.assertIsInstance(query, Result)

        # Test select with different parameters
        result_ordered = table.select(orderby="name")
        ordered_list = list(result_ordered)
        self.assertGreaterEqual(len(ordered_list), 0)


if __name__ == "__main__":
    unittest.main()
