"""
Optimized Nginx Operations Module with Enhanced Sync and Manual Tag Support
- Fixed manual tag functionality
- Optimized batch operations with single validation/reload
- Improved backup and test processes
- Simplified sync without hash comparison
- Professional-grade error handling and performance
"""
from __future__ import annotations
import re
import shutil
import socket
import subprocess
import os
import pwd
import grp
import yaml
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
# Import your internal helpers
from datetime import datetime
import tempfile
from utils_devops.core.logs import get_library_logger
from utils_devops.core.files import (
    atomic_write, ensure_dir, remove_dir, remove_file,
    file_exists, dir_exists, read_file, touch
)
from utils_devops.core.systems import is_windows, is_linux, is_root, command_exists, run
from utils_devops.core.strings import render_jinja
log = get_library_logger()
# Defaults (platform-aware)
DEFAULT_NGINX_CMD = "nginx.exe" if is_windows() else "nginx"
DEFAULT_TEST_CMD = [DEFAULT_NGINX_CMD, "-t"]
DEFAULT_RELOAD_CMD = [DEFAULT_NGINX_CMD, "-s", "reload"]
DEFAULT_START_CMD = [DEFAULT_NGINX_CMD, "-g", "daemon off;"]
DEFAULT_PID_FILE = Path(r"C:\nginx\logs\nginx.pid") if is_windows() else Path("/run/nginx.pid")
DEFAULT_LOG_DIR = Path(r"C:\nginx\logs") if is_windows() else Path("/etc/nginx/logs")
DEFAULT_SITES_AVAILABLE = Path(r"C:\nginx\conf\sites-available") if is_windows() else Path("/etc/nginx/sites-available")
DEFAULT_SITES_ENABLED = Path(r"C:\nginx\conf\sites-enabled") if is_windows() else Path("/etc/nginx/sites-enabled")
DEFAULT_CACHE_BASE = Path(r"C:\nginx\cache") if is_windows() else Path("/etc/nginx/cache")
DEFAULT_CACHE_COMBINED = (Path(r"C:\nginx\conf.d") if is_windows() else Path("/etc/nginx/conf.d")) / "cache-paths.conf"
DEFAULT_DNS_COMBINED = (Path(r"C:\etc\dnsmasq.d") if is_windows() else Path("/etc/dnsmasq.d")) / "combined-dns.conf"
DEFAULT_NGINX_CONF = Path(r"C:\nginx\conf\nginx.conf") if is_windows() else Path("/etc/nginx/nginx.conf")
DUMMY_UPSTREAM = "http://127.0.0.1:81"
DEFAULT_NGINX_IP = "172.16.229.50"
class NginxOpsError(Exception):
    """Custom exception for Nginx operations errors."""
    pass
@dataclass
class Location:
    """Represents a nested location block with its own configuration."""
    path: str
    upstream: Optional[str] = None
    flags: Dict[str, Any] = field(default_factory=dict)
    upload_limit: Optional[str] = None
    description: Optional[str] = None
    manual: bool = False
@dataclass
class Site:
    """
    Structured representation of a site with enhanced manual tag support.
    """
    name: str
    upstream: str = ""
    is_serve: bool = False
    locations: List[Location] = field(default_factory=list)
    flags: Dict[str, Any] = field(default_factory=dict)
    upload_limit: Optional[str] = None
    client_max_body_size: Optional[str] = None
    force: bool = False
    description: Optional[str] = None
    manual: bool = False
    @classmethod
    def from_parsed_line(cls, line: str) -> "Site":
        """Parse a single line from sites.txt into Site object."""
        parts = re.split(r"\s+", line.strip())
        if not parts or parts[0].startswith("#"):
            raise ValueError("empty or comment line")
        name = parts[0]
        upstream = parts[1] if len(parts) > 1 else ""
        is_serve = upstream.startswith("/") or (len(upstream) > 1 and re.match(r"[A-Za-z]:\\", upstream))
        locations: List[Location] = []
        flags: Dict[str, Any] = {}
       
        for p in parts[2:]:
            if p.startswith('/'):
                if '=' in p:
                    path, up = p.split('=', 1)
                    path = path.strip()
                    up = up.strip()
                    locations.append(Location(path=path, upstream=up))
                    flags[path] = up
                else:
                    path = p.strip()
                    locations.append(Location(path=path))
                    flags[path] = True
            else:
                if '=' in p:
                    k, v = p.split('=', 1)
                    flags[k.lower().strip()] = v.strip()
                else:
                    flags[p.lower().strip()] = True
       
        site = cls(name, upstream, is_serve, locations, flags)
        return site
    @classmethod
    def from_yaml_dict(cls, data: Dict[str, Any]) -> "Site":
        """Create Site object from YAML dictionary with proper manual tag handling."""
        name = data.get("name") or data["host"]
        upstream = data["upstream"]
        is_serve = upstream.startswith("/") or (len(upstream) > 1 and re.match(r"[A-Za-z]:\\", upstream))
       
        # Parse locations with manual flag
        locations = []
        for loc_data in data.get("locations", []):
            location = Location(
                path=loc_data["path"],
                upstream=loc_data.get("upstream"),
                flags=loc_data.get("flags", {}),
                upload_limit=loc_data.get("upload_limit"),
                manual=loc_data.get("manual", False)
            )
            locations.append(location)
       
        flags = data.get("flags", {})
        upload_limit = data.get("upload_limit")
       
        # Create site with manual flag from top level or locations
        manual = data.get("manual", False)
       
        site = cls(
            name=name,
            upstream=upstream,
            is_serve=is_serve,
            locations=locations,
            flags=flags,
            upload_limit=upload_limit,
            manual=manual
        )
       
        log.debug(f"Created site '{site.name}' with manual={site.manual}")
        return site
    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert Site to YAML-compatible dictionary."""
        result = {
            "name": self.name,
            "upstream": self.upstream
        }
       
        if self.manual == True:
            result["manual"] = True
       
        if self.flags:
            result["flags"] = self.flags
           
        if self.upload_limit:
            result["upload_limit"] = self.upload_limit
           
        if self.locations:
            result["locations"] = []
            for loc in self.locations:
                loc_dict = {"path": loc.path}
                if loc.upstream:
                    loc_dict["upstream"] = loc.upstream
                if loc.flags:
                    loc_dict["flags"] = loc.flags
                if loc.upload_limit:
                    loc_dict["upload_limit"] = loc.upload_limit
                if loc.manual == True:
                    loc_dict["manual"] = True
                result["locations"].append(loc_dict)
               
        return result
   
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
   

   
def help() -> None:
    """
Nginx Operations Module — Concise AI Guide

Overview:
Manage Nginx sites with structured Site and Location objects. Supports create/remove sites, apply flags, optimized batch sync with change detection and manual tags, backups, validation (nginx -t), reloads, cache management, and limited DNS integration. Platform: Linux (full features: symlinks, dnsmasq, backups, reloads) and Windows (basic: file copies, no DNS).

Key data classes:
Site:

* name: str (required)
* upstream: str (e.g., "[http://backend:8080](http://backend:8080)" or "/path/to/root")
* is_serve: bool (static serving mode; auto-detected)
* locations: list of Location
* flags: dict (e.g., {"cache": True, "dns": True})
* upload_limit: optional str (e.g., "500M")
* manual: bool (skip automatic sync unless forced)

Location:

* path: str (e.g., "/api")
* upstream: optional str (override)
* flags: dict
* upload_limit: optional str
* manual: bool

Core manager:
NginxManager(sites_available, sites_enabled, cache_base, dry_run=False, validate_upstreams=False)

* Renders and writes configs from templates (reverse-proxy / serve)
* Enables/disables sites (symlinks on Linux)
* Backups/restores site configs as bk.<site> in sites-available
* Validates with nginx -t and reloads safely
* Manages cache dirs and optional dnsmasq entries on Linux

Main functions:
create_site(site, proxy_tpl="reverse-proxy.conf", serve_tpl="serve.conf") -> Path
- Render config, write to sites-available, enable, create logs/cache, apply upload limit
- Safety: Backup → Create → Validate → Rollback if fail → Reload → Cleanup backup

remove_site(site_name) -> None
- Remove config, symlink, logs, cache, flags; skips manual unless forced; follows safety pattern

sync_sites(sites, force_all=False) -> dict
- Optimized batch sync using change detection and manual tags
- Process: analyze changes → backup per-site or batch → perform ops → validate once → reload once → cleanup backups on success
- Returns {"success": bool, "stats": {"added": int, "removed": int, "updated": int, "total_operations": int}}

sync_from_yaml(yaml_path, force_all=False) -> dict
- Parse YAML to Site objects and call sync_sites

sync_from_list(list_path, force_all=False) -> dict
- Parse text list to Site objects and call sync_sites

apply_flag(site, flag, value=None) -> None
- Supported flags: cache, error, dns (adds dnsmasq entry on Linux), upload (e.g., "500M"), /path=upstream
- Safety: Backup → Apply → Validate → Rollback → Reload

remove_flag(site_name, flag) -> None
- Remove a flag with safety pattern

sync_flags(sites)
- Apply/remove flags per-site with safety and batch reporting

flag_exists(site, flag) -> bool

clear_cache(site=None) -> bool
- Clear or recreate cache for a site or all; Safety: Backup → Clear → Validate → Rollback → Reload

backup_site_config(site_name) -> Path
- Create or overwrite sites-available/bk.<sitename>; single backup-per-site

restore_site_config(site_name, backup_path=None) -> bool
- Restore from bk.<sitename> or provided path and validate

backup_all_sites() -> dict
- Create bk.* for all sites and return map

list_site_backups(site_name=None) -> list of Paths
- List bk.* files in sites-available

validate_nginx_config() -> bool
- Run nginx -t and return result

reload_dns() -> bool
- Reload system DNS integration (Linux only)

manage_service() -> bool
- Generic service helper for reload/start/stop Nginx

Safety & backup pattern:

1. Create bk.<sitename> in sites-available (single backup per site)
2. Execute operation
3. Validate with nginx -t
4. On failure: rollback from bk.<sitename>
5. On success: reload nginx and remove bk.<sitename>
6. If operation fails, keep bk.<sitename> for manual recovery

Backup location & naming:

* Location: sites-available (next to configs)
* Naming: bk.<sitename>
* Policy: single backup per site, auto-cleaned on success, retained on failure

YAML & text formats:
YAML example:
sites:
- name: example.com
upstream: "[https://backend:8080](https://backend:8080)"
manual: true
flags:
cache: true
dns: true
upload_limit: "500M"
locations:
- path: /api
upstream: "[https://api:3000](https://api:3000)"
flags:
cache: false

Text (sites.txt) example:
example.com [https://backend:8080](https://backend:8080) cache dns upload=500M /api=[https://api:3000](https://api:3000)
static.site /var/www/html serve error

Supported flags:

* cache — enable proxy caching
* error — enable error interception handling
* upload / upload=100M — set client_max_body_size
* dns — add dnsmasq entry (Linux only)
* /path=upstream — add location block
* serve — static file serving mode

Quick start examples:
mgr = NginxManager(dry_run=True)
site = Site("example.com", "[http://1.2.3.4](http://1.2.3.4)", flags={"cache": True})
mgr.create_site(site)
mgr.sync_from_yaml("sites.yaml", force_all=True)
path = mgr.backup_site_config("example.com")
mgr.restore_site_config("example.com")
mgr.apply_flag(site, "upload", "500M")
mgr.clear_cache("example.com")

Errors & logging:

* Operations raise NginxOpsError on failure
* Logs emitted via get_library_logger(); batch syncs return structured results and per-site outcomes

Sync behavior summary:

* skips those with manual=True unless forced
* On detected changes, backups are created, ops executed, validation performed once for the batch, Nginx reloaded once, backups cleaned up on success

Platform support:

* Linux: full features (symlinks for sites-enabled, dnsmasq integration, enhanced backup system, reloads and validations)
* Windows: basic support (file-based backups/config writes; DNS features not supported)

One-line summary:
Safe, optimized Nginx site lifecycle manager with single-per-site backups (bk.*), change-detection batching, validation + rollback safety, and platform-appropriate features (full on Linux, basic on Windows).
"""
    print(help.__doc__)
# Small helpers (kept internal to manager but available standalone)
def _find_server_blocks(text: str) -> List[Tuple[int, int, str]]:
    """Proper server block detection with nested handling."""
    blocks = []
    pos = 0
   
    while pos < len(text):
        # Find server start
        server_match = re.search(r'server\s*\{', text[pos:])
        if not server_match:
            break
           
        start = pos + server_match.start()
        depth = 0
        i = start
       
        while i < len(text):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    blocks.append((start, end, text[start:end]))
                    pos = end
                    break
            i += 1
        else:
            break # Unclosed block
   
    return blocks
def _server_has_port(block: str, port: int) -> bool:
    """Check if server block listens on specific port."""
    return bool(re.search(rf'listen\s+[^;]*\b{port}\b', block))
def _find_location_blocks(block: str, path: str = "/") -> List[Tuple[int, int, str]]:
    """Find location blocks matching path in a server block."""
    blocks = []
    esc_path = re.escape(path)
    for m in re.finditer(rf"location\s+{esc_path}\s*\{{", block):
        start = m.start()
        depth = 1
        for i in range(m.end(), len(block)):
            if block[i] == "{":
                depth += 1
            elif block[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    blocks.append((start, end, block[start:end]))
                    break
    return blocks
@dataclass
class Flag:
    """
    Represents a configurable flag for Nginx sites.
    - name: Flag identifier (e.g., 'cache', '/api')
    - template: Template file name for primary insertion
    - placement: Insertion placement (e.g., 'inside_location', 'server_443_out', 'combined')
    - target_getter: Function to get primary target file
    - secondary_template: Optional secondary template (e.g., for combined configs)
    - secondary_target_getter: Function for secondary target
    - context_adjuster: Function to adjust rendering context
    - apply_hook: Optional custom apply function (overrides template)
    - remove_hook: Optional custom remove function
    - pre_apply: Action before apply
    - post_remove: Action after remove
    """
    name: str
    template: Optional[str] = None
    placement: Optional[str] = None
    target_getter: Callable[['NginxManager', Site], Path] = lambda mgr, site: mgr.sites_available / site.name
    secondary_template: Optional[str] = None
    secondary_target_getter: Optional[Callable[['NginxManager', Site], Path]] = None
    context_adjuster: Optional[Callable[[Dict[str, Any], 'NginxManager', Site, Optional[Any]], Dict[str, Any]]] = None
    apply_hook: Optional[Callable[['NginxManager', Site, Optional[Any]], None]] = None
    remove_hook: Optional[Callable[['NginxManager', Site], None]] = None
    pre_apply: Optional[Callable[['NginxManager', Site], None]] = None
    post_remove: Optional[Callable[['NginxManager', Site], None]] = None
    def get_markers(self, site: Site) -> Tuple[str, str]:
        """Generate begin/end markers for this flag."""
        flag_part = self.name.upper().replace("/", "LOCATION-")
        return f"# ---- BEGIN {flag_part} {site.name} ----", f"# ---- END {flag_part} {site.name} ----"
    def get_secondary_markers(self, site: Site) -> Tuple[str, str]:
        """Generate markers for secondary insertion."""
        return self.get_markers(site)
# Global manager instance for convenience functions
_global_manager: Optional[NginxManager] = None
def _get_manager() -> NginxManager:
    """Get or create global manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = NginxManager()
    return _global_manager
class NginxManager:
    """
    High-level manager for Nginx site configurations using Site and Flag objects.
    Supports creation, syncing, flag application, service management.
    """
    def __init__(
            self,
            sites_available: Path = DEFAULT_SITES_AVAILABLE,
            sites_enabled: Path = DEFAULT_SITES_ENABLED,
            cache_base: Path = DEFAULT_CACHE_BASE,
            cache_combined: Path = DEFAULT_CACHE_COMBINED,
            dns_combined: Path = DEFAULT_DNS_COMBINED if is_linux() else None,
            log_dir: Path = DEFAULT_LOG_DIR,
            flags_dir: Union[Path, str] = Path("/etc/nginx/generate-sites/templates"),
            templates_dir: Optional[Path] = None,
            dry_run: bool = False,
            validate_upstreams: bool = False,
            fallback_upstream: str = DUMMY_UPSTREAM,
        ) -> None:
            self.sites_available = Path(sites_available)
            self.sites_enabled = Path(sites_enabled)
            self.cache_base = Path(cache_base)
            self.cache_combined = Path(cache_combined)
            self.dns_combined = Path(dns_combined) if dns_combined else None
            if is_windows() and self.dns_combined:
                log.warning("DNS management skipped on Windows (dnsmasq not supported)")
                self.dns_combined = None
            self.log_dir = Path(log_dir)
            self.flags_dir = Path(flags_dir)
            self.templates_dir = Path(templates_dir) if templates_dir else self.flags_dir
            self.dry_run = dry_run
            self.validate_upstreams = validate_upstreams
            self.fallback_upstream = fallback_upstream
            self.jinja_env = Environment(loader=FileSystemLoader(str(self.templates_dir)), trim_blocks=True, lstrip_blocks=True)
           
            # Ensure directories
            ensure_dir(str(self.sites_available))
            ensure_dir(str(self.sites_enabled))
            ensure_dir(str(self.cache_base))
            ensure_dir(str(self.log_dir))
           
            # Known flags registry
            self.known_flags: Dict[str, Flag] = {
                "cache": Flag(
                    "cache",
                    template="cache.conf",
                    placement="server_443_out_after_location",
                    secondary_template="cache-path.conf",
                    secondary_target_getter=lambda mgr, site: mgr.cache_combined,
                    context_adjuster=lambda ctx, mgr, site, val: ctx | {"SITE": site.name, "CACHE_DIR": str(mgr.cache_base / site.name)},
                    pre_apply=lambda mgr, site: mgr.ensure_cache_dir(site),
                    post_remove=lambda mgr, site: mgr.clear_cache(site)
                ),
                "error": Flag(
                    "error",
                    template="error.conf",
                    placement="server_443_out",
                    context_adjuster=lambda ctx, mgr, site, val: ctx | {"SITE": site.name}
                ),
                "dns": Flag(
                    "dns",
                    template="dns.conf",
                    placement="combined",
                    target_getter=lambda mgr, site: mgr.dns_combined,
                    context_adjuster=lambda ctx, mgr, site, val: ctx | {"SITE": site.name, "IP": re.match(r"https?://([\d\.]+)", site.upstream).group(1) if re.match(r"https?://([\d\.]+)", site.upstream) else DEFAULT_NGINX_IP}
                ),
                "upload": Flag(
                    "upload",
                    apply_hook=lambda mgr, site, val: mgr._set_client_max_body_size(mgr.sites_available / site.name, val or site.client_max_body_size or "10M"),
                    remove_hook=lambda mgr, site: log.info(f"To revert upload for {site.name}, re-create the site without upload flag")
                ),
                "upload_limit": Flag(
                    "upload_limit",
                    apply_hook=lambda mgr, site, val: mgr.apply_upload_limit(site, val),
                    remove_hook=lambda mgr, site: log.info(f"To revert upload limit for {site.name}, re-create the site")
                ),
            }
       
    # -------------------- Safety Operations --------------------
    def should_skip_site_operation(self, site: Site, operation: str, force: bool = False) -> Tuple[bool, str]:
        """
        Consistent manual tag checking.
        """
        # Check manual tag - if site is manual and we're not forcing, skip most operations
        if getattr(site, 'manual', False) and not (force or getattr(site, 'force', False)):
            if operation in ['create', 'remove', 'update']:
                return True, f"manual site - {operation} requires force"
            return False, "operation allowed for manual site"
        
        return False, "not manual or forced"
   
        # -------------------- Optimized Safety Operations --------------------
   
    def _batch_safe_operation(self, operations: List[Callable], operation_name: str) -> bool:
        """
        Execute multiple operations with single backup, validation, and reload.
       
        Args:
            operations: List of operations to execute
            operation_name: Name for logging
           
        Returns:
            bool: True if all operations were successful
        """
        if self.dry_run:
            log.info(f"[dry-run] Would execute {len(operations)} operations in batch")
            return True
           
        # Backup all sites before batch operation
        backup_paths = self.backup_all_sites()
        if not backup_paths:
            log.warning("No sites to backup for batch operation")
           
        try:
            # Execute all operations
            for i, operation in enumerate(operations):
                try:
                    operation()
                    log.debug(f"✅ Batch operation {i+1}/{len(operations)} completed")
                except Exception as e:
                    log.error(f"❌ Batch operation {i+1}/{len(operations)} failed: {e}")
                    raise
                   
            # Validate configuration once
            if not self.validate_nginx_config():
                log.error(f"❌ Batch {operation_name} produced invalid configuration")
                self._restore_all_backups(backup_paths)
                return False
               
            # Reload nginx once
            if self.manage_service():
                log.info(f"✅ Batch {operation_name} completed successfully")
                self._cleanup_backups(backup_paths)
                return True
            else:
                log.error(f"❌ Batch {operation_name} completed but nginx reload failed")
                self._restore_all_backups(backup_paths)
                return False
               
        except Exception as e:
            log.error(f"❌ Batch {operation_name} failed: {e}")
            self._restore_all_backups(backup_paths)
            return False
    def _restore_all_backups(self, backup_paths: Dict[str, Path]) -> None:
        """Restore all backups from a batch operation."""
        for site_name, backup_path in backup_paths.items():
            try:
                if backup_path.exists():
                    self.restore_site_config(site_name, backup_path)
                    log.info(f"🔄 Restored backup for {site_name}")
            except Exception as e:
                log.error(f"❌ Failed to restore backup for {site_name}: {e}")
    def _cleanup_backups(self, backup_paths: Dict[str, Path]) -> None:
        """Clean up backup files after successful operation."""
        for backup_path in backup_paths.values():
            try:
                if backup_path.exists():
                    backup_path.unlink()
            except Exception as e:
                log.warning(f"Could not cleanup backup {backup_path}: {e}")
               
    def sync_from_yaml(self, yaml_path: Union[str, Path], force_all: bool = False) -> Dict[str, Any]:
        """
        Optimized sync from YAML with change detection and batch operations.
       
        Args:
            yaml_path: Path to YAML file
            force_all: Whether to force all operations
           
        Returns:
            Dict with sync results and statistics
        """
        try:
            sites = self.parse_sites_yaml(yaml_path)
        except Exception as e:
            log.error(f"❌ Failed to parse YAML: {e}")
            return {"success": False, "error": str(e)}
           
        return self.sync_sites(sites, force_all)
   


    def write_site_config(self, site: Site, rendered: str) -> Path:
        """Write and enable site config."""
        tgt_avail = self.sites_available / site.name
        tgt_enabled = self.sites_enabled / site.name
        
        # Write the config directly (no optimization)
        atomic_write(str(tgt_avail), rendered)
        
        # Enable the site
        try:
            if file_exists(str(tgt_enabled)) or tgt_enabled.is_symlink():
                tgt_enabled.unlink()
            if is_windows():
                shutil.copy(str(tgt_avail), str(tgt_enabled))
            else:
                tgt_enabled.symlink_to(tgt_avail)
        except Exception as e:
            raise NginxOpsError(f"Could not enable site {site.name}: {e}")
        
        log.info(f"Wrote and enabled config for {site.name}")
        return tgt_avail

    def _ensure_site_enabled(self, site_name: str) -> None:
        """Ensure site is enabled without validation/reload."""
        config_path = self.sites_available / site_name
        enabled_path = self.sites_enabled / site_name
        
        if not (enabled_path.exists() or enabled_path.is_symlink()):
            if is_windows():
                shutil.copy(str(config_path), str(enabled_path))
            else:
                enabled_path.symlink_to(config_path)
            log.debug(f"🔗 Enabled site: {site_name}")

    def _restore_backups_batch(self, backup_files: Dict[str, Path]) -> None:
        """Restore all backups from a batch operation."""
        for site_name, backup_path in backup_files.items():
            try:
                if backup_path.exists():
                    self.restore_site_config(site_name, backup_path)
                    log.info(f"🔄 Restored backup for {site_name}")
            except Exception as e:
                log.error(f"❌ Failed to restore backup for {site_name}: {e}")

    def _remove_site_direct(self, site_name: str) -> None:
        """Remove site directly without validation/reload."""
        # Remove from enabled
        enabled_path = self.sites_enabled / site_name
        if enabled_path.exists() or enabled_path.is_symlink():
            enabled_path.unlink(missing_ok=True)
            log.debug(f"🔓 Disabled site: {site_name}")
        
        # Remove from available
        config_path = self.sites_available / site_name
        if config_path.exists():
            config_path.unlink()
            log.debug(f"🗑️ Removed config: {site_name}")


    def sync_from_list(self, list_path: Union[str, Path], force_all: bool = False) -> Dict[str, Any]:
        """Complete sync from sites.txt with optimized operations.
    
        Args:
            list_path: Path to sites.txt file
            force_all: Whether to force all operations
        
        Returns:
            Dict with sync results
        """
        # FIX: Use the same sync_sites function for consistency
        sites = self.parse_sites_list(list_path)
        return self.sync_sites(sites, force_all)

    # FIX: Add missing method implementations
    def _set_client_max_body_size(self, conf_path: Path, val: str) -> None:
        """Set client_max_body_size in server block."""
        if self.dry_run:
            return
        txt = read_file(str(conf_path))
        blocks = _find_server_blocks(txt)
        modified = False
        for start, endpos, block in blocks:
            if not _server_has_port(block, 443):
                continue
            pattern = r"client_max_body_size\s+[^;]+;"
            if re.search(pattern, block):
                new_block = re.sub(pattern, f"client_max_body_size {val};", block)
            else:
                server_name_m = re.search(r"server_name\s+[^;]+;", block)
                insert_idx = server_name_m.end() if server_name_m else block.find("{") + 1
                new_block = block[:insert_idx] + f"\n client_max_body_size {val};" + block[insert_idx:]
            txt = txt[:start] + new_block + txt[endpos:]
            modified = True
            break
        if modified:
            atomic_write(str(conf_path), txt)

    # FIX: Add missing regex_replace function
    def regex_replace(text: str, pattern: str, replacement: str, flags: int = 0) -> str:
        """Replace pattern in text with replacement."""
        return re.sub(pattern, replacement, text, flags=flags)

    # FIX: Add missing regex_search function  
    def regex_search(text: str, pattern: str, flags: int = 0) -> Optional[re.Match]:
        """Search for pattern in text."""
        return re.search(pattern, text, flags=flags)

    # FIX: Add missing method for the upload flag hook
    def apply_upload_limit(self, site: Site, limit: str) -> None:
        """Apply upload limit from YAML configuration."""
        if not limit:
            return
            
        # Validate upload limit format
        if not re.match(r'^\d+[KM]?$', str(limit).upper()):
            log.warning(f"Invalid upload limit format: {limit}, using default")
            limit = "10M"
        
        try:
            self._set_client_max_body_size(self.sites_available / site.name, limit)
            log.info(f"Applied upload limit {limit} to {site.name}")
        except Exception as e:
            raise NginxOpsError(f"Failed to apply upload limit {limit} to {site.name}: {e}")
    
    def sync_sites(self, sites: List[Site], force_all: bool = False) -> Dict[str, Any]:
        """Simple site sync without hash comparison."""
        existing_sites = set(self.list_available_sites())
        desired_sites = {s.name for s in sites}
        site_map = {s.name: s for s in sites}
        
        # Analyze changes
        to_add = []
        to_update = []
        to_remove = []
        skipped = []
        
        for site_name in desired_sites - existing_sites:
            site = site_map[site_name]
            skip, reason = self.should_skip_site_operation(site, 'create', force_all)
            if skip:
                skipped.append((site_name, reason))
            else:
                to_add.append(site)
                
        for site_name in existing_sites - desired_sites:
            dummy_site = Site(name=site_name)
            skip, reason = self.should_skip_site_operation(dummy_site, 'remove', force_all)
            if skip:
                skipped.append((site_name, reason))
            else:
                to_remove.append(site_name)
                
        for site_name in existing_sites & desired_sites:
            site = site_map[site_name]
            skip, skip_reason = self.should_skip_site_operation(site, 'update', force_all)
        
            if skip:
                skipped.append((site_name, skip_reason))
            else:
                to_update.append(site)
        
        # Log skipped operations
        for site_name, reason in skipped:
            log.debug(f"🔄 Skipping {site_name}: {reason}")
        
        # Use batch operations for efficiency
        operations = []
        stats = {
            "added": len(to_add),
            "removed": len(to_remove), 
            "updated": len(to_update),
            "skipped": len(skipped),
            "total_operations": len(to_add) + len(to_remove) + len(to_update)
        }
        
        if stats["total_operations"] == 0:
            log.info("✅ Everything is in sync - no operations needed")
            return {"success": True, "stats": stats}
        
        # Prepare batch operations
        batch_operations = []
        
        # Add operations
        for site in to_add + to_update:
            try:
                # Render config for site
                upstream = self.validate_upstream(site.upstream or "", self.fallback_upstream) if self.validate_upstreams else (site.upstream or "")
                tpl = "serve.conf" if site.is_serve else "reverse-proxy.conf"
                context = {
                    "SITE": site.name,
                    "IP_ADDRESS": upstream,
                    "ROOT_PATH": upstream if site.is_serve else "",
                    "CLIENT_MAX_BODY_SIZE": site.upload_limit or site.client_max_body_size or "10M",
                }
                
                rendered = self.render_template(tpl, context)
                
                if site.locations:
                    location_blocks = self.build_location_blocks_extended(site.locations, "location.conf")
                    rendered += "\n" + "\n".join(location_blocks)
                
                batch_operations.append(("create", site, rendered))
            except Exception as e:
                log.error(f"❌ Failed to render config for {site.name}: {e}")
                return {"success": False, "stats": stats, "error": f"Render failed for {site.name}: {e}"}
        
        # Remove operations
        for site_name in to_remove:
            batch_operations.append(("remove", site_name, None))
        
        # Execute in single batch
        success = self._execute_batch_sync(batch_operations, f"sync {stats['total_operations']} sites")
        
        return {
            "success": success,
            "stats": stats
        }

    def _execute_batch_sync(self, operations: List[tuple], operation_name: str) -> bool:
        """Execute batch sync operations with single validation/reload."""
        if self.dry_run:
            log.info(f"[dry-run] Would execute {len(operations)} operations: {operation_name}")
            return True
            
        # Create backups for all affected sites
        backup_files = {}
        sites_to_backup = [op[1].name for op in operations if op[0] in ["create", "update"]]
        sites_to_backup.extend([op[1] for op in operations if op[0] == "remove"])
        
        for site_name in sites_to_backup:
            try:
                backup_path = self.backup_site_config(site_name)
                if backup_path:
                    backup_files[site_name] = backup_path
            except Exception as e:
                log.warning(f"Could not backup {site_name}: {e}")

        try:
            # Execute all file operations
            for op_type, target, content in operations:
                try:
                    if op_type == "create":
                        site, rendered = target, content
                        self.write_site_config(site, rendered)
                        self._ensure_site_enabled(site.name)
                        self._ensure_logs(site.name)
                        self._ensure_cache(site.name)
                        
                        
                        # Apply flags in batch later
                        
                    elif op_type == "remove":
                        site_name = target
                        self._remove_site_direct(site_name)
                        
                except Exception as e:
                    log.error(f"❌ Batch operation failed for {target if op_type == 'remove' else target.name}: {e}")
                    raise

            # Apply all flags in batch after all configs are written
            self._apply_flags_batch([op[1] for op in operations if op[0] == "create"])

            # Single validation for all changes
            if not self.validate_nginx_config():
                log.error(f"❌ Batch {operation_name} produced invalid configuration")
                self._restore_backups_batch(backup_files)
                return False

            # Single reload
            if self.manage_service():
                log.info(f"✅ {operation_name} completed successfully")
                self._cleanup_backups(backup_files)
                return True
            else:
                log.error(f"❌ {operation_name} completed but nginx reload failed")
                self._restore_backups_batch(backup_files)
                return False
                
        except Exception as e:
            log.error(f"❌ Batch {operation_name} failed: {e}")
            self._restore_backups_batch(backup_files)
            return False

    def _apply_flags_batch(self, sites: List[Site]) -> None:
        """Apply flags in batch for multiple sites."""
        all_flag_operations = []
        
        for site in sites:
            if not site.flags:
                continue
                
            for flag, value in site.flags.items():
                if flag != "force":
                    all_flag_operations.append((site, flag, value))
        
        if not all_flag_operations:
            return
            
        # Apply all flags without individual validations
        for site, flag, value in all_flag_operations:
            try:
                self._apply_flag_unsafe(site, flag, value)
            except Exception as e:
                log.error(f"❌ Failed to apply flag {flag} to {site.name}: {e}")

    def sync_flags_for_site(self, site: Site, force: bool = False) -> None:
        """Optimized flag sync that only applies necessary changes."""
        skip, reason = self.should_skip_site_operation(site, 'update', force)
        if skip:
            log.info(f"📝 Skipping flag sync for manual site {site.name}: {reason}")
            return

        config_path = self.sites_available / site.name
        if not file_exists(str(config_path)):
            log.warning(f"Site config not found: {site.name}, skipping flag sync")
            return
        
        # Get current flags from config (use cached content if available)
        current_content = read_file(str(config_path))  

        current_flags = self._extract_flags_from_content(current_content, site)
    
        # Determine desired flags
        desired_flags = set(site.flags.keys()) if site.flags else set()
        desired_locations = {loc.path for loc in site.locations}
    
        # Calculate changes
        flags_to_add = desired_flags - current_flags
        flags_to_remove = current_flags - desired_flags
        flags_to_update = set()
    
        # Check if existing flags need updates
        for flag in desired_flags & current_flags:
            if self._flag_needs_update(site, flag, current_content):
                flags_to_update.add(flag)
    
        # FIX: Batch flag operations to avoid multiple backups/reloads
        if flags_to_remove or flags_to_add or flags_to_update:
            def batch_flag_operation():
                # Remove flags first
                for flag in flags_to_remove:
                    if flag != "force":
                        self._remove_flag_unsafe(site.name, flag)
                    
                # Add/update flags
                for flag in flags_to_add | flags_to_update:
                    if flag != "force":
                        value = site.flags[flag] if site.flags and site.flags[flag] is not True else None
                        self._apply_flag_unsafe(site, flag, value)
            
                # Apply upload limit if specified
                if site.upload_limit:
                    self._apply_upload_limit_unsafe(site, site.upload_limit)
            
            # Use single safe operation for all flag changes
            self._safe_operation(batch_flag_operation, f"Sync flags for {site.name}", site.name)
        else:
            log.debug(f"✅ No flag changes needed for {site.name}")
            
    def _apply_flag_unsafe(self, site: Site, flag: str, value: Optional[Any] = None) -> None:
        """Apply flag without backup/validation - for use in batch operations."""
        if flag in self.known_flags:
            f = self.known_flags[flag]
        elif flag.startswith("/"):
            # Find the location object to get its specific upstream
            location_upstream = value
            for loc in site.locations:
                if loc.path == flag:
                    location_upstream = loc.upstream or value or site.upstream
                    break
        
            f = Flag(
                name=flag,
                template="location.conf",
                placement="server_443_out",
                context_adjuster=lambda ctx, mgr, site, val: ctx | {"PATH": flag, "UPSTREAM": location_upstream or ""},
            )
        else:
            log.warning(f"Unknown flag: {flag}")
            return
        
        if f.pre_apply:
            f.pre_apply(self, site)
        
        if f.apply_hook:
            f.apply_hook(self, site, value)
        elif f.template:
            context = {"SITE": site.name}
            if f.context_adjuster:
                context = f.context_adjuster(context, self, site, value)
            snippet = self.render_template(f.template, context)
            begin, end = f.get_markers(site)
            target = f.target_getter(self, site)
        
            if f.placement == "combined":
                self._apply_entry_to_combined(target, snippet, begin, end)
            else:
                self._apply_snippet(target, snippet, f.placement or "server_443_out", begin, end)
            
            if f.secondary_template:
                sec_context = {"SITE": site.name}
                if f.context_adjuster:
                    sec_context = f.context_adjuster(sec_context, self, site, value)
                sec_snippet = self.render_template(f.secondary_template, sec_context)
                sec_begin, sec_end = f.get_secondary_markers(site)
                sec_target = f.secondary_target_getter(self, site)
                self._apply_entry_to_combined(sec_target, sec_snippet, sec_begin, sec_end)
            
        log.debug(f"Applied flag {flag} to {site.name}")

    def _remove_flag_unsafe(self, site_name: str, flag: str) -> None:
        """Remove flag without backup/validation - for use in batch operations."""
        site = Site(name=site_name) # dummy for markers
        if flag in self.known_flags:
            f = self.known_flags[flag]
        elif flag.startswith("/"):
            f = Flag(name=flag)
        else:
            log.debug(f"Unknown flag for removal: {flag}")
            return
        
        if f.remove_hook:
            f.remove_hook(self, site)
        elif f.template or flag.startswith("/"):
            begin, end = f.get_markers(site)
            target = f.target_getter(self, site)
            self._remove_region(target, begin, end)
            if f.secondary_template:
                sec_begin, sec_end = f.get_secondary_markers(site)
                sec_target = f.secondary_target_getter(self, site)
                self._remove_entry_from_combined(sec_target, sec_begin, sec_end)
            
        if f.post_remove:
            f.post_remove(self, site)
        log.debug(f"Removed flag {flag} from {site_name}")

    def _apply_upload_limit_unsafe(self, site: Site, limit: str) -> None:
        """Apply upload limit without backup/validation - for use in batch operations."""
        config_path = self.sites_available / site.name
        if not file_exists(str(config_path)):
            return
        
        content = read_file(str(config_path))
        
        # Pattern to find client_max_body_size
        pattern = r'client_max_body_size\s+[^;]+;'
        replacement = f'client_max_body_size {limit};'
        
        if re.search(pattern, content):
            # Replace existing
            new_content = re.sub(pattern, replacement, content)
        else:
            # Add to server block
            server_pattern = r'(server\s*\{)'
            new_content = re.sub(server_pattern, rf'\1\n    client_max_body_size {limit};', content)
        
        atomic_write(str(config_path), new_content)
        log.debug(f"Applied upload limit {limit} to {site.name}")
    
    
    def _extract_flags_from_content(self, content: str, site: Site) -> set:
        """Extract currently applied flags from config content."""
        flags = set()
       
        # Check for known flags
        for flag_name, flag_obj in self.known_flags.items():
            begin, end = flag_obj.get_markers(site)
            if begin in content and end in content:
                flags.add(flag_name)
               
        # Check for location flags
        location_pattern = r'location\s+([^\s\{]+)\s*\{'
        locations = re.findall(location_pattern, content)
        for loc in locations:
            if loc != "/":
                flags.add(loc)
               
        return flags
    
    def _flag_needs_update(self, site: Site, flag: str, current_content: str) -> bool:
        """Check if a flag needs to be updated."""
        if flag in self.known_flags:
            flag_obj = self.known_flags[flag]
        elif flag.startswith("/"):
            flag_obj = Flag(name=flag)
        else:
            return False
           
        begin, end = flag_obj.get_markers(site)
        pattern = re.escape(begin) + r"(.*?)" + re.escape(end)
        match = re.search(pattern, current_content, flags=re.DOTALL)
       
        if not match:
            return True
           
        current_snippet = match.group(1).strip()
       
        # Generate desired snippet
        if flag_obj.template:
            context = {"SITE": site.name}
            if flag_obj.context_adjuster:
                context = flag_obj.context_adjuster(context, self, site, site.flags.get(flag))
            desired_snippet = self.render_template(flag_obj.template, context).strip()
           
            return current_snippet != desired_snippet
           
        return False
    # -------------------- Fast Validation & Backup --------------------
   
    def fast_validate_configs(self, config_paths: List[Path]) -> Tuple[bool, Dict[Path, str]]:
        """
        Fast validation of multiple config files.
       
        Args:
            config_paths: List of config paths to validate
           
        Returns:
            Tuple[bool, Dict[Path, str]]: (success, error_messages)
        """
        if self.dry_run:
            return True, {}
           
        errors = {}
       
        # Create temporary config that includes all files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as temp_file:
            temp_content = """
            events { worker_connections 1024; }
            http {
                include /etc/nginx/mime.types;
            %s
            }
            """ % "\n".join([f" include {path};" for path in config_paths])
           
            temp_file.write(temp_content)
            temp_file.flush()
           
            try:
                result = run(["nginx", "-t", "-c", temp_file.name], capture=True, no_die=True)
                if result.returncode != 0:
                    # Parse errors to specific files if possible
                    errors[Path("global")] = result.stdout
            finally:
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass
                   
        return len(errors) == 0, errors
    def smart_backup_sites(self, site_names: List[str]) -> Dict[str, Path]:
        """
        Smart backup that only backs up sites that will be changed.
       
        Args:
            site_names: List of site names to backup
           
        Returns:
            Dict mapping site names to backup paths
        """
        backups = {}
        for site_name in site_names:
            config_path = self.sites_available / site_name
            if config_path.exists():
                try:
                    backup_path = self.backup_site_config(site_name)
                    backups[site_name] = backup_path
                except Exception as e:
                    log.error(f"Failed to backup {site_name}: {e}")
                   
        return backups
    
    def _safe_operation(self, operation: Callable, operation_name: str, site_name: Optional[str] = None, site: Optional[Site] = None, force: bool = False) -> bool:
        """Execute an operation with manual site protection, backup, validation, and service management.
        
            Args:
                operation: The function to execute
                operation_name: Name of the operation for logging
                site_name: Optional site name for backup
                site: Optional Site object for manual check
                force: Whether to force operation for manual sites
            
            Returns:
                bool: True if operation was successful
            """  
        # Manual site protection - check first before any backup/operations
        if site and site.manual and not force:
            skip, reason = self.should_skip_site_operation(site, operation_name.split()[-1] if ' ' in operation_name else operation_name, force)
            if skip:
                log.info(f"📝 Skipping {operation_name} for manual site {site.name}: {reason}")
                return True # Return True since skipping a manual site is "successful"
        
        # Backup before operation if site specified
        backup_path = None
        if site_name:
            try:
                backup_path = self.backup_site_config(site_name, suffix=f"pre_{operation_name}")
                log.info(f"📋 Created backup for {site_name} before {operation_name}")
            except Exception as e:
                log.warning(f"Could not backup {site_name} before {operation_name}: {e}")
        
        try:
            # Execute the operation
            operation()
            
            # Validate configuration
            if not self.validate_nginx_config():
                log.error(f"❌ {operation_name} produced invalid configuration")
                # Restore backup if available
                if backup_path and site_name and backup_path.exists():
                    self.restore_site_config(site_name, backup_path)
                    log.info(f"🔄 Restored backup for {site_name} due to validation failure")
                return False
            
            # Reload nginx service
            if self.manage_service():
                log.info(f"✅ {operation_name} completed successfully and nginx reloaded")
                # Remove the pre-operation backup since everything succeeded
                if backup_path and backup_path.exists():
                    backup_path.unlink()
                return True
            else:
                log.error(f"❌ {operation_name} completed but nginx reload failed")
                # Restore backup if available
                if backup_path and site_name and backup_path.exists():
                    self.restore_site_config(site_name, backup_path)
                    log.info(f"🔄 Restored backup for {site_name} due to reload failure")
                return False
                
        except Exception as e:
            log.error(f"❌ {operation_name} failed: {e}")
            # Restore backup if available
            if backup_path and site_name and backup_path.exists():
                try:
                    self.restore_site_config(site_name, backup_path)
                    log.info(f"🔄 Restored backup for {site_name} due to operation failure")
                except Exception as restore_error:
                    log.error(f"❌ Failed to restore backup: {restore_error}")
            return False
    
    def validate_nginx_config(self) -> bool:
        """Validate the entire nginx configuration."""
        if self.dry_run:
            log.info("[dry-run] Would validate nginx configuration")
            return True
           
        try:
            result = run(["nginx", "-t"], capture=True, no_die=True)
            if result.returncode == 0:
                log.debug("✅ Nginx configuration is valid")
                return True
            else:
                log.error(f"❌ Nginx configuration validation failed: {result.stdout}")
                return False
        except Exception as e:
            log.error(f"❌ Nginx configuration validation error: {e}")
            return False
    # -------------------- Backup & Restore --------------------
    def backup_site_config(self, site_name: str, suffix: Optional[str] = None) -> Path:
        """Backup site configuration to sites-available with bk. prefix.
       
        Args:
            site_name: Name of the site to backup
            suffix: Optional suffix for backup file (not used in final name)
           
        Returns:
            Path to backup file
           
        Raises:
            NginxOpsError: If backup fails
        """
        config_path = self.sites_available / site_name
        if not file_exists(str(config_path)):
            raise NginxOpsError(f"Site config not found: {config_path}")
       
        # Backup file is in the same directory with bk. prefix
        backup_name = f"bk.{site_name}"
        backup_path = self.sites_available / backup_name
       
        if self.dry_run:
            log.info(f"[dry-run] Would backup {site_name} to {backup_path}")
            return backup_path
           
        try:
            # Remove existing backup if it exists (only keep one)
            if backup_path.exists():
                backup_path.unlink()
               
            shutil.copy2(str(config_path), str(backup_path))
            log.info(f"📋 Backed up {site_name} to {backup_path}")
            return backup_path
        except Exception as e:
            raise NginxOpsError(f"Failed to backup {site_name}: {e}")
   
    def restore_site_config(self, site_name: str, backup_path: Optional[Path] = None) -> bool:
        """Restore site configuration from backup.
       
        Args:
            site_name: Name of the site to restore
            backup_path: Specific backup file to use (uses standard bk. file if None)
           
        Returns:
            bool: True if restore was successful
        """
        if backup_path is None:
            # Use the standard backup file in sites-available
            backup_path = self.sites_available / f"bk.{site_name}"
       
        if not file_exists(str(backup_path)):
            raise NginxOpsError(f"Backup file not found: {backup_path}")
       
        config_path = self.sites_available / site_name
       
        if self.dry_run:
            log.info(f"[dry-run] Would restore {site_name} from {backup_path}")
            return True
           
        try:
            # Create temporary backup of current config before restore
            current_backup = None
            if file_exists(str(config_path)):
                current_backup = self.backup_site_config(site_name, suffix="temp_pre_restore")
                log.info(f"📋 Backed up current config before restore: {current_backup}")
           
            shutil.copy2(str(backup_path), str(config_path))
            log.info(f"✅ Restored {site_name} from {backup_path}")
           
            # Validate the restored config
            if self.validate_nginx_config():
                log.info(f"✅ Restored config for {site_name} is valid")
                # Remove temporary backup since restore was successful
                if current_backup and current_backup.exists():
                    current_backup.unlink()
                return True
            else:
                log.error(f"❌ Restored config for {site_name} is invalid")
                # Restore the pre-restore backup if available
                if current_backup and current_backup.exists():
                    shutil.copy2(str(current_backup), str(config_path))
                    log.info(f"🔄 Reverted to pre-restore backup due to validation failure")
                    # Remove temporary backup after revert
                    current_backup.unlink()
                return False
               
        except Exception as e:
            raise NginxOpsError(f"Failed to restore {site_name}: {e}")
   
    def list_site_backups(self, site_name: Optional[str] = None) -> List[Path]:
        """List available backups for sites.
       
        Args:
            site_name: Optional site name to filter backups
           
        Returns:
            List of backup paths
        """
        if site_name:
            # Only one backup per site now
            backup_path = self.sites_available / f"bk.{site_name}"
            return [backup_path] if backup_path.exists() else []
        else:
            # Find all bk.* files in sites_available
            backups = list(self.sites_available.glob("bk.*"))
            return sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True)
       
    def _validate_single_config(self, config_path: Path) -> bool:
        """Validate a single configuration file.
       
        Args:
            config_path: Path to config file to validate
           
        Returns:
            bool: True if config is valid
        """
        if self.dry_run:
            return True
           
        try:
            # Create a temporary nginx config that includes only this site
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as temp_file:
                temp_content = f"""
                events {{ worker_connections 1024; }}
                http {{
                    include /etc/nginx/mime.types;
                    include {config_path};
                }}
                """
                temp_file.write(temp_content)
                temp_file.flush()
               
                # Test with nginx
                result = run(["nginx", "-t", "-c", temp_file.name], capture=True, no_die=True)
               
                # Clean up temp file
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass
                   
                return result.returncode == 0
               
        except Exception as e:
            log.debug(f"Config validation failed for {config_path}: {e}")
            return False
   
    def backup_all_sites(self) -> Dict[str, Path]:
        """Backup all site configurations.
       
        Returns:
            Dict mapping site names to backup paths
        """
        sites = self.list_available_sites()
        backups = {}
       
        for site_name in sites:
            try:
                backup_path = self.backup_site_config(site_name, suffix="batch")
                backups[site_name] = backup_path
            except Exception as e:
                log.error(f"Failed to backup {site_name}: {e}")
       
        log.info(f"✅ Backed up {len(backups)} sites")
        return backups
   
    def create_site_backup(self, site_name: str) -> bool:
        """Create backup of site configuration alongside the site in sites-available.
    
        Returns:
            bool: True if backup was successful
        """
        try:
            backup_path = self.backup_site_config(site_name)
            log.info(f"📋 Backup created: {backup_path}")
            return True
        except Exception as e:
            log.error(f"❌ Failed to create backup for {site_name}: {e}")
            return False
    # -------------------- YAML Support --------------------
       
    def parse_sites_yaml(self, yaml_path: Union[str, Path]) -> List[Site]:
        """Parse YAML configuration into Site objects.
       
        Args:
            yaml_path: Path to YAML file
           
        Returns:
            List[Site]: Parsed site objects
           
        Raises:
            NginxOpsError: If YAML parsing fails
        """
        p = Path(yaml_path)
        if not file_exists(str(p)):
            raise NginxOpsError(f"YAML file not found: {p}")
       
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise NginxOpsError(f"Invalid YAML in {p}: {e}")
        except Exception as e:
            raise NginxOpsError(f"Failed to read YAML file {p}: {e}")
       
        # Handle both formats: list of sites or {sites: [...]}
        if isinstance(data, dict) and "sites" in data:
            sites_data = data["sites"]
        elif isinstance(data, list):
            sites_data = data
        else:
            raise NginxOpsError(f"YAML file should contain a list of sites or 'sites' key, got {type(data)}")
       
        sites = []
        for site_data in sites_data:
            try:
                site = Site.from_yaml_dict(site_data)
                sites.append(site)
            except KeyError as e:
                raise NginxOpsError(f"Missing required field in YAML: {e}")
            except Exception as e:
                raise NginxOpsError(f"Failed to parse site from YAML: {e}")
       
        log.info(f"Parsed {len(sites)} sites from YAML: {p}")
        return sites
    def generate_sites_yaml(self, sites: List[Site]) -> str:
        """Generate YAML configuration from Site objects.
       
        Args:
            sites: List of Site objects
           
        Returns:
            str: YAML formatted string with proper 'sites:' root
        """
        yaml_data = {
            "sites": [site.to_yaml_dict() for site in sites] # Wrap in "sites" root
        }
       
        return yaml.dump(yaml_data, default_flow_style=False, indent=2, allow_unicode=True, sort_keys=False)
    def validate_site_structure(self, site_config: Dict) -> Tuple[bool, List[str]]:
        """Validate YAML site structure against schema.
       
        Args:
            site_config: Dictionary from YAML
           
        Returns:
            Tuple[bool, List[str]]: (success, error_messages)
        """
        errors = []
       
        # Required fields - check for both 'name' and 'host' (backward compatibility)
        if "name" not in site_config and "host" not in site_config:
            errors.append("Missing required field: name (or host)")
        if "upstream" not in site_config:
            errors.append("Missing required field: upstream")
       
        # Validate host/name format
        name = site_config.get("name") or site_config.get("host")
        if name and not re.match(r'^[a-zA-Z0-9.*_-]+$', name):
            errors.append(f"Invalid name format: {name}")
       
        # Validate upstream format
        if "upstream" in site_config:
            upstream = site_config["upstream"]
            if not (upstream.startswith(('http://', 'https://', '/')) or re.match(r'[A-Za-z]:\\', upstream)):
                errors.append(f"Invalid upstream format: {upstream}")
       
        # Validate locations
        for i, loc in enumerate(site_config.get("locations", [])):
            if "path" not in loc:
                errors.append(f"Location {i} missing required field: path")
            elif not loc["path"].startswith('/'):
                errors.append(f"Location path must start with '/': {loc['path']}")
       
        return len(errors) == 0, errors
    def migrate_text_to_yaml(self, text_path: Union[str, Path], yaml_path: Union[str, Path]) -> None:
        """Migrate from old text format to new YAML format.
       
        Args:
            text_path: Path to old sites.txt
            yaml_path: Path for new YAML file
        """
        # Parse existing text format
        sites = self.parse_sites_list(text_path)
       
        # Generate YAML
        yaml_content = self.generate_sites_yaml(sites)
       
        # Write YAML file
        if self.dry_run:
            log.info(f"[dry-run] Would migrate {text_path} to {yaml_path}")
            log.info(f"YAML content:\n{yaml_content}")
        else:
            atomic_write(str(yaml_path), yaml_content)
            log.info(f"Migrated {text_path} to {yaml_path}")
    # -------------------- Parsing --------------------
    def parse_sites_list(self, list_path: Union[str, Path]) -> List[Site]:
        """Parse sites.txt into list of Site objects."""
        p = Path(list_path)
        if not file_exists(str(p)):
            raise NginxOpsError(f"sites.txt not found: {p}")
        sites: List[Site] = []
        for line in read_file(str(p)).splitlines():
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            try:
                sites.append(Site.from_parsed_line(s))
            except ValueError as e:
                log.warning(f"Skipping invalid line in sites.txt: {s} ({e})")
        log.info(f"Parsed {len(sites)} sites from {p}")
        return sites
    def parse_template_meta(self, template_path: Path) -> Dict[str, str]:
        """Parse META directives from template headers."""
        if not template_path.exists():
            return {}
       
        content = template_path.read_text(encoding="utf-8")
        meta = {}
       
        # Parse # META: key=value, key2=value2
        meta_match = re.search(r'^#\s*META:\s*(.+)$', content, flags=re.MULTILINE)
        if meta_match:
            meta_line = meta_match.group(1).strip()
            for item in re.split(r'\s*,\s*', meta_line):
                if '=' in item:
                    key, value = item.split('=', 1)
                    meta[key.strip()] = value.strip()
                else:
                    meta[item.strip()] = "true"
       
        return meta
    def _strip_meta_lines(self, content: str) -> str:
        """Remove META lines from template content."""
        return re.sub(r'(?m)^[ \t]*#\s*META:.*\n?', '', content)
    # -------------------- Templates & Rendering --------------------
    def render_template(self, name: Union[str, Path], context: Dict[str, Any]) -> str:
        """Render a Jinja template with context."""
        tpl_name = str(name)
        try:
            tpl = self.jinja_env.get_template(tpl_name)
            return tpl.render(**context)
        except TemplateNotFound:
            log.warning(f"Template not found: {tpl_name}, falling back to raw render")
            return render_jinja(tpl_name, context)
        except Exception as e:
            raise NginxOpsError(f"Template rendering failed for {tpl_name}: {e}")
    def build_location_blocks(self, locations: List[Tuple[str, str]], location_tpl: Union[str, Path] = "location.conf") -> List[str]:
        """Build location blocks from templates (used in create_site)."""
        blocks: List[str] = []
        for path, up in locations:
            ctx = {"PATH": path, "UPSTREAM": up}
            blocks.append(self.render_template(location_tpl, ctx))
        return blocks
    def build_location_blocks_extended(self, locations: List[Location], location_tpl: Union[str, Path] = "location.conf") -> List[str]:
        """Build location blocks with full YAML support.
       
        Args:
            locations: List of Location objects
            location_tpl: Template for location blocks
           
        Returns:
            List[str]: Rendered location blocks
        """
        blocks = []
        for location in locations:
            # Build context for location
            ctx = {
                "PATH": location.path,
                "UPSTREAM": location.upstream or "", # Use location upstream or empty
                "CLIENT_MAX_BODY_SIZE": location.upload_limit or "" # Location-specific upload limit
            }
           
            # Render the location block
            block = self.render_template(location_tpl, ctx)
            blocks.append(block)
           
            # Apply location-specific flags
            if location.flags:
                # Create a temporary site-like object for the location
                loc_site = Site(
                    name=f"location_{location.path.replace('/', '_')}",
                    upstream=location.upstream or "",
                    flags=location.flags,
                    upload_limit=location.upload_limit
                )
                # Apply flags specific to this location
                for flag_name, flag_value in location.flags.items():
                    if flag_name in self.known_flags:
                        self.apply_flag(loc_site, flag_name, flag_value)
       
        return blocks
    # -------------------- Upload Limit Management --------------------
    def apply_upload_limit(self, site: Site, limit: str) -> None:
        """Apply upload limit from YAML configuration.
       
        Args:
            site: Site object
            limit: Upload limit string (e.g., "0", "500M")
           
        Raises:
            NginxOpsError: If application fails
        """
        if not limit:
            return
           
        # Validate upload limit format
        if not re.match(r'^\d+[KM]?$', str(limit).upper()):
            log.warning(f"Invalid upload limit format: {limit}, using default")
            limit = "10M"
       
        try:
            self._set_client_max_body_size(self.sites_available / site.name, limit)
            log.info(f"Applied upload limit {limit} to {site.name}")
        except Exception as e:
            raise NginxOpsError(f"Failed to apply upload limit {limit} to {site.name}: {e}")
    # -------------------- Validation --------------------
   
    def validate_all_configs(self) -> Tuple[bool, Dict[str, str]]:
        """Validate all site configurations.
       
        Returns:
            Tuple of (overall_success, error_messages_by_site)
        """
        sites = self.list_available_sites()
        errors = {}
        all_valid = True
       
        for site_name in sites:
            config_path = self.sites_available / site_name
            if self._validate_single_config(config_path):
                log.debug(f"✅ Config valid: {site_name}")
            else:
                errors[site_name] = "Configuration validation failed"
                all_valid = False
                log.error(f"❌ Config invalid: {site_name}")
       
        return all_valid, errors
   
    def safe_apply_flag(self, site: Site, flag: str, value: Optional[Any] = None) -> bool:
        """Apply flag with backup and validation.
       
        Args:
            site: Site to apply flag to
            flag: Flag name
            value: Flag value
           
        Returns:
            bool: True if application was successful
        """
        config_path = self.sites_available / site.name
        if not file_exists(str(config_path)):
            log.warning(f"Site config not found: {site.name}")
            return False
       
        try:
            # Backup before applying flag
            backup_path = self.backup_site_config(site.name, suffix=f"pre_{flag}")
           
            # Apply the flag
            self.apply_flag(site, flag, value)
           
            # Validate after applying flag
            if self._validate_single_config(config_path):
                log.info(f"✅ Successfully applied flag {flag} to {site.name}")
                return True
            else:
                # Rollback if validation fails
                self.restore_site_config(site.name, backup_path)
                log.error(f"❌ Flag {flag} made config invalid for {site.name}, rolled back")
                return False
               
        except Exception as e:
            log.error(f"❌ Failed to apply flag {flag} to {site.name}: {e}")
            return False
       
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def validate_upstream(self, upstream: str, fallback: str = DUMMY_UPSTREAM, timeout: int = 1, use_http: bool = True) -> str:
        """Validate upstream reachability."""
        if not self.validate_upstreams:
            return upstream # Skip validation if disabled
           
        match = re.match(r'(https?://)?([^:/]+)(:\d+)?(/.*)?', upstream)
        if not match:
            log.warning(f"Invalid upstream: {upstream}, using fallback")
            return fallback
        scheme, host, port, _ = match.groups()
        scheme = scheme or "http://"
        port = port or ""
        if use_http:
            url = f"{scheme}{host}{port}"
            try:
                resp = requests.head(url, timeout=timeout)
                if resp.status_code < 400:
                    return upstream
            except Exception as e:
                log.debug(f"Upstream HTTP check failed: {e}")
        else:
            try:
                socket.getaddrinfo(host, None)
                return upstream
            except Exception as e:
                log.debug(f"Upstream DNS check failed: {e}")
        log.warning(f"Upstream {upstream} unreachable, using {fallback}")
        return fallback
    # -------------------- Files & Configs --------------------


    def _set_permissions_safe(self, path: str, mode: int = 0o644, owner: str = "root") -> None:
        """Safe permission setting that avoids I/O closed file errors."""
        if self.dry_run:
            return
           
        try:
            # Set mode using os.chmod
            os.chmod(path, mode)
           
            # Set owner safely - only if we're root and the user exists
            if is_root() and is_linux():
                try:
                    if ":" in owner:
                        user, group = owner.split(":", 1)
                    else:
                        user, group = owner, owner
                   
                    uid = pwd.getpwnam(user).pw_uid
                    gid = grp.getgrnam(group).gr_gid
                    os.chown(path, uid, gid)
                except (KeyError, PermissionError) as e:
                    log.debug(f"Could not set owner to {owner} for {path}: {e}")
                    # Fallback to root
                    try:
                        os.chown(path, 0, 0) # root:root
                    except PermissionError:
                        log.warning(f"Could not set owner to root for {path}")
        except Exception as e:
            log.warning(f"Could not set permissions for {path}: {e}")
    def setup_site_logs(self, site: Site) -> Tuple[Path, Path]:
        """Setup access/error logs for site with proper permissions."""
        access = self.log_dir / f"{site.name}-access.log"
        error = self.log_dir / f"{site.name}-error.log"
        if self.dry_run:
            log.info(f"[dry-run] Would create logs: {access}, {error}")
            return access, error
           
        touch(str(access))
        touch(str(error))
       
        # Set proper permissions using safe method
        try:
            self._set_permissions_safe(str(access), 0o644, "root")
            self._set_permissions_safe(str(error), 0o644, "root")
        except Exception as e:
            log.warning(f"Could not set log file permissions: {e}")
           
        return access, error
    def ensure_cache_dir(self, site: Site) -> Path:
        """Ensure per-site cache directory exists with proper permissions."""
        cache_dir = self.cache_base / site.name
        ensure_dir(str(cache_dir))
        if not self.dry_run:
            try:
                self._set_permissions_safe(str(cache_dir), 0o755, "root")
            except Exception as e:
                log.warning(f"Could not set cache directory permissions: {e}")
        return cache_dir
    # -------------------- Creation & Sync --------------------
    def create_site(self, site: Site, proxy_tpl: Union[str, Path] = "reverse-proxy.conf", 
                    serve_tpl: Union[str, Path] = "serve.conf", location_tpl: Union[str, Path] = "location.conf") -> Path:
        """Create or update site."""
        skip, reason = self.should_skip_site_operation(site, 'create')
        if skip:
            log.info(f"📝 Skipping create for {site.name}: {reason}")
            return self.sites_available / site.name
        
        conf_path = self.sites_available / site.name
        
        # Render config
        upstream = self.validate_upstream(site.upstream or "", self.fallback_upstream) if self.validate_upstreams else (site.upstream or "")
        tpl = serve_tpl if site.is_serve else proxy_tpl
        context = {
            "SITE": site.name,
            "IP_ADDRESS": upstream,
            "ROOT_PATH": upstream if site.is_serve else "",
            "CLIENT_MAX_BODY_SIZE": site.upload_limit or site.client_max_body_size or "10M",
        }
        
        try:
            rendered = self.render_template(tpl, context)
            
            # Add location blocks if any
            if site.locations:
                location_blocks = self.build_location_blocks_extended(site.locations, location_tpl)
                rendered += "\n" + "\n".join(location_blocks)
                
        except NginxOpsError as e:
            raise NginxOpsError(f"Failed to render templates for {site.name}: {e}")
        
        # Use optimized single operation
        def create_operation():
            self.write_site_config(site, rendered)
            self._ensure_site_enabled(site.name)
            self._ensure_logs(site.name)
            self._ensure_cache(site.name)
            
            # Apply upload limit if specified
            if site.upload_limit:
                self._apply_upload_limit_unsafe(site, site.upload_limit)
                
            # Apply flags
            if site.flags:
                for flag, value in site.flags.items():
                    if flag != "force":
                        self._apply_flag_unsafe(site, flag, value)
        
        # Use safe operation for the entire create process
        success = self._safe_operation(create_operation, f"Create site {site.name}", site.name, site)
        
        if success:
            log.info(f"✅ {'Created' if not conf_path.exists() else 'Updated'} site {site.name}")
        else:
            log.error(f"❌ Failed to {'create' if not conf_path.exists() else 'update'} site {site.name}")
            
        return conf_path
    
    def remove_site(self, site_name: str) -> None:
        """Remove a site with manual tag check."""
        site = Site(name=site_name)
        skip, reason = self.should_skip_site_operation(site, 'remove')
        if skip:
            log.info(f"📝 Skipping remove for {site_name}: {reason}")
            return
           
        conf_avail = self.sites_available / site_name
        conf_enabled = self.sites_enabled / site_name
       
        if self.dry_run:
            log.info(f"[dry-run] Would remove site {site_name}")
            return
           
        if file_exists(str(conf_enabled)) or conf_enabled.is_symlink():
            conf_enabled.unlink(missing_ok=True)
        if file_exists(str(conf_avail)):
            remove_file(str(conf_avail))
           
        # Cleanup known flags
        for flag_name in list(self.known_flags):
            self.remove_flag(site_name, flag_name)
         
        # Remove empty logs
        access = self.log_dir / f"{site_name}-access.log"
        error = self.log_dir / f"{site_name}-error.log"
        if file_exists(str(access)) and Path(access).stat().st_size == 0:
            remove_file(str(access))
        if file_exists(str(error)) and Path(error).stat().st_size == 0:
            remove_file(str(error))  
            
        log.info(f"✅ Removed site {site_name}")
        

    def list_available_sites(self) -> List[str]:
        """List available site configs."""
        if not self.sites_available.exists():
            return []
        return [p.name for p in self.sites_available.glob("*") if p.is_file()]
    

    def _ensure_logs(self, site_name: str) -> None:
        """Ensure log files exist without validation/reload."""
        access = self.log_dir / f"{site_name}-access.log"
        error = self.log_dir / f"{site_name}-error.log"
        
        if not access.exists():
            touch(str(access))
        if not error.exists():
            touch(str(error))

    def _ensure_cache(self, site_name: str) -> None:
        """Ensure cache directory exists without validation/reload."""
        cache_dir = self.cache_base / site_name
        if not cache_dir.exists():
            ensure_dir(str(cache_dir))
            
    # -------------------- Flags --------------------
    def sync_flags(self, sites: List[Site]) -> None:
        """Sync flags for given sites with batch processing."""
        success_count = 0
        failed_sites = []
        
        # Group operations by site to avoid multiple backups/reloads per site
        for s in sites:
            conf = self.sites_available / s.name
            if not file_exists(str(conf)):
                log.warning(f"Site config not found: {s.name}, skipping flag sync")
                continue
                
            try:
                # Use the optimized sync_flags_for_site which batches flag operations
                self.sync_flags_for_site(s, force=False)
                success_count += 1
            except Exception as e:
                failed_sites.append(s.name)
                log.error(f"❌ Failed to sync flags for {s.name}: {e}")
        
        if success_count > 0:
            log.info(f"✅ Successfully synced flags for {success_count} sites")
        if failed_sites:
            log.error(f"❌ Failed to sync flags for {len(failed_sites)} sites: {', '.join(failed_sites)}")

    def apply_flag(self, site: Site, flag: str, value: Optional[Any] = None) -> None:
        """Apply a flag to a site with backup and validation."""
       
        skip, reason = self.should_skip_site_operation(site, 'update')
        if skip:
            log.info(f"📝 Skipping flag {flag} for manual site {site.name}: {reason}")
            return
   
        def flag_operation():
            if flag in self.known_flags:
                f = self.known_flags[flag]
            elif flag.startswith("/"):
                # Find the location object to get its specific upstream
                location_upstream = value
                for loc in site.locations:
                    if loc.path == flag:
                        location_upstream = loc.upstream or value or site.upstream
                        break
               
                f = Flag(
                    name=flag,
                    template="location.conf",
                    placement="server_443_out",
                    context_adjuster=lambda ctx, mgr, site, val: ctx | {"PATH": flag, "UPSTREAM": location_upstream or ""},
                )
            else:
                log.warning(f"Unknown flag: {flag}")
                return
               
            if self.flag_exists(site, flag):
                log.debug(f"Flag {flag} already exists for {site.name}, updating")
               
            if f.pre_apply:
                f.pre_apply(self, site)
               
            if f.apply_hook:
                if not self.dry_run:
                    f.apply_hook(self, site, value)
            elif f.template:
                context = {"SITE": site.name}
                if f.context_adjuster:
                    context = f.context_adjuster(context, self, site, value)
                snippet = self.render_template(f.template, context)
                begin, end = f.get_markers(site)
                target = f.target_getter(self, site)
               
                if self.dry_run:
                    log.info(f"[dry-run] Would apply flag {flag} to {target}")
                else:
                    if f.placement == "combined":
                        self._apply_entry_to_combined(target, snippet, begin, end)
                    else:
                        self._apply_snippet(target, snippet, f.placement or "server_443_out", begin, end)
                       
                if f.secondary_template:
                    sec_context = {"SITE": site.name}
                    if f.context_adjuster:
                        sec_context = f.context_adjuster(sec_context, self, site, value)
                    sec_snippet = self.render_template(f.secondary_template, sec_context)
                    sec_begin, sec_end = f.get_secondary_markers(site)
                    sec_target = f.secondary_target_getter(self, site)
                    if self.dry_run:
                        log.info(f"[dry-run] Would apply secondary for {flag} to {sec_target}")
                    else:
                        self._apply_entry_to_combined(sec_target, sec_snippet, sec_begin, sec_end)
                       
            log.info(f"Applied flag {flag} to {site.name}")
        success = self._safe_operation(flag_operation, f"Apply flag {flag} to {site.name}", site.name)
        if not success:
            raise NginxOpsError(f"Failed to apply flag {flag} to {site.name}")
    def remove_flag(self, site_name: str, flag: str) -> None:
        """Remove a flag from a site using Flag object."""
        site = Site(name=site_name) # dummy for markers
        if self.should_skip_site_operation(site, flag):
            log.info(f"📝 Site {site.name} is manual, skipping sync")
            return
        if flag in self.known_flags:
            f = self.known_flags[flag]
        elif flag.startswith("/"):
            f = Flag(name=flag)
        else:
            log.debug(f"Unknown flag for removal: {flag}")
            return
           
        if f.remove_hook:
            f.remove_hook(self, site)
        elif f.template or flag.startswith("/"):
            begin, end = f.get_markers(site)
            target = f.target_getter(self, site)
            if self.dry_run:
                log.info(f"[dry-run] Would remove flag {flag} from {target}")
            else:
                self._remove_region(target, begin, end)
            if f.secondary_template:
                sec_begin, sec_end = f.get_secondary_markers(site)
                sec_target = f.secondary_target_getter(self, site)
                self._remove_entry_from_combined(sec_target, sec_begin, sec_end)
               
        if f.post_remove:
            f.post_remove(self, site)
        log.info(f"Removed flag {flag} from {site_name}")
    def flag_exists(self, site: Site, flag: str) -> bool:
        """Check if a flag is already applied to site."""
        if flag not in self.known_flags and not flag.startswith("/"):
            return False
           
        if flag in self.known_flags:
            f = self.known_flags[flag]
        else:
            f = Flag(name=flag)
           
        target = f.target_getter(self, site)
        if not file_exists(str(target)):
            return False
           
        txt = read_file(str(target))
        begin, _ = f.get_markers(site)
        return begin in txt
    # -------------------- low-level text modifications --------------------
    def _apply_snippet(self, conf_path: Path, snippet: str, placement: str = "server_443_out",
                       begin_marker: Optional[str] = None, end_marker: Optional[str] = None) -> None:
        """Robust snippet placement with marker support."""
        if self.dry_run:
            log.info(f"[dry-run] Would apply snippet to {conf_path}")
            return
       
        txt = read_file(str(conf_path))
        blocks = _find_server_blocks(txt)
        placed = False
       
        port = 443 if "443" in placement else 80
        inside_location = "inside_location" in placement
        after_locations = "after_location" in placement
       
        for start, end, block in blocks:
            if not _server_has_port(block, port):
                continue
               
            # Handle marker replacement
            if begin_marker and end_marker:
                pattern = re.escape(begin_marker) + r'.*?' + re.escape(end_marker)
                if re.search(pattern, block, flags=re.DOTALL):
                    new_block = re.sub(pattern, f"{begin_marker}\n{snippet}\n{end_marker}", block, flags=re.DOTALL)
                    txt = txt[:start] + new_block + txt[end:]
                    placed = True
                    break
                else:
                    # Insert with markers
                    wrapped = f"{begin_marker}\n{snippet}\n{end_marker}"
                    new_block = self._insert_snippet_into_block(block, wrapped, placement)
                    if new_block != block:
                        txt = txt[:start] + new_block + txt[end:]
                        placed = True
                        break
            else:
                # Insert without markers
                new_block = self._insert_snippet_into_block(block, snippet, placement)
                if new_block != block:
                    txt = txt[:start] + new_block + txt[end:]
                    placed = True
                    break
       
        if not placed:
            log.warning(f"Could not place snippet in {conf_path}, appending to file")
            txt += f"\n{snippet}"
       
        atomic_write(str(conf_path), txt)
    def _insert_snippet_into_block(self, block: str, snippet: str, placement: str) -> str:
        """Insert snippet into server block at correct position."""
        if "inside_location" in placement:
            # Find location / block
            loc_match = re.search(r'(location\s+/\s*\{[^}]*)(\})', block, flags=re.DOTALL)
            if loc_match:
                return block[:loc_match.start(1)] + loc_match.group(1) + "\n" + snippet + "\n" + block[loc_match.start(2):]
       
        elif "after_location" in placement:
            # Find last location block and insert after it
            locations = list(re.finditer(r'location\s+[^{]+\{[^}]*\}', block, flags=re.DOTALL))
            if locations:
                last_loc = locations[-1]
                return block[:last_loc.end()] + "\n" + snippet + block[last_loc.end():]
       
        # Default: insert before closing server brace
        last_brace = block.rfind('}')
        if last_brace != -1:
            return block[:last_brace] + "\n" + snippet + "\n" + block[last_brace:]
       
        return block
    def _remove_region(self, conf_path: Path, begin: str, end: str) -> None:
        """Remove a marked region from a config file."""
        if self.dry_run:
            return
        if not file_exists(str(conf_path)):
            return
        txt = read_file(str(conf_path))
        pattern = re.escape(begin) + r".*?" + re.escape(end) + r"\s*"
        # Use re.sub directly instead of regex_replace to avoid flags issue
        new_txt = re.sub(pattern, "", txt, flags=re.DOTALL)
        if new_txt != txt:
            atomic_write(str(conf_path), new_txt)
    def _apply_entry_to_combined(self, combined: Path, entry: str, begin: str, end: str) -> None:
        """Apply an entry to a combined file using markers with optimization."""
        if self.dry_run:
            return
            
        if not file_exists(str(combined)):
            ensure_dir(str(combined.parent))
            touch(str(combined))
            
        txt = read_file(str(combined))
        pattern = re.escape(begin) + r"(.*?)" + re.escape(end)
        m = re.search(pattern, txt, flags=re.DOTALL)
        
        if m:
            new_txt = re.sub(pattern, begin + "\n" + entry.strip() + "\n" + end, txt, flags=re.DOTALL)
        else:
            new_txt = txt.rstrip() + "\n" + begin + "\n" + entry.strip() + "\n" + end + "\n"
        
        # Only write if content changed
        if new_txt != txt:
            atomic_write(str(combined), new_txt)

    def _remove_entry_from_combined(self, combined: Path, begin: str, end: str) -> None:
        """Remove a marked entry from a combined file."""
        if not file_exists(str(combined)) or self.dry_run:
            return
        txt = read_file(str(combined))
        pattern = re.escape(begin) + r".*?" + re.escape(end) + r"\s*"
        # Use re.sub directly instead of regex_replace to avoid flags issue
        new_txt = re.sub(pattern, "", txt, flags=re.DOTALL)
        if new_txt != txt:
            atomic_write(str(combined), new_txt)
    def _set_client_max_body_size(self, conf_path: Path, val: str) -> None:
        """Set client_max_body_size in server block."""
        if self.dry_run:
            return
        txt = read_file(str(conf_path))
        blocks = _find_server_blocks(txt)
        modified = False
        for start, endpos, block in blocks:
            if not _server_has_port(block, 443):
                continue
            pattern = r"client_max_body_size\s+[^;]+;"
            # Use re.search directly instead of regex_search
            if re.search(pattern, block):
                # Use re.sub directly instead of regex_replace
                new_block = re.sub(pattern, f"client_max_body_size {val};", block)
            else:
                server_name_m = re.search(r"server_name\s+[^;]+;", block)
                insert_idx = server_name_m.end() if server_name_m else block.find("{") + 1
                new_block = block[:insert_idx] + f"\n client_max_body_size {val};" + block[insert_idx:]
            txt = txt[:start] + new_block + txt[endpos:]
            modified = True
            break
        if modified:
            atomic_write(str(conf_path), txt)
    # -------------------- Service control --------------------
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def manage_service(self, test_cmd: List[str] = DEFAULT_TEST_CMD, reload_cmd: List[str] = DEFAULT_RELOAD_CMD, start_cmd: List[str] = DEFAULT_START_CMD) -> bool:
        """Test and reload/start Nginx service."""
        if self.dry_run:
            log.info("[dry-run] Would manage Nginx service")
            return True
        if not is_root():
            raise NginxOpsError("Requires root privileges")
        proc = run(test_cmd, capture=True, no_die=True)
        if proc.returncode == 0:
            run(reload_cmd, capture=True)
            log.info("Nginx reloaded successfully")
            return True
        run(start_cmd, capture=True)
        log.info("Started Nginx")
        return True
    # -------------------- Reloads --------------------
    def clear_cache(self, site: Optional[Union[Site, str]] = None) -> bool:
        """Clear cache for a site with backup, validation and service reload.
       
        Args:
            site: Site name, Site object, or None for all sites
           
        Returns:
            bool: True if operation was successful
        """
        def clear_operation():
            if site is not None:
                site_name = site if isinstance(site, str) else site.name
                cache_dir = self.cache_base / site_name
                if not dir_exists(str(cache_dir)):
                    log.info(f"Cache directory not found: {cache_dir}, skipping")
                    return
                if self.dry_run:
                    log.info(f"[dry-run] Would clear cache for {site_name}")
                    return
                remove_dir(str(cache_dir), recursive=True)
                ensure_dir(str(cache_dir)) # recreate empty
                log.info(f"Cleared cache for {site_name}")
            else:
                if self.dry_run:
                    log.info("[dry-run] Would clear all caches")
                    return
                for d in self.cache_base.iterdir():
                    if d.is_dir():
                        remove_dir(str(d), recursive=True)
                        ensure_dir(str(d)) # recreate empty
                log.info("Cleared all caches")
        # Use site name for backup if provided
        site_name = None
        if site is not None:
            site_name = site if isinstance(site, str) else site.name
       
        operation_name = f"Clear cache for {site_name}" if site_name else "Clear all caches"
       
        return self._safe_operation(clear_operation, operation_name, site_name)
    def reload_dns(self) -> bool:
        """Reload dnsmasq service with validation.
       
        Returns:
            bool: True if operation was successful
        """
        def dns_operation():
            if not self.dns_combined or not is_linux():
                log.warning("DNS reload skipped (not supported)")
                return
               
            if self.dry_run:
                log.info("[dry-run] Would reload DNS (dnsmasq)")
                return
               
            run(["systemctl", "restart", "dnsmasq"], elevated=True, no_die=True)
            log.info("Reloaded DNS (dnsmasq)")
        return self._safe_operation(dns_operation, "Reload DNS")
__all__ = [
    "sync_from_yaml",
    "NginxOpsError",
    "Site",
    "Location",
    "NginxManager",
    "Flag",
    "parse_sites_list",
    "parse_sites_yaml",
    "generate_sites_yaml",
    "sync_from_list",
    "migrate_text_to_yaml",
    "backup_site_config",
    "restore_site_config",
    "list_site_backups",
    "backup_all_sites",
    "validate_nginx_config",
    "help",
]
# Convenience functions using global manager
def parse_sites_list(list_path: Union[str, Path]) -> List[Site]:
    """Parse sites.txt into Site objects."""
    return _get_manager().parse_sites_list(list_path)
def parse_sites_yaml(yaml_path: Union[str, Path]) -> List[Site]:
    """Parse YAML file into Site objects."""
    manager = NginxManager()
    return manager.parse_sites_yaml(yaml_path)
def generate_sites_yaml(sites: List[Site]) -> str:
    """Generate YAML from Site objects."""
    manager = NginxManager()
    return manager.generate_sites_yaml(sites)
def sync_from_list(list_path: Union[str, Path], force_all: bool = False) -> Dict[str, Any]:
    """Complete sync from sites.txt file."""
    return _get_manager().sync_from_list(list_path, force_all)
def sync_from_yaml(yaml_path: Union[str, Path], force_all: bool = False) -> Dict[str, Any]:
    """Complete sync from YAML file."""
    return _get_manager().sync_from_yaml(yaml_path, force_all)
def sync_sites(sites: List[Site], force_all: bool = False) -> Dict[str, Any]:
    """Optimized sync from Site objects."""
    return _get_manager().sync_sites(sites, force_all)
def migrate_text_to_yaml(text_path: Union[str, Path], yaml_path: Union[str, Path]) -> None:
    """Migrate from old text format to new YAML format."""
    return _get_manager().migrate_text_to_yaml(text_path, yaml_path)
def backup_site_config(site_name: str, suffix: Optional[str] = None) -> Path:
    """Convenience function to backup site config."""
    return _get_manager().backup_site_config(site_name, suffix)
def restore_site_config(site_name: str, backup_path: Optional[Path] = None) -> bool:
    """Convenience function to restore site config."""
    return _get_manager().restore_site_config(site_name, backup_path)
def list_site_backups(site_name: Optional[str] = None) -> List[Path]:
    """Convenience function to list site backups."""
    return _get_manager().list_site_backups(site_name)
def backup_all_sites() -> Dict[str, Path]:
    """Convenience function to backup all sites."""
    return _get_manager().backup_all_sites()
def validate_nginx_config() -> bool:
    """Convenience function to validate nginx configuration."""
    return _get_manager().validate_nginx_config()
def clear_cache(site: Optional[Union[Site, str]] = None) -> bool:
    """Convenience function to clear cache."""
    return _get_manager().clear_cache(site)
def reload_dns() -> bool:
    """Convenience function to reload DNS."""
    return _get_manager().reload_dns()