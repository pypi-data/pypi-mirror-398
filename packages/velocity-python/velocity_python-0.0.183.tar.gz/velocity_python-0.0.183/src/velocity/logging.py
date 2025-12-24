"""Shared logging helpers for the Velocity package."""

import json
import logging
import os
import sys
from typing import Any, Dict, Optional

_LOGGING_CONFIGURED = False
_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"
_LEVEL_ENV_VAR = "LOGLEVEL"
_FORMAT_ENV_VAR = "VELOCITY_LOG_FORMAT"
_DEFAULT_LOGGER_NAME = "velocity"


def _running_in_lambda() -> bool:
    return any(
        os.environ.get(var)
        for var in ("AWS_LAMBDA_FUNCTION_NAME", "AWS_EXECUTION_ENV", "LAMBDA_TASK_ROOT")
    )


def _resolve_level(level: Optional[str]) -> str:
    candidate = (level or os.environ.get(_LEVEL_ENV_VAR, "INFO")).upper()
    resolved = getattr(logging, candidate, None)
    if isinstance(resolved, int):
        return candidate
    return "INFO"


def _determine_formatter() -> logging.Formatter:
    forced_format = os.environ.get(_FORMAT_ENV_VAR, "").strip().lower()
    target = forced_format if forced_format in {"json", "text"} else None
    if not target:
        target = "json" if _running_in_lambda() else "text"
    if target == "json":
        return _CloudWatchJSONFormatter(datefmt=_DEFAULT_DATEFMT)
    return logging.Formatter(_DEFAULT_FORMAT, _DEFAULT_DATEFMT)


def configure_logging(level: Optional[str] = None, force: bool = False) -> None:
    """Ensure a single logging configuration is applied across Velocity."""
    global _LOGGING_CONFIGURED
    resolved_level = _resolve_level(level)
    level_value = getattr(logging, resolved_level)

    root = logging.getLogger()
    if _LOGGING_CONFIGURED and not force:
        root.setLevel(level_value)
        return

    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_determine_formatter())
    root.addHandler(handler)
    root.setLevel(level_value)
    root.propagate = False
    _LOGGING_CONFIGURED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger that honors the shared Velocity configuration."""
    if not _LOGGING_CONFIGURED:
        configure_logging()
    return logging.getLogger(name or _DEFAULT_LOGGER_NAME)


def set_log_level(level: str) -> None:
    """Reset the logging level after configuration."""
    resolved_level = _resolve_level(level)
    if not _LOGGING_CONFIGURED:
        configure_logging(resolved_level, force=True)
        return
    logging.getLogger().setLevel(getattr(logging, resolved_level))


class _CloudWatchJSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            payload["stack_info"] = record.stack_info

        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "asctime",
            }
        }
        if extras:
            payload["extra"] = extras

        return json.dumps(payload, default=str)
