import os
from ..base.initializer import BaseInitializer
from velocity.db.core import engine
from .sql import SQL


class MySQLInitializer(BaseInitializer):
    """MySQL database initializer."""

    @staticmethod
    def initialize(config=None, schema_locked=False, **kwargs):
        """
        Initialize MySQL engine with mysql.connector driver.
        
        Args:
            config: Configuration dictionary
            schema_locked: Boolean to lock schema modifications
            **kwargs: Additional configuration parameters
            
        Returns:
            Configured Engine instance
        """
        try:
            import mysql.connector
        except ImportError:
            raise ImportError(
                "MySQL connector not available. Install with: pip install mysql-connector-python"
            )
        
        # Base configuration from environment (if available)
        base_config = {
            "database": os.environ.get("DBDatabase"),
            "host": os.environ.get("DBHost"),
            "port": os.environ.get("DBPort"),
            "user": os.environ.get("DBUser"),
            "password": os.environ.get("DBPassword"),
        }
        
        # Remove None values
        base_config = {k: v for k, v in base_config.items() if v is not None}
        
        # Set MySQL-specific defaults
        mysql_defaults = {
            "host": "localhost",
            "port": 3306,
            "charset": "utf8mb4",
            "autocommit": False,
        }
        
        # Merge configurations: defaults < env < config < kwargs
        final_config = mysql_defaults.copy()
        final_config.update(base_config)
        final_config = MySQLInitializer._merge_config(final_config, config, **kwargs)
        
        # Validate required configuration
        required_keys = ["database", "host", "user"]
        MySQLInitializer._validate_required_config(final_config, required_keys)
        
        # Check for environment variable override for schema locking
        if os.environ.get("VELOCITY_SCHEMA_LOCKED", "").lower() in ('true', '1', 'yes'):
            schema_locked = True
        
        return engine.Engine(mysql.connector, final_config, SQL, schema_locked=schema_locked)


# Maintain backward compatibility
def initialize(config=None, schema_locked=False, **kwargs):
    """Backward compatible initialization function."""
    # Check for environment variable override for schema locking
    if os.environ.get("VELOCITY_SCHEMA_LOCKED", "").lower() in ('true', '1', 'yes'):
        schema_locked = True
        
    return MySQLInitializer.initialize(config, schema_locked, **kwargs)
