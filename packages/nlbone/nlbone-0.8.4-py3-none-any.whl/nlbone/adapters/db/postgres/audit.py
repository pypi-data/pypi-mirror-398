import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum as _Enum
from typing import Any

from sqlalchemy import event
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session as SASession

from nlbone.config.settings import get_settings
from nlbone.core.domain.models import AuditLog
from nlbone.utils.context import current_context_dict

setting = get_settings()
DEFAULT_EXCLUDE = {"updated_at", "created_at"}
DEFAULT_ENABLED = setting.AUDIT_DEFAULT_ENABLE
DEFAULT_OPS = {"INSERT", "UPDATE", "DELETE"}


def _get_ops_for(obj) -> set[str]:
    ops = getattr(obj, "__audit_ops__", None)
    if ops is None:
        return set(DEFAULT_OPS)
    return {str(op).upper() for op in ops}


def _is_audit_disabled(obj) -> bool:
    if getattr(obj, "__audit_disable__", False):
        return True

    if not DEFAULT_ENABLED:
        if hasattr(obj, "__audit_enable__") and getattr(obj, "__audit_enable__"):
            return False
        return True

    if hasattr(obj, "__audit_enable__") and not getattr(obj, "__audit_enable__"):
        return True

    return False


def _is_op_enabled(obj, op: str) -> bool:
    if _is_audit_disabled(obj):
        return False
    return op.upper() in _get_ops_for(obj)


def _ser(val):
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    # UUID
    if isinstance(val, uuid.UUID):
        return str(val)
    # Enum
    if isinstance(val, _Enum):
        return val.value
    if isinstance(val, Decimal):
        return str(val)
    if isinstance(val, set):
        return list(val)
    return val


def _entity_name(obj: Any) -> str:
    return (
        getattr(getattr(obj, "__table__", None), "name", None)
        or getattr(obj, "__tablename__", None)
        or obj.__class__.__name__
    )


def _entity_id(obj: Any) -> str:
    insp = sa_inspect(obj)
    if insp.identity and len(insp.identity) == 1:
        return _ser(insp.identity[0])
    for pk in insp.mapper.primary_key:
        v = getattr(obj, pk.key)
        if v is not None:
            return _ser(v)
    return _ser(getattr(obj, "id", "?"))


def _changes_for_update(obj: any) -> dict[str, dict[str, any]]:
    changes = {}
    insp = sa_inspect(obj)
    exclude = set(getattr(obj, "__audit_exclude__", set())) | DEFAULT_EXCLUDE

    for col in insp.mapper.column_attrs:
        key = col.key
        if key in exclude:
            continue

        try:
            state = insp.attrs[key]
        except KeyError:
            continue

        hist = state.history  # History object
        if hist.has_changes():
            old = hist.deleted[0] if hist.deleted else None
            new = hist.added[0] if hist.added else None
            if old != new:
                changes[key] = {"old": _ser(old), "new": _ser(new)}
    return changes


@event.listens_for(SASession, "before_flush")
def before_flush(session: SASession, flush_context, instances):
    entries = session.info.setdefault("_audit_entries", [])

    # INSERT
    for obj in session.new:
        if isinstance(obj, AuditLog) or not _is_op_enabled(obj, "INSERT"):
            continue
        insp = sa_inspect(obj)
        exclude = set(getattr(obj, "__audit_exclude__", set())) | DEFAULT_EXCLUDE
        row = {}
        for col_attr in insp.mapper.column_attrs:
            key = col_attr.key
            if key in exclude:
                continue
            row[key] = _ser(getattr(obj, key, None))
        entries.append({"obj": obj, "op": "INSERT", "changes": {k: {"old": None, "new": v} for k, v in row.items()}})

    # UPDATE
    for obj in session.dirty:
        if isinstance(obj, AuditLog) or not _is_op_enabled(obj, "UPDATE"):
            continue
        if session.is_modified(obj, include_collections=False):
            ch = _changes_for_update(obj)
            if ch:
                entries.append({"obj": obj, "op": "UPDATE", "changes": ch})

    # DELETE
    for obj in session.deleted:
        if isinstance(obj, AuditLog) or not _is_op_enabled(obj, "DELETE"):
            continue
        entries.append({"obj": obj, "op": "DELETE", "changes": None})


@event.listens_for(SASession, "after_flush_postexec")
def after_flush_postexec(session: SASession, flush_context):
    entries = session.info.pop("_audit_entries", [])
    if not entries:
        return
    ctx = current_context_dict()
    for e in entries:
        obj = e["obj"]
        al = AuditLog(
            entity=_entity_name(obj),
            entity_id=str(_entity_id(obj)),
            operation=e["op"],
            changes=e.get("changes"),
            actor_id=ctx.get("user_id"),
            request_id=ctx.get("request_id"),
            ip=ctx.get("ip"),
            user_agent=ctx.get("user_agent"),
        )
        session.add(al)
