"""
Abstract base class for database type mapping implementations.
"""
from abc import ABC, abstractmethod
from typing import Any, Type, Union
import datetime
import decimal


class BaseTypes(ABC):
    """
    Abstract base class that defines the interface for database type mappings.
    
    Each database implementation should provide concrete implementations of these
    type mapping methods to handle conversion between Python types and SQL types.
    """

    # Basic SQL type constants - should be overridden by subclasses
    TEXT: str = "TEXT"
    INTEGER: str = "INTEGER"  
    NUMERIC: str = "NUMERIC"
    BOOLEAN: str = "BOOLEAN"
    DATE: str = "DATE"
    TIME: str = "TIME"
    DATETIME: str = "DATETIME"
    TIMESTAMP: str = "TIMESTAMP"
    BINARY: str = "BINARY"
    BIGINT: str = "BIGINT"
    SMALLINT: str = "SMALLINT"

    @classmethod
    @abstractmethod
    def get_type(cls, v: Any) -> str:
        """
        Returns a suitable SQL type string for a Python value/object.
        
        This method should handle conversion of Python types to appropriate
        SQL column types for table creation and schema operations.
        
        Args:
            v: Python value or type to convert
            
        Returns:
            SQL type string appropriate for this database
            
        Examples:
            get_type(str) -> "TEXT"
            get_type("hello") -> "TEXT"
            get_type(int) -> "INTEGER" 
            get_type(123) -> "INTEGER"
            get_type(datetime.datetime.now()) -> "TIMESTAMP"
        """
        pass

    @classmethod
    @abstractmethod  
    def get_conv(cls, v: Any) -> str:
        """
        Returns a base SQL type for expression usage (e.g. CAST operations).
        
        This is typically used for CAST expressions and should return
        the fundamental SQL type without precision/scale specifiers.
        
        Args:
            v: Python value or type to convert
            
        Returns:
            Base SQL type string for casting
            
        Examples:
            get_conv(decimal.Decimal("123.45")) -> "NUMERIC"
            get_conv(datetime.datetime.now()) -> "TIMESTAMP"
        """
        pass

    @classmethod
    @abstractmethod
    def py_type(cls, sql_type: str) -> Type:
        """
        Returns the Python type that corresponds to an SQL type string.
        
        This method handles the reverse mapping from SQL types back to
        Python types, typically used when reading schema information.
        
        Args:
            sql_type: SQL type string from database schema
            
        Returns:
            Corresponding Python type
            
        Examples:
            py_type("INTEGER") -> int
            py_type("TEXT") -> str
            py_type("TIMESTAMP") -> datetime.datetime
            
        Raises:
            Exception: If the SQL type is not recognized
        """
        pass

    @classmethod
    def _handle_special_values(cls, v: Any) -> tuple[bool, str]:
        """
        Helper method to handle special value prefixes like @@CURRENT_TIMESTAMP.
        
        Args:
            v: Value to check
            
        Returns:
            Tuple of (is_special, processed_value)
        """
        if isinstance(v, str) and v.startswith("@@"):
            return True, v[2:] or cls.TEXT
        return False, ""

    @classmethod
    def _get_basic_type_mapping(cls) -> dict[Type, str]:
        """
        Returns basic Python type to SQL type mappings.
        Subclasses can override this to customize mappings.
        
        Returns:
            Dictionary mapping Python types to SQL types
        """
        return {
            str: cls.TEXT,
            int: cls.INTEGER,
            float: cls.NUMERIC,
            bool: cls.BOOLEAN,
            datetime.datetime: cls.DATETIME,
            datetime.date: cls.DATE,
            datetime.time: cls.TIME,
            decimal.Decimal: cls.NUMERIC,
            bytes: cls.BINARY,
        }
