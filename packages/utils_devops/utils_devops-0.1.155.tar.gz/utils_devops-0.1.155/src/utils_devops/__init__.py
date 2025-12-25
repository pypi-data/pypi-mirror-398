# src/utils_devops/__init__.py
"""
utils_devops - Lightweight DevOps utilities for automation scripts.

Design decisions:
- `core` is a real package (always imported).
- `extras` is a real package that performs lazy imports on attribute access
  (see utils_devops/extras/__init__.py). This means both:
      import utils_devops.extras
  and
      from utils_devops.extras import nginx_ops
  will work and lazily import the submodule when needed.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any

__version__ = "0.1.5"
__author__ = "Hamed Sheikhan <sh.sheikhan.m@gmail.com>"

# console (optional)
try:
    from rich.console import Console
    console = Console()
except Exception:
    console = None  # type: ignore

# --- Core package (always imported) ---
# Import the core package module itself (not individual functions).
try:
    core = importlib.import_module("utils_devops.core")
except Exception as e:
    # Fail fast if core cannot import
    raise ImportError("Failed to import utils_devops.core — check installation") from e

# re-export convenient names to match older API
datetimes = core.datetimes
envs = core.envs
files = core.files
logs = core.logs
strings = core.strings
systems = core.systems
script_helpers = core.script_helpers

# --- Extras package (the package module implements lazy loading) ---
# Import the extras package module (it will internally lazy-load submodules).
try:
    extras = importlib.import_module("utils_devops.extras")
except Exception:
    # extras is optional — leave it as a placeholder module with limited behavior
    extras = None  # type: ignore

# top-level visible names
__all__ = [
    "__version__",
    "core",
    "extras",
    # core convenience re-exports
    "datetimes",
    "envs",
    "files",
    "logs",
    "strings",
    "systems",
    "script_helpers",
]

if console:
    console.log("[bold green]utils_devops core modules loaded[/bold green]")
