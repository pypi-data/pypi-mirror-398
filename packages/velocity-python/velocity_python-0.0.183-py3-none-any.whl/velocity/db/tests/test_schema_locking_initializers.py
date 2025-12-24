#!/usr/bin/env python3
"""
Test schema locking support in all database initializers.
"""

import unittest
import os
from unittest.mock import patch, MagicMock

from velocity.db.servers.mysql import MySQLInitializer
from velocity.db.servers.sqlite import SQLiteInitializer  
from velocity.db.servers.sqlserver import SQLServerInitializer
from velocity.db.servers.postgres import PostgreSQLInitializer


class TestSchemaLockingInitializers(unittest.TestCase):
    """Test that all database initializers support schema locking parameters."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock the database drivers
        self.mock_mysql = MagicMock()
        self.mock_sqlite = MagicMock()
        self.mock_pytds = MagicMock()
        self.mock_psycopg2 = MagicMock()
        
    @patch('mysql.connector')
    def test_mysql_schema_locked_parameter(self, mock_mysql_connector):
        """Test MySQL initializer accepts schema_locked parameter."""
        mock_mysql_connector.return_value = self.mock_mysql
        
        config = {
            "database": "test_db",
            "host": "localhost", 
            "user": "test_user",
            "password": "test_pass"
        }
        
        # Test with schema_locked=True
        engine = MySQLInitializer.initialize(config, schema_locked=True)
        self.assertTrue(engine.schema_locked)
        
        # Test with schema_locked=False (default)
        engine = MySQLInitializer.initialize(config, schema_locked=False)
        self.assertFalse(engine.schema_locked)
        
        # Test default behavior
        engine = MySQLInitializer.initialize(config)
        self.assertFalse(engine.schema_locked)

    def test_sqlite_schema_locked_parameter(self):
        """Test SQLite initializer accepts schema_locked parameter."""
        config = {"database": ":memory:"}
        
        # Test with schema_locked=True
        engine = SQLiteInitializer.initialize(config, schema_locked=True)
        self.assertTrue(engine.schema_locked)
        
        # Test with schema_locked=False (default)
        engine = SQLiteInitializer.initialize(config, schema_locked=False)
        self.assertFalse(engine.schema_locked)
        
        # Test default behavior
        engine = SQLiteInitializer.initialize(config)
        self.assertFalse(engine.schema_locked)

    @patch('pytds')
    def test_sqlserver_schema_locked_parameter(self, mock_pytds):
        """Test SQL Server initializer accepts schema_locked parameter."""
        mock_pytds.return_value = self.mock_pytds
        
        config = {
            "database": "test_db",
            "server": "localhost",
            "user": "test_user", 
            "password": "test_pass"
        }
        
        # Test with schema_locked=True
        engine = SQLServerInitializer.initialize(config, schema_locked=True)
        self.assertTrue(engine.schema_locked)
        
        # Test with schema_locked=False (default)
        engine = SQLServerInitializer.initialize(config, schema_locked=False)
        self.assertFalse(engine.schema_locked)
        
        # Test default behavior
        engine = SQLServerInitializer.initialize(config)
        self.assertFalse(engine.schema_locked)

    @patch('psycopg2')
    def test_postgres_schema_locked_parameter(self, mock_psycopg2):
        """Test PostgreSQL initializer accepts schema_locked parameter."""
        mock_psycopg2.return_value = self.mock_psycopg2
        
        config = {
            "database": "test_db",
            "host": "localhost",
            "user": "test_user", 
            "password": "test_pass"
        }
        
        # Test with schema_locked=True
        engine = PostgreSQLInitializer.initialize(config, schema_locked=True)
        self.assertTrue(engine.schema_locked)
        
        # Test with schema_locked=False (default)
        engine = PostgreSQLInitializer.initialize(config, schema_locked=False)
        self.assertFalse(engine.schema_locked)
        
        # Test default behavior
        engine = PostgreSQLInitializer.initialize(config)
        self.assertFalse(engine.schema_locked)

    @patch.dict(os.environ, {"VELOCITY_SCHEMA_LOCKED": "true"})
    @patch('mysql.connector')
    def test_mysql_environment_variable_override(self, mock_mysql_connector):
        """Test MySQL respects VELOCITY_SCHEMA_LOCKED environment variable."""
        mock_mysql_connector.return_value = self.mock_mysql
        
        config = {
            "database": "test_db",
            "host": "localhost",
            "user": "test_user",
            "password": "test_pass"
        }
        
        # Environment variable should override default
        engine = MySQLInitializer.initialize(config)
        self.assertTrue(engine.schema_locked)
        
        # Environment variable should override explicit False
        engine = MySQLInitializer.initialize(config, schema_locked=False)
        self.assertTrue(engine.schema_locked)

    @patch.dict(os.environ, {"VELOCITY_SCHEMA_LOCKED": "true"})
    def test_sqlite_environment_variable_override(self):
        """Test SQLite respects VELOCITY_SCHEMA_LOCKED environment variable."""
        config = {"database": ":memory:"}
        
        # Environment variable should override default
        engine = SQLiteInitializer.initialize(config)
        self.assertTrue(engine.schema_locked)
        
        # Environment variable should override explicit False
        engine = SQLiteInitializer.initialize(config, schema_locked=False)
        self.assertTrue(engine.schema_locked)

    @patch.dict(os.environ, {"VELOCITY_SCHEMA_LOCKED": "true"})
    @patch('pytds')
    def test_sqlserver_environment_variable_override(self, mock_pytds):
        """Test SQL Server respects VELOCITY_SCHEMA_LOCKED environment variable."""
        mock_pytds.return_value = self.mock_pytds
        
        config = {
            "database": "test_db",
            "server": "localhost",
            "user": "test_user",
            "password": "test_pass"
        }
        
        # Environment variable should override default
        engine = SQLServerInitializer.initialize(config)
        self.assertTrue(engine.schema_locked)
        
        # Environment variable should override explicit False
        engine = SQLServerInitializer.initialize(config, schema_locked=False)
        self.assertTrue(engine.schema_locked)

    @patch.dict(os.environ, {"VELOCITY_SCHEMA_LOCKED": "true"})
    @patch('psycopg2')
    def test_postgres_environment_variable_override(self, mock_psycopg2):
        """Test PostgreSQL respects VELOCITY_SCHEMA_LOCKED environment variable."""
        mock_psycopg2.return_value = self.mock_psycopg2
        
        config = {
            "database": "test_db",
            "host": "localhost",
            "user": "test_user",
            "password": "test_pass"
        }
        
        # Environment variable should override default
        engine = PostgreSQLInitializer.initialize(config)
        self.assertTrue(engine.schema_locked)
        
        # Environment variable should override explicit False
        engine = PostgreSQLInitializer.initialize(config, schema_locked=False)
        self.assertTrue(engine.schema_locked)

    @patch.dict(os.environ, {"VELOCITY_SCHEMA_LOCKED": "1"})
    @patch('mysql.connector')
    def test_environment_variable_various_true_values(self, mock_mysql_connector):
        """Test that various 'true' values in environment variable work."""
        mock_mysql_connector.return_value = self.mock_mysql
        
        config = {
            "database": "test_db",
            "host": "localhost",
            "user": "test_user",
            "password": "test_pass"
        }
        
        # Test "1"
        with patch.dict(os.environ, {"VELOCITY_SCHEMA_LOCKED": "1"}):
            engine = MySQLInitializer.initialize(config)
            self.assertTrue(engine.schema_locked)
        
        # Test "yes"
        with patch.dict(os.environ, {"VELOCITY_SCHEMA_LOCKED": "yes"}):
            engine = MySQLInitializer.initialize(config)
            self.assertTrue(engine.schema_locked)
        
        # Test "TRUE" (case insensitive)
        with patch.dict(os.environ, {"VELOCITY_SCHEMA_LOCKED": "TRUE"}):
            engine = MySQLInitializer.initialize(config)
            self.assertTrue(engine.schema_locked)
        
        # Test "false" (should not lock)
        with patch.dict(os.environ, {"VELOCITY_SCHEMA_LOCKED": "false"}):
            engine = MySQLInitializer.initialize(config)
            self.assertFalse(engine.schema_locked)


if __name__ == "__main__":
    unittest.main()
