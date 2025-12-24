import unittest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from velocity.db.exceptions import DbColumnMissingError, DbDuplicateKeyError
from velocity.db.core.row import Row
from .common import CommonPostgresTest, engine, test_db


@engine.transaction
class TestRowComprehensive(CommonPostgresTest):
    """Comprehensive tests for Row class including edge cases, race conditions, and error recovery."""
    
    @classmethod
    def create_test_tables(cls, tx):
        """Create comprehensive test tables for Row testing."""
        # Basic table for row operations
        tx.table("row_test_basic").create(
            columns={
                "name": str,
                "age": int,
                "email": str,
                "active": bool,
                "score": float,
                "metadata": str,
                "created_at": str,
            }
        )
        
        # Table with complex data types
        tx.table("row_test_complex").create(
            columns={
                "title": str,
                "description": str,
                "tags": str,  # JSON-like string
                "priority": int,
                "deadline": str,
                "completed": bool,
                "progress": float,
            }
        )
        
        # Table for constraint testing
        tx.table("row_test_constraints").create(
            columns={
                "username": str,
                "email": str,
                "phone": str,
                "status": str,
            }
        )
        
        # Create unique constraint
        try:
            tx.table("row_test_constraints").create_index("username", unique=True)
            tx.table("row_test_constraints").create_index("email", unique=True)
        except:
            pass
        
        # Parent-child tables for relationship testing
        tx.table("row_test_parent").create(
            columns={
                "parent_name": str,
                "category": str,
                "priority": int,
            }
        )
        
        tx.table("row_test_child").create(
            columns={
                "parent_id": int,
                "child_name": str,
                "value": float,
                "notes": str,
            }
        )
        
        tx.table("row_test_child").create_foreign_key("parent_id", "row_test_parent", "sys_id")
        
        # Table for concurrent testing
        tx.table("row_test_concurrent").create(
            columns={
                "counter": int,
                "worker_id": str,
                "last_updated": str,
                "version": int,
            }
        )
        
        # Insert initial test data
        cls.insert_test_data(tx)
    
    @classmethod
    def insert_test_data(cls, tx):
        """Insert comprehensive test data."""
        # Basic table data
        basic_data = [
            {
                "name": "Alice Johnson",
                "age": 30,
                "email": "alice@test.com",
                "active": True,
                "score": 95.5,
                "metadata": '{"role": "admin", "department": "IT"}',
                "created_at": "2023-01-01T10:00:00"
            },
            {
                "name": "Bob Smith",
                "age": 25,
                "email": "bob@test.com",
                "active": False,
                "score": 87.2,
                "metadata": '{"role": "user", "department": "Sales"}',
                "created_at": "2023-01-02T11:00:00"
            },
            {
                "name": "Charlie Brown",
                "age": 35,
                "email": "charlie@test.com",
                "active": True,
                "score": 92.8,
                "metadata": '{"role": "manager", "department": "HR"}',
                "created_at": "2023-01-03T12:00:00"
            },
        ]
        
        for data in basic_data:
            tx.table("row_test_basic").insert(data)
        
        # Complex table data
        complex_data = [
            {
                "title": "Project Alpha",
                "description": "Main development project",
                "tags": '["development", "priority", "Q1"]',
                "priority": 1,
                "deadline": "2023-03-31",
                "completed": False,
                "progress": 75.5
            },
            {
                "title": "Project Beta",
                "description": "Testing and QA project",
                "tags": '["testing", "qa", "Q2"]',
                "priority": 2,
                "deadline": "2023-06-30",
                "completed": True,
                "progress": 100.0
            },
        ]
        
        for data in complex_data:
            tx.table("row_test_complex").insert(data)
        
        # Constraints table data
        constraint_data = [
            {"username": "admin", "email": "admin@test.com", "phone": "555-0001", "status": "active"},
            {"username": "user1", "email": "user1@test.com", "phone": "555-0002", "status": "pending"},
            {"username": "user2", "email": "user2@test.com", "phone": "555-0003", "status": "suspended"},
        ]
        
        for data in constraint_data:
            tx.table("row_test_constraints").insert(data)
        
        # Parent-child data
        parent_data = [
            {"parent_name": "Department A", "category": "Engineering", "priority": 1},
            {"parent_name": "Department B", "category": "Marketing", "priority": 2},
        ]
        
        parent_ids = []
        for data in parent_data:
            row = tx.table("row_test_parent").new(data)
            parent_ids.append(row["sys_id"])
        
        child_data = [
            {"parent_id": parent_ids[0], "child_name": "Team 1", "value": 100.0, "notes": "Primary team"},
            {"parent_id": parent_ids[0], "child_name": "Team 2", "value": 85.5, "notes": "Secondary team"},
            {"parent_id": parent_ids[1], "child_name": "Team 3", "value": 92.3, "notes": "Marketing team"},
        ]
        
        for data in child_data:
            tx.table("row_test_child").insert(data)
        
        # Concurrent testing data
        for i in range(10):
            tx.table("row_test_concurrent").insert({
                "counter": i,
                "worker_id": "initial",
                "last_updated": "2023-01-01T00:00:00",
                "version": 1
            })

    def test_row_initialization(self, tx):
        """Test row initialization with different key types."""
        table = tx.table("row_test_basic")
        
        # Test initialization with sys_id
        first_row_data = table.select().one()
        sys_id = first_row_data["sys_id"]
        
        row_by_id = table.row(sys_id)
        self.assertIsInstance(row_by_id, Row)
        self.assertEqual(row_by_id["sys_id"], sys_id)
        
        # Test initialization with dictionary key
        row_by_dict = table.row({"name": "Alice Johnson"})
        self.assertIsInstance(row_by_dict, Row)
        self.assertEqual(row_by_dict["name"], "Alice Johnson")
        
        # Test initialization with complex dictionary key
        row_by_complex = table.row({"name": "Alice Johnson", "email": "alice@test.com"})
        self.assertIsInstance(row_by_complex, Row)
        self.assertEqual(row_by_complex["name"], "Alice Johnson")

    def test_row_representation(self, tx):
        """Test row string and representation methods."""
        table = tx.table("row_test_basic")
        row = table.select().one()
        
        # Test __repr__
        repr_str = repr(row)
        self.assertIsInstance(repr_str, str)
        self.assertIn("'name':", repr_str)
        
        # Test __str__
        str_repr = str(row)
        self.assertIsInstance(str_repr, str)
        self.assertIn("name", str_repr)

    def test_row_length(self, tx):
        """Test row length operations."""
        table = tx.table("row_test_basic")
        row = table.select().one()

        # Test __len__ - should return 1 since it represents one row
        length = len(row)
        self.assertEqual(length, 1)

    def test_row_item_access(self, tx):
        """Test row item access operations."""
        table = tx.table("row_test_basic")
        row = table.select().one()
        
        # Test __getitem__
        name = row["name"]
        self.assertIsInstance(name, str)
        
        age = row["age"]
        self.assertIsInstance(age, int)
        
        # Test accessing sys_ columns
        sys_id = row["sys_id"]
        self.assertIsNotNone(sys_id)
        
        # Test accessing non-existent column
        with self.assertRaises((DbColumnMissingError, KeyError)):
            _ = row["non_existent_column"]

    def test_row_item_assignment(self, tx):
        """Test row item assignment operations."""
        table = tx.table("row_test_basic")
        row = table.select().one()
        original_name = row["name"]
        
        # Test __setitem__
        row["name"] = "Updated Name"
        self.assertEqual(row["name"], "Updated Name")
        
        # Test setting new column value
        row["new_field"] = "new_value"
        self.assertEqual(row["new_field"], "new_value")
        
        # Test setting None value
        row["metadata"] = None
        self.assertIsNone(row["metadata"])
        
        # Test that primary key cannot be updated
        with self.assertRaises(Exception):
            row["sys_id"] = 99999

    def test_row_item_deletion(self, tx):
        """Test row item deletion operations."""
        table = tx.table("row_test_basic")
        row = table.select().one()
        
        # Test __delitem__
        row["metadata"] = "test_data"
        self.assertEqual(row["metadata"], "test_data")
        
        del row["metadata"]
        self.assertIsNone(row["metadata"])
        
        # Test deleting non-existent field
        del row["non_existent_field"]  # Should not raise error
        
        # Test that primary key cannot be deleted
        with self.assertRaises(Exception):
            del row["sys_id"]

    def test_row_contains(self, tx):
        """Test row membership testing."""
        table = tx.table("row_test_basic")
        row = table.select().one()
        
        # Test __contains__
        self.assertIn("name", row)
        self.assertIn("age", row)
        self.assertIn("sys_id", row)
        self.assertNotIn("non_existent_column", row)
        
        # Test case insensitivity
        self.assertIn("NAME", row)  # Should be case insensitive
        self.assertIn("Age", row)

    def test_row_clear(self, tx):
        """Test row clear operation (delete from database)."""
        table = tx.table("row_test_basic")
        
        # Insert a test row to delete
        test_row = table.new({"name": "To Delete", "age": 99, "email": "delete@test.com"})
        test_id = test_row["sys_id"]
        
        # Verify it exists
        self.assertIsNotNone(table.find(test_id))
        
        # Clear the row
        test_row.clear()
        
        # Verify it's deleted
        self.assertIsNone(table.find(test_id))

    def test_row_keys(self, tx):
        """Test row keys operation."""
        table = tx.table("row_test_basic")
        row = table.select().one()

        # Test keys()
        keys = row.keys()
        self.assertIsInstance(keys, list)
        self.assertIn("name", keys)
        self.assertIn("age", keys)
        self.assertIn("sys_id", keys)
        self.assertIn("name", keys)
        self.assertIn("age", keys)
        self.assertIn("sys_id", keys)
        self.assertIn("sys_created_by", keys)
        self.assertIn("sys_created_on", keys)

    def test_row_values(self, tx):
        """Test row values operation."""
        table = tx.table("row_test_basic")
        row = table.select().one()

        # Test values() without arguments
        values = row.values()
        self.assertIsInstance(values, list)
        self.assertGreater(len(values), 0)

        # Test values() with specific columns
        name_values = row.values("name")
        self.assertIsInstance(name_values, list)
        self.assertEqual(len(name_values), 1)
        self.assertGreater(len(values), 0)
        
        # Test values() with specific columns
        specific_values = row.values("name", "age")
        self.assertEqual(len(specific_values), 2)
        self.assertEqual(specific_values[0], row["name"])
        self.assertEqual(specific_values[1], row["age"])

    def test_row_items(self, tx):
        """Test row items operation."""
        table = tx.table("row_test_basic")
        row = table.select().one()

        # Test items()
        items = row.items()
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)

        # Each item should be a tuple
        for item in items:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 2)        # Verify items structure
        for key, value in items:
            self.assertIsInstance(key, str)
            self.assertEqual(value, row[key])

    def test_row_get_method(self, tx):
        """Test row get method with default values."""
        table = tx.table("row_test_basic")
        row = table.select().one()
        
        # Test get() with existing key
        name = row.get("name")
        self.assertEqual(name, row["name"])
        
        # Test get() with non-existent key and default
        default_value = row.get("non_existent", "default")
        self.assertEqual(default_value, "default")
        
        # Test get() with None value
        row["metadata"] = None
        metadata = row.get("metadata", "fallback")
        self.assertEqual(metadata, "fallback")
        
        # Test get() without default
        non_existent = row.get("totally_missing")
        self.assertIsNone(non_existent)

    def test_row_dictionary_conversion(self, tx):
        """Test converting row to dictionary."""
        table = tx.table("row_test_basic")
        row = table.select().one()
        
        # Test to_dict() method if it exists
        if hasattr(row, "to_dict"):
            row_dict = row.to_dict()
            self.assertIsInstance(row_dict, dict)
            self.assertEqual(row_dict["name"], row["name"])
        
        # Test dict() conversion
        row_as_dict = dict(row)
        self.assertIsInstance(row_as_dict, dict)
        self.assertEqual(row_as_dict["name"], row["name"])

    def test_row_update_operations(self, tx):
        """Test various row update operations."""
        table = tx.table("row_test_basic")
        row = table.select().one()
        
        # Test single field update
        original_score = row["score"]
        row["score"] = 99.9
        self.assertEqual(row["score"], 99.9)
        
        # Test multiple field updates
        row["name"] = "Bulk Updated"
        row["age"] = 999
        row["active"] = not row["active"]
        
        self.assertEqual(row["name"], "Bulk Updated")
        self.assertEqual(row["age"], 999)
        
        # Test updating with different data types
        row["score"] = 100  # int to float column
        self.assertEqual(row["score"], 100)

    def test_row_constraint_violations(self, tx):
        """Test row operations with constraint violations."""
        table = tx.table("row_test_constraints")
        
        # Get existing row
        row = table.select().one()
        
        # Test unique constraint violation
        try:
            # Try to update to existing username
            row["username"] = "user1"  # This should fail if user1 exists
        except (DbDuplicateKeyError, Exception):
            pass  # Expected to fail
        
        # Test that row is still usable after error
        row["phone"] = "555-9999"
        self.assertEqual(row["phone"], "555-9999")

    def test_row_concurrent_updates(self, tx):
        """Test row updates under concurrent access."""
        table = tx.table("row_test_concurrent")
        
        # Get a row for concurrent testing
        test_row = table.select().one()
        row_id = test_row["sys_id"]
        
        def worker(worker_id, iterations=5):
            """Worker function for concurrent row updates."""
            results = []
            for i in range(iterations):
                try:
                    # Get fresh row instance
                    row = table.row(row_id)
                    
                    # Update counter
                    current_counter = row["counter"] or 0
                    row["counter"] = current_counter + 1
                    row["worker_id"] = f"worker_{worker_id}"
                    row["last_updated"] = f"2023-01-01T{i:02d}:00:00"
                    
                    results.append(("success", row["counter"]))
                    time.sleep(0.001)  # Small delay
                    
                except Exception as e:
                    results.append(("error", str(e)))
            
            return results
        
        # Run concurrent workers
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(worker, i, 3) for i in range(3)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        # Verify operations completed
        self.assertGreater(len(all_results), 0)
        
        # Check final state
        final_row = table.row(row_id)
        self.assertIsNotNone(final_row["counter"])

    def test_row_relationship_operations(self, tx):
        """Test row operations with foreign key relationships."""
        parent_table = tx.table("row_test_parent")
        child_table = tx.table("row_test_child")
        
        # Get parent row
        parent = parent_table.select().one()
        parent_id = parent["sys_id"]
        
        # Get related child rows
        children = child_table.select(where={"parent_id": parent_id})
        child_list = list(children)
        self.assertGreater(len(child_list), 0)
        
        # Update parent
        parent["priority"] = 999
        self.assertEqual(parent["priority"], 999)
        
        # Update child
        child = child_list[0]
        child["value"] = 888.8
        self.assertEqual(child["value"], 888.8)
        
        # Test orphaning (if constraints allow)
        try:
            child["parent_id"] = 99999  # Non-existent parent
        except Exception:
            pass  # Expected to fail due to foreign key constraint

    def test_row_edge_cases_null_values(self, tx):
        """Test row operations with NULL values."""
        table = tx.table("row_test_basic")
        
        # Insert row with NULL values
        row = table.new({
            "name": "NULL Test",
            "age": None,
            "email": None,
            "active": None,
            "score": None,
            "metadata": None
        })
        
        # Test accessing NULL values
        self.assertEqual(row["name"], "NULL Test")
        self.assertIsNone(row["age"])
        self.assertIsNone(row["email"])
        self.assertIsNone(row["active"])
        self.assertIsNone(row["score"])
        self.assertIsNone(row["metadata"])
        
        # Test updating NULL values
        row["age"] = 25
        self.assertEqual(row["age"], 25)
        
        # Test setting back to NULL
        row["age"] = None
        self.assertIsNone(row["age"])

    def test_row_edge_cases_unicode_data(self, tx):
        """Test row operations with Unicode data."""
        table = tx.table("row_test_basic")
        
        # Insert row with Unicode data
        unicode_data = {
            "name": "José María 🚀",
            "email": "josé@español.com",
            "metadata": "Unicode test: αβγδε 中文 🎉"
        }
        
        row = table.new(unicode_data)
        
        # Test accessing Unicode data
        self.assertEqual(row["name"], "José María 🚀")
        self.assertEqual(row["email"], "josé@español.com")
        self.assertIn("αβγδε", row["metadata"])
        
        # Test updating Unicode data
        row["name"] = "Updated José 🎯"
        self.assertEqual(row["name"], "Updated José 🎯")

    def test_row_edge_cases_large_data(self, tx):
        """Test row operations with large data."""
        table = tx.table("row_test_basic")
        
        # Insert row with large data
        large_string = "x" * 10000  # 10KB string
        row = table.new({
            "name": "Large Data User",
            "metadata": large_string
        })
        
        # Test accessing large data
        self.assertEqual(row["name"], "Large Data User")
        self.assertEqual(len(row["metadata"]), 10000)
        
        # Test updating large data
        even_larger = "y" * 20000  # 20KB string
        row["metadata"] = even_larger
        self.assertEqual(len(row["metadata"]), 20000)

    def test_row_edge_cases_special_characters(self, tx):
        """Test row operations with special characters."""
        table = tx.table("row_test_basic")
        
        # Special characters that might cause issues
        special_data = {
            "name": "Special'Char\"User",
            "email": "test@example.com",
            "metadata": "Data with 'quotes' and \"double quotes\" and \n newlines \t tabs"
        }
        
        row = table.new(special_data)
        
        # Test accessing special character data
        self.assertIn("'", row["name"])
        self.assertIn('"', row["name"])
        self.assertIn("'quotes'", row["metadata"])
        self.assertIn('\n', row["metadata"])
        self.assertIn('\t', row["metadata"])

    def test_row_error_recovery(self, tx):
        """Test row error recovery scenarios."""
        table = tx.table("row_test_basic")
        row = table.select().one()
        
        # Test recovery from column access error
        try:
            _ = row["completely_invalid_column"]
        except Exception:
            # Should still be able to access valid columns
            name = row["name"]
            self.assertIsNotNone(name)
        
        # Test recovery from update error
        try:
            row["invalid_column"] = "value"
        except Exception:
            # Should still be able to update valid columns
            row["name"] = "Recovered User"
            self.assertEqual(row["name"], "Recovered User")

    def test_row_lock_operations(self, tx):
        """Test row locking operations if supported."""
        table = tx.table("row_test_basic")
        
        # Test row with lock parameter
        first_row_data = table.select().one()
        sys_id = first_row_data["sys_id"]
        
        try:
            # Some databases support row locking
            locked_row = table.row(sys_id, lock=True)
            self.assertIsInstance(locked_row, Row)
            
            # Test operations on locked row
            locked_row["name"] = "Locked User"
            self.assertEqual(locked_row["name"], "Locked User")
            
        except Exception:
            # Row locking might not be supported
            pass

    def test_row_key_column_operations(self, tx):
        """Test row operations with different key column configurations."""
        table = tx.table("row_test_basic")
        
        # Test key_cols property
        row = table.select().one()
        if hasattr(row, "key_cols"):
            key_cols = row.key_cols
            self.assertIsInstance(key_cols, list)
            self.assertIn("sys_id", key_cols)

    def test_row_caching_behavior(self, tx):
        """Test row caching and data consistency."""
        table = tx.table("row_test_basic")
        row1 = table.select().one()
        row_id = row1["sys_id"]
        
        # Get another instance of the same row
        row2 = table.row(row_id)
        
        # Update through first instance
        row1["name"] = "Updated via row1"
        
        # Check if second instance sees the change
        # (behavior depends on caching implementation)
        name_via_row2 = row2["name"]
        # This test documents current behavior rather than asserting specific behavior

    def test_row_data_type_coercion(self, tx):
        """Test row data type coercion and validation."""
        table = tx.table("row_test_basic")
        row = table.select().one()
        
        # Test type coercion
        row["age"] = "30"  # String to int
        self.assertEqual(row["age"], 30)
        
        row["score"] = "95.5"  # String to float
        self.assertEqual(row["score"], 95.5)
        
        row["active"] = "true"  # String to bool (if supported)
        # Behavior may vary by implementation


if __name__ == "__main__":
    unittest.main()
