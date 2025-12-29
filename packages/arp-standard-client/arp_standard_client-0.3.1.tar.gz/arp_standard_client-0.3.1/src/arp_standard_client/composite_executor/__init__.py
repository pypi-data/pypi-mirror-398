"""ARP Composite Executor API facade (preferred) + low-level client package."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
    'ArpApiError',
    'CompositeExecutorClient',
]

_EXPORT_MAP: dict[str, str] = {
    'CompositeExecutorClient': '.facade',
}

if TYPE_CHECKING:
    from arp_standard_client.errors import ArpApiError
    from .facade import CompositeExecutorClient

def __getattr__(name: str) -> Any:
    if name == "ArpApiError":
        from arp_standard_client.errors import ArpApiError as _ArpApiError

        return _ArpApiError
    module = _EXPORT_MAP.get(name)
    if module is None:
        raise AttributeError(name)
    if module.startswith("."):
        return getattr(import_module(module, __name__), name)
    return getattr(import_module(module), name)

