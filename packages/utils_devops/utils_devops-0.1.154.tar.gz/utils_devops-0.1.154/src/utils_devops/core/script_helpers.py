"""
Script helpers for utils_devops (script_helpers module).
Utilities for building and running scripts: CLI helpers, retries, progress bars,
file locking, user prompts, notifications, and script lifecycle helpers.
This file includes __all__ and a help() index so IDEs show a clean API surface.
Note: many imports are optional extras (typer, inquirer, slack_sdk, filelock, etc.).
If an optional dependency is missing the module-level functions that require it will
raise a clear error when called; import-time failures should be avoided in production
by installing the extras you need (e.g. `poetry install --with cli,interaction,notify`).
"""
from __future__ import annotations
import contextlib
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Callable, Generator, List, Optional, Dict, Any, Union, Sequence, Tuple
# Optional/extras imports — keep them at module-level since these helpers are extras-driven
try:
    import typer  # extras.cli
except Exception:  # pragma: no cover - optional
    typer = None  # type: ignore
try:
    from tenacity import retry, stop_after_attempt, wait_fixed  # tenacity
except Exception:  # pragma: no cover - optional
    retry = None  # type: ignore
    stop_after_attempt = None  # type: ignore
    wait_fixed = None  # type: ignore
try:
    from rich.progress import Progress, BarColumn, TextColumn  # rich
    from rich.prompt import Prompt, Confirm  # rich for prompts
except Exception:  # pragma: no cover - optional
    Progress = None  # type: ignore
    BarColumn = None  # type: ignore
    TextColumn = None  # type: ignore
    Prompt = None  # type: ignore
    Confirm = None  # type: ignore
try:
    from rich.table import Table  # rich for tables
except Exception:  # pragma: no cover - optional
    Table = None  # type: ignore
try:
    from filelock import FileLock  # extras.advanced
except Exception:  # pragma: no cover - optional
    FileLock = None  # type: ignore
# inquirer (UI) — we import common widgets used across scripts
try:
    # inquirer 3.x provides these names
    from inquirer import prompt as inquirer_prompt, List as InqList, Text as InqText, Checkbox as InqCheckbox, Editor as InqEditor
except Exception:  # pragma: no cover - optional
    inquirer_prompt = None  # type: ignore
    InqList = None  # type: ignore
    InqText = None  # type: ignore
    InqCheckbox = None  # type: ignore
    InqEditor = None  # type: ignore
try:
    from slack_sdk import WebClient  # extras.notify
except Exception:  # pragma: no cover - optional
    WebClient = None  # type: ignore
try:
    from dateutil import parser as date_parser  # extras.advanced
except Exception:  # pragma: no cover - optional
    date_parser = None  # type: ignore
from .logs import get_library_logger, task
from .envs import load_env_file
from .systems import run
from .datetimes import datetime
from .files import backup_file, restore_file, read_file, write_file
from .strings import render_jinja  # For render_block
log = get_library_logger()
__all__ = [
    "ScriptHelpersError",
    "help",
    "allhelps",
    "create_cli_app",
    "parse_args",
    "prompt_user",
    "menu_prompt",
    "prompt_multiline",
    "prompt_editor",
    "retry_func",
    "show_progress",
    "acquire_lock",
    "send_slack_notify",
    "script_main",
    "handle_error",
    "parse_date",
    "run_command_with_log",
    # New: Temp dir and backups
    "with_temp_dir",
    "create_tempdir",
    "backup_many",
    "rollback_backups",
    # New: Cache template helpers (generalized)
    "split_cache_template",
    "render_block",
    # New: Rich table (underutilized dep)
    "create_rich_table",
    # Backwards compatibility exports
    "inquirer_prompt",
    "InqList",
    "InqText",
    "InqCheckbox",
    "InqEditor",
    # New: Interactive & Menu Helpers
    "build_cli_from_menu",
    "create_rich_menu",
    "prompt_with_validation",
    "run_menu_with_hooks",
    "generate_menu_from_commands",
    "interactive_confirm_action",
    "edit_multiline_interactive",
    "setup_interactive_session",
    "run_interactive_menu",
    "edit_file_interactive",
]
class ScriptHelpersError(Exception):
    """Custom exception for script helpers failures."""
    pass
# ========================
# ALL HELPS - Comprehensive Core Package Help
# ========================
def help() -> None:
    """Print a short index of the script_helpers API for interactive use.
    IDEs will pick up `__all__` and function docstrings for completion/help.
    """
    print(
        """
DevOps Utils — Script Helpers Module
Key functions:
ScriptHelpersError: Custom exception for script helpers failures.
help() -> None: Print a short index of the script_helpers API for interactive use.
allhelps() -> None: Print comprehensive help for ALL utils_devops.core modules.
create_cli_app(commands: Dict[str, Callable]) -> "typer.Typer": Create a Typer app with given command name -> callables mapping.
parse_args() -> Dict[str, Any]: Parse simplistic CLI args from sys.argv into a dict.
prompt_user(question: str, type: str = "text", choices: Optional[List[str]] = None, default: Optional[Any] = None) -> Any: Prompt user using inquirer (text, list, checkbox).
menu_prompt(message: str, choices: List[str]) -> str: Show a single-selection menu.
prompt_multiline(default: str = "") -> str: Get multi-line input via inquirer.Editor or fallback.
prompt_editor(default: str = "") -> str: Editor prompt specifically.
retry_func(func: Callable, attempts: int = 3, delay: int = 1) -> Any: Run func with retries using tenacity. Returns the function result.
show_progress(task_desc: str, total: int = 100) -> "Progress": Create and return a rich Progress instance.
acquire_lock(lock_file: str, timeout: int = 10): Context-managed file lock (use `with acquire_lock(path):`).
send_slack_notify(message: str, channel: str, token: Optional[str] = None) -> None: Send a message to Slack using slack_sdk.WebClient.
script_main(main_func: Callable, env_file: Optional[str] = None) -> None: Run main_func loading env_file first (if provided) and wrapping in a task.
handle_error(exc: Exception) -> None: Log and re-raise an exception as ScriptHelpersError.
parse_date(s: str) -> "datetime.datetime": Parse date/time string using python-dateutil if available.
run_command_with_log(cmd: Union[str, List[str]]) -> None: Run a command via systems.run and log the captured stdout/stderr.
with_temp_dir(prefix: str = "utils_devops") -> Generator[Path, None, None]: Context manager for a temporary directory with auto-cleanup.
create_tempdir(prefix: str = "utils_devops") -> str: Create a temp dir and return its path. Use with_temp_dir for auto-cleanup.
backup_many(paths: Sequence[str], backup_dir: str) -> List[Tuple[str, str]]: Backup multiple files to backup_dir, return list of (orig, backup) pairs.
rollback_backups(backups_list: Sequence[Tuple[str, str]]) -> None: Restore files from list of (orig, backup) pairs.
split_cache_template(template_path: str, path_start: str, path_end: str, server_start: str, server_end: str) -> Tuple[Optional[str], Optional[str]]: Extract path and server blocks from template file using markers.
render_block(block: str, **ctx: Any) -> str: Render a string block with Jinja placeholders (e.g., {{SITE}}).
create_rich_table(title: str, columns: List[str]) -> "Table": Create a rich Table for pretty output (e.g., site listings).
build_cli_from_menu(menu_options: Dict[str, Callable], app_name: str = "CLI App") -> typer.Typer: Creates a Typer CLI app where each menu option becomes a command.
create_rich_menu(title: str, choices: List[str], multi_select: bool = False) -> Union[str, List[str]]: Builds and runs a menu using rich.prompt for console apps without inquirer.
prompt_with_validation(prompt_msg: str, validator: Callable[[str], bool], error_msg: str = "Invalid input") -> str: Prompts user with text input and validates response in a loop.
run_menu_with_hooks(menu_func: Callable, pre_hook: Optional[Callable] = None, post_hook: Optional[Callable] = None) -> None: Runs an interactive menu with optional pre/post actions (e.g., load env, cleanup).
generate_menu_from_commands(commands: List[Dict[str, Any]]) -> Dict[str, Callable]: Generates a menu dict from a list of command defs (e.g., [{'name': 'sync', 'func': sync_all, 'desc': 'Sync sites'}]).
interactive_confirm_action(action_desc: str, confirm_prompt: str = "Confirm?") -> bool: Displays action description and prompts for yes/no confirmation with details.
edit_multiline_interactive(default_text: str = "", validator: Optional[Callable[[str], bool]] = None) -> str: Opens an editor for multiline input with optional validation.
setup_interactive_session(require_root: bool = False, env_file: Optional[Path] = None) -> None: Initializes a session with root check and env loading before running menus.
run_interactive_menu(options: Dict[str, Callable], title: str = "Choose action") -> None: Runs a loop with inquirer menu calling functions on selection.
edit_file_interactive(file_path: Path, sync_func: Optional[Callable] = None) -> bool: Edits file with inquirer.Editor, optionally calls sync_func after.
"""
    )
def allhelps() -> None:
    """Print comprehensive help for ALL utils_devops.core modules.
    Initializes logger and calls .help() for: logs, files, systems, strings,
    datetimes, envs, and script_helpers. Use: utils_devops.core.allhelps()
    """
    log.info("=== Help of ALL Core Functions! ===")
    # Logs
    log.info("--- LOGS HELP ---")
    from .logs import help as logs_help
    logs_help()
    log.info("End of logs")
    # Files
    log.info("--- FILES HELP ---")
    from .files import help as files_help
    files_help()
    log.info("End of files")
    # Systems
    log.info("--- SYSTEMS HELP ---")
    from .systems import help as systems_help
    systems_help()
    log.info("End of systems")
    # Strings
    log.info("--- STRINGS HELP ---")
    from .strings import help as strings_help
    strings_help()
    log.info("End of strings")
    # Datetimes
    log.info("--- DATETIMES HELP ---")
    from .datetimes import help as datetimes_help
    datetimes_help()
    log.info("End of datetimes")
    # Envs
    log.info("--- ENVS HELP ---")
    from .envs import help as envs_help
    envs_help()
    log.info("End of envs")
    # Script Helpers (self)
    log.info("--- SCRIPT HELPERS HELP ---")
    help()  # Call our own help()
    log.info("End of script_helpers")
    log.info("=== End of ALL Core Packages ===")
# ========================
# CLI Parsing & App
# ========================
def create_cli_app(commands: Dict[str, Callable]) -> "typer.Typer":
    """Create a Typer app with given command name -> callables mapping.
    Requires the `typer` extra. If typer is not installed this will raise
    ScriptHelpersError with a hint to install the `cli` extra.
    """
    if typer is None:
        raise ScriptHelpersError("typer is not installed. Install extras: poetry install --with cli")
    app = typer.Typer()
    for name, func in commands.items():
        app.command(name)(func)
    log.info(f"Created CLI app with {len(commands)} commands")
    return app
def parse_args() -> Dict[str, Any]:
    """Parse simplistic CLI args from sys.argv into a dict.
    Supports `--key=value` and `--flag` styles.
    """
    args = sys.argv[1:]
    data: Dict[str, Any] = {}
    for arg in args:
        if "=" in arg:
            k, v = arg.split("=", 1)
            data[k.lstrip("-")] = v
        else:
            data[arg.lstrip("-")] = True
    log.debug(f"Parsed args: {data}")
    return data
# ========================
# INQUIRER / PROMPTS (UI)
# ========================
def _require_inquirer():
    if inquirer_prompt is None:
        raise ScriptHelpersError("inquirer is not installed. Install extras: poetry install --with interaction")
def prompt_user(question: str, type: str = "text", choices: Optional[List[str]] = None, default: Optional[Any] = None) -> Any:
    """Prompt user using inquirer.
    type: 'text' | 'list' | 'checkbox' | 'editor'
    choices: required for list/checkbox
    default: default value or default text
    """
    _require_inquirer()
    if type == "text":
        q = [InqText("answer", message=question, default=default or "")]
    elif type == "list":
        if not choices:
            raise ScriptHelpersError("choices required for list prompt")
        q = [InqList("answer", message=question, choices=choices, default=default)]
    elif type == "checkbox":
        if not choices:
            raise ScriptHelpersError("choices required for checkbox prompt")
        q = [InqCheckbox("answer", message=question, choices=choices, default=default)]
    elif type == "editor":
        # Use inquirer Editor for multiline editing when available
        if InqEditor is None:
            # fallback to manual multiline
            return prompt_multiline(default or "")
        q = [InqEditor("answer", message=question, default=default or "")]
    else:
        raise ScriptHelpersError(f"Unsupported prompt type: {type}")
    answers = inquirer_prompt(q)
    result = answers.get("answer") if isinstance(answers, dict) else None
    log.debug(f"User prompt '{question}': {result}")
    return result
def menu_prompt(message: str, choices: List[str], default: Optional[str] = None) -> str:
    """Show a single-selection menu and return the chosen item."""
    _require_inquirer()
    q = [InqList("choice", message=message, choices=choices, default=default)]
    ans = inquirer_prompt(q)
    return ans.get("choice")
def prompt_multiline(default: str = "") -> str:
    """Collect multi-line input from stdin (fallback if no inquirer.Editor)."""
    _require_inquirer()
    # Try Editor if available
    if InqEditor is not None:
        ans = inquirer_prompt([InqEditor("text", message="Enter text (editor)", default=default)])
        return ans.get("text", "")
    # Fallback: simple multi-line input - end on empty line
    print("Enter lines. Submit empty line to finish.")
    if default:
        print("----- current/default -----")
        print(default)
        print("----- edit below -----")
    lines = []
    while True:
        try:
            l = input()
        except EOFError:
            break
        if l == "":
            break
        lines.append(l)
    return "\n".join(lines) if lines else default
def prompt_editor(default: str = "") -> str:
    """Editor prompt specifically. Alias to prompt_user(type='editor')."""
    return prompt_user("Edit text", type="editor", default=default)
# ========================
# Retries & Resilience
# ========================
def retry_func(func: Callable, attempts: int = 3, delay: int = 1) -> Any:
    """Run `func` with retries using tenacity. Returns the function result.
    If tenacity is not installed this will run the function once and return.
    """
    if retry is None:
        # graceful fallback: call once
        try:
            result = func()
            log.info(f"Function {getattr(func, '__name__', str(func))} executed (no tenacity installed)")
            return result
        except Exception as e:
            log.error(f"Function {getattr(func, '__name__', str(func))} failed: {e}")
            raise ScriptHelpersError(f"Function failed: {e}") from e
    @retry(stop=stop_after_attempt(attempts), wait=wait_fixed(delay))
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    try:
        result = wrapper()
        log.info(f"Function {getattr(func, '__name__', str(func))} succeeded after retries")
        return result
    except Exception as e:
        log.error(f"Function {getattr(func, '__name__', str(func))} failed after {attempts} attempts: {e}")
        raise ScriptHelpersError(f"Retry failed: {e}") from e
# ========================
# Progress & UI (rich)
# ========================
def show_progress(task_desc: str, total: int = 100) -> "Progress":
    """Create and return a rich Progress instance.
    If rich is not installed raises ScriptHelpersError.
    """
    if Progress is None or BarColumn is None or TextColumn is None:
        raise ScriptHelpersError("rich is not installed. Install rich to use progress bars")
    progress = Progress(TextColumn("[progress.description]{task.description}"), BarColumn(), "{task.completed}/{task.total}")
    progress.add_task(task_desc, total=total)
    log.info(f"Started progress: {task_desc}")
    return progress
def create_rich_table(title: str, columns: List[str]) -> "Table":
    """Create a rich Table for pretty output (e.g., site listings).
    If rich is not installed raises ScriptHelpersError.
    """
    if Table is None:
        raise ScriptHelpersError("rich is not installed. Install rich to use tables")
    table = Table(title=title)
    for col in columns:
        table.add_column(col)
    log.debug(f"Created rich table: {title}")
    return table
# ========================
# Locking (contextmanager)
# ========================
@contextlib.contextmanager
def acquire_lock(lock_file: str, timeout: int = 10) -> Generator[Any, None, None]:
    """Acquire a file lock and yield the lock object. Use as context manager.
    Requires filelock extra. If not present raises ScriptHelpersError.
    """
    if FileLock is None:
        raise ScriptHelpersError("filelock is not installed. Install extras: poetry install --with advanced")
    lock = FileLock(lock_file, timeout=timeout)
    try:
        lock.acquire()
        log.info(f"Acquired lock: {lock_file}")
        try:
            yield lock
        finally:
            try:
                lock.release()
                log.info(f"Released lock: {lock_file}")
            except Exception:
                log.debug("Lock already released or failed to release")
    except Exception as e:
        log.error(f"Failed acquiring lock {lock_file}: {e}")
        raise
# ========================
# Notifications
# ========================
def send_slack_notify(message: str, channel: str, token: Optional[str] = None) -> None:
    """Send a message to Slack using slack_sdk.WebClient.
    Requires the notify extra or an environment variable SLACK_TOKEN.
    """
    if WebClient is None:
        raise ScriptHelpersError("slack_sdk not installed. Install extras: poetry install --with notify")
    token = token or os.environ.get("SLACK_TOKEN")
    if not token:
        raise ScriptHelpersError("No Slack token provided")
    client = WebClient(token=token)
    try:
        client.chat_postMessage(channel=channel, text=message)
        log.info(f"Sent Slack notify to {channel}: {message}")
    except Exception as e:
        log.error(f"Slack notify failed: {e}")
        raise ScriptHelpersError(f"Slack notify failed: {e}") from e
# ========================
# Temp Dir Management
# ========================
@contextlib.contextmanager
def with_temp_dir(prefix: str = "utils_devops") -> Generator[Path, None, None]:
    """Context manager for a temporary directory with auto-cleanup.
    Wraps tempfile.TemporaryDirectory. Yields Path; cleans up on exit.
    """
    temp_dir = tempfile.TemporaryDirectory(prefix=prefix)
    path = Path(temp_dir.name)
    log.debug(f"Created temp dir: {path}")
    try:
        yield path
    finally:
        temp_dir.cleanup()
        log.debug(f"Cleaned up temp dir: {path}")
def create_tempdir(prefix: str = "utils_devops") -> str:
    """Create a temp dir and return its path. Use with_temp_dir for auto-cleanup."""
    path = tempfile.mkdtemp(prefix=prefix)
    log.info(f"Created temp dir: {path}")
    return path
# ========================
# Backup & Rollback Helpers
# ========================
def backup_many(paths: Sequence[str], backup_dir: str) -> List[Tuple[str, str]]:
    """Backup multiple files to backup_dir, return list of (orig, backup) pairs."""
    backups = []
    Path(backup_dir).mkdir(parents=True, exist_ok=True)
    for p in paths:
        if os.path.exists(p):
            bak = backup_file(p, suffix=os.path.join(backup_dir, os.path.basename(p) + ".bak"))
            backups.append((p, str(bak)))
    log.info(f"Backed up {len(backups)} files to {backup_dir}")
    return backups
def rollback_backups(backups_list: Sequence[Tuple[str, str]]) -> None:
    """Restore files from list of (orig, backup) pairs."""
    for orig, bak in backups_list:
        if os.path.exists(bak):
            restore_file(orig, bak)
    log.info(f"Rolled back {len(backups_list)} files")
# ========================
# Cache Template Helpers
# ========================
def split_cache_template(
    template_path: str,
    path_start: str,
    path_end: str,
    server_start: str,
    server_end: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Extract path and server blocks from template file using markers.
    Returns (path_block, server_block) or (None, None) if missing.
    """
    content = read_file(template_path)
    path_match = re.search(rf"{re.escape(path_start)}([\s\S]*?){re.escape(path_end)}", content)
    server_match = re.search(rf"{re.escape(server_start)}([\s\S]*?){re.escape(server_end)}", content)
    path_block = path_match.group(1).strip() if path_match else None
    server_block = server_match.group(1).strip() if server_match else None
    if path_block and server_block:
        log.debug(f"Extracted blocks from {template_path}")
    else:
        log.warning(f"Missing markers in {template_path}")
    return path_block, server_block
def render_block(block: str, **ctx: Any) -> str:
    """Render a string block with Jinja placeholders (e.g., {{SITE}})."""
    try:
        rendered = render_jinja(block, ctx)
        log.debug(f"Rendered block: {rendered}")
        return rendered
    except Exception as e:
        log.error(f"Render block failed: {e}")
        raise ScriptHelpersError(f"Render block failed: {e}") from e
# ========================
# Script Lifecycle
# ========================
def script_main(main_func: Callable, env_file: Optional[str] = None) -> None:
    """Run `main_func` loading env_file first (if provided) and wrapping in a task.
    Exits the process with status 1 on unhandled exceptions.
    """
    if env_file:
        load_env_file(env_file)
    try:
        with task("Main script"):
            main_func()
    except Exception as e:
        handle_error(e)
        sys.exit(1)
def handle_error(exc: Exception) -> None:
    """Log and re-raise an exception as ScriptHelpersError."""
    log.error(f"Script error: {exc}")
    raise ScriptHelpersError(f"Script error: {exc}") from exc
# ========================
# Utilities
# ========================
def parse_date(s: str) -> "datetime.datetime":
    """Parse date/time string using python-dateutil if available."""
    if date_parser is None:
        raise ScriptHelpersError("python-dateutil is not installed. Install extras: poetry install --with advanced")
    dt = date_parser.parse(s)
    log.debug(f"Parsed date '{s}': {dt}")
    return dt
def run_command_with_log(cmd: Union[str, List[str]]) -> None:
    """Run a command via systems.run and log the captured stdout/stderr."""
    res = run(cmd)
    # CompletedProcess-like may vary; be defensive
    out = getattr(res, "stdout", None)
    err = getattr(res, "stderr", None)
    if out:
        log.info(f"Command '{cmd}' STDOUT:\n{out}")
    if err:
        log.warning(f"Command '{cmd}' STDERR:\n{err}")
# ========================
# Interactive & Menu Helpers
# ========================
def build_cli_from_menu(menu_options: Dict[str, Callable], app_name: str = "CLI App") -> typer.Typer:
    """Creates a Typer CLI app where each menu option becomes a command. Input: menu_options (dict of "Description" -> function), app_name (str for app help). Output: typer.Typer (ready-to-run CLI app). Rationale: Automates converting interactive menus to CLI for dual-mode scripts; simplifies usage by allowing non-interactive runs, enhancing accuracy with Typer's arg parsing."""
    if typer is None:
        raise ScriptHelpersError("typer is not installed. Install extras: poetry install --with cli")
    app = typer.Typer(name=app_name, help=app_name)
    for desc, func in menu_options.items():
        command_name = re.sub(r'\W+', '_', desc.lower())
        app.command(command_name, help=desc)(func)
    log.info(f"Created CLI app '{app_name}' with {len(menu_options)} commands")
    return app

def create_rich_menu(title: str, choices: List[str], multi_select: bool = False) -> Union[str, List[str]]:
    """Builds and runs a menu using rich.prompt for console apps without inquirer. Input: title (str), choices (list of str), multi_select (bool for checkbox-like). Output: str or List[str] (selected item(s)). Rationale: Provides a fallback or alternative to inquirer for richer, terminal-friendly menus; automates pretty printing, making interactive scripts simpler and more accurate without external deps."""
    if Prompt is None:
        raise ScriptHelpersError("rich is not installed. Install rich to use rich menus")
    print(title)
    for i, choice in enumerate(choices, 1):
        print(f"{i}. {choice}")
    if not multi_select:
        sel = Prompt.ask("Select number", choices=[str(i) for i in range(1, len(choices) + 1)])
        return choices[int(sel) - 1]
    else:
        sels = Prompt.ask("Select numbers (comma separated)")
        idxs = [int(s.strip()) - 1 for s in sels.split(",") if s.strip().isdigit()]
        return [choices[i] for i in idxs if 0 <= i < len(choices)]

def prompt_with_validation(prompt_msg: str, validator: Callable[[str], bool], error_msg: str = "Invalid input") -> str:
    """Prompts user with text input and validates response in a loop. Input: prompt_msg (str), validator (callable returning bool), error_msg (str). Output: str (valid input). Rationale: Enhances accuracy by automating input checks (e.g., for site names or upstreams in your add_site_interactive); simplifies robust prompting without manual loops."""
    while True:
        if Prompt:
            response = Prompt.ask(prompt_msg)
        else:
            response = input(prompt_msg + ": ")
        if validator(response):
            return response
        print(error_msg)

def run_menu_with_hooks(menu_func: Callable, pre_hook: Optional[Callable] = None, post_hook: Optional[Callable] = None) -> None:
    """Runs an interactive menu with optional pre/post actions (e.g., load env, cleanup). Input: menu_func (callable for menu loop), pre_hook (optional callable), post_hook (optional callable). Output: None. Rationale: Automates lifecycle around menus (like your ensure_root_or_sudo before terminal); improves simplicity for wrapped interactive modes."""
    if pre_hook:
        pre_hook()
    try:
        menu_func()
    finally:
        if post_hook:
            post_hook()

def generate_menu_from_commands(commands: List[Dict[str, Any]]) -> Dict[str, Callable]:
    """Generates a menu dict from a list of command defs (e.g., [{'name': 'sync', 'func': sync_all, 'desc': 'Sync sites'}]). Input: commands (list of dicts with 'name', 'func', 'desc'). Output: Dict[str, Callable] (menu-ready options). Rationale: Simplifies building dynamic menus from existing functions; automates menu creation for modular scripts like yours."""
    return {cmd['desc']: cmd['func'] for cmd in commands}

def interactive_confirm_action(action_desc: str, confirm_prompt: str = "Confirm?") -> bool:
    """Displays action description and prompts for yes/no confirmation with details. Input: action_desc (str), confirm_prompt (str). Output: bool (True if confirmed). Rationale: Ports and generalizes your ask_yes_no in remove_site; enhances accuracy with descriptive confirmations, automating safe interactions."""
    print(action_desc)
    if Confirm:
        return Confirm.ask(confirm_prompt)
    else:
        while True:
            resp = input(confirm_prompt + " (y/n): ").lower()
            if resp in ['y', 'n']:
                return resp == 'y'
            print("Invalid input, please enter y or n.")

def edit_multiline_interactive(default_text: str = "", validator: Optional[Callable[[str], bool]] = None) -> str:
    """Opens an editor for multiline input with optional validation. Input: default_text (str), validator (optional callable). Output: str (edited text). Rationale: Builds on prompt_multiline; automates config-like edits (e.g., for sites.txt lines) with checks, simplifying complex inputs like your flags in add_site."""
    while True:
        if InqEditor:
            ans = inquirer_prompt([InqEditor("text", message="Edit text", default=default_text)])
            text = ans.get("text", "")
        else:
            with tempfile.NamedTemporaryFile(suffix=".tmp", mode="w+", delete=False) as tf:
                tf.write(default_text)
                tf.flush()
                editor = os.environ.get('EDITOR', 'vi')
                os.system(f"{editor} {tf.name}")
                with open(tf.name, 'r') as f:
                    text = f.read()
            os.unlink(tf.name)
        if not validator or validator(text):
            return text
        print("Invalid input, please edit again.")

def setup_interactive_session(require_root: bool = False, env_file: Optional[Path] = None) -> None:
    """Initializes a session with root check and env loading before running menus. Input: require_root (bool), env_file (optional Path). Output: None. Rationale: Automates setup like your terminal (ensure_root_or_sudo + potential env); makes starting interactive modes simpler and more consistent."""
    if env_file:
        load_env_file(str(env_file))
    if require_root and os.getuid() != 0:
        raise ScriptHelpersError("This session requires root privileges.")

def run_interactive_menu(options: Dict[str, Callable], title: str = "Choose action") -> None:
    """Runs a loop with inquirer menu calling functions on selection. Input: options (dict of "Description" -> function), title (str). Output: None. Rationale: Generalizes your interactive_terminal for reusable menus."""
    while True:
        if inquirer_prompt:
            choices = list(options.keys()) + ["Exit"]
            q = [InqList("action", message=title, choices=choices)]
            ans = inquirer_prompt(q)
            sel = ans.get("action")
            if sel == "Exit":
                break
            options[sel]()
        else:
            # Fallback without inquirer
            print(title)
            descs = list(options.keys())
            for i, desc in enumerate(descs, 1):
                print(f"{i}. {desc}")
            print("0. Exit")
            sel = input("Select: ")
            if sel == "0":
                break
            try:
                idx = int(sel) - 1
                if 0 <= idx < len(descs):
                    list(options.values())[idx]()
                else:
                    print("Invalid selection")
            except ValueError:
                print("Invalid input")

def edit_file_interactive(file_path: Path, sync_func: Optional[Callable] = None) -> bool:
    """Edits file with inquirer.Editor, optionally calls sync_func after. Input: file_path (Path), sync_func (optional callable). Output: bool (True if changed). Rationale: Ports your edit_sites_file_interactive for config edits with sync."""
    original = read_file(str(file_path))
    new_text = edit_multiline_interactive(default_text=original)
    changed = new_text != original
    if changed:
        write_file(str(file_path), new_text)
        if sync_func:
            sync_func()
    return changed