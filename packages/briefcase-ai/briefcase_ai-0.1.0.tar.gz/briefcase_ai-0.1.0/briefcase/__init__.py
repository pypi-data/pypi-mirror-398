"""Public ``briefcase`` namespace that aliases the internal ``oss`` package."""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
import pkgutil
import sys
from typing import Optional, Sequence

_TARGET_PACKAGE = "oss"
_target_pkg = importlib.import_module(_TARGET_PACKAGE)

__all__ = getattr(_target_pkg, "__all__", [])
__version__ = getattr(_target_pkg, "__version__", None)
__path__ = list(getattr(_target_pkg, "__path__", []))


class _AliasLoader(importlib.abc.Loader):
    """Loader that reuses the real module and registers it under the briefcase alias."""

    def __init__(self, alias: str, target: str) -> None:
        self.alias = alias
        self.target = target

    def create_module(self, spec):  # type: ignore[override]
        return None  # Use default module creation semantics

    def exec_module(self, module) -> None:  # type: ignore[override]
        target_module = importlib.import_module(self.target)
        sys.modules[self.alias] = target_module

        parent_name, _, child_name = self.alias.rpartition(".")
        if parent_name:
            parent_module = sys.modules.get(parent_name)
            if parent_module is not None:
                setattr(parent_module, child_name, target_module)


class _AliasFinder(importlib.abc.MetaPathFinder):
    """Finder that maps ``briefcase.*`` imports to ``oss.*`` modules."""

    prefix = __name__ + "."
    target_prefix = _TARGET_PACKAGE + "."

    def find_spec(
        self,
        fullname: str,
        path: Optional[Sequence[str]],
        target=None,
    ):  # type: ignore[override]
        if not fullname.startswith(self.prefix):
            return None

        target_name = self.target_prefix + fullname[len(self.prefix):]
        target_spec = importlib.util.find_spec(target_name)
        if target_spec is None:
            return None

        spec = importlib.util.spec_from_loader(
            fullname,
            _AliasLoader(fullname, target_name),
            origin=target_spec.origin,
        )
        if spec is None:
            return None

        if target_spec.submodule_search_locations is not None:
            spec.submodule_search_locations = target_spec.submodule_search_locations
        spec.has_location = target_spec.has_location
        spec.cached = target_spec.cached
        return spec


def _install_alias_finder() -> None:
    for existing in sys.meta_path:
        if isinstance(existing, _AliasFinder):
            return
    sys.meta_path.insert(0, _AliasFinder())


_install_alias_finder()


def __getattr__(name: str):
    if hasattr(_target_pkg, name):
        return getattr(_target_pkg, name)

    alias_name = f"{__name__}.{name}"
    module = sys.modules.get(alias_name)
    if module is not None:
        return module

    target_name = f"{_TARGET_PACKAGE}.{name}"
    module = importlib.import_module(target_name)
    sys.modules[alias_name] = module
    return module


def __dir__():
    names = set(dir(_target_pkg))
    names.update(spec.name for spec in pkgutil.iter_modules(__path__))
    return sorted(names)
