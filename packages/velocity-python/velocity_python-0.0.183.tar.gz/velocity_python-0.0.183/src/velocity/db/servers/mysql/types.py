import decimal
import datetime
from ..base.types import BaseTypes


class TYPES(BaseTypes):
    """
    MySQL-specific type mapping implementation.
    """

    TEXT = "TEXT"
    INTEGER = "INTEGER"
    NUMERIC = "DECIMAL"
    DATETIME = "DATETIME"
    TIMESTAMP = "TIMESTAMP"
    DATE = "DATE"
    TIME = "TIME"
    BIGINT = "BIGINT"
    SMALLINT = "SMALLINT"
    TINYINT = "TINYINT"
    BOOLEAN = "BOOLEAN"
    BINARY = "BLOB"
    LONGTEXT = "LONGTEXT"
    MEDIUMTEXT = "MEDIUMTEXT"
    VARCHAR = "VARCHAR"

    @classmethod
    def get_type(cls, v):
        """
        Returns a suitable SQL type string for a Python value/object (MySQL).
        """
        is_special, special_val = cls._handle_special_values(v)
        if is_special:
            return special_val
            
        if isinstance(v, str) or v is str:
            return cls.TEXT
        if isinstance(v, bool) or v is bool:
            return cls.BOOLEAN
        if isinstance(v, int) or v is int:
            return cls.BIGINT
        if isinstance(v, float) or v is float:
            return f"{cls.NUMERIC}(19, 6)"
        if isinstance(v, decimal.Decimal) or v is decimal.Decimal:
            return f"{cls.NUMERIC}(19, 6)"
        if isinstance(v, datetime.datetime) or v is datetime.datetime:
            return cls.DATETIME
        if isinstance(v, datetime.date) or v is datetime.date:
            return cls.DATE
        if isinstance(v, datetime.time) or v is datetime.time:
            return cls.TIME
        if isinstance(v, bytes) or v is bytes:
            return cls.BINARY
        return cls.TEXT

    @classmethod
    def get_conv(cls, v):
        """
        Returns a base SQL type for expression usage (MySQL).
        """
        is_special, special_val = cls._handle_special_values(v)
        if is_special:
            return special_val
            
        if isinstance(v, str) or v is str:
            return cls.TEXT
        if isinstance(v, bool) or v is bool:
            return cls.BOOLEAN
        if isinstance(v, int) or v is int:
            return cls.BIGINT
        if isinstance(v, float) or v is float:
            return cls.NUMERIC
        if isinstance(v, decimal.Decimal) or v is decimal.Decimal:
            return cls.NUMERIC
        if isinstance(v, datetime.datetime) or v is datetime.datetime:
            return cls.DATETIME
        if isinstance(v, datetime.date) or v is datetime.date:
            return cls.DATE
        if isinstance(v, datetime.time) or v is datetime.time:
            return cls.TIME
        if isinstance(v, bytes) or v is bytes:
            return cls.BINARY
        return cls.TEXT

    @classmethod
    def py_type(cls, v):
        """
        Returns the Python type that corresponds to an SQL type string (MySQL).
        """
        v = str(v).upper()
        if v in (cls.INTEGER, cls.SMALLINT, cls.BIGINT, cls.TINYINT):
            return int
        if v == cls.NUMERIC or "DECIMAL" in v:
            return decimal.Decimal
        if v in (cls.TEXT, cls.LONGTEXT, cls.MEDIUMTEXT, cls.VARCHAR) or "VARCHAR" in v or "CHAR" in v:
            return str
        if v == cls.BOOLEAN:
            return bool
        if v == cls.DATE:
            return datetime.date
        if v == cls.TIME:
            return datetime.time
        if v in (cls.DATETIME, cls.TIMESTAMP):
            return datetime.datetime
        if v == cls.BINARY or "BLOB" in v:
            return bytes
        raise Exception(f"Unmapped MySQL type {v}")
