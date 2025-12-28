from __future__ import annotations

import sys

from .lazy_module import LazyModule

__all__ = ["lazyload"]


def lazyload(name: str) -> LazyModule:
    """
    Lazily load a module.

    Example:
        lazyload("pygame")
        pygame.display.set_mode((800, 600))

    Or:
        pygame = lazyload("pygame")

    :param name: Name of the module to load.
    :param inject: Whether to inject generated LazyModule instance to global variables.
    :return: Generated LazyModule instance.
        This can be used instead of the injected variable if injection doesn't work or is disabled.
    """

    existing = sys.modules.get(name)
    if isinstance(existing, LazyModule):
        proxy = existing
    elif existing is not None:
        return LazyModule(name)
    else:
        proxy = LazyModule(name)
        sys.modules[name] = proxy

    return proxy
