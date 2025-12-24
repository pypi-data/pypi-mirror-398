import json
import logging
import re
from typing import Any

SENSITIVE_KEYS = {"password", "token", "access_token", "refresh_token", "secret", "card_number", "cvv", "pan"}


class PiiRedactor(logging.Filter):
    def _redact_in_obj(self, obj: Any):
        if isinstance(obj, dict):
            return {k: ("***" if k.lower() in SENSITIVE_KEYS else self._redact_in_obj(v)) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._redact_in_obj(v) for v in obj]
        if isinstance(obj, str):
            obj = re.sub(r"\b(\d{6})\d{6}(\d{4})\b", r"\1******\2", obj)
        return obj

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.args, dict):
                record.args = self._redact_in_obj(record.args)
            if isinstance(record.msg, dict):
                record.msg = self._redact_in_obj(record.msg)
            elif isinstance(record.msg, str):
                try:
                    data = json.loads(record.msg)
                    record.msg = json.dumps(self._redact_in_obj(data), ensure_ascii=False)
                except Exception:
                    record.msg = self._redact_in_obj(record.msg)
        except Exception:
            pass
        return True
