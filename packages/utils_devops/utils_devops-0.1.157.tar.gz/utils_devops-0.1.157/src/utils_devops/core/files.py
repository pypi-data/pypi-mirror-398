"""
File operations for utils_devops (files module).
Provides a comprehensive set of file and directory utilities designed for DevOps
automation scripts. This version is annotated and exposes an explicit `__all__`
so IDEs and `help()` show a friendly list of available functions and their
signatures.
Key behaviors / guarantees:
- Uses pathlib.Path for path handling.
- Logs actions via utils_devops.core.logger (get_library_logger()()).
- Raises FileOpsError for exceptional failures after logging.
- Provides idempotent helpers (ensure_dir/ensure_file), safe mutating ops with
  automatic backups, and archiving/checksum utilities.
Note: this file intentionally preserves your original function APIs while
adding typing, docstrings, and a module-level __all__ for better IDE support.
"""
from __future__ import annotations
import os
import re
import shutil
import tarfile
import zipfile
import hashlib
import time
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Union, Dict, Generator, ContextManager
from .logs import get_library_logger
from .systems import is_windows, is_linux, run
try:
    import filelock  # Assuming filelock is available as extra
except ImportError:
    filelock = None
log = get_library_logger()
class FileOpsError(Exception):
    """Custom exception for file operations failures."""
    pass
# Public API for IDEs / help()
__all__ = [
    "FileOpsError",
    "help",
    "atomic_write",
    "comment_block_between_markers",
    "create_symlink",
    "file_exists",
    "dir_exists",
    "ensure_file",
    "ensure_dir",
    "create_file",
    "create_dir",
    "remove_file",
    "remove_dir",
    "move",
    "copy",
    "rename",
    "read_file",
    "truncate_file",
    "touch",
    "write_file",
    "append_file",
    "search_in_file",
    "replace_in_file",
    "replace_regex_in_file",
    "delete_lines_in_file",
    "insert_after",
    "insert_before",
    "backup_file",
    "restore_file",
    "set_mode",
    "set_owner",
    "set_group",
    "set_owner_recursive",
    "find_files_by_ext",
    "find_pattern_in_files",
    "list_files_in_dir",
    "archive_file",
    "compress_dir",
    "extract_archive",
    "zip_file",
    "zip_dir",
    "extract_zip",
    "checksum_file",
    "read_marked_block",
    "remove_block_between_markers",  
    "insert_block",
    "resolve_symlink",
    "uncomment_block_between_markers",
    # New additions
    "simple_backup",
    "simple_restore",
    "batch_atomic_write",
    "verify_file_integrity",
    "safe_read_large_file",
    "auto_backup_on_write",
    "extract_archive_auto",
    "find_and_replace_in_dir",
    "merge_files",
    "lock_file",
    # Shutil wrappers
    "safe_copy",
    "safe_move",
    # Re wrapper (alias)
    "regex_search_file",
]
def help() -> None:
    """Print a concise index of functions in this module for interactive use.
    IDEs will also pick up `__all__` and individual function docstrings.
    """
    print(
        """
DevOps Utils — File Operations Module
This module provides a comprehensive set of file and directory utilities designed for DevOps automation scripts.
Key functions include:
FileOpsError: Custom exception for file operations failures.
help() -> None: Print a concise index of functions in this module for interactive use.
atomic_write(path: Union[str, Path], content: str, mode: int = 0o644) -> None: Atomically write `content` to `path` (write to temp then replace). Parent dirs created if needed.
comment_block_between_markers(path: Union[str, Path], start: str, end: str, backup: bool = True) -> None: Comment each line between `start` and `end` markers (inclusive) by adding '# ' prefix.
create_symlink(target: Union[str, Path], link_name: Union[str, Path], force: bool = False) -> None: Create a symlink from `link_name` to `target`. If `force=True`, overwrite existing link.
file_exists(path: Union[str, Path]) -> bool: Return True if `path` exists and is a file.
dir_exists(path: Union[str, Path]) -> bool: Return True if `path` exists and is a directory.
ensure_file(path: Union[str, Path], create_parents: bool = True) -> None: Create a file if it doesn't exist. Optionally create parent directories.
ensure_dir(path: Union[str, Path]) -> None: Create a directory (and parents) if missing.
create_file(path: Union[str, Path], create_parents: bool = True) -> None: Alias for ensure_file.
create_dir(path: Union[str, Path]) -> None: Alias for ensure_dir.
remove_file(path: Union[str, Path]) -> None: Remove a file if it exists.
remove_dir(path: Union[str, Path], recursive: bool = True) -> None: Remove a directory. If recursive=True, remove tree; else only empty dir.
move(src: Union[str, Path], dest: Union[str, Path]) -> None: Move a file or directory to destination.
copy(src: Union[str, Path], dest: Union[str, Path], preserve_attrs: bool = True) -> None: Copy file or directory. If preserve_attrs, use copy2 / copytree with metadata.
rename(src: Union[str, Path], dest: Union[str, Path]) -> None: Alias for move.
read_file(path: Union[str, Path], mode: str = "r") -> str: Read and return file content. Raises FileOpsError on failure.
truncate_file(path: Union[str, Path]) -> None: Truncate (empty) a file's contents.
touch(path: Union[str, Path]) -> None: Touch a file: create if missing or update mtime.
write_file(path: Union[str, Path], content: str, mode: str = 'w') -> None: Write `content` to `path`. Parent dirs are created if needed.
append_file(path: Union[str, Path], content: str) -> None: Append a line of text to `path`. Creates file if missing.
search_in_file(path: Union[str, Path], pattern: str, regex: bool = False) -> bool: Return True if pattern (or regex) is found in file.
replace_in_file(path: Union[str, Path], search: str, replace: str, regex: bool = False, backup: bool = True) -> None: Replace occurrences of `search` with `replace` in file. Back up original by default.
replace_regex_in_file(path: Union[str, Path], regex: str, replace: str, backup: bool = True) -> None: Alias for regex replace in file.
delete_lines_in_file(path: Union[str, Path], pattern: str, regex: bool = True, backup: bool = True) -> None: Delete lines matching pattern from file. Back up original by default.
insert_after(path: Union[str, Path], match: str, line: str, regex: bool = False, backup: bool = True) -> None: Insert `line` after the first line that matches `match`.
insert_before(path: Union[str, Path], match: str, line: str, regex: bool = False, backup: bool = True) -> None: Insert `line` before the first line that matches `match`.
backup_file(path: Union[str, Path], suffix: Optional[str] = None) -> Path: Create a timestamped backup of `path` and return backup path.
restore_file(path: Union[str, Path], from_backup: Optional[Union[str, Path]] = None) -> None: Restore `path` from the specified backup or the most recent backup found.
set_mode(path: Union[str, Path], mode: Union[int, str]) -> None: Set file/dir permissions (mode can be int or string like '755').
set_owner(path: Union[str, Path], owner: str, recursive: bool = False) -> None: Set owner (user or user:group on Linux). Uses elevated system command via systems.run.
set_group(path: Union[str, Path], group: str, recursive: bool = True) -> None: Set group ownership (Linux only).
set_owner_recursive(p: Union[str, Path], o: str) -> None: Alias for recursive owner.
find_files_by_ext(directory: Union[str, Path] = '.', extension: str = '') -> List[Path]: Find files under directory matching extension (recursive).
find_pattern_in_files(directory: Union[str, Path] = '.', pattern: str = '', regex: bool = True) -> List[str]: Search files recursively and return matches as 'file:line:match'.
list_files_in_dir(directory: Union[str, Path]) -> List[str]: Return a list of file names in a directory (non-recursive).
archive_file(file: Union[str, Path], output: Optional[Union[str, Path]] = None) -> Path: Create a tar.gz archive containing a single file and return path to archive.
compress_dir(directory: Union[str, Path], output: Optional[Union[str, Path]] = None) -> Path: Create a tar.gz archive of a directory and return path to archive.
extract_archive(archive: Union[str, Path], dest: Union[str, Path] = '.') -> None: Extract tar.gz archive to destination directory.
zip_file(file: Union[str, Path], output: Optional[Union[str, Path]] = None) -> Path: Create a zip archive containing a single file and return path to archive.
zip_dir(directory: Union[str, Path], output: Optional[Union[str, Path]] = None) -> Path: Create a zip archive of a directory recursively and return path to archive.
extract_zip(archive: Union[str, Path], dest: Union[str, Path] = '.') -> None: Extract a zip archive to destination.
checksum_file(path: Union[str, Path], algo: str = 'sha256') -> str: Compute and return checksum of file using chosen algorithm (md5|sha256).
read_marked_block(path: Union[str, Path], start: str, end: str) -> str: Extract and return the text block between `start` and `end` markers (inclusive, preserves newlines).
remove_block_between_markers(path: Union[str, Path], start: str, end: str, backup: bool = True) -> None: Remove the block between `start` and `end` markers (inclusive).
insert_block(path: Union[str, Path], block: str, before_marker: Optional[str] = None, after_marker: Optional[str] = None, at_line: Optional[int] = None, backup: bool = True) -> None: Insert a block of text into a file at a specific location.
resolve_symlink(path: Union[str, Path]) -> Path: Resolve symlink(s) and return the canonical (absolute) path, following all links.
uncomment_block_between_markers(path: Union[str, Path], start: str, end: str, backup: bool = True) -> None: Uncomment lines between `start` and `end` markers (inclusive) by removing '# ' prefix if present.
simple_backup(path: Union[str, Path], suffix: str = ".backup") -> Path: Creates a single backup by copying to path + suffix.
simple_restore(path: Union[str, Path], backup_suffix: str = ".backup") -> None: Restores from path + backup_suffix to path, then removes backup.
batch_atomic_write(files_dict: Dict[Path, str], create_parents: bool = True) -> None: Atomically writes multiple files from a dict of path -> content.
verify_file_integrity(path: Path, expected_checksum: str, algo: str = "sha256") -> bool: Verifies a file's checksum matches the expected value.
safe_read_large_file(path: Path, chunk_size: int = 1024*1024) -> Generator[str, None, None]: Reads large files in chunks to avoid memory overload.
auto_backup_on_write(path: Path, content: str, suffix: str = ".backup", mode: str = "w") -> None: Writes content with automatic backup if file exists.
extract_archive_auto(archive_path: Path, dest: Path = Path("."), password: Optional[str] = None) -> None: Extracts archives detecting type (zip/tar.gz) automatically.
find_and_replace_in_dir(directory: Path, pattern: str, replacement: str, extensions: Optional[List[str]] = None, recursive: bool = True) -> int: Finds and replaces in multiple files, returning count of changes.
merge_files(source_paths: List[Path], dest: Path, delimiter: str = "\n") -> None: Merges multiple files into one, with optional delimiter between contents.
lock_file(path: Path, timeout: int = 10) -> ContextManager: Context manager for file locking (using flock or similar).
safe_copy(src: Union[str, Path], dest: Union[str, Path], preserve_attrs: bool = True, backup: bool = True) -> None: Safe copy with optional backup of destination if exists.
safe_move(src: Union[str, Path], dest: Union[str, Path], backup: bool = True) -> None: Safe move with optional backup of destination if exists.
regex_search_file(path: Union[str, Path], pattern: str) -> bool: Alias for search_in_file with regex=True.
"""
    )
# ========================
# File & Directory Existence and Creation
# ========================
def file_exists(path: Union[str, Path]) -> bool:
    """Return True if `path` exists and is a file."""
    path = Path(path)
    exists = path.is_file()
    log.debug(f"Checked file existence: {path} -> {exists}")
    return exists
def dir_exists(path: Union[str, Path]) -> bool:
    """Return True if `path` exists and is a directory."""
    path = Path(path)
    exists = path.is_dir()
    log.debug(f"Checked dir existence: {path} -> {exists}")
    return exists
def ensure_file(path: Union[str, Path], create_parents: bool = True) -> None:
    """Create a file if it doesn't exist. Optionally create parent directories."""
    path = Path(path)
    if create_parents:
        ensure_dir(path.parent)
    if not path.exists():
        try:
            path.touch()
            log.info(f"Created file: {path}")
        except OSError as e:
            log.error(f"Failed to create file {path}: {e}")
            raise FileOpsError(f"Failed to create file {path}: {e}") from e
    else:
        log.debug(f"File already exists: {path}")
def ensure_dir(path: Union[str, Path]) -> None:
    """Create a directory (and parents) if missing."""
    path = Path(path)
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
            log.info(f"Created dir: {path}")
        except OSError as e:
            log.error(f"Failed to create dir {path}: {e}")
            raise FileOpsError(f"Failed to create dir {path}: {e}") from e
    else:
        log.debug(f"Dir already exists: {path}")
# Aliases
create_file = ensure_file
create_dir = ensure_dir
# ========================
# Removal Operations
# ========================
def remove_file(path: Union[str, Path]) -> None:
    """Remove a file if it exists."""
    path = Path(path)
    if path.is_file():
        try:
            path.unlink()
            log.info(f"Removed file: {path}")
        except OSError as e:
            log.error(f"Failed to remove file {path}: {e}")
            raise FileOpsError(f"Failed to remove file {path}: {e}") from e
    else:
        log.debug(f"File does not exist, skipping remove: {path}")
def remove_dir(path: Union[str, Path], recursive: bool = True) -> None:
    """Remove a directory. If recursive=True, remove tree; else only empty dir."""
    path = Path(path)
    if path.is_dir():
        try:
            if recursive:
                shutil.rmtree(path)
                log.info(f"Removed dir recursively: {path}")
            else:
                path.rmdir()
                log.info(f"Removed empty dir: {path}")
        except OSError as e:
            log.error(f"Failed to remove dir {path}: {e}")
            raise FileOpsError(f"Failed to remove dir {path}: {e}") from e
    else:
        log.debug(f"Dir does not exist, skipping remove: {path}")
# ========================
# Move, Copy, Rename
# ========================
def move(src: Union[str, Path], dest: Union[str, Path]) -> None:
    """Move a file or directory to destination."""
    src = Path(src)
    dest = Path(dest)
    try:
        shutil.move(str(src), str(dest))
        log.info(f"Moved {src} to {dest}")
    except OSError as e:
        log.error(f"Failed to move {src} to {dest}: {e}")
        raise FileOpsError(f"Failed to move {src} to {dest}: {e}") from e
def copy(src: Union[str, Path], dest: Union[str, Path], preserve_attrs: bool = True) -> None:
    """Copy file or directory. If preserve_attrs, use copy2 / copytree with metadata."""
    src = Path(src)
    dest = Path(dest)
    try:
        if src.is_dir():
            if preserve_attrs:
                shutil.copytree(str(src), str(dest), dirs_exist_ok=True)
            else:
                shutil.copytree(str(src), str(dest))
        else:
            if preserve_attrs:
                shutil.copy2(str(src), str(dest))
            else:
                shutil.copy(str(src), str(dest))
        log.info(f"Copied {src} to {dest}")
    except OSError as e:
        log.error(f"Failed to copy {src} to {dest}: {e}")
        raise FileOpsError(f"Failed to copy {src} to {dest}: {e}") from e
def create_symlink(target: Union[str, Path], link_name: Union[str, Path], force: bool = False) -> None:
    """Create a symlink from `link_name` to `target`. If `force=True`, overwrite existing link."""
    target = Path(target)
    link_name = Path(link_name)
    try:
        if force and link_name.exists():
            link_name.unlink()
            log.debug(f"Removed existing link for force: {link_name}")
        os.symlink(str(target), str(link_name))
        log.info(f"Created symlink {link_name} -> {target}")
    except OSError as e:
        log.error(f"Failed to create symlink {link_name} -> {target}: {e}")
        raise FileOpsError(f"Failed to create symlink {link_name} -> {target}: {e}") from e
def resolve_symlink(path: Union[str, Path]) -> Path:
    """Resolve symlink(s) and return the canonical (absolute) path, following all links."""
    path = Path(path)
    try:
        resolved = Path(os.path.realpath(str(path)))
        log.debug(f"Resolved symlink {path} -> {resolved}")
        return resolved
    except OSError as e:
        log.error(f"Failed to resolve symlink {path}: {e}")
        raise FileOpsError(f"Failed to resolve symlink {path}: {e}") from e
# Alias
rename = move
# Shutil safe wrappers
def safe_copy(src: Union[str, Path], dest: Union[str, Path], preserve_attrs: bool = True, backup: bool = True) -> None:
    """Safe copy with optional backup of destination if exists."""
    dest = Path(dest)
    if dest.exists() and backup:
        simple_backup(dest)
    copy(src, dest, preserve_attrs)
def safe_move(src: Union[str, Path], dest: Union[str, Path], backup: bool = True) -> None:
    """Safe move with optional backup of destination if exists."""
    dest = Path(dest)
    if dest.exists() and backup:
        simple_backup(dest)
    move(src, dest)
# ========================
# File Content Operations
# ========================
def read_file(path: Union[str, Path], mode: str = "r") -> str:
    """Read and return file content. Raises FileOpsError on failure."""
    path = Path(path)
    try:
        with open(path, mode) as f:
            content = f.read()
        log.info(f"Read from file: {path}")
        return content
    except OSError as e:
        log.error(f"Failed to read {path}: {e}")
        raise FileOpsError(f"Failed to read {path}: {e}") from e
def truncate_file(path: Union[str, Path]) -> None:
    """Truncate (empty) a file's contents."""
    path = Path(path)
    if path.is_file():
        try:
            with open(path, 'w'):
                pass
            log.info(f"Truncated file: {path}")
        except OSError as e:
            log.error(f"Failed to truncate {path}: {e}")
            raise FileOpsError(f"Failed to truncate {path}: {e}") from e
    else:
        log.warn(f"Cannot truncate non-file: {path}")
def touch(path: Union[str, Path]) -> None:
    """Touch a file: create if missing or update mtime."""
    path = Path(path)
    try:
        path.touch(exist_ok=True)
        log.debug(f"Touched file: {path}")
    except OSError as e:
        log.error(f"Failed to touch {path}: {e}")
        raise FileOpsError(f"Failed to touch {path}: {e}") from e
def write_file(path: Union[str, Path], content: str, mode: str = 'w') -> None:
    """Write `content` to `path`. Parent dirs are created if needed."""
    path = Path(path)
    ensure_dir(path.parent)
    try:
        with open(path, mode) as f:
            f.write(content)
        log.info(f"Wrote to file: {path}")
    except OSError as e:
        log.error(f"Failed to write {path}: {e}")
        raise FileOpsError(f"Failed to write {path}: {e}") from e
def append_file(path: Union[str, Path], content: str) -> None:
    """Append a line of text to `path`. Creates file if missing."""
    write_file(path, content + '\n', mode='a')
def search_in_file(path: Union[str, Path], pattern: str, regex: bool = False) -> bool:
    """Return True if pattern (or regex) is found in file."""
    path = Path(path)
    if not path.is_file():
        log.debug(f"File not found for search: {path}")
        return False
    try:
        with open(path, 'r') as f:
            content = f.read()
        found = bool(re.search(pattern, content) if regex else pattern in content)
        log.debug(f"Searched {path} for '{pattern}': {found}")
        return found
    except OSError as e:
        log.error(f"Failed to search {path}: {e}")
        raise FileOpsError(f"Failed to search {path}: {e}") from e
def regex_search_file(path: Union[str, Path], pattern: str) -> bool:
    """Alias for search_in_file with regex=True."""
    return search_in_file(path, pattern, regex=True)
def replace_in_file(path: Union[str, Path], search: str, replace: str, regex: bool = False, backup: bool = True) -> None:
    """Replace occurrences of `search` with `replace` in file. Back up original by default."""
    path = Path(path)
    if backup:
        backup_file(path)
    try:
        with open(path, 'r') as f:
            content = f.read()
        if regex:
            new_content = re.sub(search, replace, content, flags=re.MULTILINE | re.DOTALL)
        else:
            new_content = content.replace(search, replace)
        with open(path, 'w') as f:
            f.write(new_content)
        log.info(f"Replaced in {path}: '{search}' -> '{replace}'")
    except OSError as e:
        log.error(f"Failed to replace in {path}: {e}")
        raise FileOpsError(f"Failed to replace in {path}: {e}") from e
def replace_regex_in_file(path: Union[str, Path], regex: str, replace: str, backup: bool = True) -> None:
    """Alias for regex replace in file."""
    replace_in_file(path, regex, replace, regex=True, backup=backup)
def delete_lines_in_file(path: Union[str, Path], pattern: str, regex: bool = True, backup: bool = True) -> None:
    """Delete lines matching pattern from file. Back up original by default."""
    path = Path(path)
    if backup:
        backup_file(path)
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
        new_lines = [line for line in lines if not (re.search(pattern, line) if regex else pattern in line)]
        with open(path, 'w') as f:
            f.writelines(new_lines)
        log.info(f"Deleted matching lines in {path}: '{pattern}'")
    except OSError as e:
        log.error(f"Failed to delete lines in {path}: {e}")
        raise FileOpsError(f"Failed to delete lines in {path}: {e}") from e
def insert_after(path: Union[str, Path], match: str, line: str, regex: bool = False, backup: bool = True) -> None:
    """Insert `line` after the first line that matches `match`."""
    path = Path(path)
    if backup:
        backup_file(path)
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
        for i, ln in enumerate(lines):
            if (re.search(match, ln) if regex else match in ln):
                lines.insert(i + 1, line + '\n')
                break
        with open(path, 'w') as f:
            f.writelines(lines)
        log.info(f"Inserted after '{match}' in {path}: '{line}'")
    except OSError as e:
        log.error(f"Failed to insert after in {path}: {e}")
        raise FileOpsError(f"Failed to insert after in {path}: {e}") from e
def insert_before(path: Union[str, Path], match: str, line: str, regex: bool = False, backup: bool = True) -> None:
    """Insert `line` before the first line that matches `match`."""
    path = Path(path)
    if backup:
        backup_file(path)
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
        for i, ln in enumerate(lines):
            if (re.search(match, ln) if regex else match in ln):
                lines.insert(i, line + '\n')
                break
        with open(path, 'w') as f:
            f.writelines(lines)
        log.info(f"Inserted before '{match}' in {path}: '{line}'")
    except OSError as e:
        log.error(f"Failed to insert before in {path}: {e}")
        raise FileOpsError(f"Failed to insert before in {path}: {e}") from e
def atomic_write(path: Union[str, Path], content: str, mode: int = 0o644) -> None:
    """Atomically write `content` to `path` (write to temp then replace). Parent dirs created if needed.
    
    This prevents partial writes in case of failures. Mode is applied to the new file.
    """
    path = Path(path)
    ensure_dir(path.parent)
    try:
        # Write to temp in same dir for atomicity across filesystems
        with tempfile.NamedTemporaryFile(mode='w', dir=str(path.parent), delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        tmp_path.chmod(mode)
        os.replace(str(tmp_path), str(path))
        log.info(f"Atomically wrote to file: {path}")
    except OSError as e:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)  # Clean up temp on failure
        log.error(f"Failed to atomically write {path}: {e}")
        raise FileOpsError(f"Failed to atomically write {path}: {e}") from e
# ========================
# Block Manipulation Operations
# ========================
def read_marked_block(path: Union[str, Path], start: str, end: str) -> str:
    """Extract and return the text block between `start` and `end` markers (inclusive, preserves newlines).
    
    Assumes first occurrence; returns empty string if not found.
    """
    path = Path(path)
    try:
        content = read_file(path)
        lines = content.splitlines(keepends=True)
        block_lines = []
        inside = False
        for line in lines:
            if start in line:
                inside = True
            if inside:
                block_lines.append(line)
            if inside and end in line:
                break
        block = ''.join(block_lines)
        log.debug(f"Extracted block from {path} between '{start}' and '{end}'")
        return block
    except FileOpsError:
        raise  # Propagate read error
    except Exception as e:
        log.error(f"Failed to read marked block in {path}: {e}")
        raise FileOpsError(f"Failed to read marked block in {path}: {e}") from e
def comment_block_between_markers(path: Union[str, Path], start: str, end: str, backup: bool = True) -> None:
    """Comment each line between `start` and `end` markers (inclusive) by adding '# ' prefix.
    
    Assumes first occurrence and markers on own lines.
    """
    path = Path(path)
    if backup:
        backup_file(path)
    try:
        content = read_file(path)
        lines = content.splitlines(keepends=True)
        new_lines = []
        inside = False
        for line in lines:
            if inside:
                new_lines.append(f"# {line}")
                if end in line:
                    inside = False
            else:
                new_lines.append(line)
                if start in line:
                    inside = True
        new_content = ''.join(new_lines)
        write_file(path, new_content)
        log.info(f"Commented block in {path} between '{start}' and '{end}'")
    except OSError as e:
        log.error(f"Failed to comment block in {path}: {e}")
        raise FileOpsError(f"Failed to comment block in {path}: {e}") from e
def uncomment_block_between_markers(path: Union[str, Path], start: str, end: str, backup: bool = True) -> None:
    """Uncomment lines between `start` and `end` markers (inclusive) by removing '# ' prefix if present.
    
    Assumes first occurrence and markers on own lines.
    """
    path = Path(path)
    if backup:
        backup_file(path)
    try:
        content = read_file(path)
        lines = content.splitlines(keepends=True)
        new_lines = []
        inside = False
        for line in lines:
            if inside:
                if line.startswith('# '):
                    new_line = line[2:]
                elif line.startswith('#'):
                    new_line = line[1:]
                else:
                    new_line = line
                new_lines.append(new_line)
                if end in line:
                    inside = False
            else:
                new_lines.append(line)
                if start in line:
                    inside = True
        new_content = ''.join(new_lines)
        write_file(path, new_content)
        log.info(f"Uncommented block in {path} between '{start}' and '{end}'")
    except OSError as e:
        log.error(f"Failed to uncomment block in {path}: {e}")
        raise FileOpsError(f"Failed to uncomment block in {path}: {e}") from e
def remove_block_between_markers(path: Union[str, Path], start: str, end: str, backup: bool = True) -> None:
    """Remove the block between `start` and `end` markers (inclusive).
    
    Assumes first occurrence and markers on own lines.
    """
    path = Path(path)
    if backup:
        backup_file(path)
    try:
        content = read_file(path)
        lines = content.splitlines(keepends=True)
        new_lines = []
        inside = False
        for line in lines:
            if inside:
                if end in line:
                    inside = False
                continue
            if start in line:
                inside = True
                continue
            new_lines.append(line)
        new_content = ''.join(new_lines)
        write_file(path, new_content)
        log.info(f"Removed block in {path} between '{start}' and '{end}'")
    except OSError as e:
        log.error(f"Failed to remove block in {path}: {e}")
        raise FileOpsError(f"Failed to remove block in {path}: {e}") from e
    
def insert_block(
    path: Union[str, Path],
    block: str,
    *,
    before_marker: Optional[str] = None,
    after_marker: Optional[str] = None,
    at_line: Optional[int] = None,
    backup: bool = True,
) -> None:
    """
    Insert a block of text into a file at a specific location.
    Exactly one of the positioning options must be specified:
    - `before_marker`: Insert just before the first line containing this text.
    - `after_marker`: Insert just after the first line containing this text.
    - `at_line`: Insert at the beginning of the specified line (1-indexed).
    The block is inserted as-is (preserves newlines). If `backup=True`, a
    timestamped backup is created before modification.
    Raises:
        ValueError: If no positioning option is provided or more than one is used.
        FileOpsError: On I/O or parsing failures.
    """
    path = Path(path)
    if backup:
        backup_file(path)
    if sum(bool(x) for x in (before_marker, after_marker, at_line)) != 1:
        raise ValueError("Exactly one of before_marker, after_marker, or at_line must be specified")
    try:
        content = read_file(path)
        lines = content.splitlines(keepends=True)
        if at_line is not None:
            if not (1 <= at_line <= len(lines) + 1):
                raise ValueError(f"at_line {at_line} out of range (1-{len(lines) + 1})")
            insert_idx = at_line - 1
        else:
            marker = before_marker or after_marker
            for i, line in enumerate(lines):
                if marker in line:
                    insert_idx = i if before_marker else i + 1
                    break
            else:
                raise ValueError(f"Marker '{marker}' not found in {path}")
        # Insert block (split into lines, preserve trailing newline if present)
        block_lines = block.splitlines(keepends=True)
        new_lines = lines[:insert_idx] + block_lines + lines[insert_idx:]
        write_file(path, "".join(new_lines))
        log.info(f"Inserted block into {path} (before_marker={before_marker!r}, after_marker={after_marker!r}, at_line={at_line!r})")
    except (OSError, ValueError) as e:
        log.error(f"Failed to insert block in {path}: {e}")
        raise FileOpsError(f"Failed to insert block in {path}: {e}") from e
# ========================
# Backup and Restore
# ========================
def backup_file(path: Union[str, Path], suffix: Optional[str] = None) -> Path:
    """Create a timestamped backup of `path` and return backup path.
    If file doesn't exist, returns the original Path (no-op).
    """
    path = Path(path)
    if not path.is_file():
        log.warn(f"No file to backup: {path}")
        return path
    timestamp = int(time.time())
    bak_suffix = suffix or f".bak.{timestamp}"
    bak_path = path.with_suffix(path.suffix + bak_suffix)
    try:
        shutil.copy2(str(path), str(bak_path))
        log.info(f"Backed up {path} to {bak_path}")
        return bak_path
    except OSError as e:
        log.error(f"Failed to backup {path}: {e}")
        raise FileOpsError(f"Failed to backup {path}: {e}") from e
def restore_file(path: Union[str, Path], from_backup: Optional[Union[str, Path]] = None) -> None:
    """Restore `path` from the specified backup or the most recent backup found."""
    path = Path(path)
    if from_backup:
        bak_path = Path(from_backup)
    else:
        bak_files = list(path.parent.glob(f"{path.stem}{path.suffix}.bak.*"))
        if not bak_files:
            log.warn(f"No backups found for {path}")
            return
        bak_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        bak_path = bak_files[0]
    if bak_path.is_file():
        try:
            shutil.copy2(str(bak_path), str(path))
            log.info(f"Restored {path} from {bak_path}")
        except OSError as e:
            log.error(f"Failed to restore {path}: {e}")
            raise FileOpsError(f"Failed to restore {path}: {e}") from e
    else:
        log.warn(f"Backup not found: {bak_path}")
def simple_backup(path: Union[str, Path], suffix: str = ".backup") -> Path:
    """Creates a single backup by copying to path + suffix. Input: path (file to backup), suffix (optional str). Output: Path to backup file. Rationale: Your script uses shutil.copy2 for quick backups; this generalizes it without timestamp accumulation."""
    path = Path(path)
    if not path.is_file():
        log.warn(f"No file to backup: {path}")
        return path
    bak_path = path.with_suffix(path.suffix + suffix)
    try:
        shutil.copy2(str(path), str(bak_path))
        log.info(f"Simple backed up {path} to {bak_path}")
        return bak_path
    except OSError as e:
        log.error(f"Failed to simple backup {path}: {e}")
        raise FileOpsError(f"Failed to simple backup {path}: {e}") from e

def simple_restore(path: Union[str, Path], backup_suffix: str = ".backup") -> None:
    """Restores from path + backup_suffix to path, then removes backup. Input: path (file to restore), backup_suffix (str). Output: None. Rationale: Matches your _restore_site_backup for atomic rollback."""
    path = Path(path)
    bak_path = path.with_suffix(path.suffix + backup_suffix)
    if bak_path.is_file():
        try:
            shutil.copy2(str(bak_path), str(path))
            bak_path.unlink()
            log.info(f"Simple restored {path} from {bak_path} and removed backup")
        except OSError as e:
            log.error(f"Failed to simple restore {path}: {e}")
            raise FileOpsError(f"Failed to simple restore {path}: {e}") from e
    else:
        log.warn(f"Simple backup not found: {bak_path}")
# ========================
# Permissions and Ownership
# ========================
def set_mode(path: Union[str, Path], mode: Union[int, str]) -> None:
    """Set file/dir permissions (mode can be int or string like '755')."""
    path = Path(path)
    if isinstance(mode, str):
        mode = int(mode, 8)
    try:
        path.chmod(mode)
        log.info(f"Set mode {oct(mode)} on {path}")
    except OSError as e:
        log.error(f"Failed to set mode on {path}: {e}")
        raise FileOpsError(f"Failed to set mode on {path}: {e}") from e
def set_owner(path: Union[str, Path], owner: str, recursive: bool = False) -> None:
    """Set owner (user or user:group on Linux). Uses elevated system command via systems.run."""
    path = Path(path)
    try:
        if is_windows():
            cmd = f'icacls "{path}" /setowner {owner}'
            if recursive and path.is_dir():
                cmd += ' /T'
            run(cmd, elevated=True)
        elif is_linux():
            cmd = f'chown {"-R " if recursive else ""}{owner} "{path}"'
            run(cmd, elevated=True)
        else:
            raise NotImplementedError("Unsupported platform for set_owner")
        log.info(f"Set owner {owner} on {path} (recursive={recursive})")
    except Exception as e:
        log.error(f"Failed to set owner on {path}: {e}")
        raise FileOpsError(f"Failed to set owner on {path}: {e}") from e
def set_group(path: Union[str, Path], group: str, recursive: bool = True) -> None:
    """Set group ownership (Linux only)."""
    path = Path(path)
    if is_windows():
        log.warn("set_group not supported on Windows")
        return
    try:
        cmd = f'chgrp {"-R " if recursive else ""}{group} "{path}"'
        run(cmd, elevated=True)
        log.info(f"Set group {group} on {path} (recursive={recursive})")
    except Exception as e:
        log.error(f"Failed to set group on {path}: {e}")
        raise FileOpsError(f"Failed to set group on {path}: {e}") from e
# Alias for recursive owner
set_owner_recursive = lambda p, o: set_owner(p, o, recursive=True)
# ========================
# Search and List
# ========================
def find_files_by_ext(directory: Union[str, Path] = '.', extension: str = '') -> List[Path]:
    """Find files under directory matching extension (recursive)."""
    directory = Path(directory)
    files = list(directory.rglob(f"*.{extension.strip('.')}")) if extension else list(directory.rglob("*"))
    files = [f for f in files if f.is_file()]
    log.debug(f"Found {len(files)} files with ext '{extension}' in {directory}")
    return files
def find_pattern_in_files(directory: Union[str, Path] = '.', pattern: str = '', regex: bool = True) -> List[str]:
    """Search files recursively and return matches as 'file:line:match'."""
    directory = Path(directory)
    results: List[str] = []
    for file in directory.rglob("*"):
        if file.is_file():
            try:
                with open(file, 'r') as f:
                    for i, line in enumerate(f, 1):
                        if (re.search(pattern, line) if regex else pattern in line):
                            results.append(f"{file}:{i}:{line.strip()}")
            except OSError:
                log.warn(f"Skipped unreadable file: {file}")
    log.info(f"Found {len(results)} matches for '{pattern}' in {directory}")
    return results
def list_files_in_dir(directory: Union[str, Path]) -> List[str]:
    """Return a list of file names in a directory (non-recursive)."""
    directory = Path(directory)
    files = [f.name for f in directory.iterdir() if f.is_file()]
    log.debug(f"Listed {len(files)} files in {directory}")
    return files
# ========================
# Archiving and Checksums
# ========================
def archive_file(file: Union[str, Path], output: Optional[Union[str, Path]] = None) -> Path:
    """Create a tar.gz archive containing a single file and return path to archive."""
    file = Path(file)
    output = Path(output or f"{file}.tar.gz")
    try:
        with tarfile.open(output, "w:gz") as tar:
            tar.add(str(file), arcname=file.name)
        log.info(f"Archived file {file} to {output}")
        return output
    except OSError as e:
        log.error(f"Failed to archive {file}: {e}")
        raise FileOpsError(f"Failed to archive {file}: {e}") from e
def compress_dir(directory: Union[str, Path], output: Optional[Union[str, Path]] = None) -> Path:
    """Create a tar.gz archive of a directory and return path to archive."""
    directory = Path(directory)
    output = Path(output or f"{directory}.tar.gz")
    try:
        with tarfile.open(output, "w:gz") as tar:
            tar.add(str(directory), arcname=directory.name)
        log.info(f"Compressed dir {directory} to {output}")
        return output
    except OSError as e:
        log.error(f"Failed to compress {directory}: {e}")
        raise FileOpsError(f"Failed to compress {directory}: {e}") from e
def extract_archive(archive: Union[str, Path], dest: Union[str, Path] = '.') -> None:
    """Extract tar.gz archive to destination directory."""
    archive = Path(archive)
    dest = Path(dest)
    ensure_dir(dest)
    try:
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(str(dest))
        log.info(f"Extracted {archive} to {dest}")
    except OSError as e:
        log.error(f"Failed to extract {archive}: {e}")
        raise FileOpsError(f"Failed to extract {archive}: {e}") from e
def zip_file(file: Union[str, Path], output: Optional[Union[str, Path]] = None) -> Path:
    """Create a zip archive containing a single file and return path to archive."""
    file = Path(file)
    output = Path(output or f"{file}.zip")
    try:
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(str(file), file.name)
        log.info(f"Zipped file {file} to {output}")
        return output
    except OSError as e:
        log.error(f"Failed to zip {file}: {e}")
        raise FileOpsError(f"Failed to zip {file}: {e}") from e
def zip_dir(directory: Union[str, Path], output: Optional[Union[str, Path]] = None) -> Path:
    """Create a zip archive of a directory recursively and return path to archive."""
    directory = Path(directory)
    output = Path(output or f"{directory}.zip")
    try:
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    full_path = os.path.join(root, file)
                    zf.write(full_path, os.path.relpath(full_path, directory))
        log.info(f"Zipped dir {directory} to {output}")
        return output
    except OSError as e:
        log.error(f"Failed to zip {directory}: {e}")
        raise FileOpsError(f"Failed to zip {directory}: {e}") from e
def extract_zip(archive: Union[str, Path], dest: Union[str, Path] = '.') -> None:
    """Extract a zip archive to destination."""
    archive = Path(archive)
    dest = Path(dest)
    ensure_dir(dest)
    try:
        with zipfile.ZipFile(archive, 'r') as zf:
            zf.extractall(str(dest))
        log.info(f"Extracted zip {archive} to {dest}")
    except OSError as e:
        log.error(f"Failed to extract zip {archive}: {e}")
        raise FileOpsError(f"Failed to extract zip {archive}: {e}") from e
def checksum_file(path: Union[str, Path], algo: str = 'sha256') -> str:
    """Compute and return checksum of file using chosen algorithm (md5|sha256)."""
    path = Path(path)
    if algo not in ('md5', 'sha256'):
        raise FileOpsError(f"Unsupported algo: {algo}")
    hash_func = hashlib.md5() if algo == 'md5' else hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        checksum = hash_func.hexdigest()
        log.debug(f"Checksum ({algo}) for {path}: {checksum}")
        return checksum
    except OSError as e:
        log.error(f"Failed to checksum {path}: {e}")
        raise FileOpsError(f"Failed to checksum {path}: {e}") from e
# ========================
# New Functions
# ========================
def batch_atomic_write(files_dict: Dict[Path, str], create_parents: bool = True) -> None:
    """Atomically writes multiple files from a dict of path -> content. Input: files_dict (Dict[Path, str]), create_parents (bool). Output: None. Rationale: Automates multi-file updates (e.g., configs + logs); ensures accuracy with atomicity across files, simplifying bulk ops like site syncs."""
    temps = []
    try:
        for path, content in files_dict.items():
            if create_parents:
                ensure_dir(path.parent)
            with tempfile.NamedTemporaryFile(mode='w', dir=str(path.parent), delete=False) as tmp:
                tmp.write(content)
                temps.append((Path(tmp.name), path))
        for tmp_path, path in temps:
            os.replace(str(tmp_path), str(path))
        log.info(f"Batch atomically wrote {len(files_dict)} files")
    except OSError as e:
        for tmp_path, _ in temps:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
        log.error(f"Failed batch atomic write: {e}")
        raise FileOpsError(f"Failed batch atomic write: {e}") from e

def verify_file_integrity(path: Path, expected_checksum: str, algo: str = "sha256") -> bool:
    """Verifies a file's checksum matches the expected value. Input: path (Path), expected_checksum (str), algo (str like "md5"). Output: bool (True if match). Rationale: Enhances accuracy for downloads/backups (e.g., post-sync validation); automates integrity checks, preventing corruption issues in your permission fixes or restores."""
    try:
        computed = checksum_file(path, algo)
        match = computed == expected_checksum
        log.debug(f"Verified integrity of {path} ({algo}): {match}")
        return match
    except FileOpsError:
        return False

def safe_read_large_file(path: Path, chunk_size: int = 1024*1024) -> Generator[str, None, None]:
    """Reads large files in chunks to avoid memory overload. Input: path (Path), chunk_size (int bytes). Output: Generator[str] (yields chunks). Rationale: Automates handling big logs/configs without OOM; improves simplicity for processing (e.g., search_in_file on large Nginx logs), ensuring accuracy in memory-constrained envs."""
    try:
        with open(path, 'r') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
        log.debug(f"Safe read large file {path} in chunks")
    except OSError as e:
        log.error(f"Failed to safe read {path}: {e}")
        raise FileOpsError(f"Failed to safe read {path}: {e}") from e

def auto_backup_on_write(path: Path, content: str, suffix: str = ".backup", mode: str = "w") -> None:
    """Writes content with automatic backup if file exists. Input: path (Path), content (str), suffix (str), mode (str). Output: None. Rationale: Combines write_file + simple_backup; automates safe writes (like your _backup_site_config before changes), simplifying idempotent ops with built-in rollback."""
    if path.exists():
        simple_backup(path, suffix)
    write_file(path, content, mode)

def extract_archive_auto(archive_path: Path, dest: Path = Path("."), password: Optional[str] = None) -> None:
    """Extracts archives detecting type (zip/tar.gz) automatically. Input: archive_path (Path), dest (Path), password (optional str for encrypted). Output: None. Rationale: Enhances extract_zip/archive; automates type detection for mixed formats, improving simplicity for asset handling (e.g., template downloads) with accurate extraction."""
    ensure_dir(dest)
    try:
        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path, 'r') as zf:
                if password:
                    zf.setpassword(password.encode())
                zf.extractall(str(dest))
            log.info(f"Auto extracted zip {archive_path} to {dest}")
        elif tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(str(dest))
            log.info(f"Auto extracted tar.gz {archive_path} to {dest}")
        else:
            raise FileOpsError(f"Unsupported archive type: {archive_path}")
    except OSError as e:
        log.error(f"Failed to auto extract {archive_path}: {e}")
        raise FileOpsError(f"Failed to auto extract {archive_path}: {e}") from e

def find_and_replace_in_dir(directory: Path, pattern: str, replacement: str, extensions: Optional[List[str]] = None, recursive: bool = True) -> int:
    """Finds and replaces in multiple files, returning count of changes. Input: directory (Path), pattern (str or regex), replacement (str), extensions (optional list like [".conf"]), recursive (bool). Output: int (changes made). Rationale: Automates batch edits (e.g., flag updates across sites); ensures accuracy with previews (via dry-run if added), simplifying maintenance tasks."""
    count = 0
    glob_pattern = '**/*' if recursive else '*'
    for file in directory.glob(glob_pattern):
        if file.is_file() and (not extensions or file.suffix in extensions):
            try:
                with open(file, 'r') as f:
                    content = f.read()
                new_content, num = re.subn(pattern, replacement, content)
                if num > 0:
                    with open(file, 'w') as f:
                        f.write(new_content)
                    count += num
            except OSError:
                log.warn(f"Skipped file in replace: {file}")
    log.info(f"Find and replace in {directory}: {count} changes")
    return count

def merge_files(source_paths: List[Path], dest: Path, delimiter: str = "\n") -> None:
    """Merges multiple files into one, with optional delimiter between contents. Input: source_paths (List[Path]), dest (Path), delimiter (str). Output: None. Rationale: Automates config aggregation (e.g., combining Nginx includes); improves simplicity for modular files, ensuring accurate ordering without manual concatenation."""
    contents = []
    for src in source_paths:
        contents.append(read_file(src))
    merged = delimiter.join(contents)
    write_file(dest, merged)
    log.info(f"Merged {len(source_paths)} files to {dest}")

import contextlib
@contextlib.contextmanager
def lock_file(path: Path, timeout: int = 10) -> Generator[Any, None, None]:
    """Context manager for file locking (using flock or similar). Input: path (Path), timeout (int seconds). Output: ContextManager (for with-statement). Rationale: Integrates with acquire_lock from script_helpers but file-specific; automates concurrent-safe access (e.g., during syncs), enhancing accuracy in multi-process DevOps setups."""
    if filelock is None:
        raise FileOpsError("filelock not installed")
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock = filelock.FileLock(str(lock_path), timeout=timeout)
    try:
        lock.acquire()
        log.debug(f"Acquired lock on {path}")
        yield
    finally:
        lock.release()
        log.debug(f"Released lock on {path}")