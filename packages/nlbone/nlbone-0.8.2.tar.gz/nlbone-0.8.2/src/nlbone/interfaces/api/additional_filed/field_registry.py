from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, Optional, Set, Tuple, Type

from pydantic import BaseModel

PermissionChecker = Callable[[Any, str], bool]
Loader = Callable


def _schema_fields(schema: Type[BaseModel], by_alias: bool = True) -> Set[str]:
    names = set()
    for name, f in schema.model_fields.items():
        if f.json_schema_extra and f.json_schema_extra.get("exclude_none"):
            continue
        names.add(f.alias or name if by_alias else name)
    return names


def _prefix_name(prefix: str, name: str) -> str:
    return f"{prefix}.{name}" if name else prefix


@dataclass(frozen=True)
class FieldRule:
    """
    name: field name (nested with dot)
    permission: None for public
    deps: dependencies
    columns: relationship (SQLAlchemy Column/InstrumentedAttribute)
    join_paths: required paths for eager-load (ex. Product.supplier, Supplier.address)
    loader:
    """

    name: str
    default: bool = False
    permission: Optional[str] = None
    deps: Tuple[str, ...] = ()
    columns: Tuple[Any, ...] = ()
    join_paths: Tuple[Any, ...] = ()
    loader: Optional[Loader] = None


class DefaultsMergeMode(str, Enum):
    STRICT = "strict"  # schema == rules; else raise
    SCHEMA_PRIORITY = "schema"  # defaults = schema_fields
    RULES_PRIORITY = "rules"  # defaults = rules_default_fields
    UNION = "union"  # defaults = schema ∪ rules
    INTERSECTION = "intersection"  # defaults = schema ∩ rules


@dataclass
class ResourceRegistry:
    resource: str
    default_fields: Set[str] = field(default_factory=set)
    base_schema: Optional[Type[BaseModel]] = None
    rules: Dict[str, FieldRule] = field(default_factory=dict)
    bundles: Dict[str, Set[str]] = field(default_factory=dict)
    _schema_fields_cache: Set[str] = field(default_factory=set, repr=False)
    mounts: Dict[str, "ResourceRegistry"] = field(default_factory=dict)

    def add_rule(self, rule: FieldRule) -> "ResourceRegistry":
        self.rules[rule.name] = rule
        return self

    def add_bundle(self, bundle: str, items: Iterable[str]) -> "ResourceRegistry":
        self.bundles[bundle] = set(items)
        return self

    def set_defaults(self, fields: Iterable[str]) -> "ResourceRegistry":
        self.default_fields = set(fields)
        return self

    def recompute_defaults_from_rules(self) -> "ResourceRegistry":
        self.default_fields = {r.name for r in self.rules.values() if r.default}
        return self

    def from_paydantc(self, schema: Type[BaseModel], *, by_alias: bool = True) -> "ResourceRegistry":
        self.base_schema = schema
        self._schema_fields_cache = _schema_fields(schema, by_alias=by_alias)
        return self

    def finalize_defaults(self, mode: DefaultsMergeMode = DefaultsMergeMode.UNION) -> "ResourceRegistry":
        schema_set: Set[str] = self._schema_fields_cache if self.base_schema else set()
        rules_set: Set[str] = {r.name for r in self.rules.values() if r.default}

        manual_set: Set[str] = set(self.default_fields)

        if mode == DefaultsMergeMode.STRICT:
            if self.base_schema is None or not rules_set:
                base = schema_set or rules_set
            else:
                if schema_set != rules_set:
                    raise ValueError(
                        f"[{self.resource}] Default fields diverged: "
                        f"schema={sorted(schema_set)} vs rules={sorted(rules_set)}"
                    )
                base = schema_set
        elif mode == DefaultsMergeMode.SCHEMA_PRIORITY:
            base = schema_set or rules_set
        elif mode == DefaultsMergeMode.RULES_PRIORITY:
            base = rules_set or schema_set
        elif mode == DefaultsMergeMode.UNION:
            base = schema_set | rules_set
        elif mode == DefaultsMergeMode.INTERSECTION:
            base = schema_set & rules_set
        else:
            base = schema_set or rules_set
        final = base | manual_set

        self.default_fields = final
        return self

    def mount(
        self,
        child: "ResourceRegistry",
        *,
        at: str,
        include_child_defaults: bool = False,
        include_child_bundles: bool = True,
    ) -> "ResourceRegistry":
        # 1) rules
        for r in child.rules.values():
            prefixed = FieldRule(
                name=_prefix_name(at, r.name),
                default=(include_child_defaults and r.default),
                permission=r.permission,
                deps=tuple(_prefix_name(at, d) for d in r.deps),
                columns=r.columns,
                join_paths=r.join_paths,
                loader=None,  # load by parent
            )
            self.add_rule(prefixed)

        if include_child_defaults:
            self.default_fields |= {_prefix_name(at, f) for f in child.default_fields}

        if include_child_bundles:
            for bname, items in child.bundles.items():
                pb = _prefix_name(at, bname)
                prefixed_items = set()
                for it in items:
                    if it.startswith("@"):
                        prefixed_items.add(_prefix_name(at, it))
                    else:
                        prefixed_items.add(_prefix_name(at, it))
                self.add_bundle(pb, prefixed_items)

        self.mounts[at] = child
        return self
