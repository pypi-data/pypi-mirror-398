import json
import logging
import sys
from datetime import datetime, timezone
from logging.config import dictConfig
from typing import Any, MutableMapping

from nlbone.config.settings import get_settings
from nlbone.utils.context import current_context_dict
from nlbone.utils.redactor import PiiRedactor

settings = get_settings()


# ---------- Filters ----------
class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        ctx = current_context_dict()
        record.request_id = ctx.get("request_id")
        record.user_id = ctx.get("user_id")
        record.ip = ctx.get("ip")
        record.user_agent = ctx.get("user_agent")
        return True


# ---------- Formatter ----------
class JsonFormatter(logging.Formatter):
    RESERVED = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: MutableMapping[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "user_id": getattr(record, "user_id", None),
            "ip": getattr(record, "ip", None),
            "user_agent": getattr(record, "user_agent", None),
        }

        for k, v in record.__dict__.items():
            if k in self.RESERVED or k in payload:
                continue
            payload[k] = v

        if record.exc_info:
            etype = record.exc_info[0].__name__ if record.exc_info[0] else None
            payload["exc_type"] = etype
            payload["exc"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


class PlainFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)s | %(name)s | req=%(request_id)s user=%(user_id)s ip=%(ip)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )


# ---------- Setup ----------
def setup_logging(
    *,
    log_json: bool = settings.LOG_JSON,
    log_level: str = settings.LOG_LEVEL,
    log_file: str | None = None,
    silence_uvicorn_access: bool = True,
):
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "filters": ["ctx", "pii"],
            "formatter": "json" if log_json else "plain",
        }
    }
    if log_file:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "filters": ["ctx", "pii"],
            "formatter": "json" if log_json else "plain",
        }

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "ctx": {"()": ContextFilter},
                "pii": {"()": PiiRedactor},
            },
            "formatters": {
                "json": {"()": JsonFormatter},
                "plain": {"()": PlainFormatter},
            },
            "handlers": handlers,
            "root": {
                "level": log_level,
                "handlers": list(handlers.keys()),
            },
        }
    )

    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    uvicorn_error = logging.getLogger("uvicorn.error")
    uvicorn_error.handlers = []
    uvicorn_error.propagate = True

    uvicorn_access = logging.getLogger("uvicorn.access")
    if silence_uvicorn_access:
        uvicorn_access.handlers = []
        uvicorn_access.propagate = False
    else:
        uvicorn_access.handlers = []
        uvicorn_access.propagate = True


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or "app")
