import json
import os
import re
import boto3
import uuid
from velocity.misc.format import to_json
from velocity.misc.merge import deep_merge
from datetime import datetime
from velocity.aws.handlers.exceptions import AlertError
from botocore.exceptions import ClientError
import hashlib
import velocity
import velocity.db
from velocity.logging import get_logger

engine = velocity.db.postgres.initialize()


cognito_client = boto3.client("cognito-idp")
logger = get_logger("velocity.aws.handlers.context")


@engine.transaction
class Context:

    def __init__(
        self, aws_event, aws_context, args, postdata, response, session, log=None
    ):
        self.__args = args
        self.__postdata = postdata
        self.__response = response
        self.__session = {} if session is None else session
        self.__aws_event = aws_event
        self.__aws_context = aws_context
        self.__log = log
        self._job_record_cache = {}
        self._job_cancelled_flag = False
        self._feature_flags_cache = None

    def postdata(self, keys=-1, default=None):
        if keys == -1:
            return self.__postdata
        if not isinstance(keys, list):
            keys = [keys]
        data = self.__postdata
        for key in keys:
            if key in data:
                data = data[key]
            else:
                return default
        return data

    def payload(self, keys=-1, default={}):
        if "payload" not in self.__postdata:
            return default
        if keys == -1:
            return self.__postdata["payload"]
        if not isinstance(keys, list):
            keys = [keys]
        data = self.__postdata["payload"]
        for key in keys:
            if key in data:
                data = data[key]
            else:
                return default
        return data

    def action(self):
        return self.__postdata.get("action", self.__args.get("action", ""))

    def args(self):
        return self.__args

    def response(self):
        return self.__response

    def session(self):
        return self.__session

    def dataset(self):
        return self.payload().get("dataset", {})

    def log(self, message, function=None):
        if self.__log:
            return self.__log(message, function)
        if function:
            logger.info("%s: %s", function, message)
        else:
            logger.info("%s", message)

    def update_job(self, tx, data=None):
        """Update job status and message in aws_job_activity table.

        This method only UPDATES existing jobs. For creating new jobs, use create_job.
        """
        if not data:
            return
        if self.postdata("job_id"):
            # Sanitize data before storing in database
            sanitized_data = self._sanitize_job_data(data)
            job_id = self.postdata("job_id")
            tx.table("aws_job_activity").update(sanitized_data, {"job_id": job_id})
            self._job_record_cache.pop(job_id, None)
            tx.commit()

    def create_job(self, tx, job_data=None):
        """Create a new job record in aws_job_activity table using independent transaction."""
        if not job_data:
            return
        sanitized_data = self._sanitize_job_data(job_data)
        tx.table("aws_job_activity").insert(sanitized_data)
        job_id = sanitized_data.get("job_id")
        if job_id:
            self._job_record_cache.pop(job_id, None)
        tx.commit()

    def _sanitize_job_data(self, data):
        """Sanitize sensitive data before storing in aws_job_activity table."""
        if not isinstance(data, dict):
            return data

        sanitized = {}

        # List of sensitive field patterns to sanitize
        sensitive_patterns = [
            "password",
            "token",
            "secret",
            "key",
            "credential",
            "auth",
            "cognito_user",
            "session",
            "cookie",
            "authorization",
        ]

        for key, value in data.items():
            # Check if key contains sensitive patterns
            if any(pattern in key.lower() for pattern in sensitive_patterns):
                sanitized[key] = "[REDACTED]" if value else value
            elif key == "error" and value:
                # Sanitize error messages - keep first 500 chars and remove potential sensitive info
                error_str = str(value)[:500]
                for pattern in sensitive_patterns:
                    if pattern in error_str.lower():
                        # Replace potential sensitive values with placeholder
                        import re

                        # Remove patterns like password=value, token=value, etc.
                        error_str = re.sub(
                            rf"{pattern}[=:]\s*[^\s,\]}}]+",
                            f"{pattern}=[REDACTED]",
                            error_str,
                            flags=re.IGNORECASE,
                        )
                sanitized[key] = error_str
            elif key == "traceback" and value:
                # Sanitize traceback - keep structure but remove sensitive values
                tb_str = str(value)
                for pattern in sensitive_patterns:
                    if pattern in tb_str.lower():
                        import re

                        # Remove patterns like password=value, token=value, etc.
                        tb_str = re.sub(
                            rf"{pattern}[=:]\s*[^\s,\]}}]+",
                            f"{pattern}=[REDACTED]",
                            tb_str,
                            flags=re.IGNORECASE,
                        )
                # Limit traceback size to prevent DB bloat
                sanitized[key] = tb_str[:2000]
            elif key == "message" and value:
                # Sanitize message field
                message_str = str(value)
                for pattern in sensitive_patterns:
                    if pattern in message_str.lower():
                        import re

                        message_str = re.sub(
                            rf"{pattern}[=:]\s*[^\s,\]}}]+",
                            f"{pattern}=[REDACTED]",
                            message_str,
                            flags=re.IGNORECASE,
                        )
                sanitized[key] = message_str[:1000]  # Limit message size
            else:
                # For other fields, copy as-is but check for nested dicts
                if isinstance(value, dict):
                    sanitized[key] = self._sanitize_job_data(value)
                elif isinstance(value, str) and len(value) > 5000:
                    # Limit very large string fields
                    sanitized[key] = value[:5000] + "...[TRUNCATED]"
                else:
                    sanitized[key] = value

        return sanitized

    def _get_job_record(self, tx, job_id=None, refresh=False):
        job_id = job_id or self.postdata("job_id")
        if not job_id:
            return None

        if refresh or job_id not in self._job_record_cache:
            record = tx.table("aws_job_activity").find({"job_id": job_id})
            if record is not None:
                self._job_record_cache[job_id] = record
            elif job_id in self._job_record_cache:
                del self._job_record_cache[job_id]

        return self._job_record_cache.get(job_id)

    def is_job_cancel_requested(self, tx, force_refresh=False):
        job = self._get_job_record(tx, refresh=force_refresh)
        if not job:
            return False

        status = (job.get("status") or "").lower()
        if status in {"cancelrequested", "cancelled"}:
            return True

        message_raw = job.get("message")
        if not message_raw:
            return False

        if isinstance(message_raw, dict):
            message = message_raw
        else:
            try:
                message = json.loads(message_raw)
            except (TypeError, ValueError, json.JSONDecodeError):
                return False

        return bool(message.get("cancel_requested") or message.get("cancelled"))

    def mark_job_cancelled(self, tx, detail=None, requested_by=None):
        job_id = self.postdata("job_id")
        if not job_id:
            return

        job = self._get_job_record(tx, refresh=True) or {}
        message_raw = job.get("message")
        if isinstance(message_raw, dict):
            message = dict(message_raw)
        else:
            try:
                message = json.loads(message_raw) if message_raw else {}
            except (TypeError, ValueError, json.JSONDecodeError):
                message = {}

        message.update(
            {
                "detail": detail or "Job cancelled",
                "cancelled": True,
            }
        )

        tx.table("aws_job_activity").update(
            {
                "status": "Cancelled",
                "message": to_json(message),
                "handler_complete_timestamp": datetime.now(),
                "sys_modified": datetime.now(),
                "sys_modified_by": requested_by
                or self.session().get("email_address")
                or "system",
            },
            {"job_id": job_id},
        )
        tx.commit()
        self._job_record_cache.pop(job_id, None)
        self._job_cancelled_flag = True

    def was_job_cancelled(self):
        return self._job_cancelled_flag

    def enqueue(self, action, payload={}, user=None, suppress_job_activity=False):
        """
        Enqueue jobs to SQS with independent job activity tracking.

        This method uses its own transaction for aws_job_activity updates to ensure
        job tracking is never rolled back with other operations.
        """
        batch_id = str(uuid.uuid4())
        results = {"batch_id": batch_id}
        queue = boto3.resource("sqs").get_queue_by_name(
            QueueName=os.environ["SqsWorkQueue"]
        )
        if isinstance(payload, dict):
            payload = [payload]
        messages = []
        if user is None:
            user = self.session().get("email_address") or "EnqueueTasks"
        for item in payload:
            message = {"action": action, "payload": item}
            id = str(uuid.uuid4()).split("-")[0]
            if suppress_job_activity:
                messages.append({"Id": id, "MessageBody": to_json(message)})
            else:
                message["job_id"] = id
                # Use separate transaction for job activity - this should never be rolled back
                self.create_job(
                    {
                        "action": action,
                        "initial_timestamp": datetime.now(),
                        "created_by": user,
                        "sys_modified_by": user,
                        "payload": to_json(message),
                        "batch_id": str(batch_id),
                        "job_id": id,
                        "status": "Initialized",
                        "message": "Job Initialized",
                    }
                )
                messages.append({"Id": id, "MessageBody": to_json(message)})

            if len(messages) == 10:
                result = queue.send_messages(Entries=messages)
                results = deep_merge(results, result)
                messages.clear()

        if messages:
            result = queue.send_messages(Entries=messages)
            results = deep_merge(results, result)

        return results

    def _is_production(self):
        """Return True when running in production environment."""
        return os.environ.get("USER_BRANCH", "").lower() == "production"

    def get_environment(self):
        """Return the current USER_BRANCH value (defaults to demo)."""
        return os.environ.get("USER_BRANCH", "demo")

    def get_current_lambda_layers(self):
        """Return details about the Lambda layers attached to the running function."""
        try:
            lambda_client = boto3.client("lambda")
            function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME")

            if not function_name:
                return []

            response = lambda_client.get_function_configuration(
                FunctionName=function_name
            )
            layers = response.get("Layers", [])

            layer_info = []
            for layer in layers:
                layer_arn = layer["Arn"]
                layer_name = layer_arn.split(":")[-2]
                layer_version = layer_arn.split(":")[-1]

                layer_info.append(
                    {"name": layer_name, "version": layer_version, "arn": layer_arn}
                )

            return layer_info
        except Exception as exc:
            logger.error("Error getting layer information: %s", exc)
            return []

    def get_pass_through_vars(self, tx, current_user=None):
        """Return environment and layer information for controls.vars."""
        vars = dict(
            [
                (x, os.environ.get(x))
                for x in [
                    "USER_BRANCH",
                    "AWS_JOB_ID",
                    "LOGLEVEL",
                    "USER_REGION",
                    "ProjectName",
                    "DBDatabase",
                    "BUILD_DATETIME",
                ]
            ]
        )

        vars["velocity"] = velocity.__version__
        vars["layers"] = self.get_current_lambda_layers()

        temp = {"controls": {"vars": vars}}

        if current_user:
            temp["controls"]["current_user"] = current_user

        return temp

    def _load_feature_flags(self, tx):
        """Load feature flag values from the shared helpers module."""
        try:
            from support.app import helpers
        except ImportError as exc:
            raise RuntimeError(
                "support.app.helpers is required for feature flag lookups"
            ) from exc
        return helpers.get_feature_flags(tx)

    def _get_feature_flag_cache(self, tx):
        """Return cached feature flags, loading them once per request."""
        if self._feature_flags_cache is None:
            self._feature_flags_cache = self._load_feature_flags(tx)
        return self._feature_flags_cache

    def _split_notification_addresses(self, input_value):
        """Normalize newline-separated recipient strings into a clean list."""
        if not input_value:
            return []
        return [line.strip() for line in str(input_value).splitlines() if line.strip()]

    def get_error_notification_recipients(self, tx):
        """Return newline-specified recipients from feature flags."""
        flags = self._get_feature_flag_cache(tx)
        return self._split_notification_addresses(
            flags.get("error_notification_recipients")
        )

    def get_error_notification_sender(self, tx):
        """Return the configured sender address for error notifications."""
        flags = self._get_feature_flag_cache(tx)
        sender = flags.get("error_notification_sender")
        if isinstance(sender, str) and sender.strip():
            return sender.strip()
        if sender is None:
            return ""
        return str(sender).strip()

    def merge_user_data(self, tx, base_data, email_address):
        """Merge stored user settings from the user_data table into base_data."""
        data = tx.table("user_data").select(
            ["key", "val"], {"userid": email_address}
        )

        for row in data:
            base_data = deep_merge(base_data, json.loads(row["val"]), update=True)

        return base_data

    def get_tracking_table(self, input):
        if isinstance(input, dict):
            email = input.get("email_address")
        else:
            email = input
        if not isinstance(email, str) or not email.strip():
            return None
        return tracking_table_name_for_email(email)

    def resolve_tracking_email(self, override=None):
        if isinstance(override, str) and override.strip():
            return override.strip().lower()
        if isinstance(override, dict):
            for field in ("email_address", "email", "userid", "user_id"):
                value = override.get(field)
                if isinstance(value, str) and value.strip():
                    return value.strip().lower()
        session_email = self.session().get("email_address")
        if isinstance(session_email, str) and session_email.strip():
            return session_email.strip().lower()
        cognito_user = self.session().get("cognito_user")
        if isinstance(cognito_user, str) and cognito_user.strip():
            return cognito_user.strip().lower()
        return None

    def get_cognito_user(self, aws_event):
        provider = (
            aws_event.get("requestContext", {})
            .get("identity", {})
            .get("cognitoAuthenticationProvider")
        )

        if not provider:
            raise AlertError("Cognito identity not found in requestContext") from None

        parts = provider.split(",")

        try:
            user_pool_segment = parts[0]
            user_pool_id = user_pool_segment.split("/")[-1]
            sign_in_segment = parts[-1]
            user_sub = sign_in_segment.split(":")[-1]
        except (IndexError, AttributeError):
            raise AlertError(
                "Unable to parse Cognito identity provider string"
            ) from None

        if not user_pool_id or not user_sub:
            raise AlertError("Incomplete Cognito identity provider data") from None

        try:
            response = cognito_client.admin_get_user(
                UserPoolId=user_pool_id,
                Username=user_sub,
            )
            resolved_username = response.get("Username")
        except cognito_client.exceptions.UserNotFoundException:
            try:
                list_response = cognito_client.list_users(
                    UserPoolId=user_pool_id,
                    Filter=f'sub = "{user_sub}"',
                    Limit=1,
                )
            except ClientError as exc:
                message = exc.response.get("Error", {}).get("Message", "Unknown error")
                raise AlertError(
                    f"Failed to search Cognito user by sub: {message}"
                ) from None

            users = list_response.get("Users", [])
            if not users:
                raise AlertError("Cognito user not found") from None

            user = users[0]
            response = {
                "Username": user.get("Username"),
                "UserAttributes": user.get("Attributes", []),
                "Enabled": user.get("Enabled"),
                "UserStatus": user.get("UserStatus"),
                "UserCreateDate": user.get("UserCreateDate"),
                "UserLastModifiedDate": user.get("UserLastModifiedDate"),
            }
            resolved_username = response.get("Username")
        except ClientError as exc:
            message = exc.response.get("Error", {}).get("Message", "Unknown error")
            raise AlertError(f"Failed to retrieve Cognito user: {message}") from None

        attributes = {
            attr["Name"]: attr.get("Value")
            for attr in response.get("UserAttributes", [])
        }

        user = {
            "username": resolved_username or user_sub,
            "email": attributes.get("email"),
            "attributes": attributes,
            "enabled": response.get("Enabled"),
            "user_status": response.get("UserStatus"),
            "sub": attributes.get("sub", user_sub),
        }

        return user

    def get_cognito_user_optional(self, aws_event):
        """Return Cognito user data if present, otherwise None."""
        try:
            return self.get_cognito_user(aws_event)
        except Exception:
            return None


_MAX_TRACKING_FIELDS = 30
_MAX_TRACKING_PAYLOAD_BYTES = 4096
_MAX_TRACKING_STRING_LENGTH = 2048
_MAX_TRACKING_LIST_ITEMS = 10
_TRACKING_PRIORITIZED_KEYS = (
    "path",
    "notes",
    "client_timestamp",
    "client_datetime",
    "utc_datetime",
)
_SENSITIVE_TRACKING_PATTERNS = (
    "password",
    "token",
    "secret",
    "key",
    "credential",
    "auth",
    "cookie",
)


def sanitize_tracking_payload(payload):
    if not isinstance(payload, dict):
        return {}

    sanitized = {}
    for index, (raw_key, raw_value) in enumerate(payload.items()):
        if index >= _MAX_TRACKING_FIELDS:
            break
        key = _sanitize_tracking_key(raw_key)
        if _is_sensitive_tracking_key(key):
            sanitized[key] = "[REDACTED]"
            continue
        sanitized[key] = _sanitize_tracking_value(raw_value)

    return _prune_tracking_payload(sanitized)


def _sanitize_tracking_value(value, depth=0):
    if depth > 2:
        return _truncate_tracking_string(str(value))

    if isinstance(value, str):
        return _truncate_tracking_string(value)

    if isinstance(value, (int, float, bool)):
        return value

    if isinstance(value, dict):
        sanitized = {}
        for index, (raw_key, raw_value) in enumerate(value.items()):
            if index >= _MAX_TRACKING_FIELDS:
                break
            nested_key = _sanitize_tracking_key(raw_key)
            if _is_sensitive_tracking_key(nested_key):
                sanitized[nested_key] = "[REDACTED]"
            else:
                sanitized[nested_key] = _sanitize_tracking_value(raw_value, depth + 1)
        return sanitized

    if isinstance(value, (list, tuple, set)):
        sanitized_list = []
        for item in list(value)[: _MAX_TRACKING_LIST_ITEMS]:
            sanitized_list.append(_sanitize_tracking_value(item, depth + 1))
        return sanitized_list

    return _truncate_tracking_string(str(value))


def _truncate_tracking_string(value, max_length=None):
    if value is None:
        return value
    normalized = re.sub(r"[\x00-\x1F\x7F]+", " ", value).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    limit = max_length or _MAX_TRACKING_STRING_LENGTH
    if len(normalized) > limit:
        return normalized[:limit].rstrip() + "...[TRUNCATED]"
    return normalized


def _sanitize_tracking_key(key):
    if not isinstance(key, str):
        key = str(key)
    cleaned = re.sub(r"\s+", "_", key.strip().lower())
    return cleaned[:64]


def _is_sensitive_tracking_key(key):
    lower_key = key.lower()
    return any(pattern in lower_key for pattern in _SENSITIVE_TRACKING_PATTERNS)


def _prune_tracking_payload(payload):
    try:
        serialized = json.dumps(payload)
    except Exception:
        return {"payload_truncated": True}

    if len(serialized) <= _MAX_TRACKING_PAYLOAD_BYTES:
        return payload

    pruned = {}
    for key in _TRACKING_PRIORITIZED_KEYS:
        if key in payload:
            pruned[key] = payload[key]

    if not pruned and payload:
        first_key = next(iter(payload))
        pruned[first_key] = payload[first_key]

    pruned["payload_truncated"] = True
    return pruned


def tracking_table_name_for_email(email):
    if not isinstance(email, str):
        return None
    normalized = email.strip().lower()
    if not normalized:
        return None
    table = f"CC_{hashlib.md5(normalized.encode('utf-8')).hexdigest()}".lower()
    return f"user_tracking.{table}"