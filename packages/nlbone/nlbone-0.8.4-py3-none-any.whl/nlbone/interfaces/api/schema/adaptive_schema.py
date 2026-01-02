from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Iterable, Optional, Type, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, TypeAdapter


class ResponsePreference(str, Enum):
    minimal = "minimal"
    lite = "lite"
    full = "full"


M = TypeVar("M", bound=BaseModel)


class AdaptiveSchemaBase(ABC):
    """Base for a *family* of Pydantic schemas of the same resource."""

    @classmethod
    @abstractmethod
    def minimal(cls) -> Type[M]: ...
    @classmethod
    @abstractmethod
    def lite(cls) -> Type[M]: ...
    @classmethod
    @abstractmethod
    def full(cls) -> Type[M]: ...

    @classmethod
    def choose(cls, pref: Optional[ResponsePreference]) -> Type[M]:
        if pref is None:
            pref = ResponsePreference.lite
        return {
            ResponsePreference.minimal: cls.minimal(),
            ResponsePreference.lite: cls.lite(),
            ResponsePreference.full: cls.full(),
        }.get(pref, cls.lite())

    @classmethod
    def serialize(cls, obj: Any, pref: Optional[ResponsePreference] = None) -> Any:
        schema = cls.choose(pref)
        adapter = TypeAdapter(schema)

        if _is_iterable(obj):
            return [cls._serialize_one(adapter, schema, x, pref) for x in obj]
        return cls._serialize_one(adapter, schema, obj, pref)

    @classmethod
    def _serialize_one(
        cls, adapter: TypeAdapter, schema_cls: Type[BaseModel], item: Any, pref: Optional[ResponsePreference]
    ) -> dict:
        model = adapter.validate_python(item)
        data = model.model_dump()

        annotations = getattr(schema_cls, "__annotations__", {})
        for field_name, annotated_type in annotations.items():
            if field_name not in data:
                continue
            value = getattr(item, field_name, None)
            if value is None:
                continue

            if _is_adaptive(annotated_type):
                # تک‌شیء
                data[field_name] = annotated_type.serialize(value, pref)
            elif _is_list_of_adaptive(annotated_type):
                data[field_name] = annotated_type.__args__[0].serialize(value, pref)
            elif _is_optional_of_adaptive(annotated_type):
                inner = _unwrap_optional(annotated_type)
                data[field_name] = None if value is None else inner.serialize(value, pref)

        return data


# ---------- helpers ----------
def _is_iterable(x: Any) -> bool:
    if isinstance(x, (str, bytes, dict)):
        return False
    try:
        iter(x)
        return True
    except TypeError:
        return False


def _is_adaptive(t) -> bool:
    return isinstance(t, type) and issubclass(t, AdaptiveSchemaBase)


def _is_list_of_adaptive(t) -> bool:
    origin = get_origin(t)
    if origin not in (
        list,
        list.__class__,
        Iterable,
    ):
        return False
    args = get_args(t)
    return len(args) == 1 and _is_adaptive(args[0])


def _is_optional_of_adaptive(t) -> bool:
    return (
        get_origin(t) is Union
        and len([a for a in get_args(t) if a is not type(None)]) == 1
        and _is_adaptive([a for a in get_args(t) if a is not type(None)][0])
    )


def _unwrap_optional(t):
    return [a for a in get_args(t) if a is not type(None)][0]
