# src/utils_devops/extras/ssh_ops.py
"""
Professional SSH Operations Module for utils_devops

Enterprise-grade SSH operations with machine configuration management,
connection pooling, comprehensive diagnostics, and advanced features.

Dependencies: paramiko, scp
"""

import os
import sys
import json
import hashlib
import socket
from contextlib import contextmanager
from pathlib import Path
import time
from typing import Callable, Optional, Tuple, Union, List, Dict, Generator, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
import concurrent.futures
import threading
import select
from ..core import datetimes

# Core imports
from ..core.logs import task,get_library_logger
from ..core import systems
from ..core import files , envs
from ..core.strings import parse_yaml, dump_yaml

try:
    import paramiko
    from paramiko.ssh_exception import (
        SSHException, AuthenticationException, 
        BadHostKeyException, ChannelException
    )
    from scp import SCPClient
    SCP_AVAILABLE = True
except ImportError:
    SCP_AVAILABLE = False
    paramiko = None
    raise ImportError(
        "ssh_ops requires paramiko and scp. Install with: "
        "pip install paramiko scp"
    )

DEFULT_COMMAND_DIR = "/home/{user}/app/scripts/"
DEFULT_COMMAND = "./deploy-compose.py deploy"

__all__ = [
    # Data Classes
    "MachineConfig",
    "SSHConnectionStats",
    "ExecutionResult",
    "SSHKeyInfo",
    
    # Core SSH Operations
    "ssh_connect",
    "ssh_execute_command",
    "ssh_interactive_shell",
    
    # File Operations
    "scp_upload",
    "scp_download",
    "scp_upload_with_progress",
    "scp_download_with_progress",
    "remote_file_exists",
    "remote_file_size",
    "remote_file_hash",
    "sync_directory",
    
    # Key Management
    "ssh_register_key",
    "ssh_register_key_with_verification",
    "ssh_generate_key",
    "ssh_key_info",
    "ssh_test_key",
    
    # Connection Management
    "ssh_test_connection",
    "ssh_test_connection_with_retry",
    "ssh_diagnostics",
    "ssh_ping",
    
    
    # Parallel Operations
    "ssh_parallel_commands",
    "ssh_parallel_connect",
    "ssh_batch_execute",
    
    # Configuration Management
    "load_machines_config",
    "save_machines_config",
    "add_machine_to_config",
    "remove_machine_from_config",
    "update_machine_in_config",
    "validate_machine_config",
    "export_machines_to_csv",
    "import_machines_from_csv",

    
    # Machine-based Operations
    "execute_on_machine",
    "deploy_to_machine",
    "backup_from_machine",
    "gather_machine_info",
    "test_machine_connection",
    
    
    # Connection Pooling
    "SSHConnectionPool",
    "get_ssh_pool",
    "clear_ssh_pool",
    
    # Session Management
    "ssh_session_record",
    
    # Utilities
    "read_ssh_config",
    "generate_ssh_config",
    "resolve_host_alias",
    "get_ssh_agent_keys",
    "help",
    
    # Exceptions
    "SSHOpsError",
    "SSHAuthError",
    "SSHConfigError",
    "SSHTimeoutError",
]

# Module logger
_logger = get_library_logger()

# =============================================================================
# DATA CLASSES (Keep these - they're essential)
# =============================================================================

@dataclass
class SSHKeyInfo:
    """Information about an SSH key."""
    path: Path
    type: str  # rsa, ed25519, ecdsa
    size: int  # Key size in bits
    fingerprint: str
    public_key: str
    created: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_encrypted: bool = False

@dataclass
class MachineConfig:
    """Configuration for a target machine."""
    name: str
    host: str
    user: str
    port: int = 22
    deploy_dir: str = DEFULT_COMMAND_DIR
    command: str = DEFULT_COMMAND
    key_file: Optional[str] = None
    password: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    retry_delay: int = 5
    sudo: bool = False
    ssh_options: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    aliases: List[str] = field(default_factory=list)

@dataclass
class SSHConnectionStats:
    """SSH connection statistics."""
    host: str
    username: str
    port: int
    connected: bool
    auth_method: Optional[str] = None
    connect_time: Optional[float] = None
    last_used: Optional[datetime] = None
    total_connections: int = 0
    failed_connections: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    commands_executed: int = 0
    average_latency: float = 0.0

@dataclass
class ExecutionResult:
    """Result of a remote command execution."""
    machine_name: str
    success: bool
    command: str
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: float = 0.0

# =============================================================================
# EXCEPTIONS (Keep these)
# =============================================================================

class SSHOpsError(Exception):
    """Custom exception for SSH operations failures."""
    pass

class SSHAuthError(SSHOpsError):
    """Authentication failed."""
    pass

class SSHConfigError(SSHOpsError):
    """Configuration error."""
    pass

class SSHTimeoutError(SSHOpsError):
    """Connection or command timeout."""
    pass

# =============================================================================
# CORE SSH OPERATIONS - ONLY ESSENTIAL FUNCTIONS
# =============================================================================

def help() -> None:
    """Print comprehensive help."""
    help_text = """
Professional SSH Operations Module
==================================

CORE OPERATIONS:
----------------
ssh_connect(host, username, **kwargs)
    Context manager for SSH connections.

ssh_execute_command(host, command, **kwargs)
    Execute command on remote host.

ssh_interactive_shell(host, username, command=None)
    Start interactive SSH shell.

scp_upload(local_path, remote_path, host, username, **kwargs)
    Upload file via SCP.

scp_download(remote_path, local_path, host, username, **kwargs)
    Download file via SCP.

ssh_register_key(host, username, key_file, password=None)
    Register SSH key on remote host.

MACHINE-BASED OPERATIONS:
-------------------------
execute_on_machine(machine, command, **kwargs)
    Execute command using machine configuration.

deploy_to_machine(machine, local_path, remote_path=None)
    Deploy files to machine.

CONFIGURATION MANAGEMENT:
-------------------------
load_machines_config(config_file)
    Load machine configurations from YAML.

save_machines_config(config_file, machines)
    Save machines to configuration.

add_machine_to_config(config_file, machine)
    Add machine to configuration.

CONNECTION POOLING:
-------------------
SSHConnectionPool: Thread-safe connection pool.
get_ssh_pool(): Get global connection pool.
"""
    print(help_text)

@contextmanager
def ssh_connect(
    host: str,
    username: str = "root",
    password: Optional[str] = None,
    key_file: Optional[Union[str, Path]] = None,
    port: int = 22,
    timeout: int = 30,
    compress: bool = True,
    auto_add_host: bool = True,
    use_agent: bool = True,
    **kwargs: Any,
) -> Generator[paramiko.SSHClient, None, None]:
    """
    Professional SSH connection context manager.
    
    Args:
        host: Remote hostname or IP
        username: SSH username
        password: SSH password
        key_file: Path to private key file, env var name ($VAR), or key content
        port: SSH port
        timeout: Connection timeout in seconds
        compress: Enable compression
        auto_add_host: Automatically add host to known_hosts
        use_agent: Use SSH agent if available
        **kwargs: Additional connection parameters
    
    Yields:
        paramiko.SSHClient: Connected SSH client
    """
    client = None
    start_time = time.time()
    temp_key_file = None  # Track temporary file for cleanup
    
    try:
        _logger.debug(f"Connecting to {username}@{host}:{port}")
        client = paramiko.SSHClient()
        
        # Host key policy
        if auto_add_host:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            try:
                client.load_system_host_keys()
            except:
                _logger.warning("Could not load system host keys")
        
        # Build connection arguments
        connect_kwargs = {
            'hostname': host,
            'username': username,
            'port': port,
            'timeout': timeout,
            'compress': compress,
            'allow_agent': use_agent,
        }
        
        # Resolve key input (could be file, env var, or content)
        key_path, key_content = _resolve_ssh_key(key_file)
        
        if key_content:
            # **FIXED HERE**: Ensure proper line endings in the key content
            # SSH keys MUST have newlines at specific positions
            key_content = _normalize_ssh_key_content(key_content)
            
            # Create temporary file for key content
            import tempfile
            temp_key_file = tempfile.NamedTemporaryFile(
                mode='w',  # Text mode for proper newline handling
                suffix='_ssh_key',
                delete=False,
                newline='\n'  # Explicitly use LF newlines
            )
            
            # **CRITICAL FIX**: Write with proper line endings
            temp_key_file.write(key_content)
            temp_key_file.flush()  # Ensure data is written
            os.fsync(temp_key_file.fileno())  # Force sync to disk
            temp_key_file.close()
            
            # Set strict permissions for SSH keys
            os.chmod(temp_key_file.name, 0o600)
            
            # **DEBUG**: Verify what was written
            with open(temp_key_file.name, 'r') as f:
                written_content = f.read()
                _logger.debug(f"Written key length: {len(written_content)}")
                _logger.debug(f"Key first 100 chars: {written_content[:100]}")
                _logger.debug(f"Key lines: {written_content.count(chr(10))}")
            
            connect_kwargs['key_filename'] = temp_key_file.name
            _logger.debug(f"Using temporary SSH key file: {temp_key_file.name}")
            
        elif key_path:
            # Use existing key file
            connect_kwargs['key_filename'] = str(key_path)
            _logger.debug(f"Using SSH key file: {key_path}")
        
        # Add password if provided
        if password:
            connect_kwargs['password'] = password
        
        # Merge additional kwargs
        connect_kwargs.update(kwargs)
        
        # Connect
        client.connect(**connect_kwargs)
        
        connect_time = time.time() - start_time
        _logger.info(f"✅ Connected to {username}@{host}:{port} in {connect_time:.2f}s")
        
        yield client
        
    except AuthenticationException as e:
        _logger.error(f"Authentication failed for {username}@{host}:{port}")
        raise SSHAuthError(f"Authentication failed: {e}") from e
    except socket.timeout as e:
        _logger.error(f"Connection timeout to {host}:{port}")
        raise SSHTimeoutError(f"Connection timeout: {e}") from e
    except Exception as e:
        _logger.error(f"SSH connection failed to {host}: {e}")
        raise SSHOpsError(f"SSH connection failed: {e}") from e
    finally:
        # Clean up temporary key file if we created one
        if temp_key_file and os.path.exists(temp_key_file.name):
            try:
                os.unlink(temp_key_file.name)
                _logger.debug(f"Cleaned up temporary key file: {temp_key_file.name}")
            except Exception as e:
                _logger.warning(f"Failed to cleanup temp key file: {e}")
        
        if client:
            try:
                client.close()
                _logger.debug(f"Disconnected from {host}")
            except:
                pass


def _normalize_ssh_key_content(key_content: str) -> str:
    """
    Normalize SSH key content to ensure proper formatting.
    
    SSH keys require specific line breaks:
    - Must start with -----BEGIN ...-----
    - Base64 content should be on separate lines (64 chars max per line)
    - Must end with -----END ...-----
    
    Args:
        key_content: Raw key content (may be single line or malformed)
    
    Returns:
        Properly formatted SSH key
    """
    # If already looks properly formatted, return as-is
    if "-----BEGIN" in key_content and "-----END" in key_content and '\n' in key_content:
        # Verify line endings
        lines = key_content.splitlines()
        if len(lines) > 1:
            return key_content
    
    # Parse and reformat
    lines = []
    current_line = []
    
    # Remove all existing whitespace and split
    clean_content = key_content.strip()
    
    if clean_content.startswith("-----BEGIN"):
        # Extract header
        header_end = clean_content.find("-----", 10) + 5
        header = clean_content[:header_end]
        lines.append(header)
        
        # Get base64 content between headers
        base64_start = header_end
        base64_end = clean_content.find("-----END")
        base64_content = clean_content[base64_start:base64_end].strip()
        
        # Remove all whitespace from base64
        base64_clean = ''.join(base64_content.split())
        
        # Split into 64 character lines (standard for SSH keys)
        for i in range(0, len(base64_clean), 64):
            lines.append(base64_clean[i:i+64])
        
        # Add footer
        footer_start = base64_end
        lines.append(clean_content[footer_start:].strip())
    else:
        # Assume it's just base64, wrap in OpenSSH header/footer
        lines.append("-----BEGIN OPENSSH PRIVATE KEY-----")
        clean_base64 = ''.join(clean_content.split())
        for i in range(0, len(clean_base64), 64):
            lines.append(clean_base64[i:i+64])
        lines.append("-----END OPENSSH PRIVATE KEY-----")
    
    return '\n'.join(lines) + '\n'


# Also update your _resolve_ssh_key function to preserve newlines:
def _resolve_ssh_key(key_input: Optional[Union[str, Path]]) -> Tuple[Optional[Path], Optional[str]]:
    """
    Resolve SSH key input to either a file path or key content.
    
    Args:
        key_input: Could be:
            - Path to key file
            - Environment variable name ($VAR)
            - Raw key content string
    
    Returns:
        Tuple of (file_path, key_content)
    """
    if not key_input:
        return None, None
    
    # If it's a Path object
    if isinstance(key_input, Path):
        if key_input.exists():
            return key_input, None
        else:
            raise FileNotFoundError(f"SSH key file not found: {key_input}")
    
    key_input_str = str(key_input)
    
    # Check if it's an environment variable reference
    if key_input_str.startswith('$'):
        env_var = key_input_str[1:]
        key_content = os.environ.get(env_var)
        if not key_content:
            raise ValueError(f"Environment variable not set: {env_var}")
        
        # **CRITICAL**: Don't strip newlines from env var content!
        # SSH keys in env vars often have escaped newlines (\n)
        # Replace literal \n with actual newlines
        if '\\n' in key_content:
            key_content = key_content.replace('\\n', '\n')
        
        return None, key_content
    
    # Check if it's a file path
    if os.path.exists(key_input_str):
        return Path(key_input_str), None
    
    # Assume it's raw key content
    # **IMPORTANT**: Preserve any newlines in the content
    return None, key_input_str

def _inject_environment_variables(
    environment: Optional[Dict[str, str]] = None,
    base_command: str = "",
    remote_os: str = "linux" 
) -> str:
    """
    Creates a command string that safely injects environment variables.
    """
    if not environment:
        return base_command

    env_lines = []
    if remote_os is "linux":
        # Linux syntax: export VAR='value'
        for key, value in environment.items():
            print(f"DEBUG _inject_environment_variables: key='{key}', value='{value}', type={type(value)}")  # DEBUG
            escaped_value = value.replace("'", "'\"'\"'")
            env_lines.append(f"export {key}='{escaped_value}'")
        env_setup = " && ".join(env_lines)
        prefix = f"{env_setup} && "
    elif remote_os is "windows":
        env_lines.append("powershell ")
        # Windows syntax (PowerShell)
        for key, value in environment.items():
            print(f"DEBUG _inject_environment_variables: key='{key}', value='{value}', type={type(value)}")  # DEBUG
            escaped_value = value.replace("'", "''").replace("`", "``")
            env_lines.append(f"$env:{key}='{escaped_value}'")
        env_setup = "; ".join(env_lines)
        prefix = f"{env_setup}; "

    return f"{prefix}{base_command}"

def _detect_remote_os(client) -> str:
    """
    Detect the operating system of the remote SSH host.
    Returns: "linux", "windows", or "unknown"
    """
    try:
        # Try Linux command first
        stdin, stdout, stderr = client.exec_command("uname -s", timeout=5)
        output = stdout.read().decode('utf-8', errors='ignore').strip().lower()
        if "linux" in output or "darwin" in output:
            return "linux"
    except:
        pass
    
    try:
        # Try Windows command
        stdin, stdout, stderr = client.exec_command("ver", timeout=5)
        output = stdout.read().decode('utf-8', errors='ignore').strip().lower()
        if "windows" in output or "microsoft" in output:
            return "windows"
    except:
        pass
    
    # Try PowerShell (Windows)
    try:
        stdin, stdout, stderr = client.exec_command("Get-Host", timeout=5)
        output = stdout.read().decode('utf-8', errors='ignore').strip().lower()
        if "powershell" in output or "windows" in output:
            return "windows"
    except:
        pass
    
    # Default to linux (backward compatibility)
    return "linux"

def ssh_execute_command(
    host: str,
    command: Union[str, List[str]],
    username: str = "root",
    password: Optional[str] = None,
    key_file: Optional[Union[str, Path]] = None,
    port: int = 22,
    sudo: bool = False,
    hide_on_success: bool = True,
    check: bool = False,
    timeout: Optional[int] = None,
    environment: Optional[Dict[str, str]] = None,
    stream_output: bool = False,
    **kwargs: Any,
) -> systems.subprocess.CompletedProcess:
    """
    Execute command on remote host.
    
    Args:
        host: Remote hostname or IP
        command: Command to execute
        username: SSH username
        password: SSH password
        key_file: Path to private key file, env var name ($VAR), or key content
        port: SSH port
        sudo: Run command with sudo
        hide_on_success: Hide output on success
        check: Raise exception on non-zero exit code
        timeout: Command timeout in seconds
        environment: Environment variables to set
        **kwargs: Additional SSH connection parameters
    
    Returns:
        systems.subprocess.CompletedProcess: Command result
    """
    # Build command string
    if isinstance(command, list):
        command_str = " ".join(command)
    else:
        command_str = command
    
    with ssh_connect(
        host, username, password, key_file, port, **kwargs
    ) as client:
        # 1. DETECT REMOTE OS
        remote_os = _detect_remote_os(client)
    
    # Add environment variables
    if environment:
        command_str = _inject_environment_variables(environment, command_str,remote_os=remote_os)
    
    # Add sudo
    if sudo:
        command_str = f"sudo {command_str}"
    
    # Add timeout
    if timeout:
        command_str = f"{command_str}"
    
    task_name = f"SSH {username}@{host}: {command_str}"
    
    with task(task_name, hide_on_success=hide_on_success):
        try:
            with ssh_connect(
                host, username, password, key_file, port, **kwargs
            ) as client:
                _logger.debug(f"Executing: {command_str}")
                
                # Set command timeout
                exec_timeout = kwargs.get('timeout', 60)
                
                # Execute command
                stdin, stdout, stderr = client.exec_command(
                    command_str,
                    timeout=exec_timeout,
                    get_pty=True
                )
                
                stdout_lines = []
                stderr_lines = []
                
                if stream_output:
                    # Stream output in real-time
                    
                    # Read from stdout and stderr simultaneously
                    while True:
                        # Check if command is still running
                        if stdout.channel.exit_status_ready():
                            break
                            
                        # Use select to wait for data
                        rlist, _, _ = select.select([stdout.channel], [], [], 0.1)
                        
                        if rlist:
                            if stdout.channel.recv_ready():
                                chunk = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                                if chunk:
                                    sys.stdout.write(chunk)  # Print in real-time
                                    sys.stdout.flush()
                                    stdout_lines.append(chunk)
                                    
                            if stdout.channel.recv_stderr_ready():
                                chunk = stdout.channel.recv_stderr(1024).decode('utf-8', errors='ignore')
                                if chunk:
                                    sys.stderr.write(chunk)  # Print in real-time
                                    sys.stderr.flush()
                                    stderr_lines.append(chunk)
                
                # Read remaining output (if any)
                stdout_text = "".join(stdout_lines) + stdout.read().decode('utf-8', errors='ignore').strip()
                stderr_text = "".join(stderr_lines) + stderr.read().decode('utf-8', errors='ignore').strip()
                
                # Get exit code
                exit_code = stdout.channel.recv_exit_status()
                
                # Log output if needed
                if stdout_text and not hide_on_success:
                    _logger.debug(f"STDOUT: {stdout_text}")
                if stderr_text:
                    _logger.debug(f"STDERR: {stderr_text}")
                
                result = systems.subprocess.CompletedProcess(
                    args=command_str,
                    returncode=exit_code,
                    stdout=stdout_text,
                    stderr=stderr_text
                )
                
                if check and exit_code != 0:
                    raise SSHOpsError(
                        f"Command failed with exit code {exit_code}: {stderr_text}"
                    )
                
                return result
                
        except socket.timeout as e:
            _logger.error(f"Command timeout on {host}: {command_str}")
            raise SSHTimeoutError(f"Command timeout: {e}") from e
        except Exception as e:
            _logger.error(f"SSH command failed on {host}: {e}")
            if check:
                raise
            return systems.subprocess.CompletedProcess(
                args=command_str,
                returncode=1,
                stdout="",
                stderr=str(e)
            )

def scp_upload(
    local_path: Union[str, Path],
    remote_path: str,
    host: str,
    username: str = "root",
    recursive: bool = True,
    preserve_times: bool = True,
    **kwargs: Any,
) -> None:
    """
    Upload file or directory via SCP.
    
    Args:
        local_path: Local file/directory path
        remote_path: Remote destination path
        host: Remote hostname or IP
        username: SSH username
        recursive: Recursive copy for directories
        preserve_times: Preserve file timestamps
        **kwargs: Additional arguments for ssh_connect
    
    Raises:
        SSHOpsError: If upload fails
    """
    if not SCP_AVAILABLE:
        raise SSHOpsError("SCP not available. Install with: pip install scp")
    
    local_path = Path(local_path).expanduser().resolve()
    
    if not local_path.exists():
        raise SSHOpsError(f"Local path does not exist: {local_path}")
    
    task_name = f"SCP UPLOAD {local_path} → {username}@{host}:{remote_path}"
    
    with task(task_name):
        try:
            with ssh_connect(host, username, **kwargs) as client:
                with SCPClient(client.get_transport()) as scp:
                    if local_path.is_dir() and recursive:
                        scp.put(str(local_path), remote_path, 
                               recursive=True, preserve_times=preserve_times)
                        _logger.info(f"Uploaded directory: {local_path} → {remote_path}")
                    else:
                        scp.put(str(local_path), remote_path, 
                               preserve_times=preserve_times)
                        _logger.info(f"Uploaded file: {local_path} → {remote_path}")
                        
        except Exception as e:
            _logger.error(f"SCP upload failed: {e}")
            raise SSHOpsError(f"SCP upload failed: {e}") from e

def scp_download(
    remote_path: str,
    local_path: Union[str, Path],
    host: str,
    username: str = "root",
    recursive: bool = True,
    **kwargs: Any,
) -> None:
    """
    Download file or directory via SCP.
    
    Args:
        remote_path: Remote file/directory path
        local_path: Local destination path
        host: Remote hostname or IP
        username: SSH username
        recursive: Recursive copy for directories
        **kwargs: Additional arguments for ssh_connect
    
    Raises:
        SSHOpsError: If download fails
    """
    if not SCP_AVAILABLE:
        raise SSHOpsError("SCP not available. Install with: pip install scp")
    
    local_path = Path(local_path).expanduser().resolve()
    
    # Ensure parent directory exists
    files.ensure_dir(local_path.parent)
    
    task_name = f"SCP DOWNLOAD {username}@{host}:{remote_path} → {local_path}"
    
    with task(task_name):
        try:
            with ssh_connect(host, username, **kwargs) as client:
                with SCPClient(client.get_transport()) as scp:
                    scp.get(remote_path, str(local_path), recursive=recursive)
                    _logger.info(f"Downloaded: {remote_path} → {local_path}")
                        
        except Exception as e:
            _logger.error(f"SCP download failed: {e}")
            raise SSHOpsError(f"SCP download failed: {e}") from e

def ssh_register_key(
    host: str,
    username: str = "root",
    public_key: Optional[Union[str, Path]] = None,
    key_file: Optional[Union[str, Path]] = None,
    password: Optional[str] = None,
    port: int = 22,
) -> None:
    """
    Setup passwordless SSH login by adding public key to remote authorized_keys.
    
    Args:
        host: Remote hostname or IP
        username: SSH username
        public_key: Path to public key file, or public key string
        key_file: Path to private key file (used to derive public key)
        password: SSH password for initial connection
        port: SSH port
    
    Raises:
        SSHOpsError: If registration fails
    """
    # Determine public key content
    pubkey_content = None
    
    if public_key:
        if isinstance(public_key, str) and public_key.startswith('ssh-'):
            # public_key is the actual key string
            pubkey_content = public_key.strip()
        else:
            # public_key is a file path
            pubkey_path = Path(public_key).expanduser()
            if pubkey_path.exists():
                pubkey_content = pubkey_path.read_text().strip()
            else:
                raise SSHOpsError(f"Public key file not found: {pubkey_path}")
    
    if not pubkey_content and key_file:
        # Try to derive public key from private key
        privkey_path = Path(key_file).expanduser()
        pubkey_path = Path(f"{key_file}.pub")
        
        if pubkey_path.exists():
            pubkey_content = pubkey_path.read_text().strip()
        else:
            _logger.warning(f"Public key not found: {pubkey_path}")
            # Try to generate public key from private key
            try:
                key = paramiko.RSAKey(filename=str(privkey_path))
                pubkey_content = f"{key.get_name()} {key.get_base64()}"
            except Exception as e:
                raise SSHOpsError(f"Failed to read key file: {e}")
    
    if not pubkey_content:
        raise SSHOpsError("Could not determine public key content")
    
    task_name = f"Register SSH key for {username}@{host}"
    
    with task(task_name):
        try:
            # Create .ssh directory and authorized_keys file
            commands = [
                "mkdir -p ~/.ssh",
                "chmod 700 ~/.ssh",
                f"echo '{pubkey_content}' >> ~/.ssh/authorized_keys",
                "chmod 600 ~/.ssh/authorized_keys"
            ]
            
            for cmd in commands:
                result = ssh_execute_command(
                    host, cmd, username, password=password, port=port,
                    check=True, hide_on_success=False , 
                )
            
            _logger.info(f"SSH key registered for {username}@{host}")
            
        except Exception as e:
            _logger.error(f"SSH key registration failed: {e}")
            raise SSHOpsError(f"SSH key registration failed: {e}") from e

def ssh_test_connection(
    host: str,
    username: str = "root",
    port: int = 22,
    timeout: int = 10,
    **kwargs: Any,
) -> bool:
    """
    Quick SSH connectivity test.
    
    Args:
        host: Remote hostname or IP
        username: SSH username
        port: SSH port
        timeout: Connection timeout
        **kwargs: Additional arguments for ssh_connect
    
    Returns:
        bool: True if connection successful
    """
    try:
        with ssh_connect(host, username, port=port, timeout=timeout, **kwargs):
            _logger.debug(f"SSH test successful: {username}@{host}:{port}")
            return True
    except Exception as e:
        _logger.debug(f"SSH test failed: {username}@{host}:{port} - {e}")
        return False

def ssh_parallel_commands(
    hosts: List[str],
    command: Union[str, List[str]],
    max_workers: int = 15,
    **common_kwargs: Any,
) -> Dict[str, systems.subprocess.CompletedProcess]:
    """
    Run command on multiple hosts in parallel.
    
    Args:
        hosts: List of hostnames or IPs
        command: Command to execute on all hosts
        max_workers: Maximum number of parallel workers
        **common_kwargs: Common arguments for all SSH connections
    
    Returns:
        Dict mapping host -> subprocess.CompletedProcess
    """
    results = {}
    
    def _run_on_host(host):
        try:
            result = ssh_execute_command(host, command, **common_kwargs)
            return host, result
        except Exception as e:
            _logger.error(f"Parallel command failed on {host}: {e}")
            return host, systems.subprocess.CompletedProcess(
                args=command,
                returncode=1,
                stdout="",
                stderr=str(e)
            )
    
    with task(f"Parallel SSH on {len(hosts)} hosts: {command}"):
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_host = {
                executor.submit(_run_on_host, host): host 
                for host in hosts
            }
            
            for future in concurrent.futures.as_completed(future_to_host):
                host, result = future.result()
                results[host] = result
                
                if result.returncode == 0:
                    _logger.debug(f"✅ {host}: Success")
                else:
                    _logger.warning(f"❌ {host}: Failed (code {result.returncode})")
    
    return results

# =============================================================================
# MACHINE-BASED OPERATIONS (Keep these - they're professional)
# =============================================================================
def _normalize_env_input(env_input) -> Dict[str, str]:
    """
    Normalize environment input to dictionary.
    
    Supports:
    - dict: {"KEY": "value"}
    - string: "KEY" (gets value from environment)
    - list: ["KEY1", "KEY2"] (gets values from environment)
    """
    if isinstance(env_input, dict):
        return env_input
    
    elif isinstance(env_input, str):
        # Single variable name
        value = envs.get_system_env(env_input)
        return {env_input: value} if value is not None else {}
    
    elif isinstance(env_input, (list, tuple)):
        # List of variable names
        env_dict = {}
        for var_name in env_input:
            value = envs.get_system_env(var_name)
            if value is not None:
                env_dict[var_name] = value
        return env_dict
    
    else:
        # Return empty dict for any other type
        return {}

def execute_on_machine(
    machine: MachineConfig,
    command: str,
    timeout: Optional[int] = None,
    sudo: Optional[bool] = None,
    environment: Optional[Union[Dict[str, str], List[str]]] = None,
    check: bool = False,
    stream_output: bool = False,
    **kwargs
) -> ExecutionResult:
    """
    Execute command using machine configuration.
    
    Args:
        machine: MachineConfig object
        command: Command to execute
        timeout: Command timeout (overrides machine.timeout)
        sudo: Use sudo (overrides machine.sudo)
        environment: Environment variables
        check: Raise exception on failure
        **kwargs: Additional SSH parameters
    
    Returns:
        ExecutionResult: Execution result
    """
    start_time = datetime.now()
    
    try:
        # Merge environments
        cmd_env = {}
        
        # 1. Add machine environment (from YAML - should already be dict)
        if machine.environment:
            if isinstance(machine.environment, dict):
                cmd_env.update(machine.environment)
            else:
                # Convert if somehow it's not a dict
                cmd_env.update(_normalize_env_input(machine.environment))
        
        # 2. Add passed environment (could be dict, string, or list)
        if environment:
            cmd_env.update(_normalize_env_input(environment))
        
        # Run command
        ssh_result = ssh_execute_command(
            host=machine.host,
            command=command,
            username=machine.user,
            password=machine.password,
            key_file=machine.key_file,
            port=machine.port,
            sudo=sudo if sudo is not None else machine.sudo,
            timeout=timeout or machine.timeout,
            environment=cmd_env,
            check=check,
            stream_output=stream_output,
            **{**machine.ssh_options, **kwargs}
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Create execution result
        result = ExecutionResult(
            machine_name=machine.name,
            success=ssh_result.returncode == 0,
            command=command,
            returncode=ssh_result.returncode,
            stdout=ssh_result.stdout or "",
            stderr=ssh_result.stderr or "",
            start_time=start_time,
            end_time=end_time,
            duration=duration
        )
        
        return result
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return ExecutionResult(
            machine_name=machine.name,
            success=False,
            command=command,
            returncode=1,
            stdout="",
            stderr=str(e),
            error=str(e),
            start_time=start_time,
            end_time=end_time,
            duration=duration
        )

def deploy_to_machine(
    machine: MachineConfig,
    local_path: Union[str, Path],
    remote_path: Optional[str] = None,
    clean: bool = False,
    progress: bool = True,
    **kwargs
) -> bool:
    """
    Deploy files to a machine.
    
    Args:
        machine: MachineConfig object
        local_path: Local file/directory path
        remote_path: Remote destination path
        clean: Clean remote directory before deploy
        progress: Show progress bar
        **kwargs: Additional SCP parameters
    
    Returns:
        True if deployment successful
    """
    local_path = Path(local_path).expanduser().resolve()
    
    if not local_path.exists():
        _logger.error(f"Local path not found: {local_path}")
        return False
    
    if remote_path is None:
        remote_path = machine.deploy_dir
    
    try:
        # Clean remote directory if requested
        if clean and remote_path:
            _logger.info(f"🧹 Cleaning remote directory: {remote_path}")
            execute_on_machine(
                machine=machine,
                command=f"rm -rf {remote_path}/*",
                sudo=machine.sudo,
                check=False
            )
        
        # Deploy files
        task_name = f"Deploy {local_path} → {machine.name}:{remote_path}"
        
        with task(task_name):
            scp_upload(
                local_path=local_path,
                remote_path=remote_path,
                host=machine.host,
                username=machine.user,
                key_file=machine.key_file,
                password=machine.password,
                port=machine.port,
                **kwargs
            )
        
        _logger.info(f"✅ Deployed to {machine.name}")
        return True
        
    except Exception as e:
        _logger.error(f"❌ Deployment failed to {machine.name}: {e}")
        return False

# =============================================================================
# CONFIGURATION MANAGEMENT (Keep these - they're professional)
# =============================================================================

def load_machines_config(
    config_file: Union[str, Path],
    create_if_missing: bool = False,
    template: Optional[Dict[str, Any]] = None
) -> List[MachineConfig]:
    """
    Load machine configurations from YAML file.
    
    Args:
        config_file: Path to configuration file
        create_if_missing: Create file if it doesn't exist
        template: Template to use if creating new file
    
    Returns:
        List of MachineConfig objects
    """
    config_file = Path(config_file).expanduser().resolve()
    
    if not config_file.exists():
        if create_if_missing:
            _create_machines_config(config_file, template)
        else:
            raise SSHConfigError(f"Config file not found: {config_file}")
    
    try:
        content = files.read_file(config_file)
        config_data = parse_yaml(content)
        
        machines = []
        
        if 'machines' not in config_data:
            raise SSHConfigError("Config missing 'machines' section")
        
        for machine_data in config_data['machines']:
            try:
                # Fill in defaults
                defaults = {
                    'name': machine_data.get('host'),
                    'host': machine_data['host'],
                    'user': machine_data.get('user', 'root'),
                    'port': machine_data.get('port', 22),
                    'deploy_dir': machine_data.get('deploy_dir', DEFULT_COMMAND_DIR),
                    'command': machine_data.get('command', DEFULT_COMMAND),  # ADD THIS LINE
                    'key_file': machine_data.get('key_file'),
                    'password': machine_data.get('password'),
                    'tags': machine_data.get('tags', []),
                    'description': machine_data.get('description'),
                    # Also add these fields if they exist in your dataclass:
                    'timeout': machine_data.get('timeout', 30),
                    'retry_count': machine_data.get('retry_count', 3),
                    'retry_delay': machine_data.get('retry_delay', 5),
                    'sudo': machine_data.get('sudo', False),
                    'ssh_options': machine_data.get('ssh_options', {}),
                    'environment': machine_data.get('environment', {}),
                    'aliases': machine_data.get('aliases', []),
                }
                
                machine = MachineConfig(**defaults)
                machines.append(machine)
            except Exception as e:
                _logger.error(f"Failed to parse machine config: {e}")
                continue
        
        _logger.info(f"Loaded {len(machines)} machines from {config_file}")
        return machines
        
    except Exception as e:
        raise SSHConfigError(f"Failed to load config: {e}") from e


def save_machines_config(
    config_file: Union[str, Path],
    machines: List[MachineConfig],
    backup: bool = True
) -> None:
    """
    Save machine configurations to YAML file.
    
    Args:
        config_file: Path to configuration file
        machines: List of MachineConfig objects
        backup: Create backup of existing file
    """
    config_file = Path(config_file).expanduser().resolve()
    
    try:
        config_data = {
            'machines': [],
            'metadata': {
                'generated': datetimes.current_datetime().isoformat(),
                'count': len(machines),
            }
        }
        
        for machine in machines:
            machine_dict = {
                'name': machine.name,
                'host': machine.host,
                'user': machine.user,
                'port': machine.port,
                'deploy_dir': machine.deploy_dir,
                'command': machine.command,  # ADD THIS LINE
                'key_file': machine.key_file,
                'tags': machine.tags,
                'description': machine.description,
                # Also save these fields if you want them persisted:
                'timeout': machine.timeout,
                'retry_count': machine.retry_count,
                'retry_delay': machine.retry_delay,
                'sudo': machine.sudo,
                'environment': machine.environment,
            }
            config_data['machines'].append(machine_dict)
        
        yaml_content = dump_yaml(config_data)
        files.write_file(config_file, yaml_content)
        _logger.info(f"Saved {len(machines)} machines to {config_file}")
        
    except Exception as e:
        raise SSHConfigError(f"Failed to save config: {e}") from e

def add_machine_to_config(
    config_file: Union[str, Path],
    machine: MachineConfig,
    overwrite: bool = False
) -> bool:
    """
    Add a machine to configuration file.
    
    Args:
        config_file: Path to configuration file
        machine: MachineConfig to add
        overwrite: Overwrite if machine with same name exists
    
    Returns:
        True if added successfully
    """
    config_file = Path(config_file).expanduser().resolve()
    
    try:
        # Load existing machines
        existing_machines = []
        if config_file.exists():
            existing_machines = load_machines_config(config_file)
        
        # Check for duplicate name
        existing_names = [m.name for m in existing_machines]
        if machine.name in existing_names:
            if overwrite:
                # Remove existing machine
                existing_machines = [m for m in existing_machines if m.name != machine.name]
            else:
                _logger.warning(f"Machine '{machine.name}' already exists. Use overwrite=True to replace.")
                return False
        
        # Add new machine
        existing_machines.append(machine)
        
        # Save updated config
        save_machines_config(config_file, existing_machines)
        
        _logger.info(f"Added machine '{machine.name}' to {config_file}")
        return True
        
    except Exception as e:
        _logger.error(f"Failed to add machine to config: {e}")
        return False

# =============================================================================
# CONNECTION POOLING (Keep this - it's professional)
# =============================================================================

class SSHConnectionPool:
    """Thread-safe SSH connection pool."""
    
    def __init__(self, max_size: int = 20, idle_timeout    : int = 300):
        self._pool: Dict[str, paramiko.SSHClient] = {}
        self._lock = threading.RLock()
        self._max_size = max_size
        self._idle_timeout = idle_timeout
        self._last_used: Dict[str, float] = {}
    
    def get(
        self,
        host: str,
        username: str = "root",
        **kwargs
    ) -> paramiko.SSHClient:
        """Get or create SSH connection."""
        pool_key = f"{username}@{host}:{kwargs.get('port', 22)}"
        
        with self._lock:
            # Clean up idle connections
            self._clean_idle_connections()
            
            # Check if connection exists and is valid
            if pool_key in self._pool:
                client = self._pool[pool_key]
                
                # Check if connection is still active
                if (client.get_transport() and 
                    client.get_transport().is_active() and 
                    client.get_transport().is_authenticated()):
                    
                    self._last_used[pool_key] = time.time()
                    _logger.debug(f"Reusing connection: {pool_key}")
                    return client
                else:
                    # Remove dead connection
                    del self._pool[pool_key]
                    if pool_key in self._last_used:
                        del self._last_used[pool_key]
            
            # Check pool size limit
            if len(self._pool) >= self._max_size:
                # Remove least recently used connection
                self._remove_lru_connection()
            
            # Create new connection
            _logger.debug(f"Creating new connection: {pool_key}")
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Build connection arguments
                connect_kwargs = {
                    'hostname': host,
                    'username': username,
                    'timeout': kwargs.get('timeout', 30),
                }
                
                # Copy relevant kwargs
                for key in ['port', 'password', 'key_filename', 'compress']:
                    if key in kwargs:
                        connect_kwargs[key] = kwargs[key]
                
                client.connect(**connect_kwargs)
                
                # Add to pool
                self._pool[pool_key] = client
                self._last_used[pool_key] = time.time()
                
                _logger.info(f"Created new connection to {username}@{host}")
                return client
                
            except Exception as e:
                _logger.error(f"Failed to create connection: {e}")
                raise
    
    def _clean_idle_connections(self):
        """Remove idle connections."""
        current_time = time.time()
        to_remove = []
        
        for key, last_used in self._last_used.items():
            if current_time - last_used > self._idle_timeout:
                to_remove.append(key)
        
        for key in to_remove:
            if key in self._pool:
                try:
                    self._pool[key].close()
                except:
                    pass
                del self._pool[key]
                del self._last_used[key]
                _logger.debug(f"Removed idle connection: {key}")
    
    def _remove_lru_connection(self):
        """Remove least recently used connection."""
        if not self._last_used:
            return
        
        lru_key = min(self._last_used.items(), key=lambda x: x[1])[0]
        
        if lru_key in self._pool:
            try:
                self._pool[lru_key].close()
            except:
                pass
            
            del self._pool[lru_key]
            del self._last_used[lru_key]
            _logger.debug(f"Removed LRU connection: {lru_key}")
    
    def close_all(self):
        """Close all connections in pool."""
        with self._lock:
            for client in self._pool.values():
                try:
                    client.close()
                except:
                    pass
            
            self._pool.clear()
            self._last_used.clear()
            _logger.info(f"Closed all connections")

# Global connection pool
_ssh_pool = SSHConnectionPool()

def get_ssh_pool() -> SSHConnectionPool:
    """Get the global SSH connection pool."""
    return _ssh_pool

def clear_ssh_pool():
    """Clear the global SSH connection pool."""
    _ssh_pool.close_all()

# =============================================================================
# UTILITY FUNCTIONS (Keep only essential ones)
# =============================================================================

def _create_machines_config(
    config_file: Path,
    template: Optional[Dict[str, Any]] = None
) -> None:
    """Create a new machines configuration file."""
    if template is None:
        template = {
            'machines': [
                {
                    'name': 'example-server',
                    'host': '192.168.1.100',
                    'user': 'deploy',
                    'port': 22,
                    'deploy_dir': '/var/www/app',
                    'key_file': '~/.ssh/id_rsa',
                    'tags': ['production', 'web'],
                    'description': 'Example production server'
                }
            ],
            'metadata': {
                'created': datetimes.current_datetime().isoformat(),
            }
        }
    
    yaml_content = dump_yaml(template)
    files.ensure_dir(config_file.parent)
    files.write_file(config_file, yaml_content)
    _logger.info(f"Created new config file: {config_file}")
    
    
# =============================================================================
# ADD THESE FUNCTIONS TO THE ssh_ops.py MODULE
# =============================================================================

def remove_machine_from_config(
    config_file: Union[str, Path],
    machine_name: str
) -> bool:
    """
    Remove a machine from configuration file.
    
    Args:
        config_file: Path to configuration file
        machine_name: Name of machine to remove
    
    Returns:
        True if removed successfully
    """
    config_file = Path(config_file).expanduser().resolve()
    
    try:
        # Load existing machines
        existing_machines = []
        if config_file.exists():
            existing_machines = load_machines_config(config_file)
        
        # Check if machine exists
        existing_names = [m.name for m in existing_machines]
        if machine_name not in existing_names:
            _logger.warning(f"Machine '{machine_name}' not found in config")
            return False
        
        # Remove machine
        updated_machines = [m for m in existing_machines if m.name != machine_name]
        
        # Save updated config
        save_machines_config(config_file, updated_machines)
        
        _logger.info(f"Removed machine '{machine_name}' from {config_file}")
        return True
        
    except Exception as e:
        _logger.error(f"Failed to remove machine from config: {e}")
        return False

def update_machine_in_config(
    config_file: Union[str, Path],
    machine: MachineConfig
) -> bool:
    """
    Update a machine in configuration file.
    
    Args:
        config_file: Path to configuration file
        machine: Updated MachineConfig
    
    Returns:
        True if updated successfully
    """
    config_file = Path(config_file).expanduser().resolve()
    
    try:
        # Load existing machines
        existing_machines = []
        if config_file.exists():
            existing_machines = load_machines_config(config_file)
        
        # Check if machine exists
        existing_names = [m.name for m in existing_machines]
        if machine.name not in existing_names:
            _logger.warning(f"Machine '{machine.name}' not found in config")
            return add_machine_to_config(config_file, machine, overwrite=False)
        
        # Update machine
        updated_machines = []
        for m in existing_machines:
            if m.name == machine.name:
                updated_machines.append(machine)
            else:
                updated_machines.append(m)
        
        # Save updated config
        save_machines_config(config_file, updated_machines)
        
        _logger.info(f"Updated machine '{machine.name}' in {config_file}")
        return True
        
    except Exception as e:
        _logger.error(f"Failed to update machine in config: {e}")
        return False

def validate_machine_config(machine: MachineConfig) -> List[str]:
    """
    Validate machine configuration.
    
    Args:
        machine: MachineConfig to validate
    
    Returns:
        List of error messages, empty if valid
    """
    errors = []
    
    # Basic validation
    if not machine.name or not machine.name.strip():
        errors.append("Machine name cannot be empty")
    
    if not machine.host or not machine.host.strip():
        errors.append("Host cannot be empty")
    
    if not machine.user or not machine.user.strip():
        errors.append("User cannot be empty")
    
    if machine.port <= 0 or machine.port > 65535:
        errors.append(f"Invalid port: {machine.port}")
    
    if not machine.deploy_dir or not machine.deploy_dir.strip():
        errors.append("Deploy directory cannot be empty")
    
    if not machine.command or not machine.command.strip():
        errors.append("Command cannot be empty")
    
    # Validate deploy_dir format
    if '{user}' in machine.deploy_dir and machine.user:
        try:
            machine.deploy_dir.format(user=machine.user)
        except Exception as e:
            errors.append(f"Invalid deploy_dir format: {e}")
    
    # Validate key file if specified
    # if machine.key_file:
    #     key_path = Path(machine.key_file).expanduser()
    #     if not key_path.exists():
    #         errors.append(f"SSH key file not found: {key_path}")
    
    return errors

def test_machine_connection(
    machine: MachineConfig,
    detailed: bool = False
) -> Dict[str, Any]:
    """
    Test connection to a machine with comprehensive diagnostics.
    
    Args:
        machine: MachineConfig to test
        detailed: Return detailed test results
    
    Returns:
        Dictionary with test results
    """
    results = {
        'machine': machine.name,
        'host': machine.host,
        'user': machine.user,
        'port': machine.port,
        'tests': {},
        'overall': {
            'success': False,
            'message': '',
            'auth_method': 'unknown'
        }
    }
    
    try:
        # Test 1: Network connectivity (ping)
        try:
            import subprocess
            ping_cmd = ['ping', '-c', '1', '-W', '2', machine.host]
            ping_result = subprocess.run(
                ping_cmd, 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            results['tests']['network'] = {
                'success': ping_result.returncode == 0,
                'output': ping_result.stdout if ping_result.returncode == 0 else ping_result.stderr
            }
        except Exception as e:
            results['tests']['network'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test 2: SSH port connectivity
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((machine.host, machine.port))
            sock.close()
            results['tests']['port'] = {
                'success': result == 0,
                'message': 'Port open' if result == 0 else f'Port closed (error: {result})'
            }
        except Exception as e:
            results['tests']['port'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test 3: SSH authentication
        try:
            success, auth_method = ssh_test_connection_with_retry(
                host=machine.host,
                username=machine.user,
                port=machine.port,
                key_file=machine.key_file,
                password=machine.password,
                timeout=machine.timeout,
                max_retries=machine.retry_count,
                retry_delay=machine.retry_delay
            )
            
            results['tests']['ssh_auth'] = {
                'success': success,
                'auth_method': auth_method or 'unknown'
            }
            
            if success:
                results['overall']['success'] = True
                results['overall']['auth_method'] = auth_method or 'unknown'
                results['overall']['message'] = f'Connected via {auth_method}'
            else:
                results['overall']['message'] = 'SSH authentication failed'
                
        except Exception as e:
            results['tests']['ssh_auth'] = {
                'success': False,
                'error': str(e)
            }
            results['overall']['message'] = f'SSH test failed: {e}'
        
        # Test 4: Directory access (if connected)
        if results['overall']['success']:
            try:
                # Test if we can access deploy directory
                test_command = f"cd {machine.deploy_dir} && pwd"
                result = ssh_execute_command(
                    host=machine.host,
                    command=test_command,
                    username=machine.user,
                    key_file=machine.key_file,
                    password=machine.password,
                    port=machine.port,
                    timeout=10,
                    check=False
                )
                
                results['tests']['directory'] = {
                    'success': result.returncode == 0,
                    'output': result.stdout if result.returncode == 0 else result.stderr
                }
                
            except Exception as e:
                results['tests']['directory'] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
        
    except Exception as e:
        _logger.error(f"Machine connection test failed for {machine.name}: {e}")
        results['overall']['message'] = f'Test failed: {e}'
        return results

def gather_machine_info(machine: MachineConfig) -> Dict[str, Any]:
    """
    Gather comprehensive information about a machine.
    
    Args:
        machine: MachineConfig to gather info from
    
    Returns:
        Dictionary with machine information
    """
    info_data = {
        'name': machine.name,
        'host': machine.host,
        'user': machine.user,
        'port': machine.port,
        'timestamp': datetimes.current_datetime().isoformat(),
        'system_info': {},
        'network_info': {},
        'disk_info': {},
        'process_info': {},
        'success': False,
        'error': None
    }
    
    try:
        # System information
        commands = {
            'system_info': 'uname -a',
            'os_info': 'cat /etc/os-release 2>/dev/null || lsb_release -a 2>/dev/null || echo "Not available"',
            'uptime': 'uptime',
            'cpu_info': 'lscpu 2>/dev/null || nproc',
            'memory_info': 'free -h',
            'load_average': 'cat /proc/loadavg',
        }
        
        for key, cmd in commands.items():
            try:
                result = ssh_execute_command(
                    host=machine.host,
                    command=cmd,
                    username=machine.user,
                    key_file=machine.key_file,
                    password=machine.password,
                    port=machine.port,
                    timeout=10,
                    check=False,
                    hide_on_success=True
                )
                
                if result.returncode == 0:
                    info_data['system_info'][key] = result.stdout.strip()
                else:
                    info_data['system_info'][key] = f'Error: {result.stderr}'
                    
            except Exception as e:
                info_data['system_info'][key] = f'Failed: {e}'
        
        # Network information
        network_commands = {
            'ip_address': 'hostname -I 2>/dev/null || ip addr show 2>/dev/null | grep "inet " | grep -v "127.0.0.1" | head -1',
            'hostname': 'hostname',
            'dns': 'cat /etc/resolv.conf 2>/dev/null | grep nameserver',
        }
        
        for key, cmd in network_commands.items():
            try:
                result = ssh_execute_command(
                    host=machine.host,
                    command=cmd,
                    username=machine.user,
                    key_file=machine.key_file,
                    password=machine.password,
                    port=machine.port,
                    timeout=10,
                    check=False,
                    hide_on_success=True
                )
                
                if result.returncode == 0:
                    info_data['network_info'][key] = result.stdout.strip()
                else:
                    info_data['network_info'][key] = f'Error: {result.stderr}'
                    
            except Exception as e:
                info_data['network_info'][key] = f'Failed: {e}'
        
        # Disk information
        try:
            result = ssh_execute_command(
                host=machine.host,
                command='df -h',
                username=machine.user,
                key_file=machine.key_file,
                password=machine.password,
                port=machine.port,
                timeout=10,
                check=False,
                hide_on_success=True
            )
            
            if result.returncode == 0:
                info_data['disk_info'] = result.stdout.strip()
            else:
                info_data['disk_info'] = f'Error: {result.stderr}'
                
        except Exception as e:
            info_data['disk_info'] = f'Failed: {e}'
        
        # Process information (top 5 by CPU)
        try:
            result = ssh_execute_command(
                host=machine.host,
                command='ps aux --sort=-%cpu | head -6',
                username=machine.user,
                key_file=machine.key_file,
                password=machine.password,
                port=machine.port,
                timeout=10,
                check=False,
                hide_on_success=True
            )
            
            if result.returncode == 0:
                info_data['process_info'] = result.stdout.strip()
            else:
                info_data['process_info'] = f'Error: {result.stderr}'
                
        except Exception as e:
            info_data['process_info'] = f'Failed: {e}'
        
        info_data['success'] = True
        
    except Exception as e:
        info_data['error'] = str(e)
        _logger.error(f"Failed to gather info for {machine.name}: {e}")
    
    return info_data

def ssh_register_key_with_verification(
    host: str,
    username: str = "root",
    key_file: Optional[Union[str, Path]] = None,
    password: Optional[str] = None,
    port: int = 22,
    timeout: int = 30,
    test_after: bool = True,
    **kwargs
) -> bool:
    """
    Register SSH key and verify the registration.
    
    Args:
        host: Remote hostname or IP
        username: SSH username
        key_file: Path to private key file
        password: SSH password for initial connection
        port: SSH port
        timeout: Connection timeout
        test_after: Test connection after registration
        **kwargs: Additional arguments
    
    Returns:
        True if registration and verification successful
    """
    try:
        # Register the key
        ssh_register_key(
            host=host,
            username=username,
            key_file=key_file,
            password=password,
            port=port
        )
        
        _logger.info(f"SSH key registered for {username}@{host}")
        
        # Test after registration if requested
        if test_after:
            _logger.info(f"Verifying key registration for {username}@{host}")
            
            # Test without password (should work with key now)
            success, auth_method = ssh_test_connection_with_retry(
                host=host,
                username=username,
                key_file=key_file,
                password=None,  # Should not need password now
                port=port,
                timeout=timeout,
                max_retries=2,
                retry_delay=2
            )
            
            if success and auth_method and 'key' in auth_method.lower():
                _logger.info(f"✅ Key registration verified for {username}@{host} via {auth_method}")
                return True
            else:
                _logger.warning(f"⚠️  Key registration may not have worked for {username}@{host}")
                return False
        
        return True
        
    except Exception as e:
        _logger.error(f"SSH key registration with verification failed: {e}")
        return False

def ssh_generate_key(
    key_path: Union[str, Path],
    key_type: str = "rsa",
    key_size: int = 4096,
    comment: str = "",
    passphrase: Optional[str] = None,
    overwrite: bool = False,
    **kwargs
) -> SSHKeyInfo:
    """
    Generate a new SSH key pair.
    
    Args:
        key_path: Path where to save the key (without extension)
        key_type: Type of key (rsa, ed25519, ecdsa, dsa)
        key_size: Key size in bits (for RSA, ECDSA)
        comment: Comment to add to public key
        passphrase: Passphrase to encrypt private key
        overwrite: Overwrite existing key files
        **kwargs: Additional parameters
    
    Returns:
        SSHKeyInfo object with key details
    
    Raises:
        SSHOpsError: If key generation fails
    """
    key_path = Path(key_path).expanduser().resolve()
    private_key_path = key_path
    public_key_path = Path(f"{key_path}.pub")
    
    # Check if key already exists
    if not overwrite and (private_key_path.exists() or public_key_path.exists()):
        raise SSHOpsError(
            f"Key files already exist: {private_key_path}, {public_key_path}. "
            "Use overwrite=True to replace."
        )
    
    try:
        # Generate key based on type
        if key_type.lower() == "rsa":
            key = paramiko.RSAKey.generate(bits=key_size)
        elif key_type.lower() == "ed25519":
            key = paramiko.Ed25519Key.generate()
        elif key_type.lower() == "ecdsa":
            key = paramiko.ECDSAKey.generate()
        elif key_type.lower() == "dsa":
            key = paramiko.DSSKey.generate(bits=key_size)
        else:
            raise SSHOpsError(f"Unsupported key type: {key_type}")
        
        # Write private key
        if passphrase:
            key.write_private_key_file(
                str(private_key_path),
                password=passphrase.encode() if passphrase else None
            )
        else:
            key.write_private_key_file(str(private_key_path))
        
        # Set secure permissions
        private_key_path.chmod(0o600)
        
        # Generate and write public key
        public_key = f"{key.get_name()} {key.get_base64()}"
        if comment:
            public_key = f"{public_key} {comment}"
        
        files.write_file(public_key_path, public_key)
        public_key_path.chmod(0o644)
        
        # Get fingerprint
        fingerprint = hashlib.md5(key.get_base64().encode()).hexdigest()
        fingerprint_formatted = ':'.join(
            [fingerprint[i:i+2] for i in range(0, len(fingerprint), 2)]
        )
        
        # Create key info
        key_info = SSHKeyInfo(
            path=private_key_path,
            type=key_type.lower(),
            size=key_size,
            fingerprint=fingerprint_formatted,
            public_key=public_key,
            created=datetimes.current_datetime(),
            is_encrypted=bool(passphrase)
        )
        
        _logger.info(f"✅ Generated {key_type.upper()} key: {private_key_path}")
        _logger.info(f"   Fingerprint: {fingerprint_formatted}")
        _logger.info(f"   Public key: {public_key_path}")
        
        return key_info
        
    except Exception as e:
        _logger.error(f"Failed to generate SSH key: {e}")
        
        # Clean up any partial files
        if private_key_path.exists():
            try:
                private_key_path.unlink()
            except:
                pass
        if public_key_path.exists():
            try:
                public_key_path.unlink()
            except:
                pass
        
        raise SSHOpsError(f"SSH key generation failed: {e}") from e

def ssh_test_connection_with_retry(
    host: str,
    username: str = "root",
    password: Optional[str] = None,
    key_file: Optional[Union[str, Path]] = None,
    port: int = 22,
    timeout: int = 10,
    max_retries: int = 3,
    retry_delay: int = 5,
    **kwargs
) -> Tuple[bool, Optional[str]]:
    """
    Test SSH connection with retry mechanism.
    
    Args:
        host: Remote hostname or IP
        username: SSH username
        password: SSH password
        key_file: Path to private key file, env var name ($VAR), or key content
        port: SSH port
        timeout: Connection timeout per attempt
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        **kwargs: Additional arguments
    
    Returns:
        Tuple of (success, auth_method)
    """
    for attempt in range(1, max_retries + 1):
        try:
            with ssh_connect(
                host=host,
                username=username,
                password=password,
                key_file=key_file,
                port=port,
                timeout=timeout,
                **kwargs
            ) as client:
                # Connection successful
                _logger.info(f"✅ Connected to {username}@{host}:{port} (attempt {attempt})")
                
                # Determine auth method based on what was provided
                if key_file:
                    auth_method = "ssh_key"
                elif password:
                    auth_method = "password"
                else:
                    auth_method = "agent_or_none"
                
                return True, auth_method
                
        except Exception as e:
            _logger.debug(f"Connection attempt {attempt} failed: {e}")
            
            if attempt < max_retries:
                _logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                _logger.error(f"Failed to connect to {username}@{host}:{port} after {max_retries} attempts")
    
    return False, None

def _resolve_ssh_key(key_input: Optional[Union[str, Path]]) -> Tuple[Optional[Path], Optional[str]]:
    """
    Resolve SSH key input to either a file path or key content.
    
    Args:
        key_input: Can be:
            - Path to key file
            - Environment variable name (starting with $)
            - Actual key content string
            - None
    
    Returns:
        Tuple of (key_file_path, key_content)
    """
    if not key_input:
        return None, None
    
    key_input_str = str(key_input)
    
    # Case 1: Environment variable reference (starts with $)
    if key_input_str.startswith('$'):
        env_var_name = key_input_str[1:].strip()
        key_content = os.getenv(env_var_name)
        if key_content:
            _logger.debug(f"Resolved SSH key from environment variable: ${env_var_name}")
            # We'll need to write this to a temp file when needed
            return None, key_content
        else:
            _logger.warning(f"Environment variable not found: {env_var_name}")
            return None, None
    
    # Case 2: Check if it's a file path that exists
    key_path = Path(key_input_str).expanduser()
    if key_path.exists():
        _logger.debug(f"Using SSH key file: {key_path}")
        return key_path, None
    
    # Case 3: Check if it looks like actual key content
    # (contains "BEGIN" marker and is multi-line)
    if isinstance(key_input_str, str) and "-----BEGIN" in key_input_str and "\n" in key_input_str:
        _logger.debug(f"Using inline SSH key content")
        return None, key_input_str
    
    # Case 4: Might be a file path that doesn't exist yet (for CI/CD)
    _logger.warning(f"SSH key not found or invalid: {key_input_str}")
    return None, None

def get_ssh_agent_keys() -> List[SSHKeyInfo]:
    """
    Get SSH keys available in SSH agent.
    
    Returns:
        List of SSHKeyInfo objects for keys in agent
    """
    try:
        # Try to use paramiko's agent
        agent = paramiko.Agent()
        keys = agent.get_keys()
        
        key_infos = []
        for key in keys:
            # Get fingerprint
            fingerprint_hash = hashlib.md5(key.get_fingerprint()).hexdigest()
            fingerprint = ':'.join(
                [fingerprint_hash[i:i+2] for i in range(0, len(fingerprint_hash), 2)]
            )
            
            # Get key type
            if hasattr(key, 'key_type'):
                key_type = key.key_type
            else:
                # Determine from key object
                if isinstance(key, paramiko.RSAKey):
                    key_type = "rsa"
                elif isinstance(key, paramiko.ECDSAKey):
                    key_type = "ecdsa"
                elif isinstance(key, paramiko.Ed25519Key):
                    key_type = "ed25519"
                else:
                    key_type = "unknown"
            
            key_info = SSHKeyInfo(
                path=Path("ssh-agent"),
                type=key_type,
                size=key.get_bits() if hasattr(key, 'get_bits') else 0,
                fingerprint=fingerprint,
                public_key=f"{key.get_name()} {key.get_base64()}",
                created=None,
                last_used=None,
                is_encrypted=False
            )
            
            key_infos.append(key_info)
        
        _logger.debug(f"Found {len(key_infos)} keys in SSH agent")
        return key_infos
        
    except Exception as e:
        _logger.debug(f"SSH agent not available or error: {e}")
        return []
