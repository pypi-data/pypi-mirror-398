"""
Mixins for AWS Lambda handlers.

This package provides mixins for common Lambda handler patterns:
- WebHandler: Activity tracking, logging, and error handling
- DataServiceMixin: Generic CRUD operations for database-backed APIs
"""

from .web_handler import WebHandler
from .data_service import DataServiceMixin, RWXHookSystem, apply_sys_modified_by

__all__ = ['WebHandler', 'DataServiceMixin', 'RWXHookSystem', 'apply_sys_modified_by']
