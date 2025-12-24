"""
Abstract base class for SQL dialect implementations.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
from collections.abc import Mapping, Sequence


class BaseSQLDialect(ABC):
    """
    Abstract base class that defines the interface all database SQL dialects must implement.
    
    This class ensures consistency across all database implementations and makes it clear
    what methods each database dialect needs to provide.
    """

    # Database server identifier - must be set by subclasses
    server: str = ""
    
    # Column metadata identifiers - database specific
    type_column_identifier: str = ""
    is_nullable: str = ""
    
    # Default schema name for this database
    default_schema: str = ""
    
    # Error code classifications - must be set by subclasses
    ApplicationErrorCodes: List[str] = []
    DatabaseMissingErrorCodes: List[str] = []
    TableMissingErrorCodes: List[str] = []
    ColumnMissingErrorCodes: List[str] = []
    ForeignKeyMissingErrorCodes: List[str] = []
    ConnectionErrorCodes: List[str] = []
    DuplicateKeyErrorCodes: List[str] = []
    RetryTransactionCodes: List[str] = []
    TruncationErrorCodes: List[str] = []
    LockTimeoutErrorCodes: List[str] = []
    DatabaseObjectExistsErrorCodes: List[str] = []
    DataIntegrityErrorCodes: List[str] = []

    @classmethod
    @abstractmethod
    def get_error(cls, e: Exception) -> Optional[str]:
        """
        Extract error information from database exception.
        
        Args:
            e: Database exception
            
        Returns:
            Error code or message, or None if not applicable
        """
        pass

    # Core CRUD Operations
    @classmethod
    @abstractmethod
    def select(
        cls,
        tx: Any,
        columns: Optional[Union[str, List[str]]] = None,
        table: Optional[str] = None,
        where: Optional[Union[str, Dict, List]] = None,
        orderby: Optional[Union[str, List, Dict]] = None,
        groupby: Optional[Union[str, List]] = None,
        having: Optional[Union[str, Dict, List]] = None,
        start: Optional[int] = None,
        qty: Optional[int] = None,
        lock: Optional[bool] = None,
        skip_locked: Optional[bool] = None,
    ) -> Tuple[str, List[Any]]:
        """
        Generate a SELECT statement.
        
        Returns:
            Tuple of (sql_string, parameters)
        """
        pass

    @classmethod
    @abstractmethod
    def insert(cls, table: str, data: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Generate an INSERT statement.
        
        Args:
            table: Table name
            data: Dictionary of column names to values
            
        Returns:
            Tuple of (sql_string, parameters)
        """
        pass

    @classmethod
    @abstractmethod
    def update(
        cls, 
        tx: Any, 
        table: str, 
        data: Dict[str, Any], 
        where: Optional[Union[str, Dict, List]] = None, 
        pk: Optional[Dict[str, Any]] = None, 
        excluded: bool = False
    ) -> Tuple[str, List[Any]]:
        """
        Generate an UPDATE statement.
        
        Args:
            tx: Database transaction
            table: Table name
            data: Dictionary of columns to update
            where: WHERE clause conditions
            pk: Primary key conditions to merge with where
            excluded: If True, creates EXCLUDED.col expressions for upserts
            
        Returns:
            Tuple of (sql_string, parameters)
        """
        pass

    @classmethod
    @abstractmethod
    def delete(cls, tx: Any, table: str, where: Union[str, Dict, List]) -> Tuple[str, List[Any]]:
        """
        Generate a DELETE statement.
        
        Args:
            tx: Database transaction
            table: Table name
            where: WHERE clause conditions
            
        Returns:
            Tuple of (sql_string, parameters)
        """
        pass

    @classmethod
    @abstractmethod
    def merge(
        cls,
        tx: Any,
        table: str,
        data: Dict[str, Any],
        pk: Dict[str, Any],
        on_conflict_do_nothing: bool,
        on_conflict_update: bool
    ) -> Tuple[str, List[Any]]:
        """
        Generate an UPSERT/MERGE statement.
        
        Args:
            tx: Database transaction
            table: Table name
            data: Data to insert/update
            pk: Primary key columns
            on_conflict_do_nothing: If True, ignore conflicts
            on_conflict_update: If True, update on conflicts
            
        Returns:
            Tuple of (sql_string, parameters)
        """
        pass

    # Database Metadata Operations
    @classmethod
    @abstractmethod
    def version(cls) -> str:
        """Get database version query."""
        pass

    @classmethod
    @abstractmethod
    def timestamp(cls) -> str:
        """Get current timestamp query."""
        pass

    @classmethod
    @abstractmethod
    def user(cls) -> str:
        """Get current user query."""
        pass

    @classmethod
    @abstractmethod
    def databases(cls) -> str:
        """Get list of databases query."""
        pass

    @classmethod
    @abstractmethod
    def schemas(cls) -> str:
        """Get list of schemas query."""
        pass

    @classmethod
    @abstractmethod
    def current_schema(cls) -> str:
        """Get current schema query."""
        pass

    @classmethod
    @abstractmethod
    def current_database(cls) -> str:
        """Get current database query."""
        pass

    @classmethod
    @abstractmethod
    def tables(cls, system: bool = False) -> str:
        """
        Get list of tables query.
        
        Args:
            system: Include system tables
        """
        pass

    @classmethod
    @abstractmethod
    def views(cls, system: bool = False) -> str:
        """
        Get list of views query.
        
        Args:
            system: Include system views
        """
        pass

    # Database Structure Operations
    @classmethod
    @abstractmethod
    def create_database(cls, name: str) -> str:
        """Generate CREATE DATABASE statement."""
        pass

    @classmethod
    @abstractmethod
    def drop_database(cls, name: str) -> str:
        """Generate DROP DATABASE statement."""
        pass

    @classmethod
    @abstractmethod
    def create_table(cls, name: str, columns: Dict[str, Any] = None, drop: bool = False) -> str:
        """
        Generate CREATE TABLE statement.
        
        Args:
            name: Table name
            columns: Column definitions
            drop: Drop table if exists first
        """
        pass

    @classmethod
    @abstractmethod
    def drop_table(cls, name: str) -> str:
        """Generate DROP TABLE statement."""
        pass

    @classmethod
    @abstractmethod
    def truncate(cls, table: str) -> str:
        """Generate TRUNCATE statement."""
        pass

    # Column Operations
    @classmethod
    @abstractmethod
    def columns(cls, name: str) -> str:
        """Get table columns query."""
        pass

    @classmethod
    @abstractmethod
    def column_info(cls, table: str, name: str) -> str:
        """Get column information query."""
        pass

    @classmethod
    @abstractmethod
    def drop_column(cls, table: str, name: str, cascade: bool = True) -> str:
        """Generate DROP COLUMN statement."""
        pass

    @classmethod
    @abstractmethod
    def alter_add(cls, table: str, columns: Dict[str, Any], null_allowed: bool = True) -> str:
        """Generate ALTER TABLE ADD COLUMN statement."""
        pass

    @classmethod
    @abstractmethod
    def alter_drop(cls, table: str, columns: List[str]) -> str:
        """Generate ALTER TABLE DROP COLUMN statement."""
        pass

    @classmethod
    @abstractmethod
    def alter_column_by_type(cls, table: str, column: str, value: str, nullable: bool = True) -> str:
        """Generate ALTER COLUMN statement by type."""
        pass

    @classmethod
    @abstractmethod
    def alter_column_by_sql(cls, table: str, column: str, value: str) -> str:
        """Generate ALTER COLUMN statement by SQL."""
        pass

    @classmethod
    @abstractmethod
    def rename_column(cls, table: str, orig: str, new: str) -> str:
        """Generate RENAME COLUMN statement."""
        pass

    @classmethod
    @abstractmethod
    def rename_table(cls, table: str, new: str) -> str:
        """Generate RENAME TABLE statement."""
        pass

    # Key Operations
    @classmethod
    @abstractmethod
    def primary_keys(cls, table: str) -> str:
        """Get primary key columns query."""
        pass

    @classmethod
    @abstractmethod
    def foreign_key_info(
        cls, 
        table: Optional[str] = None, 
        column: Optional[str] = None, 
        schema: Optional[str] = None
    ) -> str:
        """Get foreign key information query."""
        pass

    @classmethod
    @abstractmethod
    def create_foreign_key(
        cls,
        table: str,
        columns: List[str],
        key_to_table: str,
        key_to_columns: List[str],
        name: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> str:
        """Generate CREATE FOREIGN KEY statement."""
        pass

    @classmethod
    @abstractmethod
    def drop_foreign_key(
        cls,
        table: str,
        columns: List[str],
        key_to_table: Optional[str] = None,
        key_to_columns: Optional[List[str]] = None,
        name: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> str:
        """Generate DROP FOREIGN KEY statement."""
        pass

    # Index Operations
    @classmethod
    @abstractmethod
    def create_index(
        cls,
        tx: Any,
        table: Optional[str] = None,
        columns: Optional[List[str]] = None,
        unique: bool = False,
        direction: Optional[str] = None,
        where: Optional[str] = None,
        name: Optional[str] = None,
        schema: Optional[str] = None,
        trigram: Optional[bool] = None,
        lower: Optional[bool] = None,
    ) -> str:
        """Generate CREATE INDEX statement."""
        pass

    @classmethod
    @abstractmethod
    def drop_index(
        cls,
        table: Optional[str] = None,
        columns: Optional[List[str]] = None,
        name: Optional[str] = None,
        schema: Optional[str] = None,
        trigram: Optional[bool] = None,
    ) -> str:
        """Generate DROP INDEX statement."""
        pass

    @classmethod
    @abstractmethod
    def indexes(cls, table: str) -> str:
        """Get table indexes query."""
        pass

    # Transaction Operations
    @classmethod
    @abstractmethod
    def create_savepoint(cls, sp: str) -> str:
        """Generate SAVEPOINT statement."""
        pass

    @classmethod
    @abstractmethod
    def release_savepoint(cls, sp: str) -> str:
        """Generate RELEASE SAVEPOINT statement."""
        pass

    @classmethod
    @abstractmethod
    def rollback_savepoint(cls, sp: str) -> str:
        """Generate ROLLBACK TO SAVEPOINT statement."""
        pass

    # View Operations
    @classmethod
    @abstractmethod
    def create_view(cls, name: str, query: str, temp: bool = False, silent: bool = True) -> str:
        """Generate CREATE VIEW statement."""
        pass

    @classmethod
    @abstractmethod
    def drop_view(cls, name: str, silent: bool = True) -> str:
        """Generate DROP VIEW statement."""
        pass

    # Sequence/Identity Operations
    @classmethod
    @abstractmethod
    def last_id(cls, table: str) -> str:
        """Get last inserted ID query."""
        pass

    @classmethod
    @abstractmethod
    def current_id(cls, table: str) -> str:
        """Get current sequence value query."""
        pass

    @classmethod
    @abstractmethod
    def set_id(cls, table: str, start: int) -> str:
        """Generate set sequence value statement."""
        pass

    @classmethod
    @abstractmethod
    def set_sequence(cls, table: str, next_value: int) -> str:
        """Generate set sequence next value statement."""
        pass

    # Utility Operations
    @classmethod
    @abstractmethod
    def massage_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Massage data before insert/update operations.
        Database-specific data transformations.
        """
        pass

    @classmethod
    @abstractmethod
    def alter_trigger(cls, table: str, state: str = "ENABLE", name: str = "USER") -> str:
        """Generate ALTER TRIGGER statement."""
        pass

    @classmethod
    @abstractmethod
    def missing(
        cls,
        tx: Any,
        table: str,
        list_values: List[Any],
        column: str = "SYS_ID",
        where: Optional[Union[str, Dict, List]] = None,
    ) -> Tuple[str, List[Any]]:
        """
        Generate query to find missing values from a list.
        
        Args:
            tx: Database transaction
            table: Table name
            list_values: List of values to check
            column: Column to check against
            where: Additional WHERE conditions
            
        Returns:
            Tuple of (sql_string, parameters)
        """
        pass
