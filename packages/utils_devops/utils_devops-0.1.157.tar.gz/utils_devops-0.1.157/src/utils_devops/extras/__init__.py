"""
Extra utilities for utils_devops.
Submodules are lazy-loaded on attribute access (PEP 562 module __getattr__).

Supports:
    import utils_devops.extras
    from utils_devops.extras import nginx_ops

If a dependency is missing a helpful install message is printed and ImportError raised.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Any, Dict, Tuple, List

# Registry: attribute_name -> (module_basename, extras_group, required_package)
_REGISTRY: Dict[str, Tuple[str, str, str]] = {
    "nginx_ops": ("nginx_ops", "nginx", "requests"),
    "docker_ops": ("docker_ops", "docker", "docker"),
    "git_ops": ("git_ops", "git", "gitpython"),
    "ssh_ops": ("ssh_ops", "ssh", "paramiko"),
    "network_ops": ("network_ops", "network", "requests"),
    "interaction": ("interaction_ops", "interaction", "inquirer"),
    "notification": ("notification_ops", "notification", "slack_sdk"),
    "vault_ops": ("vault_ops", "vault", "hvac"),
    "aws_ops": ("aws_ops", "aws", "boto3"),
    "metrics_ops": ("metrics_ops", "metrics", "prometheus_client"),
}

__all__ = list(_REGISTRY.keys())

# Optional pretty console
try:
    from rich.console import Console
    console = Console()
except Exception:
    console = None  # fallback if rich not available


def _install_hint(extra: str, pkg: str) -> str:
    """Return installation hint string for missing dependencies."""
    if extra and extra != pkg.split(" ")[0]:
        return f"poetry install -E {extra}  # or pip install {pkg}"
    return f"poetry add {pkg}  # or pip install {pkg}"


def _load_submodule(name: str) -> ModuleType:
    """Import and return the extras submodule (utils_devops.extras.<name>)."""
    if name not in _REGISTRY:
        raise AttributeError(f"utils_devops.extras has no attribute '{name}'")

    mod_basename, extra_group, req_pkg = _REGISTRY[name]
    fqname = f"utils_devops.extras.{mod_basename}"

    try:
        module = importlib.import_module(fqname)
        globals()[name] = module  # cache for next time

        # ✅ NEW: show nice “module loaded” message
        if console:
            console.log(f"[green][utils_devops.extras] Loaded module:[/green] {name}")
        else:
            print(f"[utils_devops.extras] Loaded module: {name}")

        return module

    except ModuleNotFoundError as e:
        hint = _install_hint(extra_group, req_pkg)
        msg = (
            f"Missing dependency for extras.{name}: {req_pkg}\n"
            f"Install with:\n  {hint}"
        )
        if console:
            console.print(f"[yellow]{msg}[/yellow]")
        else:
            print(msg, file=sys.stderr)
        raise ImportError(msg) from e


def __getattr__(name: str) -> Any:
    """Lazy-load a submodule when accessed via attribute."""
    if name in globals():
        return globals()[name]
    return _load_submodule(name)


def __dir__() -> List[str]:
    return sorted(list(globals().keys()) + list(_REGISTRY.keys()))


def help() -> None:
    """Show available extras and their required packages."""
    rows = [(name, extra, pkg) for name, (_, extra, pkg) in _REGISTRY.items()]
    if console:
        from rich.table import Table
        t = Table(title="utils_devops.extras")
        t.add_column("Module")
        t.add_column("Extra Group")
        t.add_column("Package")
        for r in rows:
            t.add_row(*r)
        console.print(t)
    else:
        print("Available extras:")
        for r in rows:
            print(f" - {r[0]} (extra: {r[1]}, package: {r[2]})")
