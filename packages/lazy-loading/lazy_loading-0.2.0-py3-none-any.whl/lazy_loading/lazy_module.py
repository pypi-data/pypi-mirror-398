from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Any


class LazyModule(ModuleType):
    """
    A proxy for a Python module that loads the real module on first attribute access.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self.__dict__["_lazy_name"] = name
        self.__dict__["_lazy_module"] = None

    def _load(self) -> ModuleType:
        module = self.__dict__.get("_lazy_module")
        if module is not None:
            return module

        name = self.__dict__["_lazy_name"]

        try:
            module = importlib.import_module(name)
        except ImportError as e:
            raise ImportError(
                f"Lazy-loaded module '{name}' is not installed or could not be imported.\n"
                "Make sure it is installed."
                f"(e.g. pip install {name})."
            ) from e

        # Replace proxy everywhere
        self.__dict__["_lazy_module"] = module
        sys.modules[name] = module

        return module

    def __getattr__(self, name: str) -> Any:
        module = self._load()
        return getattr(module, name)

    def __setattr__(self, attr: str, value: Any) -> None:
        module = self._load()
        setattr(module, attr, value)

    def __dir__(self) -> list[str]:
        module = self.__dict__.get("_lazy_module")
        if module is None:
            return []
        return dir(module)

    def __repr__(self) -> str:
        if self.__dict__.get("_lazy_module") is None:
            return f"<lazy module '{self.__dict__['_lazy_name']}'>"
        return repr(self.__dict__["_lazy_module"])
