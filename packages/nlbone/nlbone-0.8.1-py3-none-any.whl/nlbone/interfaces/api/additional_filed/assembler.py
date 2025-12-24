import inspect
from typing import Any, Dict

from pydantic import BaseModel

from nlbone.container import Container
from nlbone.interfaces.api.additional_filed.field_registry import FieldRule, ResourceRegistry


def assemble_response(
    obj: Any,
    reg: ResourceRegistry,
    selected_rules: Dict[str, FieldRule],
    session,
    base_schema: type[BaseModel] | None,
    scope_map: dict[str, set[str]] = None,
) -> Dict[str, Any]:
    base = {f: getattr(obj, f, None) for f in reg.default_fields - set(reg.rules.keys())}
    if base_schema:
        base = base_schema.model_validate(base).model_dump()

    ctx = {
        "file_service": Container.file_service(),
        "entity": obj,
        "db": session,
        "pricing_service": Container.pricing_service(),
    }
    roots = {name.split(".", 1)[0] for name in selected_rules.keys()}
    for root in roots:
        rule = reg.rules.get(root)
        if not rule:
            continue

        if rule.loader:
            dependencies = ctx | {"scope": scope_map.get(root, {""})} if scope_map else ctx
            value = inject_dependencies(rule.loader, dependencies=dependencies)
        else:
            value = _get_nested_attr(obj, root)

        _put_nested_key(base, root, value)

    return base


def inject_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters
    deps = {name: dependency for name, dependency in dependencies.items() if name in params}
    return handler(**deps)


def _get_nested_attr(obj: Any, dotted: str):
    cur = obj
    for part in dotted.split("."):
        if cur is None:
            return None
        cur = getattr(cur, part, None)
    return cur


def _put_nested_key(base: Dict[str, Any], dotted: str, value: Any):
    parts = dotted.split(".")
    cur = base
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value
