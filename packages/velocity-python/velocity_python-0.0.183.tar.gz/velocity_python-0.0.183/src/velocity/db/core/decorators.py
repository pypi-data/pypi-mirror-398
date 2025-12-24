import time
import random
from functools import wraps
from velocity.db import exceptions


_PRIMARY_KEY_PATTERNS = (
    "primary key",
    "key 'primary'",
    'key "primary"',
)


def _is_primary_key_duplicate(error):
    """Return True when the duplicate-key error is targeting the primary key."""

    message = str(error or "")
    lowered = message.lower()

    if "sys_id" in lowered:
        return True

    return any(pattern in lowered for pattern in _PRIMARY_KEY_PATTERNS)


def retry_on_dup_key(func):
    """Retry when insert/update fails because the primary key already exists."""

    @wraps(func)
    def retry_decorator(self, *args, **kwds):
        max_retries = 10
        retries = 0
        while retries < max_retries:
            sp = self.tx.create_savepoint(cursor=self.cursor())
            try:
                result = func(self, *args, **kwds)
                self.tx.release_savepoint(sp, cursor=self.cursor())
                return result
            except exceptions.DbDuplicateKeyError as error:
                self.tx.rollback_savepoint(sp, cursor=self.cursor())
                if "sys_id" in kwds.get("data", {}):
                    raise
                if not _is_primary_key_duplicate(error):
                    raise
                retries += 1
                if retries >= max_retries:
                    raise
                backoff_time = (2**retries) * 0.01 + random.uniform(0, 0.02)
                time.sleep(backoff_time)
        raise exceptions.DbDuplicateKeyError("Max retries reached.")

    return retry_decorator


def reset_id_on_dup_key(func):
    """Retry sys_id sequence bump only when the primary key collides."""

    @wraps(func)
    def reset_decorator(self, *args, retries=0, **kwds):
        sp = self.tx.create_savepoint(cursor=self.cursor())
        try:
            result = func(self, *args, **kwds)
            self.tx.release_savepoint(sp, cursor=self.cursor())
            return result
        except exceptions.DbDuplicateKeyError as error:
            self.tx.rollback_savepoint(sp, cursor=self.cursor())
            if "sys_id" in kwds.get("data", {}):
                raise
            if not _is_primary_key_duplicate(error):
                raise
            if retries < 3:
                backoff_time = (2**retries) * 0.01 + random.uniform(0, 0.02)
                time.sleep(backoff_time)
                self.set_sequence(self.max("sys_id") + 1)
                return reset_decorator(self, *args, retries=retries + 1, **kwds)
        raise exceptions.DbDuplicateKeyError("Max retries reached.")

    return reset_decorator


def return_default(
    default=None,
    exceptions=(
        StopIteration,
        exceptions.DbApplicationError,
        exceptions.DbTableMissingError,
        exceptions.DbColumnMissingError,
        exceptions.DbTruncationError,
        exceptions.DbObjectExistsError,
    ),
):
    """
    If the wrapped function raises one of the specified exceptions, or returns None,
    this decorator returns the `default` value instead.
    """

    def decorator(func):
        func.default = default
        func.exceptions = exceptions

        @wraps(func)
        def wrapper(self, *args, **kwds):
            sp = self.tx.create_savepoint(cursor=self.cursor())
            try:
                result = func(self, *args, **kwds)
                if result is None:
                    result = default
            except func.exceptions:
                self.tx.rollback_savepoint(sp, cursor=self.cursor())
                return default
            self.tx.release_savepoint(sp, cursor=self.cursor())
            return result

        return wrapper

    return decorator


def create_missing(func):
    """
    If the function call fails with DbColumnMissingError or DbTableMissingError, 
    tries to create them and re-run (only if schema is not locked).
    """

    @wraps(func)
    def wrapper(self, *args, **kwds):
        sp = self.tx.create_savepoint(cursor=self.cursor())
        try:
            result = func(self, *args, **kwds)
            self.tx.release_savepoint(sp, cursor=self.cursor())
            return result
        except exceptions.DbColumnMissingError as e:
            self.tx.rollback_savepoint(sp, cursor=self.cursor())
            
            # Check if schema is locked
            if self.tx.engine.schema_locked:
                raise exceptions.DbSchemaLockedError(
                    f"Cannot create missing column: schema is locked. Original error: {e}"
                ) from e
                
            # Existing logic for automatic creation
            data = {}
            if "pk" in kwds:
                data.update(kwds["pk"])
            if "data" in kwds:
                data.update(kwds["data"])
            for i, arg in enumerate(args):
                if isinstance(arg, dict):
                    data.update(arg)
            self.alter(data, mode="add")
            return func(self, *args, **kwds)
        except exceptions.DbTableMissingError as e:
            self.tx.rollback_savepoint(sp, cursor=self.cursor())
            
            # Check if schema is locked
            if self.tx.engine.schema_locked:
                raise exceptions.DbSchemaLockedError(
                    f"Cannot create missing table: schema is locked. Original error: {e}"
                ) from e
                
            # Existing logic for automatic creation
            data = {}
            if "pk" in kwds:
                data.update(kwds["pk"])
            if "data" in kwds:
                data.update(kwds["data"])
            for i, arg in enumerate(args):
                if isinstance(arg, dict):
                    data.update(arg)
            self.create(data)
            return func(self, *args, **kwds)

    return wrapper
