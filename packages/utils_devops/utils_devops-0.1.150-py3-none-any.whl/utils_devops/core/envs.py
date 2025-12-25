"""
Environment operations for utils_devops (envs module).

Provides utilities to manage .env files and system environment variables,
run commands with specific env settings, and safely update env files with
backup/restore support. This module is typed and exposes __all__ so IDEs
show a friendly API surface.

Notes:
- Uses python-dotenv for parsing/setting .env files.
- Uses files for backups and read/write operations.
- Uses systems.run for command execution with an injected environment.
- Logs actions via utils_devops.core.logger.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, Union, List, Any
from dotenv import load_dotenv, dotenv_values, set_key as dotenv_set_key
from subprocess import CompletedProcess

from .logs import get_library_logger
from .files import backup_file, restore_file, write_file, read_file, FileOpsError
from .systems import run

log = get_library_logger()

# Public API for IDEs / help()
__all__ = [
    "EnvOpsError",
    "help",
    "load_env_file",
    "load_env_dict",
    "load_env_lines",
    "write_env_file",     
    "dump_env_file",
    "update_env_var",
    "remove_env_var",
    "backup_env_file",
    "restore_env_file",
    "get_system_env",
    "set_system_env",
    "export_system_to_env",
    "import_env_to_system",
    "run_with_env",
    "sync_env_to_system",
    "sync_system_to_env",
    "get_all_system_env",
    "validate_env_file",             
    "validate_env_files_compatibility", 
    "merge_env_files",   
    "diff_env_files",     
    "filter_env_file",   
    "env_to_shell_export",
    "validate_env_key",   
    "sanitize_env_value", 
]


class EnvOpsError(Exception):
    """Custom exception for environment operations failures."""
    pass


def help() -> None:
    """Print a short index of the envs API for interactive use."""
    print(
        """
DevOps Utils — Environment Operations Module
Key functions:
EnvOpsError: Custom exception for environment operations failures.
help() -> None: Print a short index of the envs API for interactive use.

Loading Environment Files:
load_env_file(file_path: Union[str, Path], as_dict: bool = True) -> Union[Dict[str, str], List[str]]: Load a .env file and return a dict of key->value or list of lines.
load_env_dict(file_path: Union[str, Path]) -> Dict[str, str]: Load .env file as dictionary (alias for backward compatibility).
load_env_lines(file_path: Union[str, Path]) -> List[str]: Load .env file as list of non-comment, non-empty lines.

Writing Environment Files:
write_env_file(data: Dict[str, str], file_path: Union[str, Path], backup: bool = True) -> None: Write environment variables to a .env file.
dump_env_file(data: Dict[str, str], file_path: Union[str, Path], backup: bool = True) -> None: Write data to file_path as KEY=VALUE lines.

Environment File Operations:
update_env_var(key: str, value: str, file_path: Union[str, Path], backup: bool = True) -> None: Set or update a single key in a .env file.
remove_env_var(key: str, file_path: Union[str, Path], backup: bool = True) -> None: Remove key from the .env file (if present).
backup_env_file(file_path: Union[str, Path]) -> Path: Create a backup of the .env file and return backup path.
restore_env_file(file_path: Union[str, Path], from_backup: Optional[Union[str, Path]] = None) -> None: Restore a .env file from backup.

System Environment Operations:
get_system_env(key: str, default: Optional[str] = None) -> Optional[str]: Get environment variable from os.environ (returns default if missing).
set_system_env(key: str, value: str) -> None: Set environment variable in the current process (os.environ).
export_system_to_env(file_path: Union[str, Path], keys: Optional[List[str]] = None) -> None: Export current process environment to a .env file.
import_env_to_system(file_path: Union[str, Path], overwrite: bool = True) -> None: Load variables from .env into the process environment.
get_all_system_env() -> Dict[str, str]: Return a copy of the current process environment as a dict.

Command Execution:
run_with_env(cmd: Union[str, List[str]], env_file: Optional[Union[str, Path]] = None, additional_env: Optional[Dict[str, str]] = None, **run_kwargs: Any) -> CompletedProcess: Run cmd with environment variables loaded from env_file.
sync_env_to_system(file_path: Union[str, Path], overwrite: bool = True) -> None: Alias for import_env_to_system.
sync_system_to_env(file_path: Union[str, Path], keys: Optional[List[str]] = None) -> None: Alias for export_system_to_env.

Advanced Operations:
merge_env_files(env_file1: Union[str, Path], env_file2: Union[str, Path], output_file: Union[str, Path], strategy: str = 'update', backup: bool = True) -> Dict[str, str]: Merge two environment files with different strategies.
diff_env_files(env_file1: Union[str, Path], env_file2: Union[str, Path]) -> Dict[str, Any]: Compare two environment files and return differences.
filter_env_file(env_file: Union[str, Path], keys: List[str], output_file: Optional[Union[str, Path]] = None, include: bool = True, backup: bool = True) -> Dict[str, str]: Filter environment file to include or exclude specific keys.
env_to_shell_export(env_file: Union[str, Path], shell: str = 'bash') -> str: Convert .env file to shell export commands.

Validation & Utilities:
validate_env_file(file_path: Union[str, Path], strict: bool = False) -> Dict[str, List[str]]: Validate an environment file for common issues.
validate_env_files_compatibility(env_file1: Union[str, Path], env_file2: Union[str, Path]) -> Dict[str, Any]: Validate compatibility between two environment files.
validate_env_key(key: str) -> bool: Validate if a key is a valid environment variable name.
sanitize_env_value(value: str) -> str: Sanitize environment variable value for safe writing.
"""
    )


# ========================
# Core Environment File Operations
# ========================

def load_env_file(file_path: Union[str, Path], as_dict: bool = True) -> Union[Dict[str, str], List[str]]:
    """
    Load a .env file and return a dict of key->value or list of lines.
    
    Args:
        file_path: path to the .env file
        as_dict: if True returns dict, if False returns list of lines
        
    Returns:
        Dict[str, str] if as_dict=True, List[str] if as_dict=False
        If file doesn't exist returns empty dict/list
    """
    try:
        if as_dict:
            data = dotenv_values(file_path)
            log.info(f"Loaded .env from {file_path}: {len(data)} keys")
            # dotenv_values may return values as None for missing values; normalize to str
            result = {k: (v if v is not None else "") for k, v in data.items()}
        else:
            # Return as list of lines
            if not Path(file_path).exists():
                log.warning(f"Env file not found: {file_path}")
                return []
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            result = [line for line in lines if line.strip() and not line.strip().startswith('#')]
            log.info(f"Loaded .env from {file_path}: {len(result)} lines")
        
        return result
        
    except Exception as e:
        log.error(f"Failed to load .env {file_path}: {e}")
        raise EnvOpsError(f"Failed to load .env: {e}") from e


def load_env_dict(file_path: Union[str, Path]) -> Dict[str, str]:
    """Load .env file as dictionary (alias for load_env_file for backward compatibility)."""
    return load_env_file(file_path)


def load_env_lines(file_path: Union[str, Path]) -> List[str]:
    """Load .env file as list of non-comment, non-empty lines."""
    return load_env_file(file_path, as_dict=False)


def write_env_file(data: Dict[str, str], file_path: Union[str, Path], backup: bool = True) -> None:
    """
    Write environment variables to a .env file.
    
    Args:
        data: Dictionary of key-value pairs to write
        file_path: Path to the .env file
        backup: Whether to create a backup before writing
    
    Raises:
        EnvOpsError: If writing fails
    """
    try:
        file_path = Path(file_path)
        
        # Create backup if requested and file exists
        if backup and file_path.exists():
            backup_env_file(file_path)
        
        # Prepare content
        lines = []
        for key, value in data.items():
            # Handle special characters and spaces in values
            if any(char in value for char in [' ', '#', '$', '"', "'"]) or not value:
                # Quote the value if it contains special characters or is empty
                lines.append(f'{key}="{value}"')
            else:
                lines.append(f'{key}={value}')
        
        # Write to file
        content = '\n'.join(lines) + '\n'
        file_path.write_text(content, encoding='utf-8')
        
        log.info(f"Wrote {len(data)} environment variables to {file_path}")
        
    except Exception as e:
        log.error(f"Failed to write .env file {file_path}: {e}")
        raise EnvOpsError(f"Failed to write .env file: {e}") from e


def dump_env_file(data: Dict[str, str], file_path: Union[str, Path], backup: bool = True) -> None:
    """Write `data` to `file_path` as KEY=VALUE lines. Optionally back up original file.

    Overwrites the target file.
    """
    # Alias for write_env_file for backward compatibility
    write_env_file(data, file_path, backup)


def update_env_var(key: str, value: str, file_path: Union[str, Path], backup: bool = True) -> None:
    """Set or update a single key in a .env file using python-dotenv's set_key helper.

    If `file_path` doesn't exist it will be created.
    """
    file_path = Path(file_path)
    if backup and file_path.exists():
        backup_file(file_path)
    try:
        # dotenv_set_key returns tuple (success, new_value) on some implementations,
        # we'll rely on it to write to file. Ensure parent exists.
        file_path.parent.mkdir(parents=True, exist_ok=True)
        dotenv_set_key(str(file_path), key, value)
        log.info(f"Updated env var '{key}' in {file_path}")
    except Exception as e:
        log.error(f"Failed to update env var '{key}': {e}")
        raise EnvOpsError(f"Failed to update env var: {e}") from e


def remove_env_var(key: str, file_path: Union[str, Path], backup: bool = True) -> None:
    """Remove `key` from the .env file (if present)."""
    file_path = Path(file_path)
    if backup and file_path.exists():
        backup_file(file_path)
    try:
        data = load_env_file(file_path)
        data.pop(key, None)
        write_env_file(data, file_path, backup=False)
        log.info(f"Removed env var '{key}' from {file_path}")
    except Exception as e:
        log.error(f"Failed to remove env var '{key}': {e}")
        raise EnvOpsError(f"Failed to remove env var: {e}") from e


def backup_env_file(file_path: Union[str, Path]) -> Path:
    """Create a backup of the .env file and return backup path."""
    return backup_file(file_path)


def restore_env_file(file_path: Union[str, Path], from_backup: Optional[Union[str, Path]] = None) -> None:
    """Restore a .env file from backup (or the most recent one)."""
    restore_file(file_path, from_backup)


# ========================
# System Environment Operations
# ========================


def get_system_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable from os.environ (returns default if missing)."""
    value = os.environ.get(key, default)
    log.debug(f"Got system env '{key}': {'[hidden]' if value else None}")
    return value


def set_system_env(key: str, value: str) -> None:
    """Set environment variable in the current process (os.environ)."""
    os.environ[key] = value
    log.info(f"Set system env '{key}'")


def export_system_to_env(file_path: Union[str, Path], keys: Optional[List[str]] = None) -> None:
    """Export current process environment (or selected keys) to a .env file."""
    data = {k: os.environ[k] for k in (keys or os.environ.keys())}
    write_env_file(data, file_path)
    log.info(f"Exported {len(data)} system env vars to {file_path}")


def import_env_to_system(file_path: Union[str, Path], overwrite: bool = True) -> None:
    """Load variables from .env into the process environment.

    If overwrite is False existing os.environ keys are left untouched.
    """
    try:
        load_dotenv(dotenv_path=str(file_path), override=overwrite)
        log.info(f"Imported .env from {file_path} to system (overwrite={overwrite})")
    except Exception as e:
        log.error(f"Failed to import .env to system: {e}")
        raise EnvOpsError(f"Failed to import .env: {e}") from e


def get_all_system_env() -> Dict[str, str]:
    """Return a copy of the current process environment as a dict."""
    data = dict(os.environ)
    log.debug(f"Got all system env: {len(data)} keys")
    return data


# ========================
# Command Execution with Env
# ========================


def run_with_env(
    cmd: Union[str, List[str]],
    env_file: Optional[Union[str, Path]] = None,
    additional_env: Optional[Dict[str, str]] = None,
    **run_kwargs: Any,
) -> CompletedProcess:
    """Run `cmd` with environment variables loaded from `env_file` and merged with additional_env.

    `run_kwargs` are forwarded to systems.run (cwd, elevated, dry_run, etc.). Returns CompletedProcess.
    """
    env = os.environ.copy()
    if env_file:
        env_file_data = load_env_file(env_file)
        env.update(env_file_data)
    if additional_env:
        env.update(additional_env)
    log.info(f"Running command with {len(env)} env vars")
    return run(cmd, env=env, **run_kwargs)


# Convenience aliases
sync_env_to_system = import_env_to_system
sync_system_to_env = export_system_to_env


# ========================
# Advanced Environment Operations
# ========================


def merge_env_files(env_file1: Union[str, Path], env_file2: Union[str, Path], 
                   output_file: Union[str, Path], strategy: str = 'update',
                   backup: bool = True) -> Dict[str, str]:
    """
    Merge two environment files with different strategies.
    
    Args:
        env_file1: First environment file
        env_file2: Second environment file  
        output_file: Output file path
        strategy: Merge strategy - 'update', 'preserve', 'replace', 'safe'
        backup: Whether to backup output file if it exists
    
    Returns:
        Dict with merge results and statistics
    """
    try:
        env1 = load_env_file(env_file1)
        env2 = load_env_file(env_file2)
        
        result_env = {}
        changes = {'added': [], 'updated': [], 'removed': [], 'preserved': []}
        
        if strategy == 'replace':
            # Completely replace with env2
            result_env = env2.copy()
            changes['added'] = list(env2.keys())
            
        elif strategy == 'update':
            # Update env1 with env2, add new keys from env2
            result_env = env1.copy()
            for key, value in env2.items():
                if key in env1:
                    if env1[key] != value:
                        changes['updated'].append(key)
                else:
                    changes['added'].append(key)
                result_env[key] = value
                
        elif strategy == 'preserve':
            # Preserve env1, only add new keys from env2
            result_env = env1.copy()
            for key, value in env2.items():
                if key not in env1:
                    result_env[key] = value
                    changes['added'].append(key)
                else:
                    changes['preserved'].append(key)
                    
        elif strategy == 'safe':
            # Only update keys that exist in both files
            result_env = env1.copy()
            for key, value in env2.items():
                if key in env1:
                    if env1[key] != value:
                        result_env[key] = value
                        changes['updated'].append(key)
                else:
                    changes['preserved'].append(f"skip_new:{key}")
                    
        else:
            raise EnvOpsError(f"Unknown merge strategy: {strategy}")
        
        # Write merged result
        write_env_file(result_env, output_file, backup=backup)
        
        log.info(f"Merged environment files using '{strategy}' strategy: {changes}")
        return {
            'merged_data': result_env,
            'changes': changes,
            'strategy': strategy,
            'file1_keys': len(env1),
            'file2_keys': len(env2),
            'merged_keys': len(result_env)
        }
        
    except Exception as e:
        log.error(f"Failed to merge environment files: {e}")
        raise EnvOpsError(f"Failed to merge environment files: {e}") from e


def diff_env_files(env_file1: Union[str, Path], env_file2: Union[str, Path]) -> Dict[str, Any]:
    """
    Compare two environment files and return differences.
    
    Returns:
        Dict with comparison results
    """
    try:
        env1 = load_env_file(env_file1)
        env2 = load_env_file(env_file2)
        
        all_keys = set(env1.keys()) | set(env2.keys())
        differences = {
            'only_in_file1': [],
            'only_in_file2': [], 
            'different_values': {},
            'same_values': []
        }
        
        for key in sorted(all_keys):
            if key in env1 and key not in env2:
                differences['only_in_file1'].append((key, env1[key]))
            elif key in env2 and key not in env1:
                differences['only_in_file2'].append((key, env2[key]))
            elif env1[key] != env2[key]:
                differences['different_values'][key] = {
                    'file1': env1[key],
                    'file2': env2[key]
                }
            else:
                differences['same_values'].append(key)
        
        log.info(f"Environment files comparison: {len(differences['different_values'])} differences found")
        return differences
        
    except Exception as e:
        log.error(f"Failed to compare environment files: {e}")
        raise EnvOpsError(f"Failed to compare environment files: {e}") from e


def filter_env_file(env_file: Union[str, Path], keys: List[str], 
                   output_file: Optional[Union[str, Path]] = None,
                   include: bool = True, backup: bool = True) -> Dict[str, str]:
    """
    Filter environment file to include or exclude specific keys.
    
    Args:
        env_file: Input environment file
        keys: List of keys to include or exclude
        output_file: Output file path (optional)
        include: If True, include only these keys; if False, exclude these keys
        backup: Whether to backup output file if it exists
    
    Returns:
        Filtered environment data
    """
    try:
        env_data = load_env_file(env_file)
        
        if include:
            filtered_data = {k: v for k, v in env_data.items() if k in keys}
        else:
            filtered_data = {k: v for k, v in env_data.items() if k not in keys}
        
        if output_file:
            write_env_file(filtered_data, output_file, backup=backup)
            log.info(f"Filtered environment file: {len(filtered_data)} keys {'included' if include else 'excluded'}")
        
        return filtered_data
        
    except Exception as e:
        log.error(f"Failed to filter environment file: {e}")
        raise EnvOpsError(f"Failed to filter environment file: {e}") from e


def env_to_shell_export(env_file: Union[str, Path], 
                       shell: str = 'bash') -> str:
    """
    Convert .env file to shell export commands.
    
    Args:
        env_file: Environment file path
        shell: Shell type - 'bash', 'fish', 'powershell'
    
    Returns:
        String with shell export commands
    """
    try:
        env_data = load_env_file(env_file)
        
        if shell == 'bash':
            lines = [f'export {k}="{v}"' for k, v in env_data.items()]
        elif shell == 'fish':
            lines = [f'set -gx {k} "{v}"' for k, v in env_data.items()]
        elif shell == 'powershell':
            lines = [f'$env:{k} = "{v}"' for k, v in env_data.items()]
        else:
            raise EnvOpsError(f"Unsupported shell: {shell}")
        
        result = '\n'.join(lines)
        log.info(f"Converted {len(env_data)} variables to {shell} export commands")
        return result
        
    except Exception as e:
        log.error(f"Failed to convert environment to shell exports: {e}")
        raise EnvOpsError(f"Failed to convert environment to shell exports: {e}") from e


def validate_env_key(key: str) -> bool:
    """
    Validate if a key is a valid environment variable name.
    
    Args:
        key: Key to validate
    
    Returns:
        True if valid, False otherwise
    """
    # Environment variable names should start with letter or underscore,
    # and contain only letters, numbers, and underscores
    if not key:
        return False
    
    if not (key[0].isalpha() or key[0] == '_'):
        return False
    
    if not all(c.isalnum() or c == '_' for c in key):
        return False
    
    return True


def sanitize_env_value(value: str) -> str:
    """
    Sanitize environment variable value for safe writing.
    
    Args:
        value: Value to sanitize
    
    Returns:
        Sanitized value
    """
    if not value:
        return '""'
    
    # Escape quotes and special characters
    sanitized = value.replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
    
    return sanitized


def validate_env_file(file_path: Union[str, Path], strict: bool = False) -> Dict[str, List[str]]:
    """
    Validate an environment file for common issues and return validation results.
    
    Args:
        file_path: Path to the .env file to validate
        strict: If True, raises EnvOpsError on validation failures. If False, returns warnings.
    
    Returns:
        Dict with validation results containing:
        - 'errors': List of critical errors that prevent proper parsing
        - 'warnings': List of potential issues that don't prevent parsing
        - 'info': List of informational messages
        - 'valid': Boolean indicating if file is valid (no critical errors)
        - 'key_count': Number of valid environment variables found
    
    Raises:
        EnvOpsError: If strict=True and validation fails
        FileNotFoundError: If env file doesn't exist
    """
    file_path = Path(file_path)
    results = {
        'errors': [],
        'warnings': [],
        'info': [],
        'valid': False,
        'key_count': 0
    }
    
    # Check file existence
    if not file_path.exists():
        results['errors'].append(f"Environment file not found: {file_path}")
        if strict:
            raise EnvOpsError(f"Environment file not found: {file_path}")
        return results
    
    if not file_path.is_file():
        results['errors'].append(f"Path is not a file: {file_path}")
        if strict:
            raise EnvOpsError(f"Path is not a file: {file_path}")
        return results
    
    # Check file size
    file_size = file_path.stat().st_size
    if file_size == 0:
        results['warnings'].append("Environment file is empty")
    elif file_size > 1024 * 1024:  # 1MB
        results['warnings'].append(f"Environment file is unusually large: {file_size} bytes")
    
    # Read and parse file content
    try:
        content = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            content = file_path.read_text(encoding='latin-1')
            results['warnings'].append("File is not UTF-8 encoded, using latin-1 fallback")
        except Exception as e:
            results['errors'].append(f"Failed to read file: {e}")
            if strict:
                raise EnvOpsError(f"Failed to read environment file: {e}") from e
            return results
    except Exception as e:
        results['errors'].append(f"Failed to read file: {e}")
        if strict:
            raise EnvOpsError(f"Failed to read environment file: {e}") from e
        return results
    
    # Parse line by line for detailed validation
    lines = content.splitlines()
    valid_keys = set()
    line_number = 0
    
    for line in lines:
        line_number += 1
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Check for export keyword (shell syntax)
        if line.startswith('export '):
            results['warnings'].append(f"Line {line_number}: Uses 'export' keyword (shell syntax)")
            line = line[7:].strip()  # Remove 'export '
        
        # Validate key=value format
        if '=' not in line:
            results['errors'].append(f"Line {line_number}: No '=' found in environment variable assignment")
            continue
        
        key, value = line.split('=', 1)
        key = key.strip()
        
        # Validate key name
        if not key:
            results['errors'].append(f"Line {line_number}: Empty key name")
            continue
        
        if not validate_env_key(key):
            results['warnings'].append(f"Line {line_number}: Key '{key}' contains invalid characters")
        
        if key[0].isdigit():
            results['warnings'].append(f"Line {line_number}: Key '{key}' starts with a digit (may cause issues in some systems)")
        
        # Check for common issues in values
        if value.strip() != value:
            results['warnings'].append(f"Line {line_number}: Value for '{key}' has leading/trailing whitespace")
        
        # Check for unquoted spaces (potential issues)
        if ' ' in value and not (value.startswith(('"', "'")) and value.endswith(('"', "'"))):
            results['warnings'].append(f"Line {line_number}: Value for '{key}' contains spaces but is not quoted")
        
        # Check for potential secrets in keys
        secret_indicators = ['password', 'secret', 'key', 'token', 'auth', 'credential']
        if any(indicator in key.lower() for indicator in secret_indicators):
            results['info'].append(f"Line {line_number}: Key '{key}' appears to contain sensitive data")
        
        valid_keys.add(key)
    
    # Try to load with dotenv to validate parsing
    try:
        env_dict = load_env_file(file_path)
        parsed_count = len([v for v in env_dict.values() if v is not None])
        results['key_count'] = parsed_count
        results['info'].append(f"Successfully parsed {parsed_count} environment variables")
        
        # Check for None values (parsing issues)
        none_values = [k for k, v in env_dict.items() if v is None]
        if none_values:
            results['warnings'].append(f"Variables with None values (possible parsing issues): {', '.join(none_values)}")
            
    except Exception as e:
        results['errors'].append(f"Failed to parse environment file: {e}")
    
    # Determine overall validity
    results['valid'] = len(results['errors']) == 0
    
    # Log results
    if results['valid']:
        if results['warnings']:
            log.warning(f"Env file validation passed with warnings for {file_path}: {len(results['warnings'])} warnings")
        else:
            log.info(f"Env file validation passed for {file_path}: {results['key_count']} variables")
    else:
        log.error(f"Env file validation failed for {file_path}: {len(results['errors'])} errors, {len(results['warnings'])} warnings")
    
    # Raise error if strict mode and invalid
    if strict and not results['valid']:
        error_msg = f"Environment file validation failed: {'; '.join(results['errors'])}"
        raise EnvOpsError(error_msg)
    
    return results


def validate_env_files_compatibility(env_file1: Union[str, Path], env_file2: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate compatibility between two environment files.
    
    Args:
        env_file1: First environment file path
        env_file2: Second environment file path
    
    Returns:
        Dict with compatibility analysis:
        - 'compatible': Boolean indicating if files are compatible
        - 'common_keys': List of keys present in both files
        - 'file1_only': List of keys only in first file
        - 'file2_only': List of keys only in second file
        - 'conflicting_values': Dict of keys with different values
        - 'file1_validation': Validation results for first file
        - 'file2_validation': Validation results for second file
    """
    results = {
        'compatible': False,
        'common_keys': [],
        'file1_only': [],
        'file2_only': [],
        'conflicting_values': {},
        'file1_validation': None,
        'file2_validation': None
    }
    
    # Validate both files
    results['file1_validation'] = validate_env_file(env_file1)
    results['file2_validation'] = validate_env_file(env_file2)
    
    if not results['file1_validation']['valid'] or not results['file2_validation']['valid']:
        return results
    
    # Load both environment files
    try:
        env1 = load_env_file(env_file1)
        env2 = load_env_file(env_file2)
        
        # Analyze differences
        keys1 = set(env1.keys())
        keys2 = set(env2.keys())
        
        results['common_keys'] = sorted(keys1 & keys2)
        results['file1_only'] = sorted(keys1 - keys2)
        results['file2_only'] = sorted(keys2 - keys1)
        
        # Find conflicting values
        for key in results['common_keys']:
            if env1[key] != env2[key]:
                results['conflicting_values'][key] = {
                    'file1_value': env1[key],
                    'file2_value': env2[key]
                }
        
        # Determine compatibility
        results['compatible'] = len(results['conflicting_values']) == 0
        
        log.info(f"Env files compatibility: {results['compatible']}, "
                f"common: {len(results['common_keys'])}, "
                f"conflicts: {len(results['conflicting_values'])}")
                
    except Exception as e:
        log.error(f"Failed to compare environment files: {e}")
        results['compatible'] = False
    
    return results