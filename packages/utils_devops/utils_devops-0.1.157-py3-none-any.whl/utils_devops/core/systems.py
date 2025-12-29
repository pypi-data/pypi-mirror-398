"""
System Operations Module
... (docstring kept as before; trimmed here for brevity)
"""
from __future__ import annotations
import os
import sys
import platform
import subprocess
import shutil
import time
import socket
import getpass
import threading
import ctypes  # For Windows admin check
from typing import Optional, List, Dict, Union, Any, Callable, Tuple
from rich.console import Console
from rich.prompt import Prompt, Confirm
from .logs import get_library_logger  # Adjust if different
try:
    from tenacity import retry, stop_after_attempt, wait_fixed
except ImportError:
    retry = None
    stop_after_attempt = None
    wait_fixed = None
import venv
import psutil  # required dependency
logger = get_library_logger()
DEFAULT_LOGGER = logger
console = Console()
DEFAULT_SYSTEM_TIMEZONE = "Asia/Tehran"  # Change this to your preferred default
# cached sudo password living in process memory only
_SUDO_PASSWORD: Optional[str] = None
# Public API for IDEs / help()
__all__ = [
    "help",
    # Environment Detection
    "is_windows",
    "is_linux",
    "is_docker",
    "is_root",
    # Process Management
    "check_process_running",
    "kill_process",
    # Waiting Functions
    "wait_for_file",
    "wait_for_port",
    "wait_command_success",
    "retry_cmd",
    # Port Operations
    "check_port_open",
    # User Interaction
    "ask_yes_no",
    "prompt_input",
    "ask_password",
    "confirm_action",
    "ask_choice_list",
    # Command Execution
    "run",
    "exec",
    # Sudo helpers
    "set_sudo_password",
    "clear_sudo_password",
    # Access & Elevation
    "command_exists",
    # Package Management
    "install_chocolatey",
    "install_package",
    "add_apt_repository",
    # Version & Location
    "find_command_location",
    "get_command_version",
    # System Metrics
    "get_cpu_usage",
    "get_memory_info",
    "get_disk_usage",
    # PowerShell (Windows)
    "run_powershell",
    # Utilities
    "list_directory_recursive",
    "readlink_f",
    # Timezone helpers
    "set_system_timezone",
    "get_system_timezone",
    "setup_tehran_timezone",
    # Service Reload
    "reload_service",
    # constants
    "DEFAULT_SYSTEM_TIMEZONE",
    # New additions
    "schedule_task",
    "validate_system_command",
    "run_with_retry",
    "get_system_metrics",
    "isolate_env_for_run",
    "manage_service_advanced",
    "monitor_process",
    "ensure_sudo_privileges",
    "with_root_check",
    "fix_permissions",
    # Wrappers
    "safe_run",
    "get_password",
    "path_exists",
]
# ---------------------
# Helper / help
# ---------------------
def help() -> None:
    """Print a brief index of available functions in this module."""
    print(
    """
    System Operations Module - Usage Reference
    ==========================================
    Environment Detection
    ---------------------
    is_windows() -> bool
        Return True if running on Windows OS.
    is_linux() -> bool
        Return True if running on Linux OS.
    is_docker() -> bool
        Return True if running inside a Docker container (Linux only).
    is_root() -> bool
        Return True if process has administrative/root privileges.
    Process Management
    ------------------
    check_process_running(pattern: str) -> bool
        Check if any running process name or command line contains `pattern`.
    kill_process(pattern: str) -> None
        Kill all processes matching `pattern`. Raises ValueError if none found.
    Waiting Functions
    -----------------
    wait_for_file(file_path: str, timeout: int = 30) -> bool
        Wait up to `timeout` seconds for a file to appear. Return True if found.
    wait_for_port(host: str = "localhost", port: int = 80, timeout: int = 30) -> bool
        Wait up to `timeout` seconds for a TCP port to become open.
    wait_command_success(cmd: str, retries: int = 5, delay: int = 1) -> None
        Retry running a shell command until success or retries exhausted.
    retry_cmd = wait_command_success
        Alias for `wait_command_success`.
    Port Operations
    ----------------
    check_port_open(host: str = "localhost", port: int = 80) -> bool
        Return True if port is open on given host.
    User Interaction
    ----------------
    ask_yes_no(prompt: str = "Confirm (y/n)?") -> bool
        Prompt user with yes/no question. Return True for “yes”.
    prompt_input(prompt: str = "Enter:") -> str
        Ask user for text input. Return entered string.
    ask_password(prompt: str = "Password:") -> str
        Ask for password securely (no echo). Return entered string.
    confirm_action(action_desc: str) -> None
        Warn user about an action and ask confirmation. Raise RuntimeError if cancelled.
    ask_choice_list(prompt: str, options: list[str]) -> str
        Display numbered list of `options` and return chosen one.
    Command Execution
    -----------------
    run(
        cmd: str | list[str],
        shell: bool | None = None,
        cwd: PathLike | None = None,
        env: dict[str, str] | None = None,
        no_die: bool = False,
        dry_run: bool = False,
        elevated: bool = False,
        capture: bool = True
    ) -> subprocess.CompletedProcess
        Run a command safely with logging, optional sudo/UAC elevation, and output capture.
        - If elevated=True: will use cached sudo password or prompt once.
        - Returns CompletedProcess with .stdout, .stderr, .returncode.
    exec(
        cmd: str | list[str],
        shell: bool | None = None,
        cwd: PathLike | None = None,
        env: dict[str, str] | None = None,
        no_die: bool = False,
        dry_run: bool = False,
        elevated: bool = False,
        capture: bool = True,
        show_output: bool = True
    ) -> subprocess.CompletedProcess
        Same as `run()` but prints command, stdout, stderr, and return code nicely.
    Access & Elevation
    ------------------
    command_exists(cmd: str) -> bool
        Return True if command is found in system PATH.
    Package Management
    ------------------
    install_chocolatey() -> None
        Install Chocolatey on Windows if not already installed.
    install_package(package_name: str, update_first: bool = True) -> None
        Install package via apt (Linux) or Chocolatey (Windows).
    add_apt_repository(repo: str, update_after: bool = True) -> None
        Add an APT repository (Linux). Optionally run `apt update` after.
    Version & Location
    ------------------
    find_command_location(cmd: str) -> str | None
        Return full path to command, or None if not found.
    get_command_version(cmd: str) -> str | None
        Return command version output if available.
    readlink_f(path: str) -> str
        Resolve all symlinks and return canonical absolute path.
    System Metrics
    --------------
    get_cpu_usage() -> float
        Return current system CPU usage percentage.
    get_memory_info() -> dict
        Return memory stats: {"total", "available", "used", "percent"}.
    get_disk_usage(path: str = "/") -> dict
        Return disk stats for given path: {"total", "used", "free", "percent"}.
    PowerShell (Windows)
    --------------------
    run_powershell(cmd: str, elevated: bool = False) -> int
        Execute PowerShell command. Return exit code.
    Utilities
    ---------
    list_directory_recursive(path: str = ".", detailed: bool = False) -> None
        Recursively list directory tree. Show permissions/sizes if detailed=True.
    System Timezone
    ---------------
    set_system_timezone(tz: str | None = None, confirm: bool = True) -> None
        Set system timezone (default: Asia/Tehran). Uses `timedatectl` or fallback link.
    get_system_timezone() -> str
        Return current system timezone as string.
    setup_tehran_timezone(confirm: bool = True) -> None
        Shortcut to set timezone to Asia/Tehran.
    Service Management
    ------------------
    reload_service(service_cmd: str | list[str], test_cmd: str | list[str]) -> bool
        Run `test_cmd`, and if success, reload service with `service_cmd`.
        Return True if both succeed, False otherwise.
    Constants
    ---------
    DEFAULT_SYSTEM_TIMEZONE = "Asia/Tehran"
        Default timezone used in all system timezone functions.
    schedule_task(cmd: Union[str, List[str]], interval: str = "daily", use_cron: bool = True) -> None: Schedules a command to run at intervals (using cron on Linux or Task Scheduler on Windows).
    validate_system_command(cmd: str, check_output: bool = True) -> Tuple[bool, str]: Checks if a command exists and optionally runs it with --version or similar for validation.
    run_with_retry(cmd: Union[str, List[str]], retries: int = 3, delay: int = 5, **run_kwargs: Any) -> CompletedProcess: Runs a command with automatic retries on failure using tenacity.
    get_system_metrics(include_cpu: bool = True, include_memory: bool = True, include_disk: bool = True) -> Dict[str, Any]: Collects system metrics (CPU, memory, disk) in one call.
    isolate_env_for_run(cmd: Union[str, List[str]], virtual_env_path: Optional[Path] = None) -> CompletedProcess: Runs a command in an isolated virtual env (creates if needed).
    manage_service_advanced(service_name: str, action: str = "restart", validate_first: bool = True) -> bool: Handles service actions (start/stop/restart) with optional pre-validation.
    monitor_process(pattern: str, timeout: int = 60, check_interval: int = 5) -> bool: Monitors if a process matching pattern starts/stops within timeout.
    ensure_sudo_privileges(prompt: bool = True) -> bool: Prompts for sudo password if not root and validates.
    with_root_check(func: Callable, require_root: bool = True) -> Callable: Decorator to ensure root/sudo before calling func.
    fix_permissions(path: Union[str, Path], mode: int = 0o644, owner: str = "root:root", recursive: bool = False) -> None: Sets mode and owner (using chown/chmod).
    safe_run: Alias for run (subprocess wrapper).
    get_password: Alias for ask_password (getpass wrapper).
    path_exists: Wrapper for os.path.exists.
    """
    )
# -------------------------------------------------
# Secure sudo / elevation handling (improved)
# -------------------------------------------------
def clear_sudo_password() -> None:
    """Erase the cached sudo password from memory (public)."""
    global _SUDO_PASSWORD
    _SUDO_PASSWORD = None
    logger.debug("Cleared cached sudo password.")
def set_sudo_password(pw: str) -> None:
    """Set the sudo password programmatically (for automation/testing)."""
    global _SUDO_PASSWORD
    _SUDO_PASSWORD = pw
    logger.debug("Sudo password set programmatically (in-memory only).")
def _get_sudo_password(prompt: str = "Enter sudo password: ") -> str:
    """
    Ask for the sudo password once per process (cached in-memory).
    Will not re-prompt unless the cache has been cleared (clear_sudo_password()).
    Note: the password is kept only in process memory and never written to disk.
    """
    global _SUDO_PASSWORD
    if _SUDO_PASSWORD is None:
        # loop to avoid accidental empty password entry, but only a couple tries
        pw = getpass.getpass(prompt)
        # Accept empty password if user enters it explicitly (some sudo setups allow it),
        # but warn so user understands risks.
        if pw == "":
            logger.warning("Empty sudo password entered (are you sure?).")
        _SUDO_PASSWORD = pw
    else:
        logger.debug("Using cached sudo password.")
    return _SUDO_PASSWORD
# ========================
# Command Execution
# ========================
def run(
    cmd: Union[str, List[str]],
    *,
    shell: Optional[bool] = None,
    cwd: Optional[os.PathLike] = None,
    env: Optional[Dict[str, str]] = None,
    no_die: bool = False,
    dry_run: bool = False,
    elevated: bool = False,
    capture: bool = True,
    logger: Optional[logger] = None,
    stream: bool = False
) -> subprocess.CompletedProcess:
    """
    Robust run() with cross-platform threaded streaming + smart carriage-return handling.

    - stream=True : streams output in real-time using threads, understands '\r' updates.
    - capture controls whether stdout/stderr are returned in CompletedProcess (when stream=True,
      capture=True will also collect into strings).
    - If streaming fails for any reason we fallback to communicate() to collect remaining output.
    - Works on Linux and Windows.
    """
    logger = logger or DEFAULT_LOGGER

    if shell is None:
        shell = isinstance(cmd, str)

    # Normalize command forms
    if isinstance(cmd, (list, tuple)):
        cmd_str = subprocess.list2cmdline(cmd)
        cmd_list: Union[List[str], str] = list(cmd)
    else:
        cmd_str = str(cmd)
        cmd_list = cmd_str if shell else [cmd_str]

    if dry_run:
        logger.info(f"[DRY-RUN] {cmd_str}")
        return subprocess.CompletedProcess(cmd_list if not shell else cmd_str, 0, stdout="", stderr="")

    stdin_input: Optional[str] = None
    use_list: Union[List[str], str] = cmd_list

    # Determine platform
    try:
        is_win = (is_windows())
    except NameError:
        is_win = (os.name == "nt") or sys.platform.startswith("win")

    # Handle elevated
    if elevated:
        if is_win:
            # Windows: use Start-Process via powershell RunAs
            ps = f"Start-Process -Verb RunAs -FilePath powershell -ArgumentList '-NoProfile','-Command','{cmd_str}' -Wait -PassThru"
            use_list = ["powershell", "-NoProfile", "-Command", ps]
            shell = False
        else:
            # Unix: attempt to get cached sudo password via user-provided helper
            try:
                pw = _get_sudo_password()
            except NameError:
                raise RuntimeError("elevated=True requested but _get_sudo_password() is not implemented in the environment.")
            if isinstance(cmd, (list, tuple)):
                base_list = list(cmd)
            else:
                base_list = [cmd_str] if shell else [cmd_str]
            use_list = ["sudo", "-S"] + base_list
            stdin_input = (pw + "\n") if pw is not None else None
            shell = False

    # Log final command (avoid logging sensitive data)
    try:
        if isinstance(use_list, list):
            logger.debug(f"Executing (list): {' '.join(use_list)}")
        else:
            logger.debug(f"Executing (shell): {use_list}")

        proc = subprocess.Popen(
            use_list if not shell else (cmd_str),
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=subprocess.PIPE if (capture or stream) else None,
            stderr=subprocess.PIPE if (capture or stream) else None,
            stdin=subprocess.PIPE if stdin_input is not None else None,
            text=True,
            shell=shell,
            bufsize=1,
            universal_newlines=True,
        )

        # Send sudo password if needed
        if stdin_input is not None and proc.stdin:
            try:
                proc.stdin.write(stdin_input)
                proc.stdin.flush()
                proc.stdin.close()
            except Exception:
                try:
                    proc.stdin.close()
                except Exception:
                    pass

        # Output collectors
        stdout_lines: List[str] = []
        stderr_lines: List[str] = []

        # --- Smart threaded streaming implementation ---
        def _smart_reader(pipe, log_func, collector: Optional[List[str]], stop_event: threading.Event):
            """
            Read from pipe in chunks, handle '\r' (line replace) and '\n' (new line).
            Appends to collector (if provided) and logs via log_func.
            """
            try:
                buffer = ""
                last_rendered = None  # used to avoid repeated identical logs for \r updates

                # We'll read in reasonably-sized chunks. read() will block, but on separate thread that's fine.
                while not stop_event.is_set():
                    chunk = pipe.read(1024)
                    if not chunk:
                        # EOF reached
                        break
                    buffer += chunk

                    # Process as long as there's control chars
                    while True:
                        # find next control char indices
                        idx_n = buffer.find("\n")
                        idx_r = buffer.find("\r")

                        if idx_n == -1 and idx_r == -1:
                            break

                        # Which control comes first?
                        if idx_r != -1 and (idx_n == -1 or idx_r < idx_n):
                            # Carriage return: replace current line
                            line = buffer[:idx_r]
                            buffer = buffer[idx_r + 1:]
                            # Only log if changed (avoids spamming identical updates)
                            if line != last_rendered:
                                # strip trailing CR/LF but preserve internal whitespace
                                to_log = line.rstrip("\r\n")
                                try:
                                    log_func(to_log)
                                except Exception:
                                    # logging should not raise to user
                                    pass
                                if collector is not None:
                                    collector.append(line + ("\n" if collector is not None else ""))
                                last_rendered = line
                        else:
                            # Newline: finalize this line
                            line = buffer[:idx_n]
                            buffer = buffer[idx_n + 1:]
                            to_log = line.rstrip("\r\n")
                            try:
                                log_func(to_log)
                            except Exception:
                                pass
                            if collector is not None:
                                collector.append(line + "\n")
                            last_rendered = None

                # Flush whatever remains in buffer
                if buffer:
                    buf_strip = buffer.rstrip("\r\n")
                    if buf_strip:
                        try:
                            log_func(buf_strip)
                        except Exception:
                            pass
                        if collector is not None:
                            collector.append(buffer)
                # close pipe
                try:
                    pipe.close()
                except Exception:
                    pass
            except Exception as exc:
                # Ensure we don't crash the thread; bubble up via logging
                logger.exception(f"stream reader error: {exc}")
                try:
                    pipe.close()
                except Exception:
                    pass
                # re-raise to let outer context know (we'll catch in caller via threads status)
                raise

        rc = None
        if stream and (proc.stdout is not None or proc.stderr is not None):
            logger.info("Streaming command output...")
            stop_event = threading.Event()
            threads: List[threading.Thread] = []
            stream_exception = None

            # Start threads
            try:
                if proc.stdout:
                    t_out = threading.Thread(
                        target=_smart_reader,
                        args=(proc.stdout, logger.info, stdout_lines if capture else None, stop_event),
                        daemon=True
                    )
                    t_out.start()
                    threads.append(t_out)

                if proc.stderr:
                    t_err = threading.Thread(
                        target=_smart_reader,
                        args=(proc.stderr, logger.warning, stderr_lines if capture else None, stop_event),
                        daemon=True
                    )
                    t_err.start()
                    threads.append(t_err)

                # Wait for process while allowing KeyboardInterrupt
                try:
                    rc = proc.wait()
                except KeyboardInterrupt:
                    logger.debug("KeyboardInterrupt caught: terminating child process")
                    stop_event.set()
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    # wait a bit then force kill
                    try:
                        proc.wait(timeout=2)
                    except Exception:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                    rc = proc.returncode if proc.returncode is not None else -1

            except Exception as exc:
                # If any exception occurs while starting/monitoring threads -> fallback
                stream_exception = exc
                logger.exception(f"Streaming failed, falling back to communicate(): {exc}")
            finally:
                # Signal threads to stop and join
                stop_event.set()
                for t in threads:
                    t.join(timeout=1)

            # If streaming had exception, fallback to communicate to collect remaining output safely.
            if stream_exception is not None:
                try:
                    # communicate will return remaining output that reader threads didn't capture
                    comm_out, comm_err = proc.communicate(timeout=5)
                except Exception:
                    try:
                        # best-effort: kill and read whatever
                        proc.kill()
                    except Exception:
                        pass
                    try:
                        comm_out, comm_err = proc.communicate(timeout=5)
                    except Exception:
                        comm_out, comm_err = ("", "")
                # append remaining to collectors if capture True
                if capture:
                    if comm_out:
                        stdout_lines.append(comm_out)
                    if comm_err:
                        stderr_lines.append(comm_err)
                # set rc if not set
                if rc is None:
                    rc = proc.returncode if proc.returncode is not None else 0

            # Compose final stdout/stderr
            stdout = "".join(stdout_lines) if capture else ""
            stderr = "".join(stderr_lines) if capture else ""
            if rc is None:
                rc = proc.returncode if proc.returncode is not None else 0

        else:
            # original behavior: blocking wait & capture (or not)
            try:
                stdout, stderr = proc.communicate()
            except Exception as exc:
                # if communicate fails, try to kill and fallback
                logger.exception(f"proc.communicate() failed: {exc}")
                try:
                    proc.kill()
                except Exception:
                    pass
                try:
                    stdout, stderr = proc.communicate(timeout=5)
                except Exception:
                    stdout, stderr = ("", "")
            rc = proc.returncode

        # Build CompletedProcess result
        result = subprocess.CompletedProcess(
            use_list if not shell else cmd_str,
            rc,
            stdout=stdout or "",
            stderr=stderr or "",
        )

        # Post-run handling & sudo auth checks (Unix)
        if rc == 0:
            logger.info(f"Command succeeded (rc={rc})")
        else:
            if elevated and not is_win:
                lowerr = (stderr or "").lower()
                auth_tokens = [
                    "incorrect password",
                    "authentication failure",
                    "authentication token manipulation error",
                    "sorry,",
                    "sudo: 1 incorrect password attempt",
                    "sudo: a password is required",
                    "pam_authenticate",
                ]
                if any(tok in lowerr for tok in auth_tokens):
                    try:
                        clear_sudo_password()
                    except NameError:
                        logger.error("sudo authentication failed and clear_sudo_password() not implemented.")
                    else:
                        logger.error("sudo authentication failed. Cached sudo password cleared.")
                    raise subprocess.CalledProcessError(rc, use_list if not shell else cmd_str, output=stdout, stderr=stderr)
            logger.error(f"Command failed (rc={rc}) – { (stderr or '').strip() }")

        if rc != 0 and not no_die:
            raise subprocess.CalledProcessError(rc, use_list if not shell else cmd_str, output=stdout, stderr=stderr)

        return result

    except subprocess.CalledProcessError:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error running command: {e}")
        raise

# -------------------------------------------------
# Exec helper – shows command + output + logs
# -------------------------------------------------
def exec(
    cmd: Union[str, List[str]],
    *,
    shell: Optional[bool] = None,
    cwd: Optional[os.PathLike] = None,
    env: Optional[Dict[str, str]] = None,
    no_die: bool = False,
    dry_run: bool = False,
    elevated: bool = False,
    capture: bool = True,
    show_output: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run a command and show output.
    - If `cmd` is **str** → runs in shell (like bash)
    - If `cmd` is **list** → runs safely (no shell)
    - `shell=True` only when needed
    """
    # Auto-detect shell mode
    if shell is None:
        shell = isinstance(cmd, str)
    # Forward to run()
    result = run(
        cmd,
        shell=shell,
        cwd=cwd,
        env=env,
        no_die=no_die,
        dry_run=dry_run,
        elevated=elevated,
        capture=capture,
    )
    # Show output
    if not dry_run and show_output:
        cmd_str = cmd if isinstance(cmd, str) else subprocess.list2cmdline(cmd)
        console.print(f"\n[bold cyan]>>> {cmd_str}[/bold cyan]")
        if result.stdout:
            console.print(f"[green]STDOUT:[/green]\n{result.stdout.rstrip()}")
        if result.stderr:
            console.print(f"[red]STDERR:[/red]\n{result.stderr.rstrip()}")
        rc_color = "green" if result.returncode == 0 else "red"
        console.print(f"[{rc_color}]Return code: {result.returncode}[/{rc_color}]\n")
    return result
# ========================
# Section: System Timezone Management
# (unchanged except forwarded to run)
# ========================
def set_system_timezone(tz: Optional[str] = None, confirm: bool = True) -> None:
    if tz is None:
        tz = DEFAULT_SYSTEM_TIMEZONE
        logger.info(f"Using default timezone: {tz}")
    if confirm:
        confirm_action(f"change system timezone to {tz}")
    if is_windows():
        win_name = "Iran Standard Time" if tz == "Asia/Tehran" else tz.replace("/", " ")
        cmd = ["tzutil", "/s", win_name]
    else:
        if command_exists("timedatectl"):
            cmd = ["timedatectl", "set-timezone", tz]
        else:
            cmd = ["ln", "-sf", f"/usr/share/zoneinfo/{tz}", "/etc/localtime"]
    run(cmd, elevated=True)
    logger.info(f"System timezone set to: {tz}")
def get_system_timezone() -> str:
    try:
        if is_windows():
            res = run(["tzutil", "/g"], capture=True)
            return res.stdout.strip().strip('"')
        else:
            if command_exists("timedatectl"):
                res = run(
                    ["timedatectl", "show", "--property=Timezone", "--value"],
                    capture=True,
                )
                return res.stdout.strip()
            else:
                try:
                    with open("/etc/timezone", "r") as f:
                        return f.read().strip()
                except FileNotFoundError:
                    try:
                        link = os.readlink("/etc/localtime")
                        return link.split("zoneinfo/")[-1]
                    except Exception:
                        return "Unknown"
    except Exception as e:
        logger.warning(f"Failed to read system timezone: {e}")
        return "Unknown"
def setup_tehran_timezone(confirm: bool = True) -> None:
    set_system_timezone(tz=DEFAULT_SYSTEM_TIMEZONE, confirm=confirm)
# ========================
# Environment Detection
# ========================
def is_windows() -> bool:
    return platform.system() == "Windows"
def is_linux() -> bool:
    return platform.system() == "Linux"
def is_docker() -> bool:
    if not is_linux():
        return False
    try:
        with open("/proc/1/cgroup", "r") as f:
            content = f.read()
            return "docker" in content or "/docker/" in content
    except Exception as e:
        logger.debug(f"Failed to check Docker: {e}")
        return False
def is_root() -> bool:
    if is_windows():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception as e:
            logger.debug(f"Failed to check admin on Windows: {e}")
            return False
    else:
        return os.getuid() == 0
# ========================
# Process Management (psutil)
# ========================
def check_process_running(pattern: str) -> bool:
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        cmdline = " ".join(proc.info.get("cmdline") or [])
        name = proc.info.get("name") or ""
        if pattern in name or pattern in cmdline:
            return True
    return False
def kill_process(pattern: str) -> None:
    killed = False
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        cmdline = " ".join(proc.info.get("cmdline") or [])
        name = proc.info.get("name") or ""
        if pattern in name or pattern in cmdline:
            try:
                proc.kill()
                killed = True
            except psutil.NoSuchProcess:
                pass
            except Exception as e:
                logger.error(f"Failed to kill process {proc.pid}: {e}")
                raise
    if not killed:
        raise ValueError(f"No process matching '{pattern}' found to kill.")
# ========================
# Waiting Functions
# ========================
def wait_for_file(file_path: str, timeout: int = 30) -> bool:
    start = time.time()
    while not os.path.exists(file_path):
        if time.time() - start > timeout:
            logger.error(f"Timeout waiting for file: {file_path}")
            return False
        time.sleep(1)
    logger.info(f"File appeared: {file_path}")
    return True
def wait_for_port(host: str = "localhost", port: int = 80, timeout: int = 30) -> bool:
    start = time.time()
    while not check_port_open(host, port):
        if time.time() - start > timeout:
            logger.error(f"Timeout waiting for {host}:{port}")
            return False
        time.sleep(1)
    logger.info(f"Port open: {host}:{port}")
    return True
def wait_command_success(cmd: str, retries: int = 5, delay: int = 1) -> None:
    for attempt in range(1, retries + 1):
        try:
            subprocess.check_call(cmd, shell=True)
            logger.info(f"Command succeeded on attempt {attempt}: {cmd}")
            return
        except subprocess.CalledProcessError as e:
            logger.warning(f"Attempt {attempt} failed: {cmd} (rc={e.returncode})")
            time.sleep(delay)
    raise RuntimeError(f"Command failed after {retries} retries: {cmd}")
retry_cmd = wait_command_success
# ========================
# Port / User / Package / Utilities / Metrics / Service Reload
# (unchanged from prior implementation except small logging tweaks)
# ========================
def check_port_open(host: str = "localhost", port: int = 80) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    finally:
        sock.close()
def ask_yes_no(prompt: str = "Confirm (y/n)?") -> bool:
    return Confirm.ask(f"[magenta]{prompt}[/magenta]")
def prompt_input(prompt: str = "Enter:") -> str:
    return Prompt.ask(f"[magenta]{prompt}[/magenta]")
def ask_password(prompt: str = "Password:") -> str:
    console.print(f"[magenta]{prompt}[/magenta]", end=" ")
    return getpass.getpass("")
def confirm_action(action_desc: str) -> None:
    logger.warning(f"About to {action_desc}. Continue?")
    if not ask_yes_no():
        raise RuntimeError("Action cancelled by user.")
def ask_choice_list(prompt: str = "Choose:", options: Optional[List[str]] = None) -> str:
    if options is None:
        options = []
    for i, opt in enumerate(options, 1):
        console.print(f"{i}) {opt}")
    choice = Prompt.ask(f"[magenta]{prompt}[/magenta]")
    if choice.isdigit() and 1 <= int(choice) <= len(options):
        return options[int(choice) - 1]
    raise ValueError("Invalid choice.")
def command_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None
def install_chocolatey() -> None:
    if not is_windows():
        raise NotImplementedError("Chocolatey is for Windows only.")
    if command_exists("choco"):
        logger.info("Chocolatey already installed.")
        return
    ps_cmd = "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    run(f"powershell -Command \"{ps_cmd}\"", elevated=True)
    logger.info("Chocolatey installed.")
def install_package(package_name: str, update_first: bool = True) -> None:
    if is_windows():
        install_chocolatey()
        run(f"choco install {package_name} -y", elevated=True)
    elif is_linux():
        if update_first:
            run("apt update", elevated=True)
        run(f"apt install {package_name} -y", elevated=True)
    else:
        raise NotImplementedError("Unsupported OS for package installation.")
def add_apt_repository(repo: str, update_after: bool = True) -> None:
    if not is_linux():
        raise NotImplementedError("APT repositories are for Linux only.")
    run(f"add-apt-repository {repo} -y", elevated=True)
    if update_after:
        run("apt update", elevated=True)
def find_command_location(cmd: str) -> Optional[str]:
    return shutil.which(cmd)
def get_command_version(cmd: str) -> Optional[str]:
    if not command_exists(cmd):
        return None
    try:
        res = run([cmd, "--version"], capture=True)
        return res.stdout.strip()
    except Exception as e:
        logger.debug(f"Failed to get version for {cmd}: {e}")
        return None
def readlink_f(path: str) -> str:
    try:
        real_path = os.path.realpath(path)
        logger.debug(f"Resolved path {path} to {real_path}")
        return real_path
    except Exception as e:
        logger.error(f"Failed to resolve path {path}: {e}")
        raise RuntimeError(f"Failed to resolve path {path}: {e}") from e
def list_directory_recursive(path: str = ".", detailed: bool = False) -> None:
    for root, dirs, files in os.walk(path):
        console.print(f"{root}:")
        if detailed:
            total_size = 0
            for name in dirs + files:
                full = os.path.join(root, name)
                try:
                    stat = os.stat(full)
                    mode = oct(stat.st_mode)[-4:]  # Simplified permissions
                    size = stat.st_size
                    total_size += size if os.path.isfile(full) else 0
                    console.print(f"{mode} {size:8} {name}")
                except Exception as e:
                    console.print(f"Error accessing {name}: {e}")
            console.print(f"total {total_size}")
        else:
            for name in dirs + files:
                console.print(name)
        console.print("")
def get_cpu_usage() -> float:
    return psutil.cpu_percent(interval=1)
def get_memory_info() -> Dict[str, Union[int, float]]:
    mem = psutil.virtual_memory()
    return {"total": mem.total, "available": mem.available, "used": mem.used, "percent": mem.percent}
def get_disk_usage(path: str = "/") -> Dict[str, Union[int, float]]:
    disk = psutil.disk_usage(path)
    return {"total": disk.total, "used": disk.used, "free": disk.free, "percent": disk.percent}
def run_powershell(cmd: str, elevated: bool = False) -> int:
    if not is_windows():
        raise NotImplementedError("PowerShell is for Windows only.")
    ps_cmd = f"powershell -Command \"{cmd}\""
    res = run(ps_cmd, elevated=elevated)
    return res.returncode
def reload_service(service_cmd: Union[List[str], str], test_cmd: Union[List[str], str]) -> bool:
    logger.info(f"Testing with: {test_cmd}")
    try:
        test_res = run(test_cmd, capture=True, no_die=True)
        if test_res.returncode != 0:
            logger.error(f"Test failed (rc={test_res.returncode}): {test_res.stderr.strip()}")
            return False
        logger.info("Test succeeded.")
        logger.info(f"Reloading with: {service_cmd}")
        reload_res = run(service_cmd, elevated=True, capture=True)
        if reload_res.returncode == 0:
            logger.info("Reload succeeded.")
            return True
        else:
            logger.error(f"Reload failed (rc={reload_res.returncode}): {reload_res.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"Reload process failed: {e}")
        return False
# ========================
# New Functions
# ========================
def schedule_task(cmd: Union[str, List[str]], interval: str = "daily", use_cron: bool = True) -> None:
    """Schedules a command to run at intervals (using cron on Linux or Task Scheduler on Windows). Input: cmd (str or list for command), interval (str like "daily", "hourly", or cron syntax), use_cron (bool to prefer cron). Output: None. Rationale: Automates routine tasks like your log rotation or backups; improves simplicity for cron-like setups without manual config, ensuring accuracy with platform detection."""
    cmd_str = cmd if isinstance(cmd, str) else ' '.join(cmd)
    if is_linux() and use_cron:
        # Map interval to cron syntax
        cron_map = {
            "daily": "0 0 * * *",
            "hourly": "0 * * * *",
            "weekly": "0 0 * * 0",
            "monthly": "0 0 1 * *",
        }
        cron_expr = cron_map.get(interval, interval)  # Use custom if not mapped
        cron_line = f"{cron_expr} {cmd_str}\n"
        current_cron = run("crontab -l", capture=True, no_die=True).stdout
        if cron_line not in current_cron:
            new_cron = current_cron + cron_line
            run(f"echo '{new_cron}' | crontab -", shell=True, elevated=True)
        logger.info(f"Scheduled cron task: {cmd_str}")
    elif is_windows():
        # Map interval to schtasks frequency
        freq_map = {
            "daily": "DAILY",
            "hourly": "HOURLY",
            "weekly": "WEEKLY",
            "monthly": "MONTHLY",
        }
        frequency = freq_map.get(interval, "DAILY")
        task_name = f"DevOpsTask_{hash(cmd_str) % 10000}"
        run(f"schtasks /create /tn {task_name} /tr \"{cmd_str}\" /sc {frequency}", elevated=True)
        logger.info(f"Scheduled Windows task: {cmd_str}")
    else:
        raise NotImplementedError("Scheduling not supported on this OS")

def validate_system_command(cmd: str, check_output: bool = True) -> Tuple[bool, str]:
    """Checks if a command exists and optionally runs it with --version or similar for validation. Input: cmd (str command name), check_output (bool to test execution). Output: Tuple[bool, str] (success, message/output). Rationale: Enhances accuracy by pre-validating commands before run (e.g., for nginx -t); automates error-prone checks, simplifying safe exec in scripts."""
    if not command_exists(cmd):
        return False, f"Command not found: {cmd}"
    if check_output:
        try:
            res = run([cmd, "--version"], capture=True, no_die=True)
            if res.returncode == 0:
                return True, res.stdout.strip()
            else:
                return False, res.stderr.strip()
        except Exception as e:
            return False, str(e)
    return True, "Command exists"

def run_with_retry(cmd: Union[str, List[str]], retries: int = 3, delay: int = 5, **run_kwargs: Any) -> subprocess.CompletedProcess:
    """Runs a command with automatic retries on failure using tenacity. Input: cmd (str or list), retries (int), delay (int in seconds), **run_kwargs (passed to run). Output: CompletedProcess. Rationale: Automates resilient system calls (e.g., service reloads that might flake); improves accuracy in unstable envs, making ops like your manage_service simpler and more reliable."""
    if retry is None:
        logger.warning("tenacity not installed; running without retry")
        return run(cmd, **run_kwargs)
    @retry(stop=stop_after_attempt(retries), wait=wait_fixed(delay))
    def wrapped_run():
        return run(cmd, **run_kwargs)
    return wrapped_run()

def get_system_metrics(include_cpu: bool = True, include_memory: bool = True, include_disk: bool = True) -> Dict[str, Any]:
    """Collects system metrics (CPU, memory, disk) in one call. Input: include_cpu (bool), include_memory (bool), include_disk (bool). Output: Dict[str, Any] (metrics dict). Rationale: Builds on get_cpu_usage etc.; automates monitoring for DevOps dashboards or logs, simplifying holistic system checks with accurate, aggregated data."""
    metrics = {}
    if include_cpu:
        metrics["cpu"] = get_cpu_usage()
    if include_memory:
        metrics["memory"] = get_memory_info()
    if include_disk:
        metrics["disk"] = get_disk_usage()
    return metrics

def isolate_env_for_run(cmd: Union[str, List[str]], virtual_env_path: Optional[os.PathLike] = None) -> subprocess.CompletedProcess:
    """Runs a command in an isolated virtual env (creates if needed). Input: cmd (str or list), virtual_env_path (optional Path). Output: CompletedProcess. Rationale: Follows best practices for dependency isolation; automates venv handling for Python-heavy DevOps, ensuring accuracy without global pollution and simplifying script portability."""
    if virtual_env_path is None:
        virtual_env_path = os.path.join(os.getcwd(), ".venv")
    venv_path = os.path.abspath(virtual_env_path)
    if not os.path.exists(os.path.join(venv_path, "bin" if not is_windows() else "Scripts")):
        venv.create(venv_path, with_pip=True)
        logger.info(f"Created virtual env at {venv_path}")
    activate = os.path.join(venv_path, "bin", "activate") if not is_windows() else os.path.join(venv_path, "Scripts", "activate.bat")
    if isinstance(cmd, list):
        cmd = [activate, "&&"] + cmd if is_windows() else ["source", activate, "&&"] + cmd
    else:
        cmd = f"{activate} && {cmd}" if is_windows() else f"source {activate} && {cmd}"
    return run(cmd, shell=True)

def manage_service_advanced(service_name: str, action: str = "restart", validate_first: bool = True) -> bool:
    """Handles service actions (start/stop/restart) with optional pre-validation. Input: service_name (str like "nginx"), action (str), validate_first (bool). Output: bool (success). Rationale: Extends reload_service; automates full lifecycle with platform-specific commands (systemctl/Task Scheduler), improving simplicity and accuracy for ops like your Nginx reloads."""
    if is_linux():
        cmd = ["systemctl", action, service_name]
        if validate_first:
            test_cmd = ["systemctl", "status", service_name]
    elif is_windows():
        cmd = ["sc", action, service_name]
        if validate_first:
            test_cmd = ["sc", "query", service_name]
    else:
        raise NotImplementedError("Service management not supported on this OS")
    if validate_first:
        test_res = run(test_cmd, capture=True, no_die=True)
        if test_res.returncode != 0:
            logger.error(f"Service validation failed: {test_res.stderr}")
            return False
    res = run(cmd, elevated=True, capture=True)
    return res.returncode == 0

def monitor_process(pattern: str, timeout: int = 60, check_interval: int = 5) -> bool:
    """Monitors if a process matching pattern starts/stops within timeout. Input: pattern (str for process name), timeout (int seconds), check_interval (int). Output: bool (True if condition met). Rationale: Enhances check_process_running; automates waiting in deployment scripts, ensuring accurate timing without busy loops."""
    start_time = time.time()
    initial_running = check_process_running(pattern)
    while time.time() - start_time < timeout:
        current_running = check_process_running(pattern)
        if current_running != initial_running:
            logger.info(f"Process state changed for {pattern}: {'appeared' if current_running else 'disappeared'}")
            return True
        time.sleep(check_interval)
    logger.warning(f"Timeout monitoring process {pattern}")
    return False

def ensure_sudo_privileges(prompt: bool = True) -> bool:
    """Prompts for sudo password if not root and validates. Input: prompt (bool to ask for password). Output: bool (True if sudo acquired). Rationale: Generalizes your ensure_root_or_sudo for reusable privilege escalation."""
    if is_root():
        return True
    if prompt:
        _get_sudo_password()
    # Validate by running a simple sudo command
    test_res = run("sudo -n true", shell=True, no_die=True, capture=True)
    if test_res.returncode == 0:
        return True
    else:
        clear_sudo_password()
        return False

def with_root_check(func: Callable, require_root: bool = True) -> Callable:
    """Decorator to ensure root/sudo before calling func. Input: func (function to wrap), require_root (bool). Output: Wrapped callable. Rationale: Directly ports your with_root_check for CLI commands."""
    def wrapper(*args, **kwargs):
        if require_root and not ensure_sudo_privileges():
            raise RuntimeError("Root privileges required")
        return func(*args, **kwargs)
    return wrapper

def fix_permissions(path: Union[str, os.PathLike], mode: int = 0o644, owner: str = "root:root", recursive: bool = False) -> None:
    """Sets mode and owner (using chown/chmod). Input: path (file/dir), mode (int), owner (str like "user:group"), recursive (bool). Output: None. Rationale: Generalizes your _fix_permissions for logs/cache."""
    path = str(path)
    if is_linux():
        run(f"chmod {'-R ' if recursive else ''}{oct(mode)[2:]} {path}", elevated=True)
        run(f"chown {'-R ' if recursive else ''}{owner} {path}", elevated=True)
    elif is_windows():
        # Simplified for Windows; adjust as needed
        run(f"icacls {path} /setowner {owner.split(':')[0]} {'/T' if recursive else ''}", elevated=True)
    logger.info(f"Fixed permissions on {path}")

# Wrappers
safe_run = run  # Alias for subprocess safe run
get_password = ask_password  # Alias for getpass
path_exists = os.path.exists  # Wrapper for os.path.exists