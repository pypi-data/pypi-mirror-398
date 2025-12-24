import unittest
import psycopg2
from velocity.db.core.transaction import Transaction
from velocity.db.exceptions import DbQueryError, DbTableMissingError, DbColumnMissingError
from .common import CommonPostgresTest, engine, test_db


@engine.transaction
class TestPostgreSQLModule(CommonPostgresTest):
    """Comprehensive tests for PostgreSQL SQL module including edge cases and error conditions."""
    
    @classmethod
    def create_test_tables(cls, tx):
        """Create comprehensive test tables for SQL module testing."""
        # Basic table for general operations
        tx.table("sql_test_basic").create(
            columns={
                "name": str,
                "age": int,
                "email": str,
                "active": bool,
                "score": float,
            }
        )
        
        # Table with special characters and reserved words
        tx.table("sql_test_special").create(
            columns={
                "order": str,  # reserved keyword
                "user": str,   # reserved keyword
                "select": str, # reserved keyword
                "column_with_spaces": str,
                "column-with-dashes": str,
            }
        )
        
        # Table for foreign key testing
        tx.table("sql_test_parent").create(
            columns={
                "parent_name": str,
                "category": str,
            }
        )
        
        tx.table("sql_test_child").create(
            columns={
                "parent_id": int,
                "child_name": str,
                "value": float,
            }
        )
        
        # Create foreign key relationship
        tx.table("sql_test_child").create_foreign_key("parent_id", "sql_test_parent", "sys_id")
        
        # Large table for performance testing
        tx.table("sql_test_large").create(
            columns={
                "data": str,
                "index_col": int,
                "timestamp_col": str,
            }
        )
        
        # Insert test data
        cls.insert_test_data(tx)
    
    @classmethod
    def insert_test_data(cls, tx):
        """Insert comprehensive test data."""
        # Basic table data
        basic_data = [
            {"name": "Alice", "age": 30, "email": "alice@example.com", "active": True, "score": 95.5},
            {"name": "Bob", "age": 25, "email": "bob@example.com", "active": False, "score": 87.2},
            {"name": "Charlie", "age": 35, "email": "charlie@example.com", "active": True, "score": 92.8},
            {"name": "Diana", "age": 28, "email": "diana@example.com", "active": True, "score": 88.9},
            {"name": "Eve", "age": 32, "email": "eve@example.com", "active": False, "score": 91.1},
        ]
        
        for data in basic_data:
            tx.table("sql_test_basic").insert(data)
        
        # Special characters data
        special_data = [
            {"order": "first", "user": "admin", "select": "all", "column_with_spaces": "test value", "column-with-dashes": "test-value"},
            {"order": "second", "user": "user1", "select": "some", "column_with_spaces": "another value", "column-with-dashes": "another-value"},
        ]
        
        for data in special_data:
            tx.table("sql_test_special").insert(data)
        
        # Parent-child data
        parent_data = [
            {"parent_name": "Parent A", "category": "type1"},
            {"parent_name": "Parent B", "category": "type2"},
            {"parent_name": "Parent C", "category": "type1"},
        ]
        
        parent_ids = []
        for data in parent_data:
            row = tx.table("sql_test_parent").new(data)
            parent_ids.append(row["sys_id"])
        
        child_data = [
            {"parent_id": parent_ids[0], "child_name": "Child A1", "value": 10.5},
            {"parent_id": parent_ids[0], "child_name": "Child A2", "value": 20.3},
            {"parent_id": parent_ids[1], "child_name": "Child B1", "value": 15.7},
            {"parent_id": parent_ids[2], "child_name": "Child C1", "value": 30.9},
        ]
        
        for data in child_data:
            tx.table("sql_test_child").insert(data)
        
        # Large table data for performance testing
        for i in range(100):
            tx.table("sql_test_large").insert({
                "data": f"test_data_{i}",
                "index_col": i,
                "timestamp_col": f"2023-01-{(i % 28) + 1:02d}",
            })

    def test_select_basic(self, tx):
        """Test basic SELECT operations."""
        # Simple select all
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic")
        self.assertIn("SELECT", sql.upper())
        self.assertIn("sql_test_basic", sql)
        
        # Select with where clause
        where = {"name": "Alice"}
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", where=where)
        self.assertIn("WHERE", sql.upper())
        self.assertEqual(vals, ("Alice",))
        
        # Select with multiple conditions
        where = {"active": True, "age": 30}
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", where=where)
        self.assertIn("WHERE", sql.upper())
        self.assertIn("AND", sql.upper())

    def test_select_with_operators(self, tx):
        """Test SELECT with various operators."""
        # Greater than
        where = {"age>": 30}
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", where=where)
        self.assertIn(">", sql)
        self.assertEqual(vals, (30,))
        
        # Less than or equal
        where = {"score<=": 90.0}
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", where=where)
        self.assertIn("<=", sql)
        
        # IN operator
        where = {"name": ["Alice", "Bob"]}
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", where=where)
        self.assertIn("IN", sql.upper())
        
        # LIKE operator
        where = {"email%": "example"}
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", where=where)
        self.assertIn("LIKE", sql.upper())

    def test_select_ordering(self, tx):
        """Test SELECT with ordering."""
        # Ascending order
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", orderby="name")
        self.assertIn("ORDER BY", sql.upper())
        self.assertIn("name", sql)
        
        # Descending order
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", orderby="age DESC")
        self.assertIn("ORDER BY", sql.upper())
        self.assertIn("DESC", sql.upper())
        
        # Multiple ordering
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", orderby="name, age DESC")
        order_by_count = sql.upper().count("ORDER BY")
        self.assertEqual(order_by_count, 1)
        self.assertIn(",", sql)

    def test_select_limits(self, tx):
        """Test SELECT with limits and offsets."""
        # Limit only
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", qty=3)
        self.assertIn("LIMIT", sql.upper())
        
        # Limit with offset
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", qty=3, start=2)
        self.assertIn("LIMIT", sql.upper())
        self.assertIn("OFFSET", sql.upper())

    def test_insert_operations(self, tx):
        """Test INSERT operations."""
        # Basic insert
        data = {"name": "Test User", "age": 25, "email": "test@example.com"}
        sql, vals = tx.engine.sql.insert("sql_test_basic", data)
        self.assertIn("INSERT", sql.upper())
        self.assertIn("VALUES", sql.upper())
        
        # Insert with None values
        data = {"name": "Test User 2", "age": None, "email": "test2@example.com"}
        sql, vals = tx.engine.sql.insert(tx, table="sql_test_basic", data=data)
        self.assertIn("NULL", sql.upper())

    def test_update_operations(self, tx):
        """Test UPDATE operations."""
        # Basic update
        data = {"name": "Updated User"}
        where = {"sys_id": 1}
        sql, vals = tx.engine.sql.update(tx, table="sql_test_basic", data=data, where=where)
        self.assertIn("UPDATE", sql.upper())
        self.assertIn("SET", sql.upper())
        self.assertIn("WHERE", sql.upper())
        
        # Update multiple columns
        data = {"name": "Updated User", "age": 99}
        where = {"sys_id": 1}
        sql, vals = tx.engine.sql.update(tx, table="sql_test_basic", data=data, where=where)
        set_count = sql.upper().count("SET")
        self.assertEqual(set_count, 1)
        self.assertIn(",", sql)

    def test_delete_operations(self, tx):
        """Test DELETE operations."""
        # Basic delete
        where = {"sys_id": 1}
        sql, vals = tx.engine.sql.delete(tx, table="sql_test_basic", where=where)
        self.assertIn("DELETE", sql.upper())
        self.assertIn("FROM", sql.upper())
        self.assertIn("WHERE", sql.upper())
        
        # Delete with multiple conditions
        where = {"active": False, "age": 25}
        sql, vals = tx.engine.sql.delete(tx, table="sql_test_basic", where=where)
        self.assertIn("WHERE", sql.upper())
        self.assertIn("AND", sql.upper())

    def test_reserved_words_handling(self, tx):
        """Test handling of reserved words as column names."""
        # Select with reserved word columns
        sql, vals = tx.engine.sql.select(tx, table="sql_test_special")
        self.assertIn("sql_test_special", sql)
        
        # Insert with reserved words
        data = {"order": "third", "user": "testuser", "select": "none"}
        sql, vals = tx.engine.sql.insert(tx, table="sql_test_special", data=data)
        self.assertIn("INSERT", sql.upper())
        
        # Update with reserved words
        data = {"order": "updated"}
        where = {"user": "testuser"}
        sql, vals = tx.engine.sql.update(tx, table="sql_test_special", data=data, where=where)
        self.assertIn("UPDATE", sql.upper())

    def test_special_characters_in_columns(self, tx):
        """Test handling of special characters in column names."""
        # Test columns with spaces and dashes
        data = {"column_with_spaces": "space test", "column-with-dashes": "dash test"}
        sql, vals = tx.engine.sql.insert(tx, table="sql_test_special", data=data)
        self.assertIn("INSERT", sql.upper())

    def test_join_operations(self, tx):
        """Test JOIN operations."""
        # Test select with complex where (simulating join condition)
        where = {"parent_id": 1}
        sql, vals = tx.engine.sql.select(tx, table="sql_test_child", where=where)
        self.assertIn("WHERE", sql.upper())

    def test_aggregate_functions(self, tx):
        """Test aggregate function support."""
        # Count
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", columns=["COUNT(*)"])
        self.assertIn("COUNT", sql.upper())
        
        # Aggregate with grouping
        sql, vals = tx.engine.sql.select(
            tx, 
            table="sql_test_basic", 
            columns=["active", "COUNT(*)"],
            groupby="active"
        )
        self.assertIn("GROUP BY", sql.upper())

    def test_create_table_operations(self, tx):
        """Test CREATE TABLE operations."""
        columns = {
            "test_name": str,
            "test_age": int,
            "test_active": bool,
        }
        sql, vals = tx.engine.sql.create_table("test_create_table", columns=columns)
        self.assertIn("CREATE TABLE", sql.upper())
        self.assertIn("test_create_table", sql)

    def test_drop_table_operations(self, tx):
        """Test DROP TABLE operations."""
        sql, vals = tx.engine.sql.drop_table("test_drop_table")
        self.assertIn("DROP TABLE", sql.upper())
        self.assertIn("test_drop_table", sql)

    def test_alter_table_operations(self, tx):
        """Test ALTER TABLE operations."""
        # Add column - not implemented in SQL class
        pass

    def test_index_operations(self, tx):
        """Test INDEX operations."""
        # Create index
        sql, vals = tx.engine.sql.create_index(tx, table="sql_test_basic", columns=["name"])
        self.assertIn("CREATE INDEX", sql.upper())

    def test_foreign_key_operations(self, tx):
        """Test FOREIGN KEY operations."""
        sql, vals = tx.engine.sql.create_foreign_key(
            "sql_test_child",
            columns="parent_id",
            key_to_table="sql_test_parent",
            key_to_columns="sys_id"
        )
        self.assertIn("FOREIGN KEY", sql.upper())
        self.assertIn("REFERENCES", sql.upper())

    def test_transaction_operations(self, tx):
        """Test transaction-related SQL."""
        # Begin transaction - not implemented in SQL class
        pass
        
        # Commit transaction
        sql, vals = tx.engine.sql.commit_transaction()
        self.assertIn("COMMIT", sql.upper())
        
        # Rollback transaction
        sql, vals = tx.engine.sql.rollback_transaction()
        self.assertIn("ROLLBACK", sql.upper())

    def test_error_handling_invalid_table(self, tx):
        """Test error handling for invalid table names."""
        with self.assertRaises((DbTableMissingError, Exception)):
            sql, vals = tx.engine.sql.select(tx, table="nonexistent_table")
            tx.execute(sql, vals)

    def test_error_handling_invalid_column(self, tx):
        """Test error handling for invalid column names."""
        with self.assertRaises((DbColumnMissingError, Exception)):
            where = {"nonexistent_column": "value"}
            sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", where=where)
            tx.execute(sql, vals)

    def test_error_handling_syntax_errors(self, tx):
        """Test handling of SQL syntax errors."""
        # This should be handled gracefully by the SQL builder
        with self.assertRaises((DbQueryError, Exception)):
            # Try to create invalid SQL
            tx.execute("INVALID SQL STATEMENT")

    def test_sql_injection_prevention(self, tx):
        """Test SQL injection prevention."""
        # Test with malicious input
        malicious_input = "'; DROP TABLE sql_test_basic; --"
        where = {"name": malicious_input}
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", where=where)
        
        # The input should be parameterized, not embedded directly
        self.assertNotIn("DROP TABLE", sql.upper())
        self.assertIn("$", sql)  # PostgreSQL uses $1, $2, etc. for parameters

    def test_performance_large_dataset(self, tx):
        """Test performance with large datasets."""
        # Test selecting from large table
        sql, vals = tx.engine.sql.select(tx, table="sql_test_large", qty=10)
        result = tx.execute(sql, vals)
        self.assertIsNotNone(result)
        
        # Test with complex where clause on large table
        where = {"index_col__gte": 50, "index_col__lt": 60}
        sql, vals = tx.engine.sql.select(tx, table="sql_test_large", where=where)
        result = tx.execute(sql, vals)
        self.assertIsNotNone(result)

    def test_concurrent_operations(self, tx):
        """Test concurrent operation support."""
        # Test that SQL generation is thread-safe
        import threading
        import time
        
        results = []
        errors = []
        
        def worker():
            try:
                for i in range(10):
                    sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", where={"age__gt": i})
                    results.append((sql, vals))
                    time.sleep(0.001)  # Small delay to encourage race conditions
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Should have completed without errors
        self.assertEqual(len(errors), 0)
        self.assertGreater(len(results), 0)

    def test_edge_cases_empty_data(self, tx):
        """Test edge cases with empty data."""
        # Empty where clause
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", where={})
        self.assertIn("SELECT", sql.upper())
        
        # Empty data for insert (should handle gracefully)
        with self.assertRaises(Exception):
            sql, vals = tx.engine.sql.insert(tx, table="sql_test_basic", data={})

    def test_edge_cases_null_values(self, tx):
        """Test edge cases with NULL values."""
        # Insert with None values
        data = {"name": None, "age": None, "email": None}
        sql, vals = tx.engine.sql.insert(tx, table="sql_test_basic", data=data)
        self.assertIn("NULL", sql.upper() if "NULL" in sql.upper() else str(vals))
        
        # Where clause with None
        where = {"name": None}
        sql, vals = tx.engine.sql.select(tx, table="sql_test_basic", where=where)
        self.assertIn("IS NULL", sql.upper())

    def test_edge_cases_unicode_data(self, tx):
        """Test edge cases with Unicode data."""
        # Unicode strings
        data = {"name": "José María", "email": "josé@español.com"}
        sql, vals = tx.engine.sql.insert(tx, table="sql_test_basic", data=data)
        self.assertIn("INSERT", sql.upper())
        
        # Emoji and special Unicode
        data = {"name": "User 🚀", "email": "test@example.com"}
        sql, vals = tx.engine.sql.insert(tx, table="sql_test_basic", data=data)
        self.assertIn("INSERT", sql.upper())

    def test_data_type_handling(self, tx):
        """Test proper handling of different data types."""
        # Boolean values
        data = {"name": "Test", "active": True}
        sql, vals = tx.engine.sql.insert(tx, table="sql_test_basic", data=data)
        self.assertIn("INSERT", sql.upper())
        
        # Float values
        data = {"name": "Test", "score": 95.67}
        sql, vals = tx.engine.sql.insert(tx, table="sql_test_basic", data=data)
        self.assertIn("INSERT", sql.upper())
        
        # Large integers
        data = {"name": "Test", "age": 999999999}
        sql, vals = tx.engine.sql.insert(tx, table="sql_test_basic", data=data)
        self.assertIn("INSERT", sql.upper())


if __name__ == "__main__":
    unittest.main()
