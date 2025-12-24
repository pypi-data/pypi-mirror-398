"""
DataServiceMixin - Generic CRUD operations for Lambda handlers.

Provides standard database operations that can be mixed into any Lambda handler
that uses velocity.db for database access.
"""

import base64
import datetime
import importlib
from io import BytesIO

from velocity.misc import export


class DataServiceMixin:
    """
    Mixin providing generic CRUD operations for Lambda handlers.
    
    This mixin assumes:
    - Handler uses velocity.db engine with @engine.transaction decorator
    - Handler has a context object with payload() and response() methods
    - Database tables follow standard conventions (sys_id primary key)
    
    Usage:
        from velocity.aws.handlers.mixins import DataServiceMixin
        
        @engine.transaction
        class HttpEventHandler(DataServiceMixin, LambdaHandler):
            def __init__(self, aws_event, aws_context):
                super().__init__(aws_event, aws_context)
    
    Override read_hook, write_hook, etc. methods to add custom business logic.
    """
    
    # PostgreSQL type mappings for frontend display
    _pg_types = {
        "bool": "string",
        "char": "string",
        "int2": "string",
        "int4": "string",
        "int8": "string",
        "text": "string",
        "numeric": "number",
        "float4": "number",
        "float8": "number",
        "varchar": "string",
        "date": "string",
        "time": "string",
        "timestamp": "string",
    }
    
    def _get_field_type(self, column_info):
        """Convert database column type to frontend display type"""
        return (
            "string"
            if column_info["name"] in ["id", "sys_id"]
            else self._pg_types.get(column_info["type_name"], "string")
        )
    
    # ========== Hook Methods (Override These) ==========
    
    def read_hook(self, tx, table_name, sys_id, row, context):
        """
        Called after reading an object. Override to add custom logic.
        
        Args:
            tx: Database transaction
            table_name: Name of the table
            sys_id: Record ID
            row: Dictionary of record data
            context: Request context
        """
        pass
    
    def write_hook(self, tx, table_name, sys_id, incoming, context):
        """
        Called before writing an object. Override to add validation/transformation.
        
        Args:
            tx: Database transaction
            table_name: Name of the table
            sys_id: Record ID (or "@new" for new records)
            incoming: Dictionary of data to write
            context: Request context
        """
        pass
    
    def query_hook(self, tx, table_name, params, data, context):
        """
        Called after querying objects. Override to transform results.
        
        Args:
            tx: Database transaction
            table_name: Name of the table
            params: Query parameters
            data: Query results
            context: Request context
        """
        pass
    
    def delete_hook(self, tx, table_name, sys_id, context):
        """
        Called before deleting an object. Override to add authorization.
        
        Args:
            tx: Database transaction
            table_name: Name of the table
            sys_id: Record ID to delete
            context: Request context
        """
        pass
    
    # ========== CRUD Action Methods ==========
    
    def OnActionReadObject(self, tx, context):
        """
        Read a single object by sys_id.
        
        Payload:
            tableName: str - Name of the database table
            object: dict - Object containing sys_id field
        """
        payload = context.payload()
        
        # Validate required parameters
        if "tableName" not in payload:
            raise ValueError("Missing required parameter 'tableName' in payload")
        if "object" not in payload:
            raise ValueError("Missing required parameter 'object' in payload")
        
        table_name = payload["tableName"]
        obj = payload["object"]
        
        if not table_name:
            raise ValueError("Parameter 'tableName' cannot be empty")
        if not obj:
            raise ValueError("Parameter 'object' cannot be empty")
        
        sys_id = obj.get("sys_id")
        
        if not sys_id:
            raise ValueError("Object must contain 'sys_id' field")
        
        if sys_id == "@new":
            row = {}
        else:
            sys_id = int(sys_id)
            row = tx.table(table_name).find(sys_id)
            row = row.to_dict() if row else {}
        
        # Call hook for custom logic
        self.read_hook(tx, table_name, sys_id, row, context)
        
        context.response().set_body({
            "object": row,
            "lastFetch": datetime.datetime.now(),
        })
        
        if row:
            context.response().load_object(row)
        else:
            message = f"Object {obj.get('sys_id')} was not found in the database. You may create it as a new object."
            context.response().toast(message, "warning")
    
    def OnActionFindObject(self, tx, context):
        """
        Find a single object by query predicate.
        
        Payload:
            tableName: str - Name of the database table
            query: dict - Query containing 'where' clause
        """
        payload = context.payload()
        
        # Validate required parameters
        if "tableName" not in payload:
            raise ValueError("Missing required parameter 'tableName' in payload")
        if "query" not in payload:
            raise ValueError("Missing required parameter 'query' in payload")
        
        table_name = payload["tableName"]
        query = payload["query"]
        
        if not table_name:
            raise ValueError("Parameter 'tableName' cannot be empty")
        if not query or "where" not in query:
            raise ValueError("Parameter 'query' must contain 'where' clause")
        
        row = tx.table(table_name).find(query["where"])
        
        if row:
            row = row.to_dict()
            self.read_hook(tx, table_name, None, row, context)
        else:
            row = {}
        
        context.response().set_body({
            "object": row,
            "lastFetch": datetime.datetime.now(),
        })
        context.response().load_object(row)
    
    def OnActionWriteObject(self, tx, context):
        """
        Write (insert or update) an object.
        
        Payload:
            tableName: str - Name of the database table
            object: dict - Object data to write
        """
        payload = context.payload()
        
        # Validate required parameters
        if "tableName" not in payload:
            raise ValueError("Missing required parameter 'tableName' in payload")
        if "object" not in payload:
            raise ValueError("Missing required parameter 'object' in payload")
        
        table_name = payload["tableName"]
        obj = payload["object"]
        
        if not table_name:
            raise ValueError("Parameter 'tableName' cannot be empty")
        if not obj or not isinstance(obj, dict):
            raise ValueError("Parameter 'object' must be a non-empty dictionary")
        
        # Ensure the object has at least some data
        incoming = obj.copy()
        if not any(value is not None for value in incoming.values()):
            raise ValueError("Parameter 'object' cannot contain only None values")
        
        sys_id = incoming.pop("sys_id", None)
        
        # Call hook before write
        self.write_hook(tx, table_name, sys_id, incoming, context)
        
        try:
            if sys_id == "@new":
                row = tx.table(table_name).new()
                row.update(incoming)
            elif sys_id:
                sys_id = int(sys_id)
                row = tx.table(table_name).get(sys_id)
                row.update(incoming)
            else:
                raise ValueError("Object sys_id was not supplied on write operation")
            
            row_dict = row.to_dict()
            
            context.response().set_body({
                "object": row_dict,
                "lastFetch": datetime.datetime.now(),
            })
            context.response().load_object(row_dict)
            
        except Exception as e:
            raise Exception(f"Failed to write object to {table_name}: {str(e)}")
    
    def OnActionQuery(self, tx, context):
        """
        Query table for multiple rows.
        
        Payload:
            obj: str - Table name to query
            params: dict - Query parameters (where, orderby, limit, offset)
            result_format: str - 'excel', 'raw', or 'datatable' (default)
            datatable: str - Name for datatable in response (defaults to obj)
            count: bool - Include total count in response
            headers: bool - Include column headers in response
        """
        payload = context.payload()
        
        # Validate required parameters
        if "obj" not in payload:
            raise ValueError("Missing required parameter 'obj' in payload")
        
        table = payload["obj"]
        if not table:
            raise ValueError("Parameter 'obj' cannot be empty")
        
        params = payload.get("params", {})
        result = tx.table(table).select(**params)
        
        if payload.get("result_format") == "excel":
            headers = payload.get(
                "headers", [x.replace("_", " ").title() for x in result.headers]
            )
            rows = result.as_list().all()
            
            filebuffer = BytesIO()
            export.create_spreadsheet(headers, rows, filebuffer)
            context.response().file_download({
                "filename": payload.get("filename", "temp_file.xls"),
                "data": base64.b64encode(filebuffer.getvalue()).decode(),
            })
            return
        
        data = {
            "rows": result.all(),
            "config": {
                "lastFetch": datetime.datetime.now(),
                "query": result.sql,
                "format": payload.get("result_format"),
            },
        }
        
        if payload.get("count"):
            data["count"] = tx.table(table).count(where=params.get("where", None))
        
        if payload.get("headers"):
            data["columns"] = [
                {
                    "field": x["name"],
                    "headerName": x["name"].replace("_", " ").title(),
                    "type": self._get_field_type(x),
                }
                for x in result.columns.values()
            ]
        
        # Call hook after query
        self.query_hook(tx, table, params, data, context)
        
        if payload.get("result_format") == "raw":
            context.response().set_body(data)
        else:
            context.response().set_table({
                payload.get("datatable", payload.get("obj")): data
            })
    
    def OnActionDeleteObject(self, tx, context):
        """
        Delete one or more objects.
        
        Payload:
            tableName: str - Name of the database table
            deleteList: list - List of sys_id values to delete (optional)
            object: dict - Single object with sys_id to delete (optional)
        """
        payload = context.payload()
        
        # Validate required parameters
        if "tableName" not in payload:
            raise ValueError("Missing required parameter 'tableName' in payload")
        
        table_name = payload["tableName"]
        if not table_name:
            raise ValueError("Parameter 'tableName' cannot be empty")
        
        table = tx.table(table_name)
        deleteList = []
        
        if "deleteList" in payload:
            deleteList.extend(payload.get("deleteList"))
        
        if "object" in payload:
            obj = payload["object"]
            if obj and obj.get("sys_id"):
                deleteList.append(obj.get("sys_id"))
        
        for sys_id in deleteList:
            # Call hook before delete
            self.delete_hook(tx, table_name, sys_id, context)
            
            obj = table.find(int(sys_id))
            if obj:
                obj.clear()
                context.response().toast(f"Object {sys_id} deleted", "success")
            else:
                context.response().toast(f"Object {sys_id} not found", "warning")
        
        if not deleteList:
            context.response().toast("No items were selected.", "warning")
    
    def OnActionGetTables(self, tx, context):
        """Get list of all tables in the database."""
        context.response().set_body({"tables": tx.tables()})
    
    def OnActionUpdateRows(self, tx, context):
        """
        Update multiple rows with the same data.
        
        Payload:
            table: str - Table name
            updateData: dict - Data to update
            updateRows: list - List of sys_id values to update
        """
        payload = context.payload()
        
        # Validate required parameters
        required_fields = ["updateData", "updateRows", "table"]
        for field in required_fields:
            if field not in payload:
                raise ValueError(f"Missing required parameter '{field}' in payload")
        
        data = payload["updateData"]
        rows = payload["updateRows"]
        table = payload["table"]
        
        if not table:
            raise ValueError("Parameter 'table' cannot be empty")
        if not rows:
            raise ValueError("Parameter 'updateRows' cannot be empty")
        
        t = tx.table(table)
        count = t.update(data, {"sys_id": rows})
        context.response().toast(f"Updated {count} item(s).", "success")
    
    def OnActionQueryDirect(self, tx, context):
        """
        Query table directly with velocity.db parameters.
        
        Payload:
            obj: str - Table name
            params: dict - Direct velocity.db select parameters
            result_format: str - 'excel', 'raw', or 'datatable' (default)
            count: bool - Include total count
            headers: bool - Include column metadata
        """
        payload = context.payload()
        
        # Validate required parameters
        if "obj" not in payload:
            raise ValueError("Missing required parameter 'obj' in payload")
        
        table_name = payload["obj"]
        if not table_name:
            raise ValueError("Parameter 'obj' cannot be empty")
        
        params = payload.get("params", {})
        
        if payload.get("result_format") == "excel":
            result = tx.table(table_name).select(**params)
            headers = payload.get(
                "headers", [x.replace("_", " ").title() for x in result.headers]
            )
            rows = result.as_list().all()
            filebuffer = BytesIO()
            export.create_spreadsheet(headers, rows, filebuffer)
            context.response().file_download({
                "filename": payload.get("filename", "temp_file.xls"),
                "data": base64.b64encode(filebuffer.getvalue()).decode(),
            })
            return
        
        result = tx.table(table_name).select(**params)
        data = {
            "rows": result.all(),
            "config": {
                "lastFetch": datetime.datetime.now(),
                "query": result.sql,
                "format": payload.get("result_format"),
            },
        }
        
        if payload.get("count"):
            data["count"] = tx.table(table_name).count(where=params.get("where", None))
        
        if payload.get("headers"):
            data["columns"] = [
                {
                    "field": x["name"],
                    "headerName": x["name"].replace("_", " ").title(),
                    "type": self._get_field_type(x),
                }
                for x in result.columns.values()
            ]
        
        if payload.get("result_format") == "raw":
            context.response().set_body(data)
        else:
            context.response().set_table({
                payload.get("datatable", payload.get("obj")): data
            })
    
    def OnActionGetTableSchema(self, tx, context):
        """
        Get table schema from information_schema.
        
        Payload:
            tableName: str - Name of the table
        """
        payload = context.payload()
        
        # Validate required parameters
        if "tableName" not in payload:
            raise ValueError("Missing required parameter 'tableName' in payload")
        
        table_name = payload["tableName"]
        if not table_name:
            raise ValueError("Parameter 'tableName' cannot be empty")
        
        try:
            # Query information_schema to get table schema
            schema_query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale,
                    ordinal_position
                FROM information_schema.columns 
                WHERE table_name = %s 
                    AND table_schema = 'public'
                ORDER BY ordinal_position
            """
            
            schema_data = tx.execute(schema_query, [table_name])
            
            if not schema_data:
                raise ValueError(
                    f"Table '{table_name}' not found or has no accessible columns"
                )
            
            context.response().set_table({
                table_name: {
                    "schema": schema_data.all(),
                }
            })
            
        except Exception as e:
            if hasattr(self, 'log'):
                self.log(
                    f"Error retrieving schema for table {table_name}: {str(e)}",
                    "OnActionGetTableSchema",
                )
            raise Exception(f"Failed to retrieve table schema: {str(e)}")


class RWXHookSystem:
    """
    RWX (Read/Write/eXecute) hook system for table-specific business logic.
    
    This class provides a way to dynamically load and execute table-specific
    hooks (before_read, after_write, etc.) from an rwx package.
    
    Usage:
        from velocity.aws.handlers.mixins import RWXHookSystem
        
        class MyRWXSystem(RWXHookSystem):
            hook_module_name = 'rwx'  # Your rwx package
        
        class HttpEventHandler(DataServiceMixin, LambdaHandler):
            def read_hook(self, tx, table_name, sys_id, row, context):
                MyRWXSystem.call_hooks(
                    'read', tx, table_name, sys_id, row, context
                )
    """
    
    hook_module_name = None  # Override in subclass (e.g., 'rwx')
    
    @classmethod
    def _get_table_module(cls, table):
        """Load table-specific hook module if it exists"""
        if not cls.hook_module_name:
            return None
        try:
            return importlib.import_module(f".{table}", cls.hook_module_name)
        except ImportError:
            return None
    
    @classmethod
    def _call_hook(cls, hook_name, table, *args, **kwargs):
        """Call a hook on table-specific module if it exists"""
        module = cls._get_table_module(table)
        if module and hasattr(module, hook_name):
            return getattr(module, hook_name)(*args, **kwargs)
        return None
    
    @classmethod
    def call_hooks(cls, operation, tx, table_name, *args, context=None):
        """
        Call before/after hooks for an operation.
        
        Args:
            operation: 'read', 'write', 'delete', 'query'
            tx: Database transaction
            table_name: Name of the table
            *args: Operation-specific arguments
            context: Request context (keyword only)
        """
        # Call before hook
        cls._call_hook(f'before_{operation}', table_name, tx, table_name, *args, context)
        
        # Note: after hooks should be called by the application after the operation
        # This method is just for the before hook pattern
    
    @classmethod
    def call_after_hook(cls, operation, tx, table_name, *args, context=None):
        """Call after hook for an operation"""
        cls._call_hook(f'after_{operation}', table_name, tx, table_name, *args, context)


def apply_sys_modified_by(incoming, context):
    """
    Strip sys_* fields and set sys_modified_by from context.
    
    Common pattern for applications that track who modified records.
    Call this from your write_hook implementation.
    
    Args:
        incoming: Dictionary of data being written
        context: Request context with session/payload
    """
    payload = context.payload()
    
    # Strip system fields from incoming data
    for key in list(incoming.keys()):
        if "sys_" in key:
            incoming.pop(key)
    
    # Extract email from session
    session = context.session() if hasattr(context, "session") else None
    email_address = None
    
    if isinstance(session, dict):
        email_address = session.get("cognito_user_email")
        if not email_address:
            cognito_user = session.get("cognito_user")
            if isinstance(cognito_user, dict):
                email_address = cognito_user.get("email") or (
                    cognito_user.get("attributes") or {}
                ).get("email")
        if not email_address:
            email_address = session.get("email_address")
    
    if not email_address and isinstance(payload, dict):
        payload_user = payload.get("cognito_user")
        if isinstance(payload_user, dict):
            email_address = payload_user.get("email") or (
                payload_user.get("attributes") or {}
            ).get("email")
    
    incoming["sys_modified_by"] = (
        email_address.lower()
        if isinstance(email_address, str)
        else incoming.get("sys_modified_by", "unknown")
    )
    incoming["sys_dirty"] = True
