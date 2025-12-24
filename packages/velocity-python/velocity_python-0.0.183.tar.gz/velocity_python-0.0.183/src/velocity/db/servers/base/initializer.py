"""
Abstract base class for database initialization.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from velocity.db.core import engine


class BaseInitializer(ABC):
    """
    Abstract base class for database connection initialization.
    
    Each database implementation should provide a concrete implementation
    of the initialize method to set up database connections properly.
    """

    @staticmethod
    @abstractmethod
    def initialize(config: Optional[Dict[str, Any]] = None, schema_locked: bool = False, **kwargs) -> engine.Engine:
        """
        Initialize a database engine with the appropriate driver and configuration.
        
        Args:
            config: Configuration dictionary (can be None)
            schema_locked: Boolean to lock schema modifications (default: False)
            **kwargs: Additional configuration parameters
            
        Returns:
            Configured Engine instance
            
        Raises:
            ImportError: If required database driver is not available
            ValueError: If configuration is invalid
        """
        pass

    @staticmethod
    def _merge_config(base_config: Dict[str, Any], config: Optional[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Helper method to merge configuration from multiple sources.
        
        Args:
            base_config: Base configuration (e.g., from environment)
            config: User-provided configuration
            **kwargs: Additional keyword arguments
            
        Returns:
            Merged configuration dictionary
        """
        final_config = base_config.copy()
        if config:
            final_config.update(config)
        final_config.update(kwargs)
        return final_config

    @staticmethod
    def _validate_required_config(config: Dict[str, Any], required_keys: list[str]) -> None:
        """
        Validate that required configuration keys are present.
        
        Args:
            config: Configuration to validate
            required_keys: List of required configuration keys
            
        Raises:
            ValueError: If required keys are missing
        """
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {missing_keys}")
