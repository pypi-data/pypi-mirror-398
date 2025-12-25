"""
Logger module for utils_devops
Provides a friendly, IDE-helpful logging wrapper with:
- Rich terminal output when available
- Rotating file logging when configured
- Task/context buffering (task, task_start, task_pass, task_fail)
- Convenience top-level functions (info, debug, task, etc.)
- Support for internal library logs via get_library_logger(), shown only when level="TRACE"

This file is intentionally documented and typed to improve IDE completion and
`help()`/introspection display for `utils_devops.core.logger` and modules that
import `get_logger()`.
"""
from __future__ import annotations
import io
import logging
import os
import subprocess
import sys
import threading
import time
import traceback
import atexit
import inspect
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Iterator, Dict, Any, Union, List
from datetime import datetime
# Rich is optional but preferred for prettier console output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.theme import Theme
    _HAS_RICH = True
except Exception:
    _HAS_RICH = False
# Bring CompletedProcess into the namespace for typing and IDE convenience
from subprocess import CompletedProcess
# Defaults (tune in module or when calling init_logger)
_DEFAULT_LOG_FILE: Optional[str] = None
_DEFAULT_LEVEL = "INFO"
_DEFAULT_MAX_BYTES = 5 * 1024 * 1024
_DEFAULT_BACKUP_COUNT = 3
# Module-level script lifecycle state (shared across instances)
_script_started = False
_script_ended = False
_script_start_times: Dict[str, float] = {}
# Public API names for IDEs / help()
__all__ = [
    "DevopsLogger",
    "init_logger",
    "get_logger",
    "get_library_logger",
    "debug",
    "info",
    "warn",
    "warning",
    "error",
    "exception",
    "task",
    "task_start",
    "task_pass",
    "task_fail",
    "run_command",
    "run_and_log",
    "script_start",
    "script_end",
]
def help() -> None:
    """Print a quick index of available functions and usage for this module.
    This function exists primarily for interactive use (REPL / debugging).
    """
    print(
        """
Logger Module - AI Function Index
Initialization
init_logger(name: str = "utils_devops", level: str = "DEBUG", log_file: Optional[str] = None,
color: str = "auto", console: bool = True, max_bytes: int = 510241024,
backup_count: int = 3, verbose: bool = False) -> DevopsLogger: Initialize global logger.
Note: level="TRACE" enables internal library logs (via get_library_logger()) at DEBUG level.
Get Loggers
get_logger() -> DevopsLogger: Get the main logger for scripts/main use.
get_library_logger() -> Any: Get a wrapper for internal library logs (hidden unless level="TRACE").
Core Logging
debug(msg: str, *a: Any, **k: Any) -> None: Log debug message.
info(msg: str, *a: Any, **k: Any) -> None: Log info message.
warn(msg: str, *a: Any, **k: Any) -> None: Log warning (backwards-compatible alias).
warning(msg: str, *a: Any, **k: Any) -> None: Log warning message.
error(msg: str, *a: Any, **k: Any) -> None: Log error message.
exception(msg: str, *a: Any, exc_info: Any = True, **k: Any) -> None: Log error with traceback.
Task Management (Context + Manual)
task(name: str, live: bool = False, hide_on_success: bool = True) -> ContextManager: Buffer output, show concise on success.
task_start(name: str) -> str: Start manual task, return name.
task_pass(name: str, hide_on_success: bool = True) -> None: Mark task success.
task_fail(name: str, exc: Optional[BaseException] = None) -> None: Mark task failure.
Command Execution
run_command(cmd: Union[List[str], str], name: Optional[str] = None, shell: bool = False,
live: Optional[bool] = None, hide_on_success: bool = True, check: bool = False,
cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None,
timeout: Optional[int] = None, *a: Any, **k: Any) -> CompletedProcess: Run command in task buffer.
run_and_log(cmd: Union[List[str], str], shell: bool = False, live: Optional[bool] = None, check: bool = False,
cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None,
timeout: Optional[int] = None, *a: Any, **k: Any) -> CompletedProcess: Run with streaming output.
Script Lifecycle
script_start(name: Optional[str] = None) -> str: Print start banner, record time.
script_end(name: Optional[str] = None) -> None: Print end banner with duration.
Convenience (no get_logger() needed)
debug, info, warn, warning, error, exception, task, task_start, task_pass, task_fail,
run_command, run_and_log, script_start, script_end: Direct callable shortcuts.
Critical Notes
Use .warn() or .warning(), this module exposes both.
Task output is buffered; use live=True or verbose=True to show immediately.
log_file=None disables file logging even if env var set.
Color: "auto" detects TTY, honors FORCE_COLOR/NO_COLOR.
Rich used if available and color enabled.
Internal logs (via get_library_logger()) are only shown if init_logger(level="TRACE").
"""
    )
def _is_tty() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False
def _color_enabled(mode: str = "auto") -> bool:
    mode = (mode or "auto").lower()
    if mode == "on":
        return True
    if mode == "off":
        return False
    if os.environ.get("FORCE_COLOR", "").lower() in ("1", "true", "yes"):
        return True
    if "NO_COLOR" in os.environ:
        return False
    if _HAS_RICH:
        try:
            c = Console()
            return bool(getattr(c, "is_terminal", _is_tty()))
        except Exception:
            pass
    return _is_tty()
class _TaskRecord:
    """Internal: holds buffer and start time for manual tasks."""
    def __init__(self, name: str) -> None:
        self.name = name
        self.start = time.time()
        self.io = io.StringIO()
class DevopsLogger:
    """Main logger implementation.
    Provides both a programmatic API (methods) and buffered "task" context
    manager for grouping output. Initialize with :func:`init_logger`.
    """
    _instance: Optional["DevopsLogger"] = None
    def __init__(
        self,
        name: str = "utils_devops",
        level: str = _DEFAULT_LEVEL,
        log_file: Optional[str] = _DEFAULT_LOG_FILE,
        color: str = "auto",
        console: bool = True,
        max_bytes: int = _DEFAULT_MAX_BYTES,
        backup_count: int = _DEFAULT_BACKUP_COUNT,
        verbose: bool = False,
    ) -> None:
        # allow reinit: shutdown previous instance silently
        if DevopsLogger._instance is not None:
            try:
                DevopsLogger._instance._shutdown()
            except Exception:
                pass
        self.name = name
        self.verbose = bool(verbose)
        self.color_mode = color or "auto"
        # decide whether to use rich for pretty consoles
        self._use_rich = _HAS_RICH and _color_enabled(self.color_mode)
        self._console: Optional[Console] = None
        if self._use_rich:
            theme = Theme(
                {
                    "info": "green",
                    "debug": "cyan",
                    "warn": "yellow",
                    "error": "bold red",
                    "success": "bold green",
                }
            )
            force = (os.environ.get("FORCE_COLOR", "") != "") or (str(color or "").lower() == "on")
            try:
                self._console = Console(force_terminal=force, color_system="auto", markup=True, theme=theme)
            except TypeError:
                self._console = Console(color_system="auto", markup=True, theme=theme)
        # Handle special "TRACE" level for internal logs
        level_upper = level.upper()
        self.show_internal = False
        if level_upper == "TRACE":
            level_upper = "DEBUG"
            self.show_internal = True
        # underlying file logger
        self._logger = logging.getLogger(name)
        log_level = getattr(logging, level_upper, logging.INFO)
        self._logger.setLevel(log_level)
        for h in list(self._logger.handlers):
            try:
                self._logger.removeHandler(h)
            except Exception:
                pass
        self.log_file = log_file
        if self.log_file is None:
            env_val = os.environ.get("DEVOPS_UTILS_LOG", None)
            if env_val:
                resolved = env_val.strip()
                self.log_file = resolved if resolved else None
            else:
                self.log_file = _DEFAULT_LOG_FILE if _DEFAULT_LOG_FILE else None
        if self.log_file:
            try:
                print("======= Logs Store in", (Path.cwd() / (str(self.log_file))).resolve(), " ========\n")
                log_path = Path(os.path.expanduser(str(self.log_file)))
                if not log_path.is_absolute():
                    log_path = (Path.cwd() / log_path).resolve()
                log_path.parent.mkdir(parents=True, exist_ok=True)
                log_path.touch(exist_ok=True)
                fh = RotatingFileHandler(str(log_path), maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
                fh.setLevel(logging.DEBUG)
                fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
                self._logger.addHandler(fh)
            except Exception as e:
                print(f"Warning: Failed to set up file logging to {self.log_file}: {e}", file=sys.stderr)
                self.log_file = None
        # internal state
        self._task_lock = threading.RLock()
        self._manual_tasks: Dict[str, _TaskRecord] = {}
        self._active_buffer: Optional[io.StringIO] = None
        # script lifecycle detection and registration
        global _script_started, _script_ended, _script_start_times
        try:
            main_mod = sys.modules.get("__main__")
            main_file = getattr(main_mod, "__file__", None)
            if main_file:
                main_path = Path(main_file).resolve()
                if main_path != Path(__file__).resolve():
                    script_name = main_path.name
                    try:
                        if not _script_started:
                            self.script_start(script_name)
                            _script_started = True
                        if not _script_ended:
                            atexit.register(lambda name=script_name: get_logger().script_end(name))
                            _script_ended = True
                    except Exception:
                        pass
        except Exception:
            pass
        if _script_started:
            time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._log_file("info", f"*** START_SCRIPT *** : {script_name} at {time_now} ")
        DevopsLogger._instance = self
    def warning(self, msg: str, *a: Any, **k: Any) -> None:
        self.warn(msg, *a, **k)
    def _shutdown(self) -> None:
        """Cleanly remove handlers and reset singleton."""
        try:
            for h in list(self._logger.handlers):
                try:
                    self._logger.removeHandler(h)
                    try:
                        h.close()
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass
        try:
            DevopsLogger._instance = None
        except Exception:
            pass
    def _write_console(self, text: str, style: Optional[str] = None) -> None:
        """Write a line to console (rich if available)."""
        if self._use_rich and self._console:
            if style:
                self._console.print(Text(text, style=style))
            else:
                try:
                    if "[" in text and "]" in text:
                        self._console.print(Text.from_markup(text))
                    else:
                        self._console.print(text)
                except Exception:
                    print(text)
        else:
            print(text)
    def _write_buffer(self, text: str) -> None:
        """Append a plain text line to the current active buffer (if any)."""
        if self._active_buffer is not None:
            self._active_buffer.write(text + "\n")
            self._active_buffer.flush()
    def _log_file(self, level: str, msg: str) -> None:
        """Persist message to the rotating file logger at appropriate level."""
        if level == "debug":
            self._logger.debug(msg)
        elif level == "info":
            self._logger.info(msg)
        elif level == "warn":
            self._logger.warning(msg)
        elif level == "error":
            self._logger.error(msg)
        else:
            self._logger.info(msg)
    # public logging methods
    def debug(self, msg: str, *a: Any, **k: Any) -> None:
        is_internal = k.pop('internal', False)
        if is_internal and not self.show_internal:
            return
        if self._logger.isEnabledFor(logging.DEBUG):
            self._write_console(msg, style="debug" if self._use_rich else None)
            self._write_buffer(f"DEBUG | {msg}")
        self._log_file("debug", msg)
    def info(self, msg: str, *a: Any, **k: Any) -> None:
        is_internal = k.pop('internal', False)
        if is_internal and not self.show_internal:
            return
        if self._logger.isEnabledFor(logging.INFO):
            self._write_console(msg, style="info" if self._use_rich else None)
            self._write_buffer(f"INFO | {msg}")
        self._log_file("info", msg)
    def warn(self, msg: str, *a: Any, **k: Any) -> None:
        """Backward-compatible alias for warning-level messages (public API).
        Use this method in user code for parity with other devops tools.
        """
        is_internal = k.pop('internal', False)
        if is_internal and not self.show_internal:
            return
        if self._logger.isEnabledFor(logging.WARNING):
            self._write_console(msg, style="warn" if self._use_rich else None)
            self._write_buffer(f"WARN | {msg}")
        self._log_file("warn", msg)
    def error(self, msg: str, *a: Any, **k: Any) -> None:
        is_internal = k.pop('internal', False)
        if is_internal and not self.show_internal:
            return
        if self._logger.isEnabledFor(logging.ERROR):
            self._write_console(msg, style="error" if self._use_rich else None)
            self._write_buffer(f"ERROR | {msg}")
        self._log_file("error", msg)
    def exception(self, msg: str, *a: Any, exc_info: Any = True, **k: Any) -> None:
        """Log an exception message and full traceback to file/buffer/console."""
        is_internal = k.pop('internal', False)
        if is_internal and not self.show_internal:
            return
        if self._logger.isEnabledFor(logging.ERROR):
            self._write_console(msg, style="error" if self._use_rich else None)
        self._log_file("error", msg)
        tb = traceback.format_exc()
        if self._logger.isEnabledFor(logging.ERROR):
            self._write_buffer(f"EXC | {msg}")
            self._write_buffer(tb)
        self._log_file("error", tb)
    @contextmanager
    def task(self, name: str, *, live: bool = False, hide_on_success: bool = True) -> Iterator[None]:
        """Context manager to buffer output for a task and print concise summary on success.
        Args:
            name: arbitrary task name shown to the user
            live: if True, stream buffered lines to console as they arrive
            hide_on_success: if True and the buffer is empty the detailed buffer is hidden on success
        """
        start = time.time()
        with self._task_lock:
            prev_buffer = self._active_buffer
            buf = io.StringIO()
            self._active_buffer = buf
            if self._use_rich:
                self._write_console(f"[blue]>>>[/blue] START: {name}")
            else:
                self._write_console(f">>> START: {name}")
            self._write_buffer(f">>> START: {name}")
            self._log_file("info", f"START: {name}")
            try:
                yield
                elapsed = time.time() - start
                pretty = self._format_duration(elapsed)
                contents = buf.getvalue().rstrip()
                if contents:
                    if live or self.verbose or not hide_on_success:
                        self._print_task_summary(name, pretty, contents, succeeded=True)
                    else:
                        if self._use_rich:
                            self._write_console(f"[blue]>>>[/blue] [green]✔[/green] {name} [blue][{pretty}][/blue]")
                        else:
                            self._write_console(f">>> ✔ {name} [{pretty}]")
                else:
                    if self._use_rich:
                        self._write_console(f"[blue]>>>[/blue] [green]✔[/green] {name} [blue][{pretty}][/blue]")
                    else:
                        self._write_console(f">>> ✔ {name} [{pretty}]")
                self._log_file("info", f"PASS: {name} [{pretty}]")
            except Exception as exc:
                elapsed = time.time() - start
                pretty = self._format_duration(elapsed)
                contents = buf.getvalue().rstrip()
                if self._use_rich:
                    self._write_console(f"[blue]>>>[/blue] [red]✖[/red] {name} [blue][{pretty}][/blue]", style="error")
                else:
                    self._write_console(f">>> ✖ {name} [{pretty}]")
                if contents:
                    self._print_task_summary(name, pretty, contents, succeeded=False)
                tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                self._write_buffer(tb)
                self._log_file("error", f"FAIL: {name} [{pretty}]\n{contents}\n{tb}")
                raise
            finally:
                self._active_buffer = prev_buffer
    def task_start(self, name: str) -> str:
        with self._task_lock:
            rec = _TaskRecord(name)
            self._manual_tasks[name] = rec
            if self._use_rich:
                self._write_console(f"[blue]>>>[/blue] START: {name}")
            else:
                self._write_console(f">>> START: {name}")
            self._log_file("info", f"START: {name}")
            return name
    def task_pass(self, name: str, *, hide_on_success: bool = True) -> None:
        with self._task_lock:
            rec = self._manual_tasks.pop(name, None)
            if rec is None:
                self._write_console(f"task_pass called for unknown task '{name}'")
                return
            elapsed = time.time() - rec.start
            pretty = self._format_duration(elapsed)
            contents = rec.io.getvalue().rstrip()
            if contents:
                if self.verbose or not hide_on_success:
                    self._print_task_summary(name, pretty, contents, succeeded=True)
                else:
                    if self._use_rich:
                        self._write_console(f"[blue]>>>[/blue] [green]✔[/green] {name} [blue][{pretty}][/blue]")
                    else:
                        self._write_console(f">>> ✔ {name} [{pretty}]")
            else:
                if self._use_rich:
                    self._write_console(f"[blue]>>>[/blue] [green]✔[/green] {name} [blue][{pretty}][/blue]")
                else:
                    self._write_console(f">>> ✔ {name} [{pretty}]")
            self._log_file("info", f"PASS: {name} [{pretty}]")
    def task_fail(self, name: str, exc: Optional[BaseException] = None) -> None:
        with self._task_lock:
            rec = self._manual_tasks.pop(name, None)
            if rec is None:
                self._write_console(f"task_fail called for unknown task '{name}'")
                return
            elapsed = time.time() - rec.start
            pretty = self._format_duration(elapsed)
            contents = rec.io.getvalue().rstrip()
            if self._use_rich:
                self._write_console(f"[blue]>>>[/blue] [red]✖[/red] {name} [blue][{pretty}][/blue]", style="error")
            else:
                self._write_console(f">>> ✖ {name} [{pretty}]")
            if contents:
                self._print_task_summary(name, pretty, contents, succeeded=False)
            if exc is not None:
                tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                self._write_console(tb)
                self._log_file("error", f"FAIL: {name} [{pretty}]\n{contents}\n{tb}")
            else:
                self._log_file("error", f"FAIL: {name} [{pretty}]\n{contents}")
    def script_start(self, name: Optional[str] = None) -> str:
        if name is None:
            name = self.name
        start_ts = time.time()
        _script_start_times[name] = start_ts
        human_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = f"start of script ({name}) ({human_ts}) "
        line = f"{'='*8} {title} {'='*14}"
        if self._use_rich:
            self._write_console(f"[blue]{line}[/blue]")
        else:
            self._write_console(line)
        self._log_file("info", f"*** START_SCRIPT *** : {name} at {human_ts}")
        return name
    def script_end(self, name: Optional[str] = None) -> None:
        if name is None:
            name = self.name
        start_ts = _script_start_times.pop(name, None)
        end_ts = time.time()
        human_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if start_ts is None:
            pretty = "?"
        else:
            pretty = self._format_duration(end_ts - start_ts)
        title = f"end of script ({name}) ({human_ts}) [{pretty}]"
        line = f"{'='*8} {title} {'='*8}"
        if self._use_rich:
            self._write_console(f"[blue]{line}[/blue]")
        else:
            self._write_console(line)
        self._log_file("info", f"*** END_SCRIPT *** : {name} at {human_ts} elapsed {pretty} \n\n")
    def _print_task_summary(self, name: str, pretty: str, buffer_contents: str, succeeded: bool) -> None:
        title = f"{'✔' if succeeded else '✖'} {name} [{pretty}]"
        if self._use_rich and self._console:
            panel_title = Text(title, style="bold green" if succeeded else "bold red")
            panel = Panel(buffer_contents, title=panel_title, expand=True)
            self._console.print(panel)
        else:
            sep = "=" * (len(title) + 4)
            self._write_console(sep)
            self._write_console(f" {title} ")
            self._write_console(sep)
            for line in buffer_contents.splitlines():
                self._write_console(line)
            self._write_console(sep)
    def run_and_log(
        self,
        cmd: Union[List[str], str],
        *,
        shell: bool = False,
        live: Optional[bool] = None,
        check: bool = False,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> CompletedProcess:
        live = self.verbose if live is None else live
        if isinstance(cmd, str) and not shell:
            cmd_list = cmd.split()
        else:
            cmd_list = cmd if isinstance(cmd, list) else [cmd]
        proc = subprocess.Popen(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
            shell=shell,
            text=True,
            bufsize=1,
        )
        def _reader(stream, level: str = "info"):
            for raw in iter(stream.readline, ""):
                if raw == "":
                    break
                line = raw.rstrip("\n")
                if live:
                    if level == "info":
                        self.info(line)
                    else:
                        self.warn(line)
                else:
                    if self._active_buffer is not None:
                        self._active_buffer.write(f"{line}\n")
                        self._active_buffer.flush()
                    else:
                        if level == "info":
                            self.info(line)
                        else:
                            self.warn(line)
        t_out = threading.Thread(target=_reader, args=(proc.stdout, "info"))
        t_err = threading.Thread(target=_reader, args=(proc.stderr, "warn"))
        t_out.daemon = True
        t_err.daemon = True
        t_out.start()
        t_err.start()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise
        t_out.join()
        t_err.join()
        completed = subprocess.CompletedProcess(args=cmd_list, returncode=proc.returncode)
        if check and proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd_list)
        return completed
    def run_command(
        self,
        cmd: Union[List[str], str],
        *,
        name: Optional[str] = None,
        shell: bool = False,
        live: Optional[bool] = None,
        hide_on_success: bool = True,
        check: bool = False,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> CompletedProcess:
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        short_name = name or (cmd_str if len(cmd_str) <= 60 else cmd_str[:57] + "...")
        live = self.verbose if live is None else live
        with self.task(short_name, live=live, hide_on_success=hide_on_success):
            self.info(f"EXEC: {cmd_str}")
            result = self.run_and_log(cmd, shell=shell, live=live, check=False, cwd=cwd, env=env, timeout=timeout)
            if result.returncode != 0 and check:
                raise subprocess.CalledProcessError(result.returncode, result.args)
            return result
    @staticmethod
    def _format_duration(seconds: float) -> str:
        sec = int(round(seconds))
        if sec < 60:
            return f"{sec}s"
        mins, s = divmod(sec, 60)
        if mins < 60:
            return f"{mins}m {s}s"
        hrs, m = divmod(mins, 60)
        if hrs < 24:
            return f"{hrs}h {m}m {s}s"
        days, h = divmod(hrs, 24)
        return f"{days}d {h}h {m}m {s}s"
  
# ---------------- module-level helpers ----------------
_global_logger: Optional[DevopsLogger] = None
def init_logger(
    *,
    name: str = "utils_devops",
    level: str = _DEFAULT_LEVEL,
    log_file: Optional[str] = _DEFAULT_LOG_FILE,
    color: str = "auto",
    console: bool = True,
    max_bytes: int = _DEFAULT_MAX_BYTES,
    backup_count: int = _DEFAULT_BACKUP_COUNT,
    verbose: bool = False,
) -> DevopsLogger:
    """Initialize the global logger and return it.
    This function always reinitializes the global logger with the provided options.
    Note: level="TRACE" enables internal library logs (via get_library_logger()) at DEBUG level.
    """
    global _global_logger
    _global_logger = DevopsLogger(
        name=name,
        level=level,
        log_file=log_file,
        color=color,
        console=console,
        max_bytes=max_bytes,
        backup_count=backup_count,
        verbose=verbose,
    )
    return _global_logger
def get_logger() -> DevopsLogger:
    """Return the global DevopsLogger, initializing it with defaults if necessary."""
    global _global_logger
    if _global_logger is None:
        _global_logger = init_logger()
    return _global_logger
def get_library_logger():
    """Return a wrapper around the global DevopsLogger for internal library logs.
    Logs from this are hidden unless init_logger(level="TRACE").
    """
    main_logger = get_logger()
    class LibraryLoggerWrapper:
        def __init__(self, logger: DevopsLogger):
            self._logger = logger

        def __getattr__(self, name: str):
            attr = getattr(self._logger, name)
            if callable(attr):
                def wrapper(*args, **kwargs):
                    if name in ['debug', 'info', 'warn', 'warning', 'error', 'exception']:
                        kwargs['internal'] = True
                    return attr(*args, **kwargs)
                return wrapper
            return attr
    return LibraryLoggerWrapper(main_logger)
# ---------------- convenience shortcuts (no get_logger() required) ----------------
def debug(msg: str, *a: Any, **k: Any) -> None:
    """Shortcut to global logger.debug()"""
    get_logger().debug(msg, *a, **k)
def info(msg: str, *a: Any, **k: Any) -> None:
    """Shortcut to global logger.info()"""
    get_logger().info(msg, *a, **k)
def warn(msg: str, *a: Any, **k: Any) -> None:
    """Shortcut to global logger.warn (keeps public API stable)."""
    get_logger().warn(msg, *a, **k)
def warning(msg: str, *a: Any, **k: Any) -> None:
    """Shortcut to global logger.warn() (standard logging alias)."""
    get_logger().warn(msg, *a, **k)
def error(msg: str, *a: Any, **k: Any) -> None:
    """Shortcut to global logger.error()"""
    get_logger().error(msg, *a, **k)
def exception(msg: str, *a: Any, exc_info: Any = True, **k: Any) -> None:
    """Shortcut to log exception with traceback."""
    get_logger().exception(msg, *a, exc_info=exc_info, **k)
def task(name: str, *, live: bool = False, hide_on_success: bool = True):
    """Return context manager for a short-lived task (use with `with`)."""
    return get_logger().task(name, live=live, hide_on_success=hide_on_success)
def task_start(name: str) -> str:
    """Start a manual task and return its name/handle."""
    return get_logger().task_start(name)
def task_pass(name: str, *, hide_on_success: bool = True) -> None:
    """Mark manual task as passed."""
    return get_logger().task_pass(name, hide_on_success=hide_on_success)
def task_fail(name: str, exc: Optional[BaseException] = None) -> None:
    """Mark manual task as failed and optionally print exception traceback."""
    return get_logger().task_fail(name, exc=exc)
def run_command(*a: Any, **k: Any) -> CompletedProcess:
    """Helper to run a command in a task buffer (delegates to DevopsLogger.run_command)."""
    return get_logger().run_command(*a, **k)
def run_and_log(*a: Any, **k: Any) -> CompletedProcess:
    """Helper to run command with live logging (delegates to DevopsLogger.run_and_log)."""
    return get_logger().run_and_log(*a, **k)
def script_start(name: Optional[str] = None) -> str:
    """Convenience: mark script start (calls global logger)."""
    return get_logger().script_start(name)
def script_end(name: Optional[str] = None) -> None:
    """Convenience: mark script end (calls global logger)."""
    return get_logger().script_end(name)