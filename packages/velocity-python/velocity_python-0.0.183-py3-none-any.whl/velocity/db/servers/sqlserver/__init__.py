import os
from ..base.initializer import BaseInitializer
from velocity.db.core import engine
from .sql import SQL


class SQLServerInitializer(BaseInitializer):
    """SQL Server database initializer."""

    @staticmethod
    def initialize(config=None, schema_locked=False, **kwargs):
        """
        Initialize SQL Server engine with pytds driver.
        
        Args:
            config: Configuration dictionary
            schema_locked: Boolean to lock schema modifications
            **kwargs: Additional configuration parameters
            
        Returns:
            Configured Engine instance
        """
        try:
            import pytds
        except ImportError:
            raise ImportError(
                "SQL Server connector not available. Install with: pip install python-tds"
            )
        
        # Base configuration from environment (if available)
        base_config = {
            "database": os.environ.get("DBDatabase"),
            "server": os.environ.get("DBHost"),  # SQL Server uses 'server' instead of 'host'
            "port": os.environ.get("DBPort"),
            "user": os.environ.get("DBUser"),
            "password": os.environ.get("DBPassword"),
        }
        
        # Remove None values
        base_config = {k: v for k, v in base_config.items() if v is not None}
        
        # Set SQL Server-specific defaults
        sqlserver_defaults = {
            "server": "localhost",
            "port": 1433,
            "autocommit": False,
            "timeout": 30,
        }
        
        # Merge configurations: defaults < env < config < kwargs
        final_config = sqlserver_defaults.copy()
        final_config.update(base_config)
        final_config = SQLServerInitializer._merge_config(final_config, config, **kwargs)
        
        # Validate required configuration
        required_keys = ["database", "server", "user"]
        SQLServerInitializer._validate_required_config(final_config, required_keys)
        
        # Check for environment variable override for schema locking
        if os.environ.get("VELOCITY_SCHEMA_LOCKED", "").lower() in ('true', '1', 'yes'):
            schema_locked = True
        
        return engine.Engine(pytds, final_config, SQL, schema_locked=schema_locked)


# Maintain backward compatibility
def initialize(config=None, schema_locked=False, **kwargs):
    """Backward compatible initialization function."""
    # Check for environment variable override for schema locking
    if os.environ.get("VELOCITY_SCHEMA_LOCKED", "").lower() in ('true', '1', 'yes'):
        schema_locked = True
        
    return SQLServerInitializer.initialize(config, schema_locked, **kwargs)
