import decimal
import datetime
from ..base.types import BaseTypes


class TYPES(BaseTypes):
    """
    SQL Server-specific type mapping implementation.
    """

    TEXT = "NVARCHAR(MAX)"
    VARCHAR = "VARCHAR"
    NVARCHAR = "NVARCHAR"
    INTEGER = "INT"
    BIGINT = "BIGINT"
    SMALLINT = "SMALLINT"
    TINYINT = "TINYINT"
    NUMERIC = "DECIMAL"
    DECIMAL = "DECIMAL"
    FLOAT = "FLOAT"
    REAL = "REAL"
    MONEY = "MONEY"
    DATETIME = "DATETIME"
    DATETIME2 = "DATETIME2"
    DATE = "DATE"
    TIME = "TIME"
    TIMESTAMP = "ROWVERSION"
    BOOLEAN = "BIT"
    BINARY = "VARBINARY(MAX)"
    UNIQUEIDENTIFIER = "UNIQUEIDENTIFIER"

    @classmethod
    def get_type(cls, v):
        """
        Returns a suitable SQL type string for a Python value/object (SQL Server).
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
            return f"{cls.DECIMAL}(19, 6)"
        if isinstance(v, decimal.Decimal) or v is decimal.Decimal:
            return f"{cls.DECIMAL}(19, 6)"
        if isinstance(v, datetime.datetime) or v is datetime.datetime:
            return cls.DATETIME2
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
        Returns a base SQL type for expression usage (SQL Server).
        """
        is_special, special_val = cls._handle_special_values(v)
        if is_special:
            return special_val
            
        if isinstance(v, str) or v is str:
            return cls.NVARCHAR
        if isinstance(v, bool) or v is bool:
            return cls.BOOLEAN
        if isinstance(v, int) or v is int:
            return cls.BIGINT
        if isinstance(v, float) or v is float:
            return cls.DECIMAL
        if isinstance(v, decimal.Decimal) or v is decimal.Decimal:
            return cls.DECIMAL
        if isinstance(v, datetime.datetime) or v is datetime.datetime:
            return cls.DATETIME2
        if isinstance(v, datetime.date) or v is datetime.date:
            return cls.DATE
        if isinstance(v, datetime.time) or v is datetime.time:
            return cls.TIME
        if isinstance(v, bytes) or v is bytes:
            return cls.BINARY
        return cls.NVARCHAR

    @classmethod
    def py_type(cls, v):
        """
        Returns the Python type that corresponds to an SQL type string (SQL Server).
        """
        v = str(v).upper()
        if v in (cls.INTEGER, cls.SMALLINT, cls.BIGINT, cls.TINYINT):
            return int
        if v in (cls.NUMERIC, cls.DECIMAL, cls.MONEY) or "DECIMAL" in v:
            return decimal.Decimal
        if v in (cls.FLOAT, cls.REAL):
            return float
        if v in (cls.TEXT, cls.VARCHAR, cls.NVARCHAR) or "VARCHAR" in v or "CHAR" in v:
            return str
        if v == cls.BOOLEAN or v == "BIT":
            return bool
        if v == cls.DATE:
            return datetime.date
        if v == cls.TIME:
            return datetime.time
        if v in (cls.DATETIME, cls.DATETIME2):
            return datetime.datetime
        if v == cls.BINARY or "BINARY" in v:
            return bytes
        raise Exception(f"Unmapped SQL Server type {v}")
