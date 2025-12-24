#!/usr/bin/env python3
"""
Test cases for WHERE clause validation improvements.
Tests the fixes for the PostgreSQL 'argument of WHERE must be type boolean' error.
"""

import unittest
from unittest.mock import Mock, MagicMock
from velocity.db.servers.postgres.sql import SQL
from velocity.db import exceptions


class TestWhereClauseValidation(unittest.TestCase):
    """Test WHERE clause validation improvements."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_tx = Mock()
        self.mock_tx.table.return_value.primary_keys.return_value = ['sys_id']
        
        # Mock TableHelper methods
        self.mock_helper = Mock()
        self.mock_helper.resolve_references.return_value = "test_column"
        self.mock_helper.make_predicate.return_value = ("test_column = %s", 123)
        self.mock_helper.get_table_alias.return_value = "t1"
        self.mock_helper.foreign_keys = {}
        self.mock_helper.split_columns.return_value = ["column1", "column2"]

    def test_invalid_where_bare_integer(self):
        """Test that bare integers in WHERE clauses are rejected with helpful error."""
        with self.assertRaises(ValueError) as cm:
            SQL.select(self.mock_tx, table="test_table", where=1001)
        
        error_msg = str(cm.exception)
        self.assertIn("Invalid WHERE clause: 1001", error_msg)
        self.assertIn("Primitive values cannot be WHERE clauses directly", error_msg)
        self.assertIn("{'sys_id': 1001}", error_msg)
        self.assertIn("PostgreSQL 'argument of WHERE must be type boolean' errors", error_msg)

    def test_invalid_where_string_integer(self):
        """Test that string integers in WHERE clauses are rejected."""
        with self.assertRaises(ValueError) as cm:
            SQL.select(self.mock_tx, table="test_table", where="1001")
        
        error_msg = str(cm.exception)
        self.assertIn("Invalid WHERE clause: '1001'", error_msg)
        self.assertIn("Bare integers are not valid WHERE clauses", error_msg)
        self.assertIn("sys_id = 1001", error_msg)

    def test_invalid_where_boolean_literal(self):
        """Test that boolean literals in WHERE clauses are rejected."""
        test_cases = ["True", "False", "1", "0"]
        
        for bool_val in test_cases:
            with self.subTest(bool_val=bool_val):
                with self.assertRaises(ValueError) as cm:
                    SQL.select(self.mock_tx, table="test_table", where=bool_val)
                
                error_msg = str(cm.exception)
                self.assertIn(f"Invalid WHERE clause: '{bool_val}'", error_msg)
                self.assertIn("Boolean literals alone are not valid WHERE clauses", error_msg)

    def test_invalid_where_empty_string(self):
        """Test that empty string WHERE clauses are rejected."""
        with self.assertRaises(ValueError) as cm:
            SQL.select(self.mock_tx, table="test_table", where="   ")
        
        error_msg = str(cm.exception)
        self.assertIn("WHERE clause cannot be empty string", error_msg)

    def test_invalid_where_float(self):
        """Test that float values in WHERE clauses are rejected."""
        with self.assertRaises(ValueError) as cm:
            SQL.select(self.mock_tx, table="test_table", where=123.45)
        
        error_msg = str(cm.exception)
        self.assertIn("Invalid WHERE clause: 123.45", error_msg)
        self.assertIn("type: float", error_msg)

    def test_invalid_where_boolean(self):
        """Test that boolean values in WHERE clauses are rejected."""
        with self.assertRaises(ValueError) as cm:
            SQL.select(self.mock_tx, table="test_table", where=True)
        
        error_msg = str(cm.exception)
        self.assertIn("Invalid WHERE clause: True", error_msg)
        self.assertIn("type: bool", error_msg)

    def test_valid_where_dictionary(self):
        """Test that dictionary WHERE clauses work correctly."""
        try:
            sql, params = SQL.select(
                self.mock_tx, 
                table="test_table", 
                where={"sys_id": 1001}
            )
            # Should not raise an exception
            self.assertIsInstance(sql, str)
            self.assertIsInstance(params, tuple)
        except ValueError as e:
            self.fail(f"Valid dictionary WHERE clause raised ValueError: {e}")

    def test_valid_where_complete_sql_string(self):
        """Test that complete SQL string WHERE clauses work correctly."""
        try:
            sql, params = SQL.select(
                self.mock_tx, 
                table="test_table", 
                where="sys_id = 1001 AND sys_active = true"
            )
            # Should not raise an exception
            self.assertIsInstance(sql, str)
            self.assertIsInstance(params, tuple)
        except ValueError as e:
            self.fail(f"Valid SQL string WHERE clause raised ValueError: {e}")

    def test_update_where_validation(self):
        """Test that UPDATE method has the same WHERE validation."""
        with self.assertRaises(ValueError) as cm:
            SQL.update(
                self.mock_tx, 
                table="test_table", 
                data={"name": "test"}, 
                where=1001
            )
        
        error_msg = str(cm.exception)
        self.assertIn("Invalid WHERE clause: 1001", error_msg)
        self.assertIn("PostgreSQL 'argument of WHERE must be type boolean' errors", error_msg)

    def test_update_where_string_integer(self):
        """Test UPDATE method rejects string integers."""
        with self.assertRaises(ValueError) as cm:
            SQL.update(
                self.mock_tx, 
                table="test_table", 
                data={"name": "test"}, 
                where="999"
            )
        
        error_msg = str(cm.exception)
        self.assertIn("Invalid WHERE clause: '999'", error_msg)
        self.assertIn("Bare integers are not valid WHERE clauses", error_msg)


class TestEnhancedErrorMessages(unittest.TestCase):
    """Test enhanced error message functionality."""

    def test_datatype_mismatch_error_enhancement(self):
        """Test that datatype mismatch errors get enhanced messages."""
        from velocity.db.core.engine import Engine
        
        # Create a mock exception that simulates the PostgreSQL error
        mock_exception = Exception("argument of WHERE must be type boolean, not type integer")
        
        # Create an engine instance with mocked dependencies
        mock_driver = Mock()
        mock_config = Mock()
        mock_sql = Mock()
        # Set up the error code to trigger ApplicationError path
        mock_sql.get_error.return_value = ("42804", "datatype mismatch")
        mock_sql.ApplicationErrorCodes = ["42804"]
        # Add all the other error code lists that the engine checks
        mock_sql.ColumnMissingErrorCodes = []
        mock_sql.TableMissingErrorCodes = []
        mock_sql.DatabaseMissingErrorCodes = []
        mock_sql.ForeignKeyMissingErrorCodes = []
        mock_sql.TruncationErrorCodes = []
        mock_sql.DataIntegrityErrorCodes = []
        mock_sql.ConnectionErrorCodes = []
        mock_sql.DuplicateKeyErrorCodes = []
        mock_sql.DatabaseObjectExistsErrorCodes = []
        mock_sql.LockTimeoutErrorCodes = []
        mock_sql.RetryTransactionCodes = []
        
        engine = Engine(mock_driver, mock_config, mock_sql)
        
        # Mock the _format_sql_with_params method
        engine._format_sql_with_params = Mock(return_value="SELECT * FROM test WHERE 1001")
        
        # Test that the error gets enhanced
        with self.assertRaises(exceptions.DbApplicationError) as cm:
            engine.process_error(mock_exception, "SELECT * FROM test WHERE 1001", [])
        
        error_msg = str(cm.exception)
        # Verify the enhanced error message contains our WHERE clause help
        self.assertIn("*** WHERE CLAUSE ERROR ***", error_msg)
        self.assertIn("WHERE 1001 to WHERE sys_id = 1001", error_msg)
        self.assertIn("SQL Query:", error_msg)
        self.assertIn("Call Context:", error_msg)


if __name__ == '__main__':
    unittest.main()