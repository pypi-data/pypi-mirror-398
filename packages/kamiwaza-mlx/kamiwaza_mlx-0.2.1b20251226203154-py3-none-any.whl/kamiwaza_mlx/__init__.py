"""
Kamiwaza-MLX – unified server & CLI wrappers around the mlx-lm / mlx-vlm stack.

Exposes the same public API as the original scripts but packaged so it can be
installed from PyPI and run with e.g.  `python -m kamiwaza_mlx.server`.
"""

from __future__ import annotations

import importlib.metadata as _ilmd

try:
    __version__: str = _ilmd.version(__name__)
except _ilmd.PackageNotFoundError:  # pragma: no cover – during editable installs
    # When run from source before the package is built/installed.
    __version__ = "0.0.0.dev0"

del _ilmd

# Lazy imports to avoid requiring all dependencies when using just one module.
# Users can still do:
# >>> from kamiwaza_mlx import infer, server
# But `python -m kamiwaza_mlx.infer` won't fail if server deps are missing.

def __getattr__(name: str):
    """Lazy import submodules to avoid forcing all dependencies."""
    if name == "infer":
        from . import infer
        return infer
    elif name == "server":
        from . import server
        return server
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__: list[str] = ["infer", "server", "__version__"] 
