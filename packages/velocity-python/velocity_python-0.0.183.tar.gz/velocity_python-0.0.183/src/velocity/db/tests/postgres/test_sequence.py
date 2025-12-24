import unittest
import sys
import os
from velocity.db.core.sequence import Sequence
from .common import CommonPostgresTest, engine, test_db


@engine.transaction
@engine.transaction
class TestSequence(CommonPostgresTest):
    
    @classmethod
    def create_test_tables(cls, tx):
        """No special tables needed for sequence tests."""
        pass
    
    def test_sequence_create(self, tx):
        pass

    def test_sequence_next(self, tx):
        pass

    def test_sequence_current(self, tx):
        pass

    def test_sequence_reset(self, tx):
        pass

    def test_sequence_drop(self, tx):
        pass


if __name__ == "__main__":
    unittest.main()
