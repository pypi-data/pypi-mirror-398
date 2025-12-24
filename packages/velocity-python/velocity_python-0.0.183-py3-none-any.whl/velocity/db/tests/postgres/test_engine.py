import os
import datetime
import unittest
from velocity.db.core.engine import Engine
from velocity.db.core.transaction import Transaction
from .common import CommonPostgresTest, engine, test_db


@engine.transaction
class TestEngine(CommonPostgresTest):
    @classmethod
    def create_test_tables(cls, tx):
        """No special tables needed for engine tests."""
        pass

    def test_engine_init(self, tx):
        import psycopg2
        from velocity.db.servers.postgres import SQL
        
        # Test the engine instance from common test
        assert engine.sql == SQL
        assert engine.driver == psycopg2

    def test_engine_attributes(self, tx):
        import psycopg2
        from velocity.db.servers.postgres import SQL
        
        # Test private attributes
        assert engine._Engine__sql == SQL
        assert engine._Engine__driver == psycopg2

    def test_connect(self, tx):
        import psycopg2
        
        assert engine.connect() != None
        conn = engine.connect()
        self.assertIsInstance(conn, psycopg2.extensions.connection)

    def test_other_stuff(self, tx):
        assert engine.version[:10] == "PostgreSQL"

        timestamp = engine.timestamp
        self.assertIsInstance(timestamp, datetime.datetime)
        assert engine.user == os.environ["DBUser"]
        assert test_db in engine.databases
        assert "public" in engine.schemas
        assert "information_schema" in engine.schemas
        assert "public" == engine.current_schema
        assert engine.current_database == test_db
        assert [] == engine.views
        assert [] == engine.tables

    def test_process_error(self, tx):
        local_engine = Engine(None, None, None)  # Replace None with appropriate arguments
        with self.assertRaises(
            Exception
        ):  # Replace Exception with the specific exception raised by process_error
            local_engine.process_error(sql_stmt=None, sql_params=None)
        # Add additional assertions as needed

    def test_transaction_injection_1(self, tx):
        @engine.transaction
        def function():
            pass

        function()

        @engine.transaction
        def function(_tx):
            pass

        with self.assertRaises(NameError):
            function()

        @engine.transaction
        def function(tx):
            pass

        with self.assertRaises(TypeError):
            function(tx=3)
        with self.assertRaises(TypeError):
            function(tx=None)

    def test_transaction_injection_function(self, tx):
        with engine.transaction() as original:

            @engine.transaction
            def function(tx):
                assert tx != None
                assert tx != original
                self.assertIsInstance(tx, Transaction)

            function()

            @engine.transaction
            def function(tx):
                assert tx != None
                assert tx == original
                self.assertIsInstance(tx, Transaction)

            function(original)

            @engine.transaction
            def function(tx=None):
                assert tx != None
                assert tx != original
                self.assertIsInstance(tx, Transaction)

            function()

            @engine.transaction
            def function(tx=None):
                assert tx != None
                assert tx == original
                self.assertIsInstance(tx, Transaction)

            function(original)

            @engine.transaction
            def function(tx=None):
                assert tx != None
                assert tx == original
                self.assertIsInstance(tx, Transaction)

            function(tx=original)

            @engine.transaction
            def function(tx, a, b):
                assert tx != None
                assert tx != original
                self.assertIsInstance(tx, Transaction)

            function(1, 2)

            @engine.transaction
            def function(tx, a, b):
                assert tx != None
                assert tx == original
                self.assertIsInstance(tx, Transaction)

            function(original, 1, 2)

            @engine.transaction
            def function(tx, a, b):
                assert tx != None
                assert tx == original
                self.assertIsInstance(tx, Transaction)

            function(tx=original, a=1, b=2)

            @engine.transaction
            def function(tx, src, b):
                assert tx != None
                assert tx != src
                self.assertIsInstance(tx, Transaction)

            function(src=original, b=2)

            @engine.transaction
            def function(a, tx, b):
                assert tx != None
                assert tx != original
                self.assertIsInstance(tx, Transaction)

            function(1, 2)

            @engine.transaction
            def function(a, tx, b):
                assert tx != None
                assert tx == original
                self.assertIsInstance(tx, Transaction)

            function(1, original, 2)

    def test_transaction_injection_class(self, tx):
        test_class = self
        with engine.transaction() as original:

            @engine.transaction
            class TestClass:
                @engine.transaction
                def __init__(self, tx):
                    assert tx != None
                    assert tx != original
                    test_class.assertIsInstance(tx, Transaction)

                def first_method(self, tx):
                    assert tx != None
                    assert tx != original
                    test_class.assertIsInstance(tx, Transaction)

                def second_method(self, tx):
                    assert tx != None
                    assert tx == original
                    test_class.assertIsInstance(tx, Transaction)

            tc = TestClass()

            tc.first_method()
            tc.second_method(original)
            self.assertRaises(AssertionError, tc.second_method)


if __name__ == "__main__":
    unittest.main()
