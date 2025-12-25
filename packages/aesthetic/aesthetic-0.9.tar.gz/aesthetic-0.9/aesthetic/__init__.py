"""Public API for aesthetic.

Delay heavy imports so that packaging hooks can import this module without
requiring matplotlib/numpy to already be installed.
"""

from __future__ import annotations

__all__ = ["set_style", "savefig"]


def set_style(*args, **kwargs):
    """Proxy to ``plot.set_style`` with a lazy import."""
    from .plot import set_style as _set_style

    return _set_style(*args, **kwargs)


def savefig(*args, **kwargs):
    """Proxy to ``plot.savefig`` with a lazy import."""
    from .plot import savefig as _savefig

    return _savefig(*args, **kwargs)
