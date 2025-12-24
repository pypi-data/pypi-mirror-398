import decimal
import datetime
from ..base.types import BaseTypes


class TYPES(BaseTypes):
    """
    SQLite-specific type mapping implementation.
    Note: SQLite has dynamic typing, but we still define these for consistency.
    """

    TEXT = "TEXT"
    INTEGER = "INTEGER"
    NUMERIC = "NUMERIC"
    REAL = "REAL"
    BLOB = "BLOB"
    # SQLite doesn't have separate date/time types - they're stored as TEXT, REAL, or INTEGER
    DATE = "TEXT"
    TIME = "TEXT"
    DATETIME = "TEXT"
    TIMESTAMP = "TEXT"
    BOOLEAN = "INTEGER"  # SQLite stores booleans as integers

    @classmethod
    def get_type(cls, v):
        """
        Returns a suitable SQL type string for a Python value/object (SQLite).
        """
        is_special, special_val = cls._handle_special_values(v)
        if is_special:
            return special_val
            
        if isinstance(v, str) or v is str:
            return cls.TEXT
        if isinstance(v, bool) or v is bool:
            return cls.BOOLEAN
        if isinstance(v, int) or v is int:
            return cls.INTEGER
        if isinstance(v, float) or v is float:
            return cls.REAL
        if isinstance(v, decimal.Decimal) or v is decimal.Decimal:
            return cls.NUMERIC
        if isinstance(v, (datetime.datetime, datetime.date, datetime.time)) or v in (datetime.datetime, datetime.date, datetime.time):
            return cls.TEXT  # SQLite stores dates as text
        if isinstance(v, bytes) or v is bytes:
            return cls.BLOB
        return cls.TEXT

    @classmethod
    def get_conv(cls, v):
        """
        Returns a base SQL type for expression usage (SQLite).
        """
        is_special, special_val = cls._handle_special_values(v)
        if is_special:
            return special_val
            
        if isinstance(v, str) or v is str:
            return cls.TEXT
        if isinstance(v, bool) or v is bool:
            return cls.BOOLEAN
        if isinstance(v, int) or v is int:
            return cls.INTEGER
        if isinstance(v, float) or v is float:
            return cls.REAL
        if isinstance(v, decimal.Decimal) or v is decimal.Decimal:
            return cls.NUMERIC
        if isinstance(v, (datetime.datetime, datetime.date, datetime.time)) or v in (datetime.datetime, datetime.date, datetime.time):
            return cls.TEXT
        if isinstance(v, bytes) or v is bytes:
            return cls.BLOB
        return cls.TEXT

    @classmethod
    def py_type(cls, v):
        """
        Returns the Python type that corresponds to an SQL type string (SQLite).
        """
        v = str(v).upper()
        if v == cls.INTEGER:
            return int
        if v in (cls.NUMERIC, cls.REAL):
            return float  # SQLite doesn't distinguish, but float is common
        if v == cls.TEXT:
            return str
        if v == cls.BOOLEAN:
            return bool
        if v == cls.BLOB:
            return bytes
        # For date/time stored as TEXT in SQLite, we'll return str
        # The application layer needs to handle conversion
        return str
