from collections import defaultdict
from typing import Dict, List, Set, Tuple

from nlbone.interfaces.api.additional_filed.field_registry import (
    DefaultsMergeMode,
    FieldRule,
    PermissionChecker,
    ResourceRegistry,
)
from nlbone.interfaces.api.dependencies.auth import client_or_user_has_access_func
from nlbone.interfaces.api.exceptions import BadRequestException, InternalServerException

MAX_FIELDS = 50
MAX_BUNDLES = 20


class AdditionalFieldsRequest:
    """
    FastAPI dependency
    - fields: ?fields=rating,costPrice,supplier.address.city
    - bundles: ?bundles=@analytics,@internal
    """

    def __init__(
        self,
        fields: str | None = None,
        bundles: str | None = None,
    ) -> None:
        self.fields = self._parse_csv(fields)[:MAX_FIELDS]
        self.bundles = self._parse_csv(bundles)[:MAX_BUNDLES]

    @staticmethod
    def _parse_csv(s: str | None) -> List[str]:
        if not s:
            return []
        return [x.strip() for x in s.split(",") if x.strip()]


def resolve_requested_fields(
    reg: ResourceRegistry,
    additional_fields: AdditionalFieldsRequest = None,
    can: PermissionChecker = None,
    mode: DefaultsMergeMode = DefaultsMergeMode.UNION,
) -> Tuple[Set[str], Dict[str, FieldRule]]:
    if not additional_fields:
        additional_fields = AdditionalFieldsRequest()
    if not can:
        can = client_or_user_has_access_func
    reg.finalize_defaults(mode=mode)
    expanded_from_bundles = _expand_bundles(reg, set(additional_fields.bundles))

    requested = set(reg.default_fields) | set(additional_fields.fields) | expanded_from_bundles

    # validation
    unknown = {f for f in requested if (f not in reg.default_fields and f not in reg.rules)}
    if unknown:
        raise BadRequestException(f"unknown_fields: {sorted(unknown)}")

    # permission
    selected_rules: Dict[str, FieldRule] = {}
    for f in requested:
        rule = reg.rules.get(f)
        if rule and rule.permission:
            try:
                if not can(rule.permission):
                    continue
            except Exception:
                continue

        if f in reg.default_fields and f not in list(reg.rules.keys()):
            continue

        if not rule.default and f not in additional_fields.fields:
            continue
        selected_rules[f] = rule

    # dependencies
    final = set(requested)

    def add_deps(name: str):
        if name in reg.default_fields:
            return
        r = reg.rules.get(name)
        if not r:
            return
        for d in r.deps:
            final.add(d)
            add_deps(d)

    for f in list(selected_rules.keys()):
        add_deps(f)

    parents_to_add = set()
    for f in list(final):
        if "." in f:
            parent = f.split(".", 1)[0]
            if parent in reg.rules:
                parents_to_add.add(parent)

    final |= parents_to_add
    for p in parents_to_add:
        if p not in selected_rules and p in reg.rules:
            selected_rules[p] = reg.rules[p]

    # validate deps too
    unknown_deps = {d for d in final if (d not in reg.default_fields and d not in reg.rules)}
    if unknown_deps:
        raise InternalServerException(f"registry_missing_rules_for: {sorted(unknown_deps)}")

    # rules
    return final, selected_rules


def _expand_bundles(reg: ResourceRegistry, bundles: Set[str]) -> Set[str]:
    out: Set[str] = set()
    seen_bundles: Set[str] = set()

    def dfs(b: str):
        if b not in reg.bundles:
            raise BadRequestException(f"Unknown bundle: {b}")
        if b in seen_bundles:
            return
        seen_bundles.add(b)
        for item in reg.bundles[b]:
            if item.startswith("@"):
                dfs(item)
            else:
                out.add(item)

    for b in bundles:
        b = b.lstrip("@")
        dfs(b)
    return out


def build_query_plan(
    reg: ResourceRegistry,
    selected_rules: Dict[str, FieldRule],
):
    columns = []
    joins = []
    for r in selected_rules.values():
        columns.extend(r.columns or [])
        joins.extend(r.join_paths or [])
    return columns, joins


def build_field_scope(requested_fields: Set[str]) -> dict[str, set[str]]:
    """
    {'variants', 'variants.cost', 'supplier.address.city'} →
    {
      'variants': {'', 'cost'},
      'supplier': {'address.city'}
    }
    """
    scope: dict[str, set[str]] = defaultdict(set)
    for f in requested_fields:
        parts = f.split(".", 1)
        root = parts[0]
        suffix = parts[1] if len(parts) == 2 else ""  # '' یعنی خود root
        scope[root].add(suffix)
    return scope
