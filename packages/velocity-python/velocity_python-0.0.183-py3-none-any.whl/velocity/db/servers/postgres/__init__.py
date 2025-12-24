import os
import psycopg2
from .sql import SQL
from ..base.initializer import BaseInitializer
from velocity.db.core import engine


class PostgreSQLInitializer(BaseInitializer):
    """PostgreSQL database initializer."""

    @staticmethod
    def initialize(config=None, schema_locked=False, **kwargs):
        """
        Initialize PostgreSQL engine with psycopg2 driver.
        
        Args:
            config: Configuration dictionary
            schema_locked: Boolean to lock schema modifications
            **kwargs: Additional configuration parameters
            
        Returns:
            Configured Engine instance
        """
        # Base configuration from environment
        base_config = {
            "database": os.environ.get("DBDatabase"),
            "host": os.environ.get("DBHost"),
            "port": os.environ.get("DBPort"),
            "user": os.environ.get("DBUser"),
            "password": os.environ.get("DBPassword"),
        }
        
        # Remove None values
        base_config = {k: v for k, v in base_config.items() if v is not None}
        
        # Merge configurations
        final_config = PostgreSQLInitializer._merge_config(base_config, config, **kwargs)
        
        # Validate required configuration
        required_keys = ["database", "host", "user", "password"]
        PostgreSQLInitializer._validate_required_config(final_config, required_keys)
        
        # Check for environment variable override for schema locking
        if os.environ.get("VELOCITY_SCHEMA_LOCKED", "").lower() in ('true', '1', 'yes'):
            schema_locked = True
        
        return engine.Engine(psycopg2, final_config, SQL, schema_locked=schema_locked)


# Maintain backward compatibility
def initialize(config=None, schema_locked=False, **kwargs):
    """Backward compatible initialization function - matches original behavior exactly."""
    konfig = {
        "database": os.environ["DBDatabase"],
        "host": os.environ["DBHost"],
        "port": os.environ["DBPort"],
        "user": os.environ["DBUser"],
        "password": os.environ["DBPassword"],
    }
    konfig.update(config or {})
    konfig.update(kwargs)
    
    # Check for environment variable override for schema locking
    if os.environ.get("VELOCITY_SCHEMA_LOCKED", "").lower() in ('true', '1', 'yes'):
        schema_locked = True
        
    return engine.Engine(psycopg2, konfig, SQL, schema_locked=schema_locked)
