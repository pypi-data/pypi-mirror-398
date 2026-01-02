from __future__ import annotations

import inspect
import sys
from typing import Any, Callable, Dict, Optional, Type, get_args, get_origin, get_type_hints


class TypeContainer:
    """Tiny type-based DI: register_instance(T, obj) / register_factory(T, () -> obj)."""

    def __init__(self) -> None:
        self._instances: Dict[Type[Any], Any] = {}
        self._factories: Dict[Type[Any], Callable[[], Any]] = {}

    def register_instance(self, t: Type[Any], instance: Any) -> None:
        self._instances[t] = instance

    def register_factory(self, t: Type[Any], factory: Callable[[], Any]) -> None:
        self._factories[t] = factory

    def _providers(self):
        for t, v in self._instances.items():
            yield t, (lambda v=v: v)
        for t, f in self._factories.items():
            yield t, f

    def _unwrap(self, ann: Any) -> tuple[list[Type[Any]], bool]:
        if ann is inspect._empty:
            return [], True
        origin = get_origin(ann)
        args = list(get_args(ann))
        allow_none = False
        if origin in (Optional, getattr(__import__("typing"), "Union")):
            if type(None) in args:
                allow_none = True
                args = [a for a in args if a is not type(None)]
            return [a for a in args if isinstance(a, type)], allow_none
        if isinstance(ann, type):
            return [ann], False
        return [], True

    def resolve(self, ann: Any) -> Any:
        types, allow_none = self._unwrap(ann)
        if not types:
            if allow_none:
                return None
            raise LookupError(f"Cannot resolve {ann!r}")
        for T in types:
            # exact
            for pt, make in self._providers():
                if pt is T:
                    return make()
            # supertype/provider match
            best = None
            for pt, make in self._providers():
                try:
                    if issubclass(T, pt):
                        dist = _mro_distance(T, pt)
                        if best is None or dist < best[0]:
                            best = (dist, make)
                except TypeError:
                    pass
            if best:
                return best[1]()
        if allow_none:
            return None
        raise LookupError(f"No provider for {types}")


def _mro_distance(sub: Type[Any], sup: Type[Any]) -> int:
    try:
        return sub.mro().index(sup)
    except ValueError:
        return 10**6


def _type_hints(obj):
    mod = sys.modules.get(getattr(obj, "__module__", "__name__"))
    return get_type_hints(obj, globalns=vars(mod) if mod else None)


def _build_kwargs(
    sig: inspect.Signature,
    hints: Dict[str, Any],
    container: TypeContainer,
    *,
    skip_params: int = 0,
) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {}
    for name, param in list(sig.parameters.items())[skip_params:]:
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        ann = hints.get(name, param.annotation)
        if param.default is not inspect._empty:
            kwargs[name] = param.default
        else:
            kwargs[name] = container.resolve(ann)
    return kwargs


def bind_callable(fn: Callable[..., Any], c: TypeContainer) -> Callable[..., Any]:
    sig = inspect.signature(fn)
    hints = _type_hints(fn)

    def wrapper(message: Any):
        kwargs = _build_kwargs(sig, hints, c, skip_params=1)
        return fn(message, **kwargs)

    return wrapper


def bind_handler(handler: Any, c: TypeContainer) -> Callable[..., Any]:
    if inspect.isclass(handler):
        init = handler.__init__
        sig = inspect.signature(init)
        hints = _type_hints(init)

        kwargs = _build_kwargs(sig, hints, c, skip_params=1)

        instance = handler(**kwargs)  # type: ignore[arg-type]
        if not callable(instance):
            raise TypeError(f"{handler!r} must implement __call__")
        return instance

    if callable(handler):
        return bind_callable(handler, c)

    raise TypeError(f"Unsupported handler: {handler!r}")
