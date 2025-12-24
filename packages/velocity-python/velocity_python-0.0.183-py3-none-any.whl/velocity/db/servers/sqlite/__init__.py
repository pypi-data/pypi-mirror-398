import os
import sqlite3
from ..base.initializer import BaseInitializer
from velocity.db.core import engine
from .sql import SQL


class SQLiteInitializer(BaseInitializer):
    """SQLite database initializer."""

    @staticmethod
    def initialize(config=None, schema_locked=False, **kwargs):
        """
        Initialize SQLite engine with sqlite3 driver.
        
        Args:
            config: Configuration dictionary
            schema_locked: Boolean to lock schema modifications
            **kwargs: Additional configuration parameters
            
        Returns:
            Configured Engine instance
        """
        # Base configuration - SQLite is simpler
        base_config = {
            "database": os.environ.get("DBDatabase", ":memory:"),  # Default to in-memory
        }
        
        # Remove None values
        base_config = {k: v for k, v in base_config.items() if v is not None}
        
        # Set SQLite-specific defaults
        sqlite_defaults = {
            "check_same_thread": False,  # Allow usage from different threads
            "timeout": 30.0,  # Connection timeout
        }
        
        # Merge configurations: defaults < env < config < kwargs
        final_config = sqlite_defaults.copy()
        final_config.update(base_config)
        final_config = SQLiteInitializer._merge_config(final_config, config, **kwargs)
        
        # Validate required configuration - only database path is required
        required_keys = ["database"]
        SQLiteInitializer._validate_required_config(final_config, required_keys)
        
        # Check for environment variable override for schema locking
        if os.environ.get("VELOCITY_SCHEMA_LOCKED", "").lower() in ('true', '1', 'yes'):
            schema_locked = True
        
        return engine.Engine(sqlite3, final_config, SQL, schema_locked=schema_locked)


# Maintain backward compatibility
def initialize(config=None, schema_locked=False, **kwargs):
    """Backward compatible initialization function."""
    # Check for environment variable override for schema locking
    if os.environ.get("VELOCITY_SCHEMA_LOCKED", "").lower() in ('true', '1', 'yes'):
        schema_locked = True
        
    return SQLiteInitializer.initialize(config, schema_locked, **kwargs)
