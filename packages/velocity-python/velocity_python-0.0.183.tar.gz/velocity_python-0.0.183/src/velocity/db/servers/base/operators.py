"""
Abstract base class for database operator mapping implementations.
"""
from abc import ABC, abstractmethod
from typing import Dict


class BaseOperators(ABC):
    """
    Abstract base class that defines the interface for database operator mappings.
    
    Each database implementation should provide concrete implementations of operator
    mappings to handle conversion between Velocity.DB operators and SQL operators.
    """

    @classmethod
    @abstractmethod
    def get_operators(cls) -> Dict[str, str]:
        """
        Returns a dictionary mapping Velocity.DB operators to SQL operators.
        
        This method should return a complete mapping of all operators supported
        by this database implementation.
        
        Returns:
            Dictionary mapping operator symbols to SQL operators
            
        Examples:
            {
                "=": "=",
                "!=": "<>",
                "<>": "<>", 
                "%": "LIKE",
                "!%": "NOT LIKE",
                "%%": "ILIKE",  # PostgreSQL case-insensitive
                "!%%": "NOT ILIKE",
                "><": "BETWEEN",
                "!><": "NOT BETWEEN",
                # ... etc
            }
        """
        pass

    @classmethod
    def get_base_operators(cls) -> Dict[str, str]:
        """
        Returns common operators supported by most databases.
        Subclasses can use this as a starting point and override specific operators.
        
        Returns:
            Dictionary of common SQL operators
        """
        return {
            "=": "=",
            "==": "=",
            "!=": "<>",
            "<>": "<>",
            "!": "<>",
            "<": "<",
            ">": ">", 
            "<=": "<=",
            ">=": ">=",
            "%": "LIKE",
            "!%": "NOT LIKE",
            "><": "BETWEEN",
            "!><": "NOT BETWEEN",
            ">!<": "NOT BETWEEN",
        }

    @classmethod
    def supports_case_insensitive_like(cls) -> bool:
        """
        Returns True if this database supports case-insensitive LIKE operations.
        
        Returns:
            True if database supports ILIKE or similar
        """
        return False

    @classmethod
    def supports_regex(cls) -> bool:
        """
        Returns True if this database supports regular expressions.
        
        Returns:
            True if database supports regex operators
        """
        return False

    @classmethod
    def get_regex_operators(cls) -> Dict[str, str]:
        """
        Returns regex operators if supported by this database.
        
        Returns:
            Dictionary of regex operators or empty dict if not supported
        """
        return {}
