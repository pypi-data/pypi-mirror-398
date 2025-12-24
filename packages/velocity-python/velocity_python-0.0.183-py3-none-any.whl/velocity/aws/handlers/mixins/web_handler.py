"""
Web Handler mixin for Lambda handlers.

Provides comprehensive activity tracking, logging, and error handling through
web-oriented lifecycle hooks that work alongside existing beforeAction/afterAction/
onError implementations in handlers.
"""

import copy
import json
import os
import pprint
import time
from abc import ABC
from datetime import date, datetime
from typing import Any, Dict, List


class WebHandler(ABC):
    """
    Mixin providing unified activity tracking plus standardized error handling.

    Use this mixin for handlers that need consistent aws_api_activity logging,
    sys_log/error metrics, and optional notifications without duplicating the
    helpers spread across other classes.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = None
        self.end_time = None
        self.activity_log_key = None
        self.activity_data = {}

    # ------------------------------------------------------------------
    # Activity helpers
    # ------------------------------------------------------------------

    def track_activity_start(self, tx, context):
        """Start tracking activity for the current request"""
        self.start_time = time.time()

        postdata = context.postdata()
        payload = context.payload()
        session_data = context.session() or {}

        self.activity_data = {
            "action": context.action(),
            "args": json.dumps(context.args()),
            "postdata": self._sanitize_postdata(postdata),
            "handler_name": self.__class__.__name__,
            "function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "Unknown"),
            "user_branch": os.environ.get("USER_BRANCH", "Unknown"),
            "start_timestamp": self.start_time,
        }

        user_info = self._extract_user_info(payload, session_data)
        if user_info:
            self.activity_data.update(user_info)

        if session_data:
            self.activity_data.update(self._sanitize_session_data(session_data))

        self.activity_data = {
            key: self._normalize_activity_value(value)
            for key, value in self.activity_data.items()
            if value is not None
        }

        try:
            self.activity_log_key = tx.table("aws_api_activity").new(self.activity_data).pk
        except Exception as exc:
            context.log(
                f"WebHandler.track_activity_start failed: {exc}; keys={list(self.activity_data.keys())}",
                "WebHandler.track_activity_start",
            )
            raise

        return self.activity_log_key

    def track_activity_success(self, tx, context):
        """Update activity record with success information"""
        if not self.activity_log_key:
            return

        self.end_time = time.time()
        update_data = {
            "end_timestamp": self.end_time,
            "duration": self.end_time - self.start_time if self.start_time else 0,
            "status": "success",
        }

        tx.table("aws_api_activity").update(update_data, self.activity_log_key)

    def track_activity_error(self, tx, context, exception, tb_string):
        """Update activity record to reflect an error"""
        if not self.activity_log_key:
            return

        self.end_time = time.time()
        update_data = {
            "end_timestamp": self.end_time,
            "duration": self.end_time - self.start_time if self.start_time else 0,
            "status": "error",
            "exception_type": exception.__class__.__name__,
            "exception_message": str(exception),
            "traceback": tb_string,
        }
        update_data["exception"] = exception.__class__.__name__

        tx.table("aws_api_activity").update(update_data, self.activity_log_key)

    def _sanitize_postdata(self, postdata: Dict) -> str:
        """Remove sensitive information from postdata before logging"""
        if not postdata:
            return "{}"

        sanitized = copy.deepcopy(postdata)
        if "payload" in sanitized and isinstance(sanitized["payload"], dict):
            sanitized["payload"].pop("cognito_user", None)

        sensitive_fields = ["password", "token", "secret", "key", "auth", "cognito_user"]
        self._recursive_sanitize(sanitized, sensitive_fields)

        return json.dumps(sanitized)

    def _recursive_sanitize(self, data: Any, sensitive_fields: List[str]):
        """Recursively remove sensitive fields from nested data structures"""
        if isinstance(data, dict):
            for key in list(data.keys()):
                if any(field in key.lower() for field in sensitive_fields):
                    data[key] = "[REDACTED]"
                else:
                    self._recursive_sanitize(data[key], sensitive_fields)
        elif isinstance(data, list):
            for item in data:
                self._recursive_sanitize(item, sensitive_fields)

    def _extract_user_info(self, payload: Dict, session_data: Dict[str, Any]) -> Dict:
        """Extract user information from payload or session"""
        user_info = {}

        session_email = session_data.get("email_address")
        if session_email:
            user_info["email_address"] = session_email.lower()
        session_user_id = session_data.get("user_id") or session_data.get("sub")
        if session_user_id:
            user_info["user_id"] = session_user_id

        if payload and "cognito_user" in payload:
            try:
                attrs = payload["cognito_user"]["attributes"]
                if "email" in attrs and "email_address" not in user_info:
                    user_info["email_address"] = attrs["email"].lower()
                if "sub" in attrs and "user_id" not in user_info:
                    user_info["user_id"] = attrs["sub"]
            except (KeyError, TypeError):
                pass

        return user_info

    def _sanitize_session_data(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive keys and normalize session values"""
        sanitized = {}
        for key, value in session.items():
            if key == "cognito_user":
                continue
            sanitized[key] = self._normalize_activity_value(value)
        return sanitized

    def _normalize_activity_value(self, value: Any) -> Any:
        """Convert values into types acceptable by psycopg2"""
        if isinstance(value, (dict, list, tuple, set)):
            try:
                return json.dumps(value)
            except (TypeError, ValueError):
                return str(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, (bytes, bytearray)):
            return value.decode("utf-8", errors="ignore")
        return value

    # ------------------------------------------------------------------
    # Error helpers
    # ------------------------------------------------------------------

    def log_error_to_system(self, tx, context, exception: Exception, tb_string: str):
        """Log error to the sys_log table"""
        error_data = {
            "level": "ERROR",
            "message": str(exception),
            "function": f"{self.__class__.__name__}.{context.action()}",
            "traceback": tb_string,
            "exception_type": exception.__class__.__name__,
            "handler_name": self.__class__.__name__,
            "action": context.action(),
            "user_branch": os.environ.get("USER_BRANCH", "Unknown"),
            "function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "Unknown"),
            "app_name": os.environ.get("ProjectName", "Unknown"),
            "user_agent": "AWS Lambda",
            "device_type": "Lambda",
            "sys_modified_by": "Lambda",
        }

        try:
            if hasattr(self, "current_user") and self.current_user:
                error_data["user_email"] = self.current_user.get("email_address")
        except Exception:  # pragma: no cover - best effort
            pass

        tx.table("sys_log").insert(error_data)

    def send_error_notification(self, tx, context, exc: str, tb_string: str):
        """Send error notification email to administrators"""
        try:
            from support.app import helpers

            environment = os.environ.get("USER_BRANCH", "Unknown").title()
            function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "Unknown")

            subject = f"{environment} Lambda Error - {function_name}"
           
            body = f"""
Error Details:
- Handler: {self.__class__.__name__}
- Action: {context.action()}
- Exception: {exc}
- Environment: {environment}
- Function: {function_name}

Full Traceback:
{tb_string}

Request Details:
{self._get_error_context(context)}
            """
            html =  f"""
<b>Error Details:</b>
- Handler: {self.__class__.__name__}
- Action: {context.action()}
- Exception: {exc}
- Environment: {environment}
- Function: {function_name}

<b>Full Traceback:</b>
{tb_string}

<b>Request Details:</b>
{self._get_error_context(context)}
            """
            html = html.replace("\n", "<br>").replace(" ", "&nbsp;")
            recipients = self._resolve_error_notification_recipients(tx, context)
            if not recipients:
                print("No error notification recipients configured; skipping notification.")
                return

            sender = self._resolve_error_notification_sender(tx, context)

            helpers.sendmail(
                tx,
                subject=subject,
                body=body,
                html=html,
                sender=sender,
                recipient=recipients[0],
                cc=recipients[1:] if len(recipients) > 1 else None,
                bcc=None,
                email_settings_id=1001,
            )
        except Exception as email_error:  # pragma: no cover
            print(f"Failed to send error notification email: {email_error}")

    def _resolve_error_notification_recipients(self, tx, context) -> List[str]:
        recipients: List[str] = []
        context_method = getattr(context, "get_error_notification_recipients", None)
        if callable(context_method):
            try:
                recipients = context_method(tx) or []
            except Exception as exc:
                print(f"Failed to load recipients from context: {exc}")
        if recipients:
            return recipients
        return self._get_error_notification_recipients()

    def _resolve_error_notification_sender(self, tx, context) -> str:
        sender = None
        context_method = getattr(context, "get_error_notification_sender", None)
        if callable(context_method):
            try:
                sender = context_method(tx)
            except Exception as exc:
                print(f"Failed to load sender from context: {exc}")
        if sender:
            return sender
        return self._get_error_notification_sender()

    def _should_notify_error(self, exception: Exception) -> bool:
        """Determine if an error should trigger notifications"""
        non_notification_types = [
            "AuthenticationError",
            "ValidationError",
            "ValueError",
            "AlertError",
        ]
        exception_name = exception.__class__.__name__
        if "Authentication" in exception_name or "Auth" in exception_name:
            return False
        return exception_name not in non_notification_types

    def _describe_exception_message(self, exception: Exception) -> str:
        """Return the most descriptive text for the exception message"""
        if exception.args:
            meaningful = [str(arg) for arg in exception.args if arg not in (None, "")]
            if meaningful:
                return " | ".join(meaningful)
        raw = str(exception)
        if raw:
            return raw
        return exception.__class__.__name__

    def _get_error_notification_recipients(self) -> List[str]:
        """Default recipient list; override in handler if needed"""
        return []

    def _get_error_notification_sender(self) -> str:
        """Default sender address (disabled unless overridden)"""
        return ""

    def _get_error_context(self, context) -> str:
        """Sanitize request context for reporting"""
        try:
            postdata = context.postdata()
            sanitized = copy.deepcopy(postdata)
            if "payload" in sanitized and isinstance(sanitized["payload"], dict):
                sanitized["payload"].pop("cognito_user", None)
            return pprint.pformat(sanitized)
        except Exception:  # pragma: no cover - best effort
            return "Unable to retrieve request context"

    def log_error_metrics(self, tx, context, exception: Exception):
        """Log error metrics for monitoring"""
        try:
            metrics_data = {
                "metric_type": "error_count",
                "handler_name": self.__class__.__name__,
                "action": context.action(),
                "exception_type": exception.__class__.__name__,
                "environment": os.environ.get("USER_BRANCH", "Unknown"),
                "function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "Unknown"),
                "timestamp": time.time(),
                "sys_modified_by": "Lambda",
            }
            try:
                tx.table("lambda_metrics").insert(metrics_data)
            except Exception:  # pragma: no cover - optional table
                pass
        except Exception:  # pragma: no cover - best effort
            pass

    # ------------------------------------------------------------------
    # Enhanced lifecycle hooks
    # ------------------------------------------------------------------

    def _enhanced_before_action(self, tx, context):
        """Enhanced beforeAction that adds activity tracking"""
        self.track_activity_start(tx, context)

    def _enhanced_after_action(self, tx, context):
        """Enhanced afterAction that adds activity tracking"""
        self.track_activity_success(tx, context)

    def _enhanced_error_handler(self, tx, context, exc, tb):
        """Enhanced onError that adds standardized error handling"""
      

        self.track_activity_error(tx, context, exc, tb)
        self.log_error_to_system(tx, context, exc, tb)
        self.log_error_metrics(tx, context, exc)

        if not getattr(self, "_handles_own_error_notifications", False):
            if self._should_notify_error(exc):
                self.send_error_notification(tx, context, exc, tb)