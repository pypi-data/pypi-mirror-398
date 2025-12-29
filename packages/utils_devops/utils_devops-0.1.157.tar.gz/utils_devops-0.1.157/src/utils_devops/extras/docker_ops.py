"""
docker_ops.py - Functional Docker Compose operations library
High-level Docker operations with Docker SDK and CLI fallback.
"""
from __future__ import annotations
import subprocess
import json
import os
import re
from logging import Logger
import re
import sys
import tarfile
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterator, Union, Callable
from dataclasses import dataclass, field
import concurrent.futures
from typing import *
# Core imports
from utils_devops.core import logs, files, systems, strings, envs, datetimes as dt_ops
dt_ops.time.time()
# Optional imports
try:
    import docker
    from docker.errors import DockerException
    DOCKER_AVAILABLE = True
except ImportError:
    docker = None
    DOCKER_AVAILABLE = False

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    # Simple retry decorator fallback
    def retry(*args, **kwargs):
        def decorator(f):
            return f
        return decorator

# Module logger
logger = logs.get_library_logger()

# Constants
DEFAULT_DOCKER_TIMEOUT = 500
DEFAULT_CONCURRENCY_LIMIT = 4
DEFAULT_PULL_RETRIES = 3
DEFAULT_LOGGER = logger
DEFAULT_env_file = ".env"

# Exceptions
class DockerOpsError(Exception):
    pass

class ComposeConflictError(DockerOpsError):
    pass

class HealthCheckFailed(DockerOpsError):
    pass

# Data structures for type hints
@dataclass
class ExecResult:
    rc: int
    stdout: str
    stderr: str

@dataclass
class LogLine:
    timestamp: Optional[str] = None
    service: Optional[str] = None
    message: str = ""

@dataclass
class ContainerInfo:
    id: str
    name: str
    image: str
    status: str
    service: Optional[str] = None
    ports: Dict[str, Any] = field(default_factory=dict)

# Core Docker operations
def get_docker_client():
    """Get Docker client, fallback to None if not available"""
    if not DOCKER_AVAILABLE:
        return None
    
    try:
        return docker.from_env(timeout=DEFAULT_DOCKER_TIMEOUT)
    except DockerException as e:
        logger.warning(f"Docker client unavailable: {e}")
        return None

def _detect_compose_command() -> str:
    """
    Detect available compose command: 'docker compose' or 'docker-compose'
    Returns: 'compose' for modern, 'compose-legacy' for legacy, or raises error if neither available
    """
    # First try modern 'docker compose'
    try:
        result = run_docker_command(["docker", "compose", "version"], capture=True)
        if result.rc == 0:
            logger.debug("Using modern 'docker compose' command")
            return "compose"
    except Exception:
        pass
    
    # Try legacy 'docker-compose'
    try:
        result = run_docker_command(["docker-compose", "version"], capture=True)
        if result.rc == 0:
            logger.debug("Using legacy 'docker-compose' command")
            return "compose-legacy"
    except Exception:
        pass
    
    # Neither available
    raise DockerOpsError("Neither 'docker compose' nor 'docker-compose' is available. Please install Docker Compose.")

def run_docker_command(cmd: List[str], capture: bool = True, timeout: Optional[int] = None, 
                      input_text: Optional[str] = None,logger: Optional[logger] = None) -> ExecResult:
    """Run docker command and return result with detailed logging"""
    logger = logger or DEFAULT_LOGGER 
    try:
        logger.debug(f"Running: {' '.join(cmd)}")
        
        # Remove timeout parameter since systems.run doesn't support it
        if input_text:
            result = systems.run(cmd, capture=capture, input_text=input_text,logger=logger,stream=True)
        else:
            result = systems.run(cmd, capture=capture,logger=logger,stream=True)
        
        # Log the full output for debugging
        if result.returncode != 0:
            logger.error(f"Command failed with exit code {result.returncode}: {' '.join(cmd)}")
            if result.stderr:
                logger.error(f"STDERR: {result.stderr}")
            if result.stdout:
                logger.debug(f"STDOUT: {result.stdout}")
        else:
            if result.stdout:
                logger.debug(f"Command output: {result.stdout}")
            
        return ExecResult(rc=result.returncode, stdout=result.stdout, stderr=result.stderr)
    except Exception as e:
        logger.error(f"Command execution failed: {' '.join(cmd)} - {e}")
        raise DockerOpsError(f"Command failed: {' '.join(cmd)} - {e}")

def run_compose_command(compose_file: str, cmd: List[str], project_name: Optional[str] = None , env_file: Optional[str] = None,logger: Optional[logger] = None) -> ExecResult:
    """Run docker compose command using the detected compose command"""
    logger = logger or DEFAULT_LOGGER 
    try:
        compose_type = _detect_compose_command()
    except DockerOpsError as e:
        logger.error(f"💥 No compose command available: {e}")
        raise
    
    # Build the command based on detected type
    if compose_type == "compose":
        base_cmd = ["docker", "compose"]
    else:  # compose-legacy
        base_cmd = ["docker-compose"]
    
    full_cmd = base_cmd + ["-f", compose_file]
    
    if project_name:
        full_cmd.extend(["-p", project_name])
        
    if env_file:
        full_cmd.extend(["--env-file", env_file])
    
    full_cmd.extend(cmd)
    
    logger.info(f"Running: {' '.join(full_cmd)}")
    
    # Use your existing run_docker_command function
    result = run_docker_command(full_cmd, capture=True,logger=logger)
    
    if result.rc == 0:
        logger.info("✅ Compose command completed successfully")
    else:
        logger.error(f"❌ Compose command failed with code {result.rc}")
        if result.stderr:
            logger.error(f"Error details: {result.stderr}")
    
    return result
    

# Alternative version with explicit command preference
def run_compose_command_v2(compose_file: str, cmd: List[str], project_name: Optional[str] = None,
                          prefer_modern: bool = True) -> ExecResult:
    """
    Run docker compose command with configurable preference.
    
    Args:
        compose_file: Path to compose file
        cmd: Compose command and arguments
        project_name: Project name
        prefer_modern: Prefer 'docker compose' over 'docker-compose'
    """
    # Try preferred command first
    if prefer_modern:
        commands_to_try = [
            (["docker", "compose", "-f", compose_file], "modern"),
            (["docker-compose", "-f", compose_file], "legacy")
        ]
    else:
        commands_to_try = [
            (["docker-compose", "-f", compose_file], "legacy"),
            (["docker", "compose", "-f", compose_file], "modern")
        ]
    
    last_error = None
    for base_cmd, cmd_type in commands_to_try:
        try:
            full_cmd = base_cmd.copy()
            if project_name:
                full_cmd.extend(["-p", project_name])
            full_cmd.extend(cmd)
            
            logger.debug(f"Trying {cmd_type} compose: {' '.join(full_cmd)}")
            result = run_docker_command(full_cmd)
            
            if result.rc == 0:
                logger.debug(f"Success with {cmd_type} compose command")
                return result
            else:
                # Command exists but failed - don't try the other one
                return result
                
        except Exception as e:
            last_error = e
            logger.debug(f"{cmd_type} compose failed: {e}")
            continue
    
    # Both commands failed
    raise DockerOpsError(f"All compose commands failed. Last error: {last_error}")

# Image operations
@retry(stop=stop_after_attempt(DEFAULT_PULL_RETRIES), wait=wait_exponential(multiplier=1, min=4, max=10)) if TENACITY_AVAILABLE else retry
def pull_image(image_name: str, auth: Optional[Dict[str, str]] = None, logger: Optional[logger] = None) -> bool:
    """Pull Docker image with retry logic"""
    logger = logger or DEFAULT_LOGGER 
    
    client = get_docker_client()
    if client:
        try:
            logger.info(f"Pulling image: {image_name}")
            client.images.pull(image_name, auth_config=auth)
            return True
        except DockerException as e:
            logger.warning(f"SDK pull failed, falling back to CLI: {e}")
    
    # Fallback to CLI
    result = run_docker_command(["docker", "pull", image_name])
    return result.rc == 0

def push_image(image_name: str, auth: Optional[Dict[str, str]] = None) -> bool:
    """Push Docker image"""
    client = get_docker_client()
    if client:
        try:
            client.images.push(image_name, auth_config=auth)
            return True
        except DockerException:
            pass
    
    result = run_docker_command(["docker", "push", image_name])
    return result.rc == 0

def build_image(context: str, dockerfile: str = "Dockerfile", tag: Optional[str] = None, 
                build_args: Optional[Dict] = None, nocache: bool = False) -> bool:
    """Build Docker image"""
    client = get_docker_client()
    
    if client:
        try:
            build_kwargs = {
                "path": context,
                "dockerfile": dockerfile,
                "nocache": nocache,
            }
            if tag:
                build_kwargs["tag"] = tag
            if build_args:
                build_kwargs["buildargs"] = build_args
            
            client.images.build(**build_kwargs)
            return True
        except DockerException:
            pass
    
    # CLI fallback
    cmd = ["docker", "build", "-f", dockerfile, context]
    if tag:
        cmd.extend(["-t", tag])
    if nocache:
        cmd.append("--no-cache")
    if build_args:
        for k, v in build_args.items():
            cmd.extend(["--build-arg", f"{k}={v}"])
    
    result = run_docker_command(cmd)
    return result.rc == 0

# Container operations
def list_containers(all: bool = False, filters: Optional[Dict] = None) -> List[ContainerInfo]:
    """List containers"""
    client = get_docker_client()
    containers = []
    
    if client:
        try:
            docker_containers = client.containers.list(all=all, filters=filters or {})
            for c in docker_containers:
                containers.append(ContainerInfo(
                    id=c.id,
                    name=c.name,
                    image=c.image.tags[0] if c.image.tags else c.image.id,
                    status=c.status
                ))
            return containers
        except DockerException:
            pass
    
    # CLI fallback
    cmd = ["docker", "ps"]
    if all:
        cmd.append("-a")
    cmd.extend(["--format", "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}"])
    
    result = run_docker_command(cmd)
    for line in result.stdout.strip().splitlines():
        if line.strip():
            parts = line.split("|", 3)
            if len(parts) == 4:
                containers.append(ContainerInfo(
                    id=parts[0],
                    name=parts[1],
                    image=parts[2],
                    status=parts[3]
                ))
    
    return containers

def get_container_logs(container_id: str, follow: bool = False, tail: int = 100, 
                      since: Optional[str] = None) -> Iterator[LogLine]:
    """Get container logs"""
    client = get_docker_client()
    
    if client and not follow:  # SDK doesn't handle follow well in this context
        try:
            container = client.containers.get(container_id)
            logs = container.logs(tail=tail, since=since, timestamps=True).decode('utf-8')
            for line in logs.splitlines():
                yield parse_log_line(line)
            return
        except DockerException:
            pass
    
    # CLI approach
    cmd = ["docker", "logs", container_id, "--tail", str(tail)]
    if since:
        cmd.extend(["--since", since])
    if follow:
        cmd.append("-f")
    
    result = run_docker_command(cmd, capture=not follow)
    
    if not follow:
        for line in result.stdout.splitlines():
            yield parse_log_line(line)
    else:
        # For follow mode, we'd need to handle streaming properly
        logger.warning("Follow mode requires proper stream handling")

def parse_log_line(line: str) -> LogLine:
    """Parse log line into structured format"""
    # Try to extract timestamp and message
    timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(.*)', line)
    if timestamp_match:
        return LogLine(timestamp=timestamp_match.group(1), message=timestamp_match.group(2))
    return LogLine(message=line)

def exec_in_container(container_id: str, command: List[str], user: Optional[str] = None) -> ExecResult:
    """Execute command in container"""
    client = get_docker_client()
    
    if client:
        try:
            container = client.containers.get(container_id)
            result = container.exec_run(command, user=user)
            return ExecResult(
                rc=result.exit_code,
                stdout=result.output.decode('utf-8') if isinstance(result.output, bytes) else result.output,
                stderr=""
            )
        except DockerException:
            pass
    
    # CLI fallback
    cmd = ["docker", "exec"]
    if user:
        cmd.extend(["-u", user])
    cmd.append(container_id)
    cmd.extend(command)
    
    result = run_docker_command(cmd)
    return result

# Compose file operations
# Compose file operations
def read_compose_file(compose_file: str, env_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Read and parse docker-compose file with environment variable expansion
    
    Args:
        compose_file: Path to docker-compose.yml
        env_file: Optional path to .env file (defaults to .env alongside compose file)
    """
    try:
        # Get env file path
        env_path = get_env_compose(compose_file, env_file)
        
        # Load environment variables from .env file if it exists
        if env_path and files.file_exists(env_path):
            envs.import_env_to_system(get_env_compose(env_file))
        
        # Read compose file content
        content = files.read_file(compose_file)
        
        # Expand environment variables in the content
        data = _expand_env_vars_in_compose(content)
        
        # Parse YAML
        return strings.safe_parse_yaml(data, default={})
        
    except Exception as e:
        raise DockerOpsError(f"Failed to read compose file {compose_file}: {e}")


def get_env_compose(compose_file: str, env_file: Optional[str] = None) -> Optional[str]:
    """
    Get the appropriate .env file path for a docker-compose file
    
    Args:
        compose_file: Path to docker-compose.yml
        env_file: Optional explicit .env file path
        
    Returns:
        Path to .env file or None if not found
    """
    try:
        # If env_file is explicitly provided, use it
        if env_file:
            return env_file
        
        # Default 1: Look for .env in the same directory as compose file
        compose_dir = os.path.dirname(os.path.abspath(compose_file))
        default_env = os.path.join(compose_dir, '.env')
        
        if os.path.exists(default_env):
            return default_env
        
        # Default 2: Look for .env file with same name as compose file
        # (e.g., docker-compose.env.yml -> .env)
        compose_name = os.path.basename(compose_file)
        if compose_name.startswith('docker-compose'):
            # Try to extract suffix and use corresponding .env file
            parts = compose_name.split('.')
            if len(parts) > 2:
                # e.g., docker-compose.dev.yml -> .env.dev
                suffix = parts[-2]
                env_with_suffix = os.path.join(compose_dir, f'.env.{suffix}')
                if os.path.exists(env_with_suffix):
                    return env_with_suffix
        
        # Default 3: Check if compose file references env_file in yaml
        try:
            with open(compose_file, 'r') as f:
                import yaml
                compose_data = yaml.safe_load(f)
                
                # Check for env_file at root level (Docker Compose v2+)
                if isinstance(compose_data, dict) and 'env_file' in compose_data:
                    env_ref = compose_data['env_file']
                    if isinstance(env_ref, str):
                        # Resolve relative to compose file directory
                        resolved_env = os.path.join(compose_dir, env_ref)
                        if os.path.exists(resolved_env):
                            return resolved_env
        except:
            pass
        
        return None
        
    except Exception as e:
        logger.warning(f"Could not determine .env file for {compose_file}: {e}")
        return None



def write_compose_file(compose_file: str, data: Dict[str, Any], backup: bool = True) -> None:
    """Write docker-compose file"""
    if backup and files.file_exists(compose_file):
        files.backup_file(compose_file)
    
    try:
        files.write_yaml_file(compose_file, data)
    except Exception as e:
        raise DockerOpsError(f"Failed to write compose file {compose_file}: {e}")

def validate_compose_file(compose_file: str, env_file: Optional[str] = None) -> List[str]:
    """Validate compose file structure"""
    errors = []
    try:
        data = read_compose_file(compose_file, env_file)
        
        # Basic validation
        if 'version' not in data:
            errors.append("Missing 'version' field")
        
        services = data.get('services', {})
        if not services:
            errors.append("No services defined")
        
        for name, service in services.items():
            if not service.get('image') and not service.get('build'):
                errors.append(f"Service '{name}' has neither image nor build")
            
            # Validate ports format
            for port in service.get('ports', []):
                if not isinstance(port, str) and not isinstance(port, dict):
                    errors.append(f"Service '{name}' has invalid port format: {port}")
    
    except Exception as e:
        errors.append(f"Failed to parse compose file: {e}")
    
    return errors

# Compose operations
def compose_up(compose_file: str, services: Optional[List[str]] = None, 
              build: bool = False, pull: bool = False, detach: bool = True,
              project_name: Optional[str] = None , env_file: Optional[str] = None , no_build: Optional[bool] = False ,no_pull: Optional[bool] = False) -> bool:
    """Start compose services with detailed progress logging"""
    cmd = ["up"]
    if detach:
        cmd.append("-d")
    if build:
        cmd.append("--build")
        logger.info("🔨 Building images before starting...")
    if pull:
        cmd.append("--pull")
        logger.info("⬇️ Pulling latest images before starting...")
    if no_build:
        cmd.append("--no-build")
        logger.info("🔨 Forbidden Building images before starting...")
    if no_pull:
        cmd.append("--pull")
        cmd.append("never")
        logger.info("⬇️ Forbidden Pulling latest images before starting...")
    if services:
        cmd.extend(services)
        logger.info(f"🚀 Starting services: {services}")
    else:
        logger.info("🚀 Starting all services...")
    
    try:
        result = run_compose_command(compose_file, cmd, project_name,env_file)
        
        if result.rc == 0:
            # Parse output for service status
            for line in result.stdout.splitlines():
                line = line.strip()
                if "Creating" in line or "Starting" in line:
                    logger.info(f"📦 {line}")
                elif "Started" in line or "Healthy" in line:
                    logger.info(f"✅ {line}")
                elif "ERROR" in line or "Failed" in line:
                    logger.error(f"❌ {line}")
                    
            logger.info("🎉 All services started successfully")
            return True
        else:
            logger.error(f"💥 Failed to start services (exit code: {result.returncode})")
            # Log detailed errors
            for line in result.stderr.splitlines():
                if line.strip():
                    logger.error(f"   {line.strip()}")
            return False
            
    except Exception as e:
        logger.error(f"💥 Service startup failed: {e}")
        return False

def compose_down(compose_file: str, remove_volumes: bool = False, 
                remove_images: Optional[str] = None, project_name: Optional[str] = None , env_file: Optional[str] = None) -> bool:
    """Stop compose services using detected compose command"""
    cmd = ["down"]
    if remove_volumes:
        cmd.append("-v")
    if remove_images:
        cmd.extend(["--rmi", remove_images])
    
    result = run_compose_command(compose_file, cmd, project_name,env_file)
    return result.rc == 0

def compose_restart(compose_file: str, remove_volumes: bool = False, 
                remove_images: Optional[str] = None, project_name: Optional[str] = None) -> bool:
    """Restart compose services using detected compose command"""

    return None

def compose_ps(compose_file: str, project_name: Optional[str] = None, env_file: Optional[str] = None) -> List[ContainerInfo]:
    """List compose services status using detected compose command"""
    result = run_compose_command(compose_file, ["ps", "--format", "json"], project_name , env_file)
    
    containers = []
    try:
        data = json.loads(result.stdout)
        for item in data if isinstance(data, list) else [data]:
            containers.append(ContainerInfo(
                id=item.get('ID', ''),
                name=item.get('Name', ''),
                image=item.get('Image', ''),
                status=item.get('State', ''),
                service=item.get('Service', '')
            ))
    except json.JSONDecodeError:
        # Fallback to text parsing
        lines = result.stdout.strip().splitlines()[1:]  # Skip header
        for line in lines:
            parts = line.split()
            if len(parts) >= 4:
                containers.append(ContainerInfo(
                    id=parts[0],
                    name=parts[1],
                    image=parts[2],
                    status=' '.join(parts[3:])
                ))
    
    return containers

# Add a function to check compose version
def get_compose_version() -> Dict[str, str]:
    """Get detected compose command and version"""
    try:
        result = run_compose_command("", ["version"])  # Empty compose file for version check
        version_info = {
            "command": run_compose_command._compose_command if hasattr(run_compose_command, '_compose_command') else "unknown",
            "output": result.stdout.strip()
        }
        return version_info
    except Exception as e:
        return {
            "command": "unknown", 
            "error": str(e)
        }


def compose_logs(compose_file: str, services: Optional[List[str]] = None, 
                follow: bool = False, tail: int = 100, project_name: Optional[str] = None, env_file: Optional[str] = None) -> Iterator[LogLine]:
    """Get compose services logs"""
    cmd = ["logs", "--tail", str(tail)]
    if follow:
        cmd.append("-f")
    if services:
        cmd.extend(services)
    
    result = run_compose_command(compose_file, cmd, project_name,env_file)
    
    for line in result.stdout.splitlines():
        yield parse_compose_log_line(line)

def parse_compose_log_line(line: str) -> LogLine:
    """Parse compose log line"""
    # Format: service_name | timestamp message
    parts = line.split('|', 2)
    if len(parts) == 3:
        return LogLine(
            service=parts[0].strip(),
            timestamp=parts[1].strip(),
            message=parts[2].strip()
        )
    return LogLine(message=line)

def compose_pull(compose_file: str, services: Optional[List[str]] = None, 
                project_name: Optional[str] = None ,  env_file: Optional[str] = None) -> Dict[str, bool]:
    """Pull images for compose services with better error handling"""
    cmd = ["pull"]
    if services:
        cmd.extend(services)
    
    try:
        result = run_compose_command(compose_file, cmd, project_name,env_file)
        
        # Parse results even if return code is not 0 (partial success)
        pull_results = {}
        for line in result.stdout.splitlines():
            if "Pulling" in line and "..." in line:
                service = line.split("Pulling")[1].split("...")[0].strip()
                pull_results[service] = "done" in line.lower() or "complete" in line.lower() or "up to date" in line.lower()
        
        # If return code is not 0, log but don't fail immediately
        if result.rc != 0:
            logger.warning(f"Compose pull had non-zero exit code: {result.rc}")
            logger.warning(f"Stderr: {result.stderr}")
        
        return pull_results
        
    except Exception as e:
        logger.error(f"Compose pull failed completely: {e}")
        return {}

def compose_build(compose_file: str, services: Optional[List[str]] = None, 
                 no_cache: bool = False, project_name: Optional[str] = None, env_file: Optional[str] = None,logger: Optional[logger] = None) -> Dict[str, bool]:
    """Build compose services"""
    logger = logger or DEFAULT_LOGGER 
    cmd = ["build"]
    if no_cache:
        cmd.append("--no-cache")
    if services:
        cmd.extend(services)
    
    result = run_compose_command(compose_file, cmd, project_name,env_file,logger=logger)
    
    build_results = {}
    for line in result.stdout.splitlines():
        if "Building" in line:
            service = line.split("Building")[1].strip()
            build_results[service] = "done" in line.lower() or "success" in line.lower()
    
    return build_results

# Health checks
def check_service_health(compose_file: str, service: str, 
                        check_command: Optional[List[str]] = None,
                        timeout: int = 30) -> Dict[str, Any]:
    """Check service health - FIXED VERSION"""
    try:
        # Use the reliable JSON parsing method first
        health_result = check_health_from_compose_ps(compose_file)
        
        if health_result.get('healthy') is None:
            return {"healthy": False, "error": "Could not get health status"}
        
        # Check if service exists in the results
        services_data = health_result.get('services', {})
        if service not in services_data:
            return {"healthy": False, "error": f"Service {service} not found in compose output"}
        
        service_data = services_data[service]
        is_healthy = service_data.get('healthy', False)
        status = service_data.get('status', 'unknown')
        
        if is_healthy:
            return {
                "healthy": True,
                "details": f"Service is healthy: {status}",
                "status": status
            }
        else:
            return {
                "healthy": False,
                "error": f"Service is not healthy: {status}",
                "status": status
            }
                
    except Exception as e:
        logger.error(f"Error checking health for {service}: {e}")
        return {"healthy": False, "error": str(e)}

def wait_for_healthy(
    compose_file: str,
    services: List[str],
    timeout: int,
    logger: logger,
    interval: Optional[int] = 3,
    env_file: Optional[str] = None
) -> bool:
    """Wait for services to become healthy with detailed status logging."""
    start_time = time.time()
    attempt = 1
    services = services or get_services_from_compose(compose_file , env_file)
    while time.time() - start_time < timeout:
        elapsed = time.time() - start_time
        remaining = timeout - elapsed
        logger.info(f"🔍 Health check attempt {attempt} ({elapsed:.1f}s elapsed, {remaining:.1f}s remaining):")
        
        # Get detailed health status
        detailed_health = _get_detailed_health_status(compose_file, services, logger)
        
        # Group services by overall_status
        status_groups = defaultdict(list)
        for service, status in detailed_health.items():
            overall = status['overall_status']
            if overall == 'healthy':
                status_groups[overall].append(service)
            else:
                # Customize message based on overall
                msg = f"{service}: {status['status']} (health: {status['health']})"
                if overall == 'starting':
                    msg += " | Starting..."
                elif overall == 'restarting':
                    msg += " | Restarting..."
                elif overall == 'unhealthy':
                    msg += f" | Error: {status['error']}"
                elif overall == 'not found':
                    msg += f" | Not found: {status['error']}"
                status_groups[overall].append(msg)
        
        # Define order and emojis
        statuses = ['healthy', 'starting', 'restarting', 'unhealthy', 'not found']
        emojis = {'healthy': '✅', 'starting': '🚀', 'restarting': '🔄', 'unhealthy': '❌', 'not found': '❓'}
        
        # Log groups if they have items
        for status in statuses:
            group = status_groups[status]
            if group:
                emoji = emojis[status]
                logger.info(f"   {emoji} {status.capitalize()} ({len(group)}):")
                if status == 'healthy':
                    logger.info(f"      {sorted(group)}")
                else:
                    for detail in sorted(group):
                        logger.info(f"      - {detail}")
        
        # Check if all healthy using the 'healthy' bool
        all_healthy = all(status.get('healthy', False) for status in detailed_health.values())
        
        if all_healthy:
            logger.info(f"🎉 ALL SERVICES HEALTHY! Completed in {elapsed:.1f}s after {attempt} attempts")
            return True
        
        # Wait for next attempt
        logger.info(f"⏳ Waiting {interval}s before next health check...")
        time.sleep(interval)
        attempt += 1
    
    # Timeout
    logger.error(f"❌ Health check timeout after {time.time() - start_time:.1f}s")
    return False

def health_check_docker_compose(compose_file: str) -> bool:
    """
    Simple, reliable health check that uses the JSON parsing method
    """
    try:
        health_result = check_health_from_compose_ps(compose_file)
        return health_result.get('healthy', False)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False
    
def _compute_overall_status(service_status: Dict[str, Any]) -> str:
    """Compute overall status from Docker status and health."""
    if not service_status:
        return "not found"
    
    # Use 'state' for base status (e.g., "running", "restarting")
    state = service_status.get('state', '').lower()
    health = service_status.get('health', 'none').lower()
    status = service_status.get('status', '').lower()  # Fallback for parsing
    
    # Fallback parsing if state is empty
    if not state:
        if ' (health: ' in status:
            health = status.split('(health: ')[1].split(')')[0].lower()
        elif '(healthy)' in status:
            health = 'healthy'
        base_status = status.split(' (')[0]
        if base_status.startswith('up'):
            state = 'running'
        elif 'restarting' in base_status:
            state = 'restarting'
        elif 'created' in base_status or 'paused' in base_status:
            state = base_status
        else:
            state = 'unknown'
    
    if state == 'restarting':
        return "restarting"
    
    if state in ['created', 'paused']:
        return "starting" if health == 'starting' else "unhealthy"
    
    if state != 'running':
        return "unhealthy"
    
    if health == 'starting':
        return "starting"
    elif health == 'healthy':
        return "healthy"
    elif health == 'unhealthy':
        return "unhealthy"
    else:
        return "unhealthy"  # unknown or none
    
def check_health_from_compose_ps(compose_file: str) -> Dict[str, Any]:
    """
    Direct health check by parsing docker compose ps --format json
    Most reliable method since it uses the raw JSON output
    """
    try:
        # Run docker compose ps with JSON format
        result = run_compose_command(compose_file, ["ps", "--format", "json"])
        if result.rc != 0:
            return {"healthy": False, "error": f"docker compose ps failed: {result.stderr}"}
       
        # Parse JSON output - handle multiple JSON objects (one per line)
        import json
        containers_data = []
       
        # Split by lines and parse each JSON object separately
        for line in result.stdout.strip().split('\n'):
            if line.strip():  # Skip empty lines
                try:
                    container_data = json.loads(line.strip())
                    containers_data.append(container_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON line: {line}, error: {e}")
                    continue
       
        if not containers_data:
            return {"healthy": False, "error": "No container data parsed from output"}
       
        health_status = {}
        all_healthy = True
       
        for container in containers_data:
            service = container.get('Service', '')
            health = container.get('Health', '')
            status = container.get('Status', '')
            state = container.get('State', '')  # Added: the base state like "running"
           
            # Determine health status
            is_healthy = False
            if health:
                is_healthy = health.lower() == 'healthy'
            else:
                # Fallback to status parsing
                is_healthy = '(healthy)' in status.lower()
           
            health_status[service] = {
                'healthy': is_healthy,
                'health': health,
                'status': status,
                'state': state  # Added
            }
           
            if not is_healthy:
                all_healthy = False
       
        return {
            "healthy": all_healthy,
            "services": health_status,
            "details": f"{sum(1 for s in health_status.values() if s['healthy'])}/{len(health_status)} services healthy"
        }
       
    except Exception as e:
        return {"healthy": False, "error": f"Health check failed: {e}"}

def wait_for_healthy_simple(compose_file: str, timeout: int = 300) -> bool:
    """
    Simple, reliable health wait using direct JSON parsing
    """
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        health_result = check_health_from_compose_ps(compose_file)
        
        if health_result.get('healthy', False):
            logger.info(f"✅ All services healthy: {health_result.get('details', '')}")
            return True
        
        # Log progress
        elapsed = time.time() - start_time
        unhealthy_services = [svc for svc, status in health_result.get('services', {}).items() 
                            if not status.get('healthy', False)]
        
        if elapsed > 10:  # Avoid spam in first 10 seconds
            logger.info(f"⏳ Waiting for {len(unhealthy_services)} services: {unhealthy_services} "
                      f"({elapsed:.0f}s / {timeout}s)")
        
        dt_ops.time.sleep(5)
    
    logger.error(f"❌ Timeout after {timeout}s")
    return False

def get_services_from_compose(compose_file: str, env_file: Optional[str] = None) -> List[str]:
    """Get list of services from compose file"""
    data = read_compose_file(compose_file, env_file)
    return list(data.get('services', {}).keys())


def find_env_files(compose_file: str, env_file: Optional[str] = None) -> List[str]:
    """Find environment files referenced in compose file"""
    data = read_compose_file(compose_file, env_file)
    env_files = set()
    
    for service in data.get('services', {}).values():
        env_file = service.get('env_file')
        if env_file:
            if isinstance(env_file, str):
                env_files.add(env_file)
            elif isinstance(env_file, list):
                env_files.update(env_file)
    
    return [f for f in env_files if files.file_exists(f)]

def get_service_image(compose_file: str, service: str, env_file: Optional[str] = None) -> Optional[str]:
    """Get image name for service"""
    data = read_compose_file(compose_file, env_file)
    service_config = data.get('services', {}).get(service, {})
    return service_config.get('image')

def save_image_to_file(image_name: str, output_path: str) -> bool:
    """Save Docker image to file"""
    result = run_docker_command(["docker", "save", "-o", output_path, image_name])
    return result.rc == 0

def load_image_from_file(image_path: str) -> bool:
    """Load Docker image from file"""
    result = run_docker_command(["docker", "load", "-i", image_path])
    return result.rc == 0

def _update_env_version(
    env_file: str,
    source: str = 'git',
    logger: logger = None
) -> Optional[str]:
    """
    Update version in .env file based on git information.
    
    Sources:
    - 'git': Use git tag, fallback to branch name + commit hash
    - 'branch': Use branch name only  
    - 'commit': Use commit hash only
    """
    logger = logger or DEFAULT_LOGGER
    
    if not files.file_exists(env_file):
        logger.warning(f"Env file not found: {env_file}")
        return None
    
    try:
        # Read current environment
        current_env = envs.load_env_file(env_file)
        
        # Look for version-related variables
        version_keys = ['CI_COMMIT_TAG','GIT_TAG', 'VERSION', 'APP_VERSION', 'IMAGE_TAG']
        current_version = None
        version_key = None
        
        for key in version_keys:
            if key in current_env and current_env[key]:
                current_version = current_env[key]
                version_key = key
                break
        
        # Get new version based on source
        if source == 'git':
            new_version = _get_git_based_version()
        elif source == 'branch':
            new_version = _get_current_branch()
        elif source == 'commit':
            new_version = _get_commit_hash()
        else:
            logger.warning(f"Unknown version source: {source}")
            return None
        
        if not new_version:
            logger.info("No git version available - using existing version")
            return current_version
        
        # Update the environment file
        if version_key and new_version != current_version:
            _update_env_file_key(env_file, version_key, new_version)
            logger.info(f"Updated {version_key}: {current_version} → {new_version}")
            return new_version
        else:
            # If no version key found, use GIT_TAG as default
            if not version_key:
                _update_env_file_key(env_file, 'GIT_TAG', new_version)
                logger.info(f"Set GIT_TAG: {new_version}")
                return new_version
            logger.info(f"Version already up to date: {new_version}")
            return new_version
            
    except Exception as e:
        logger.error(f"Failed to update version: {e}")
        return None

def _get_git_based_version() -> Optional[str]:
    """Get version from git tag, branch, or commit."""
    # Try to get git tag first (from CI/CD or local)
    git_tag = _get_git_tag()
    if git_tag:
        return git_tag
    
    # If no tag, try branch name + commit hash
    branch = _get_current_branch()
    commit_hash = _get_commit_hash(short=True)
    
    if branch and commit_hash:
        # Clean branch name (remove special characters)
        clean_branch = branch.replace('/', '-').replace('_', '-')
        return f"{clean_branch}-{commit_hash}"
    elif branch:
        return branch.replace('/', '-').replace('_', '-')
    elif commit_hash:
        return commit_hash
    
    return None

def _get_git_tag() -> Optional[str]:
    """Get current git tag from environment or git command."""
    # First check CI/CD environment variables
    ci_vars = [
        'CI_COMMIT_TAG','GIT_TAG', 'TRAVIS_TAG', 'CIRCLE_TAG', 
        'BUILD_SOURCEBRANCH', 'DRONE_TAG'
    ]
    
    for var in ci_vars:
        tag = os.environ.get(var)
        if tag:
            # Clean the tag (remove refs/tags/ prefix if present)
            if tag.startswith('refs/tags/'):
                tag = tag[10:]
            return tag
    
    # Try git command as fallback
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'describe', '--tags', '--exact-match'],
            capture_output=True, text=True, check=True
        )
        git_tag = result.stdout.strip()
        if git_tag:
            # Remove 'v' prefix if present
            return git_tag[1:] if git_tag.startswith('v') else git_tag
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return None

def _get_current_branch() -> Optional[str]:
    """Get current git branch from environment or git command."""
    # Check CI/CD environment variables first
    ci_vars = [
        'GIT_BRANCH', 'CI_COMMIT_REF_NAME', 'TRAVIS_BRANCH', 'CIRCLE_BRANCH',
        'BUILD_SOURCEBRANCHNAME', 'DRONE_BRANCH'
    ]
    
    for var in ci_vars:
        branch = os.environ.get(var)
        if branch:
            return branch
    
    # Try git command as fallback
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True, text=True, check=True
        )
        branch = result.stdout.strip()
        if branch and branch != 'HEAD':
            return branch
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return None

def _get_commit_hash(short: bool = True) -> Optional[str]:
    """Get git commit hash from environment or git command."""
    # Check CI/CD environment variables first
    ci_vars = [
        'GIT_COMMIT', 'CI_COMMIT_SHA', 'TRAVIS_COMMIT', 'CIRCLE_SHA1',
        'BUILD_SOURCEVERSION', 'DRONE_COMMIT'
    ]
    
    for var in ci_vars:
        commit = os.environ.get(var)
        if commit:
            if short and len(commit) > 7:
                return commit[:7]
            return commit
    
    # Try git command as fallback
    try:
        import subprocess
        command = ['git', 'rev-parse', '--short', 'HEAD'] if short else ['git', 'rev-parse', 'HEAD']
        result = subprocess.run(
            command,
            capture_output=True, text=True, check=True
        )
        commit = result.stdout.strip()
        if commit:
            return commit
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return None

def _update_env_file_key(env_file: str, key: str, value: str):
    """Update a specific key in .env file."""
    if not files.file_exists(env_file):
        raise DockerOpsError(f"Env file not found: {env_file}")
    
    # Read current content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update the key
    updated = False
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith('#') and '=' in line:
            current_key = line.split('=')[0].strip()
            if current_key == key:
                lines[i] = f"{key}={value}\n"
                updated = True
                break
    
    # If key not found, append it
    if not updated:
        lines.append(f"{key}={value}\n")
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(lines)

def _cleanup_intermediate_images(logger: logger) -> Dict[str, Any]:
    """Clean up intermediate Docker images."""
    try:
        client = get_docker_client()
        
        # Remove dangling images (intermediate layers)
        result = client.images.prune(filters={'dangling': True})
        
        # Get ImagesDeleted, defaulting to empty list if None or missing
        images_deleted = result.get('ImagesDeleted')
        if images_deleted is None:
            images_deleted = []
        
        # Get SpaceReclaimed, defaulting to 0 if None or missing  
        reclaimed_space = result.get('SpaceReclaimed', 0)
        if reclaimed_space is None:
            reclaimed_space = 0
        
        logger.info(f"Cleaned up {len(images_deleted)} intermediate images, reclaimed {reclaimed_space} bytes")
        
        return {
            "success": True,
            "images_removed": len(images_deleted),
            "space_reclaimed": reclaimed_space
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {"success": False, "error": str(e)}


def _check_missing_images(
    compose_file: str,
    services: List[str],
    project_name: Optional[str],
    logger: logger,
    env_file: Optional[str] = None
) -> List[str]:
    """Check which services have missing Docker images."""
    missing_services = []
    
    # Read compose configuration
    compose_config = read_compose_file(compose_file, env_file)
    services_config = compose_config.get('services', {})
    
    for service in services:
        try:
            # Get the image name for the service
            image_name = get_service_image(compose_file, service, env_file)
            if not image_name:
                logger.debug(f"Service {service} has no image name specified")
                missing_services.append(service)
                continue
            
            # Check if image exists locally
            client = get_docker_client()
            try:
                client.images.get(image_name)
                # Image exists locally - not missing
                logger.debug(f"Image found locally for {service}: {image_name}")
            except docker.errors.ImageNotFound:
                # Image not found locally
                logger.debug(f"Image not found locally for {service}: {image_name}")
                missing_services.append(service)
                    
        except Exception as e:
            logger.warning(f"Could not check image for {service}: {e}")
            missing_services.append(service)
    
    return missing_services

from collections import defaultdict  # Add this import at the top of your file

def _perform_health_checks(
    compose_file: str,
    services: List[str],
    timeout: int,
    interval: int,
    logger: logger,
    env_file: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """Perform health checks in a single phase with total timeout."""
    health_details = {
        "success": False,
        "service_status": {},
        "final_healthy_count": 0,
        "final_unhealthy_count": 0
    }
   
    logger.info(f"🏥 Performing health check (timeout: {timeout}s, interval: {interval}s)...")
   
    # Use the enhanced wait_for_healthy function
    health_success = wait_for_healthy(
        compose_file=compose_file,
        services=services,
        timeout=timeout,
        interval=interval,
        logger=logger,
        env_file=env_file
    )
   
    # Get detailed health status for all services
    detailed_health = _get_detailed_health_status(compose_file, services, logger)
   
    # Group services by overall_status for detailed logging
    status_groups = defaultdict(list)
    for service, status in detailed_health.items():
        overall = status['overall_status']
        if overall == 'healthy':
            status_groups[overall].append(service)
        else:
            detail = f"{service}: {status['status']} (health: {status['health']}) | Error: {status['error']}"
            status_groups[overall].append(detail)
   
    # Log grouped statuses
    statuses = ['healthy', 'starting', 'restarting', 'unhealthy', 'not found']
    emojis = {'healthy': '✅', 'starting': '🚀', 'restarting': '🔄', 'unhealthy': '❌', 'not found': '❓'}
   
    for status in statuses:
        group = status_groups[status]
        if group:
            emoji = emojis[status]
            logger.info(f"{emoji} {status.capitalize()} ({len(group)}):")
            if status == 'healthy':
                logger.info(f"   {sorted(group)}")
            else:
                for detail in sorted(group):
                    logger.info(f"   - {detail}")
   
    healthy_count = len(status_groups['healthy'])
    unhealthy_count = len(services) - healthy_count
   
    logger.info(f"   Healthy: {healthy_count}/{len(services)}, Unhealthy: {unhealthy_count}")
   
    health_details["success"] = health_success
    health_details["service_status"] = detailed_health
    health_details["final_healthy_count"] = healthy_count
    health_details["final_unhealthy_count"] = unhealthy_count
   
    return health_success, health_details

def _get_detailed_health_status(
    compose_file: str,
    services: List[str],
    logger: logger
) -> Dict[str, Dict[str, Any]]:
    """Get detailed health status for each service with overall_status."""
    detailed_status = {}
    
    try:
        # Use the reliable JSON parsing method
        health_result = check_health_from_compose_ps(compose_file)
        all_services_status = health_result.get('services', {})
        
        for service in services:
            service_status = all_services_status.get(service, {})
            overall_status = _compute_overall_status(service_status)
            error_msg = "No error details"
            if overall_status == "starting":
                error_msg = "Service is starting"
            elif overall_status == "restarting":
                error_msg = "Service is restarting"
            elif overall_status == "unhealthy":
                error_msg = f"Service is unhealthy: {service_status.get('status', 'unknown')}"
            elif overall_status == "not found":
                error_msg = "Service not found"
            detailed_status[service] = {
                'healthy': overall_status == 'healthy',
                'health': service_status.get('health', 'unknown'),
                'status': service_status.get('status', 'not found'),
                'state': service_status.get('state', 'unknown'),  # Added
                'error': error_msg,
                'overall_status': overall_status
            }
            # Removed individual logging; handled in groups
        
    except Exception as e:
        logger.error(f"Failed to get detailed health status: {e}")
        # Fallback: mark all as unhealthy
        for service in services:
            detailed_status[service] = {
                'healthy': False,
                'health': 'unknown',
                'status': 'check failed',
                'state': 'unknown',
                'error': str(e),
                'overall_status': 'unhealthy'
            }
    
    return detailed_status


def _expand_env_vars_in_value(value):
    """Expand environment variables in a string value."""
    if not isinstance(value, str):
        return value
    
    def replace_var(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))
    
    # Replace ${VAR}
    value = re.sub(r'\$\{([^}]+)\}', replace_var, value)
    
    # Replace $VAR (simple format)
    def replace_simple_var(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))
    
    value = re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)', replace_simple_var, value)
    
    return value

def _expand_env_vars_in_compose(data):
    """Recursively expand environment variables in compose data."""
    if isinstance(data, dict):
        return {k: _expand_env_vars_in_compose(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_expand_env_vars_in_compose(item) for item in data]
    elif isinstance(data, str):
        return _expand_env_vars_in_value(data)
    else:
        return data

def _capture_failing_service_logs(
    compose_file: str,
    failing_services: List[str],
    tail: int,
    project_name: Optional[str],
    logger: logger
) -> Dict[str, Dict[str, Any]]:
    """Capture logs for failing services with error analysis."""
    logs_data = {}
    
    for service in failing_services:
        try:
            logger.info(f"📄 Capturing logs for {service}...")
            
            # Get recent logs
            log_result = compose_logs(
                compose_file,
                services=[service],
                tail=tail,
                project_name=project_name
            )
            
            log_lines = []
            error_logs = []
            
            if isinstance(log_result, dict) and service in log_result:
                # Logs are returned as a dictionary per service
                service_logs = log_result[service]
                if isinstance(service_logs, list):
                    log_lines = service_logs
                elif isinstance(service_logs, str):
                    log_lines = service_logs.split('\n')
            elif isinstance(log_result, str):
                # Logs are returned as a single string
                log_lines = log_result.split('\n')
            
            # Analyze logs for errors
            for line in log_lines:
                line_lower = line.lower()
                if any(error_indicator in line_lower for error_indicator in 
                      ['error', 'exception', 'failed', 'fatal', 'crash', 'panic']):
                    error_logs.append(line.strip())
            
            logs_data[service] = {
                'all_logs': log_lines[-tail:],  # Last 'tail' lines
                'error_logs': error_logs,
                'log_count': len(log_lines),
                'error_count': len(error_logs)
            }
            
            logger.info(f"   Captured {len(log_lines)} lines, {len(error_logs)} errors")
            
        except Exception as e:
            logger.error(f"Failed to capture logs for {service}: {e}")
            logs_data[service] = {
                'all_logs': [],
                'error_logs': [f"Failed to capture logs: {e}"],
                'log_count': 0,
                'error_count': 1
            }
    
    return logs_data


def _get_registries_from_services(
    compose_file: str,
    services: List[str],
    project_name: Optional[str],
    logger: logger
) -> Dict[str, Dict[str, Any]]:
    """Extract unique registries from service images."""
    registries = {}
    
    for service in services:
        try:
            image_name = get_service_image(compose_file, service)
            if not image_name:
                continue
            
            # Parse registry from image name
            registry_info = _parse_image_registry(image_name)
            registry = registry_info['registry']
            
            if registry not in registries:
                registries[registry] = {
                    'registry': registry,
                    'services': [],
                    'images': [],
                    'registry_type': registry_info['type']
                }
            
            registries[registry]['services'].append(service)
            registries[registry]['images'].append(image_name)
            
        except Exception as e:
            logger.warning(f"Could not parse registry for {service}: {e}")
    
    return registries

def _parse_image_registry(image_name: str) -> Dict[str, str]:
    """Parse registry information from image name."""
    # Handle edge cases
    if not image_name or not isinstance(image_name, str):
        return {
            'registry': 'docker.io',
            'type': 'dockerhub',
            'full_image': image_name or 'unknown'
        }
    
    # Default values
    registry = "docker.io"
    registry_type = "dockerhub"
    
    # Remove tag if present
    image_without_tag = image_name.split(':')[0] if ':' in image_name else image_name
    
    # Split by slashes
    parts = image_without_tag.split('/')
    
    if len(parts) == 1:
        # Single part (e.g., "nginx") - Docker Hub official image
        registry = "docker.io"
        registry_type = "dockerhub"
    elif len(parts) == 2:
        # Two parts (e.g., "library/nginx" or "myregistry/image")
        if '.' in parts[0] or ':' in parts[0] or parts[0] == 'localhost':
            registry = parts[0]
            registry_type = "private"
        else:
            registry = "docker.io"
            registry_type = "dockerhub"
    elif len(parts) >= 3:
        # Three or more parts (e.g., "myregistry.com/namespace/image")
        registry = parts[0]
        registry_type = "private"
    
    # Detect common registry types
    common_registries = {
        'docker.io': 'dockerhub',
        'gcr.io': 'gcr',
        'k8s.gcr.io': 'gcr',
        'eu.gcr.io': 'gcr',
        'us.gcr.io': 'gcr',
        'asia.gcr.io': 'gcr',
        'registry.gitlab.com': 'gitlab',
        'registry.hub.docker.com': 'dockerhub',
        'quay.io': 'quay',
        'ghcr.io': 'github',
    }
    
    for reg_pattern, reg_type in common_registries.items():
        if registry.startswith(reg_pattern):
            registry_type = reg_type
            break
    
    # Detect AWS ECR
    if '.ecr.' in registry and '.amazonaws.com' in registry:
        registry_type = 'ecr'
    
    # Detect Azure Container Registry
    if '.azurecr.io' in registry:
        registry_type = 'acr'
    
    return {
        'registry': registry,
        'type': registry_type,
        'full_image': image_name
    }
    
def _check_registry_auth(
    registry: str,
    registry_info: Dict[str, Any],
    logger
) -> bool:
    """Check if authenticated to a registry using Docker config and simple API test."""
    # First, check Docker config for existing credentials
    if _check_docker_config_credentials(registry, logger):
        return True
    
    # For a more reliable check, try a simple API call or use docker login test
    try:
        client = get_docker_client()
        if not client:
            return False
            
        # Try a simple operation that requires authentication
        if registry == "docker.io":
            # For Docker Hub, check if we can access a public endpoint
            # or just rely on config check since Docker Hub allows anonymous pulls
            return True  # Docker Hub allows anonymous access for public images
        else:
            # For private registries, try to get catalog (if supported)
            # This is more reliable than trying to pull specific images
            try:
                # Use docker command to check login status
                result = run_docker_command(
                    ["login", registry, "--get-login"],
                    capture=True,
                    check=False
                )
                return result.rc == 0
            except Exception:
                # If the above fails, assume we need authentication
                return False
                
    except Exception as e:
        logger.debug(f"Auth check API call failed for {registry}: {e}")
        return False

def _handle_interactive_login(
    registry: str,
    registry_info: Dict[str, Any],
    timeout: int,
    save_credentials: bool,
    logger
) -> bool:
    """Handle interactive Docker login with timeout."""
    logger.info(f"🔐 Login required for {registry}")
    
    try:
        import signal
        import getpass
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Login timeout after {timeout} seconds")
        
        # Set timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            # Get credentials
            username = input(f"   Username for {registry}: ").strip()
            if not username:
                logger.error("❌ No username provided")
                return False
            
            password = getpass.getpass(f"   Password for {registry}: ")
            if not password:
                logger.error("❌ No password provided")
                return False
            
            # Optional email for Docker Hub
            email = None
            if registry == "docker.io":
                email_input = input("   Email (optional, press Enter to skip): ").strip()
                email = email_input if email_input else None
            
            # Perform login
            login_success = docker_login(
                registry=registry,
                username=username,
                password=password,
                email=email,
                reauth=True,
                logger=logger
            )
            
            signal.alarm(0)  # Cancel timeout
            return login_success
            
        except TimeoutError:
            logger.error(f"⏰ Login timeout after {timeout} seconds")
            return False
        finally:
            signal.alarm(0)  # Ensure timeout is cancelled
            
    except Exception as e:
        logger.error(f"💥 Interactive login failed: {e}")
        return False

def _push_compose_images(
    compose_file: str,
    services: List[str],
    push_all: bool,
    timeout: int,
    project_name: Optional[str],
    env_file: Optional[str],
    logger: logger
) -> Dict[str, Any]:
    """Push compose images to registry."""
    push_results = {
        "success": False,
        "services_pushed": [],
        "images_pushed": [],
        "failed_services": [],
        "push_details": {}
    }
    
    try:
        # Use compose push command
        if push_all:
            logger.info("Pushing all services...")
            push_command = ["push"]
            if services:
                push_command.extend(services)
            
            push_result = run_compose_command(
                compose_file, 
                push_command,
                project_name=project_name,
                env_file=env_file
            )
            
            if push_result.rc == 0:
                push_results["success"] = True
                push_results["services_pushed"] = services or get_services_from_compose(compose_file , env_file)
                logger.info("✅ All services pushed successfully")
            else:
                push_results["success"] = False
                logger.error(f"❌ Push failed: {push_result.stderr}")
                # Try to parse which services failed
                push_results["failed_services"] = services or get_services_from_compose(compose_file , env_file)
        else:
            # Push services individually for better error reporting
            for service in services:
                logger.info(f"Pushing {service}...")
                try:
                    push_result = run_compose_command(
                        compose_file,
                        ["push", service],
                        project_name=project_name,
                        env_file=env_file
                    )
                    
                    if push_result.rc == 0:
                        push_results["services_pushed"].append(service)
                        image_name = get_service_image(compose_file, service)
                        if image_name:
                            push_results["images_pushed"].append(image_name)
                        logger.info(f"✅ {service} pushed successfully")
                    else:
                        push_results["failed_services"].append(service)
                        logger.error(f"❌ {service} push failed: {push_result.stderr}")
                        
                except Exception as e:
                    push_results["failed_services"].append(service)
                    logger.error(f"❌ {service} push failed: {e}")
            
            push_results["success"] = len(push_results["failed_services"]) == 0
        
        return push_results
        
    except Exception as e:
        logger.error(f"Push operation failed: {e}")
        push_results["success"] = False
        push_results["error"] = str(e)
        return push_results
    

def _handle_registry_authentication(
    registry: str,
    registry_info: Dict,
    is_ci_cd: bool,
    interactive_login: bool,
    login_timeout: int,
    save_credentials: bool,
    logger
) -> Optional[str]:
    """
    Handle registry authentication using multiple methods in order of priority.
    
    Returns: authentication method used or None if failed
    """
    # Method 1: Try environment variables
    env_auth = _try_environment_authentication(registry, registry_info, logger)
    if env_auth:
        return "environment_variables"
    
    # Method 2: Check for existing credentials in Docker config (already checked, but double-check)
    if _check_docker_config_credentials(registry, logger):
        return "docker_config"
    
    # Method 3: In CI/CD, fail if no credentials found
    if is_ci_cd:
        logger.error(f"💥 CI/CD environment: No credentials found for {registry}")
        logger.info(f"💡 Please set registry credentials via environment variables or run 'docker login {registry}'")
        return None
    
    # Method 4: Interactive login
    if interactive_login:
        login_success = _handle_interactive_login(
            registry=registry,
            registry_info=registry_info,
            timeout=login_timeout,
            save_credentials=save_credentials,
            logger=logger
        )
        if login_success:
            return "interactive"
    
    # Method 5: If all else fails and we're in a terminal, provide guidance
    if sys.stdin.isatty():
        logger.error(f"💥 No authentication method available for {registry}")
        logger.info(f"💡 Please run: docker login {registry}")
        logger.info(f"💡 Or set environment variables: REGISTRY_USERNAME, REGISTRY_PASSWORD")
    
    return None


def _try_environment_authentication(registry: str, registry_info: Dict, logger) -> bool:
    """
    Try to authenticate using environment variables.
    Supports multiple environment variable patterns.
    """
    # Try common environment variable patterns
    env_patterns = [
        # Registry-specific (e.g., HARBOR_USER, HARBOR_PASSWORD)
        (f"{_registry_to_env(registry)}_USER", f"{_registry_to_env(registry)}_PASSWORD"),
        # Generic (e.g., DOCKER_USERNAME, DOCKER_PASSWORD)
        ("HARBOR_USERNAME", "HARBOR_PASSWORD"),
        ("HARBOR_USER", "HARBOR_PASSWORD"),
        ("DOCKER_USERNAME", "DOCKER_PASSWORD"),
        ("REGISTRY_USERNAME", "REGISTRY_PASSWORD"),
        ("CI_REGISTRY_USER", "CI_REGISTRY_PASSWORD"),  # GitLab CI
    ]
    
    for username_var, password_var in env_patterns:
        username = os.environ.get(username_var)
        password = os.environ.get(password_var)
        
        if username and password:
            logger.info(f"   🔐 Trying authentication with {username_var}...")
            try:
                success = docker_login(
                    registry=registry,
                    username=username,
                    password=password,
                    logger=logger
                )
                if success:
                    logger.info(f"   ✅ Authenticated to {registry} using {username_var}")
                    return True
                else:
                    logger.warning(f"   ⚠️  Authentication failed with {username_var}")
            except Exception as e:
                logger.warning(f"   ⚠️  Authentication error with {username_var}: {e}")
    
    return False


def _registry_to_env(registry: str) -> str:
    """
    Convert registry URL to environment variable friendly format.
    e.g., 'harbor.example.com' -> 'HARBOR_EXAMPLE_COM'
    """
    # Remove protocol
    registry = registry.replace('https://', '').replace('http://', '')
    # Replace non-alphanumeric characters with underscores
    registry = re.sub(r'[^a-zA-Z0-9]', '_', registry)
    # Convert to uppercase
    return registry.upper()


def _check_docker_config_credentials(registry: str, logger) -> bool:
    """
    Check if credentials exist in Docker config file for the registry.
    """
    docker_config_path = Path.home() / '.docker' / 'config.json'
    
    if not files.file_exists(docker_config_path):
        return False
    
    try:
        with open(docker_config_path, 'r') as f:
            config = json.load(f)
        
        # Check auths section
        auths = config.get('auths', {})
        if registry in auths:
            logger.debug(f"   ✅ Found credentials for {registry} in Docker config")
            return True
        
        # Check for credential helpers
        cred_helpers = config.get('credHelpers', {})
        if registry in cred_helpers:
            logger.debug(f"   ✅ Found credential helper for {registry} in Docker config")
            return True
        
        return False
        
    except Exception as e:
        logger.warning(f"   ⚠️  Could not read Docker config: {e}")
        return False


def _detect_ci_environment() -> bool:
    """
    Detect if running in CI/CD environment.
    """
    ci_vars = [
        'CI', 'GITLAB_CI', 'JENKINS_URL', 'TRAVIS', 'CIRCLECI',
        'GITHUB_ACTIONS', 'BITBUCKET_BUILD_NUMBER', 'TEAMCITY_VERSION'
    ]
    return any(os.environ.get(var) for var in ci_vars)


def _service_has_build(service_config: Dict[str, Any]) -> bool:
    """
    Check if a service has a build configuration.
    
    Args:
        service_config: Service configuration from compose
        
    Returns:
        True if service has build configuration
    """
    return 'build' in service_config and service_config['build'] is not None

def push_compose(
    compose_file: str,
    # Environment configuration
    env_file: str = '.env',
    update_version: bool = False,
    version_source: str = 'git',
    
    # Push configuration
    services: Optional[List[str]] = None,
    push_all: bool = True,
    registry_timeout: int = 300,
    
    # Login configuration
    interactive_login: bool = True,
    login_timeout: int = 300,  # 5 minutes
    save_credentials: bool = True,
    
    # Additional options
    project_name: Optional[str] = None,
    dry_run: bool = False,
    logger: Optional[logger] = None
    
) -> Dict[str, Any]:
    """
    Push Docker Compose images to registry with authentication handling.
    
    Steps:
    1. Update version (if enabled)
    2. Check registry authentication using Docker config and environment variables
    3. Handle login via multiple methods (existing credentials, env vars, interactive)
    4. Push images to registry
    5. Verify push success
    
    Returns: Push results with authentication status
    """
    logger = logger or DEFAULT_LOGGER
    push_id = str(uuid.uuid4())[:8]
    
    result = {
        "push_id": push_id,
        "success": False,
        "steps": {},
        "services_pushed": [],
        "images_pushed": [],
        "login_required": False,
        "login_success": False,
        "auth_method": None,
        "error": None,
        "duration": 0.0
    }
    
    start_time = dt_ops.current_datetime()
    
    try:
        logger.info(f"📤 Starting push {push_id}")
        logger.info(f"   Compose: {compose_file}")
        logger.info(f"   Interactive login: {interactive_login}")
        
        # Step 0: Pre-build validation
        logger.info("📋 Step 1: Validating configuration...")
        if not files.file_exists(compose_file):
            raise DockerOpsError(f"Compose file not found: {compose_file}")
        
        if not files.file_exists(env_file):
            logger.warning(f"Environment file not found: {env_file}")
        
        # Step 1: Update version (optional)
        new_version = None
        if update_version and not dry_run:
            logger.info("🔧 Step 1: Updating version...")
            new_version = _update_env_version(
                env_file=env_file,
                source=version_source,
                logger=logger
            )
            if new_version:
                logger.info(f"✅ Version updated to: {new_version}")
                envs.import_env_to_system(get_env_compose(env_file))
                result["new_version"] = new_version
        elif dry_run and update_version:
            logger.info("🔧 Step 1: Version update skipped (dry run)")
        else:
            logger.info("🔧 Step 1: Version update disabled")
        
        # Step 2: Check and handle registry authentication
        logger.info("🔐 Step 2: Handling registry authentication...")
        
        # Detect CI/CD environment
        is_ci_cd = _detect_ci_environment()
        if is_ci_cd:
            logger.info("🔄 CI/CD environment detected")
            result["environment"] = "ci_cd"
        
        if not dry_run:
            # Get services and their images
            compose_config = read_compose_file(compose_file, env_file)
            available_services = list(compose_config.get('services', {}).keys())
            target_services = services or available_services
            
            # Extract unique registries from images
            registries = _get_registries_from_services(
                compose_file, target_services, project_name, logger
            )
            
            if not registries:
                logger.warning("⚠️ No registries found in service images")
                result["steps"]["registry_check"] = {"status": "no_registries"}
            else:
                logger.info(f"🔍 Found {len(registries)} unique registries: {list(registries.keys())}")
                result["steps"]["registry_check"] = {
                    "status": "registries_found",
                    "registries": list(registries.keys()),
                    "registry_details": registries
                }
            
            # Handle authentication for each registry
            auth_results = {}
            for registry, registry_info in registries.items():
                logger.info(f"   Handling auth for {registry}...")
                
                # Check if already authenticated via Docker config
                is_authenticated = _check_registry_auth(registry, registry_info, logger)
                
                if is_authenticated:
                    auth_results[registry] = {
                        "status": "authenticated",
                        "method": "existing_credentials",
                        "success": True
                    }
                    logger.info(f"   ✅ Already authenticated to {registry} (Docker config)")
                    continue
                
                # Try authentication with different methods
                auth_success = _handle_registry_authentication(
                    registry=registry,
                    registry_info=registry_info,
                    is_ci_cd=is_ci_cd,
                    interactive_login=interactive_login,
                    login_timeout=login_timeout,
                    save_credentials=save_credentials,
                    logger=logger
                )
                
                if auth_success:
                    auth_results[registry] = {
                        "status": "authenticated", 
                        "method": auth_success,
                        "success": True
                    }
                    result["login_required"] = True
                    result["login_success"] = True
                    result["auth_method"] = auth_success
                    logger.info(f"   ✅ Successfully authenticated to {registry} via {auth_success}")
                else:
                    auth_results[registry] = {
                        "status": "failed",
                        "method": "none",
                        "success": False
                    }
                    logger.error(f"💥 Authentication failed for {registry}")
                    raise DockerOpsError(f"Registry authentication failed for {registry}")
            
            result["steps"]["authentication"] = {
                "required": any(not auth["success"] for auth in auth_results.values()),
                "results": auth_results,
                "success": all(auth["success"] for auth in auth_results.values())
            }
        else:
            logger.info("🔐 Step 2: Authentication check skipped (dry run)")
        
        # Step 3: Push images
        logger.info("📤 Step 3: Pushing images...")
        if not dry_run:
            push_results = _push_compose_images(
                compose_file=compose_file,
                services=target_services,
                push_all=push_all,
                timeout=registry_timeout,
                project_name=project_name,
                env_file=env_file,
                logger=logger
            )
            
            result["steps"]["push"] = push_results
            result["services_pushed"] = push_results.get("services_pushed", [])
            result["images_pushed"] = push_results.get("images_pushed", [])
            
            if push_results.get("success"):
                pushed_count = len(push_results.get("services_pushed", []))
                logger.info(f"✅ Successfully pushed {pushed_count} services")
                result["success"] = True
            else:
                failed_services = push_results.get("failed_services", [])
                logger.error(f"❌ Push failed for {len(failed_services)} services: {failed_services}")
                result["success"] = False
        else:
            # Dry run simulation
            compose_config = read_compose_file(compose_file, env_file)
            available_services = list(compose_config.get('services', {}).keys())
            target_services = services or available_services
            result["services_pushed"] = target_services
            result["images_pushed"] = [
                get_service_image(compose_file, svc) or f"{svc}:latest" 
                for svc in target_services
            ]
            result["success"] = True
            logger.info("📤 Step 3: Push skipped (dry run)")
        
        # Calculate duration
        result["duration"] = (dt_ops.current_datetime() - start_time).total_seconds()
        
        if result["success"]:
            logger.info(f"🎉 Push {push_id} completed successfully in {result['duration']:.1f}s!")
            logger.info(f"   Pushed {len(result['images_pushed'])} images")
            if result.get("auth_method"):
                logger.info(f"   Auth method: {result['auth_method']}")
        else:
            logger.error(f"💥 Push {push_id} failed in {result['duration']:.1f}s!")
        
        return result
        
    except Exception as e:
        # Failure handling
        result["duration"] = (dt_ops.current_datetime() - start_time).total_seconds()
        result["error"] = str(e)
        
        logger.error(f"💥 Push {push_id} failed: {e}")
        return result


def test_compose(
    compose_file: str,
    # Environment configuration
    env_file: str = '.env',
    update_version: bool = False,
    version_source: str = 'git',
   
    # Test configuration
    services: Optional[List[str]] = None,
    health_timeout: int = 500,  # Changed to represent total max wait time (e.g., 500 seconds)
    health_interval: int = 10,
    capture_logs: bool = True,
    log_tail: int = 100,
   
    # Startup options
    pull_missing: bool = True,
    no_build: bool = True,
    no_pull: bool = True,
   
    # Cleanup options
    keep_compose_up: bool = False,
   
    # Additional options
    project_name: Optional[str] = None,
    dry_run: bool = False,
    logger: Optional[logger] = None
   
) -> Dict[str, Any]:
    """
    Test Docker Compose services with comprehensive health checks and logging.
   
    Improvements:
    - If compose up fails, capture error and skip health checks.
    - Enhanced conflict checking: Detailed info for no conflicts, shows conflicts if found, and automatically resolves them (containers and networks; volumes skipped to avoid data loss).
    - Health statuses expanded to: not found, starting, restarting, healthy, unhealthy.
    - Simplified health checking: Removed outer retries, now uses a single total health_timeout (e.g., 500s) with checks every health_interval.
    - Other upgrades: Better error handling around compose_up, more detailed logging, implemented port conflict resolution by removing conflicting containers.
   
    Steps:
    0. Pre-Test validation
    1. Update version (if enabled)
    2. Check for conflicts and resolve if found
    3. Start services with --no-build and --no-pull
    4. Perform health checks (single phase with total timeout)
    5. Capture detailed logs for failing services
    6. Bring down services (unless keep_compose_up=True)
   
    Args:
        keep_compose_up: If True, services will not be stopped after test. Default: False.
   
    Returns: Detailed test results with logs
    """
    logger = logger or DEFAULT_LOGGER
    test_id = str(uuid.uuid4())[:8]
   
    result = {
        "test_id": test_id,
        "success": False,
        "steps": {},
        "services_tested": [],
        "health_status": {},
        "failing_services": [],
        "logs_captured": {},
        "keep_compose_up": keep_compose_up,
        "error": None,
        "duration": 0.0
    }
   
    start_time = dt_ops.current_datetime()
   
    try:
        logger.info(f"🧪 Starting test {test_id}")
        logger.info(f" Compose: {compose_file}")
        logger.info(f" Health timeout: {health_timeout}s, interval: {health_interval}s")
        logger.info(f" Keep services after test: {keep_compose_up}")
       
       
        # Step 0: Pre-build validation
        logger.info("📋 Step 0: Validating configuration...")
        if not files.file_exists(compose_file):
            raise DockerOpsError(f"Compose file not found: {compose_file}")
       
        if not files.file_exists(env_file):
            logger.warning(f"Environment file not found: {env_file}")
           
        # Step 1: Update version (optional)
        new_version = None
        if update_version and not dry_run:
            logger.info("🔧 Step 1: Updating version...")
            new_version = _update_env_version(
                env_file=env_file,
                source=version_source,
                logger=logger
            )
            if new_version:
                logger.info(f"✅ Version updated to: {new_version}")
                envs.import_env_to_system(get_env_compose(env_file))
        elif dry_run and update_version:
            logger.info("🔧 Step 1: Version update skipped (dry run)")
        else:
            logger.info("🔧 Step 1: Version update disabled")
       
        # Step 2: Check for conflicts
        logger.info("🔍 Step 2: Checking for conflicts...")
        result["steps"]["conflict_check"] = {"status": "no_conflicts", "conflicts": None}
        if not dry_run:
            conflicts = check_conflicts(compose_file, project_name=project_name, env_file=env_file)
            if any(conflicts.values()):  # Check if any conflict lists are non-empty
                logger.warning(f"⚠️ Found conflicts: {conflicts}")
                result["steps"]["conflict_check"] = {
                    "status": "conflicts_found",
                    "conflicts": conflicts
                }
                # Resolve conflicts (auto-remove containers and networks; skip volumes)
                resolution = resolve_conflicts(
                    compose_file,
                    remove_conflicting_containers=True,
                    remove_conflicting_networks=True,
                    remove_conflicting_volumes=False,
                    project_name=project_name,
                    env_file=env_file
                )
                if resolution["resolved"]:
                    logger.info(f"✅ Resolved conflicts: {resolution['resolved']}")
                    result["steps"]["conflict_resolution"] = {
                        "status": "resolved",
                        "resolved": resolution["resolved"],
                        "errors": resolution["errors"]
                    }
                if resolution["errors"]:
                    raise DockerOpsError(f"Failed to resolve some conflicts: {resolution['errors']}")
            else:
                logger.info("✅ No conflicts found")
        else:
            logger.info("🔍 Step 2: Conflict check skipped (dry run)")
       
        # Step 3: Start services
        logger.info("🚀 Step 3: Starting services...")
        if not dry_run:
            # Get services that need to be tested
            compose_config = read_compose_file(compose_file, env_file)
            available_services = list(compose_config.get('services', {}).keys())
            target_services = services or available_services
           
            # Check for missing images
            missing_images = _check_missing_images(
                compose_file,
                target_services,
                project_name,
                logger,
                env_file
            )
           
            if missing_images and pull_missing:
                logger.info(f"⬇️ Pulling {len(missing_images)} missing images...")
                for service in missing_images:
                    try:
                        compose_pull(compose_file, services=[service], project_name=project_name)
                        logger.info(f"✅ Pulled image for {service}")
                    except Exception as e:
                        logger.error(f"❌ Failed to pull image for {service}: {e}")
                        raise DockerOpsError(f"Missing image for {service} and pull failed")
           
            elif missing_images and not pull_missing:
                missing_list = ", ".join(missing_images)
                raise DockerOpsError(f"Missing images for services: {missing_list}")
           
            # Start services with no-build and no-pull
            up_options = []
            if no_build:
                up_options.append("--no-build")
            if no_pull:
                up_options.append("--no-pull")
               
            logger.info(f"Starting services with options: {up_options}")
            try:
                up_result = compose_up(
                    compose_file,
                    services=services,
                    project_name=project_name,
                    no_build=no_build,
                    no_pull=no_pull,
                )
                # Assuming compose_up returns a dict with 'success'; adjust if needed
                if up_result is not True:  # If it doesn't raise, check result
                    raise DockerOpsError(f"Compose up failed: 'Fial to docker compose up  for Unknown error'")
            except Exception as e:
                result["error"] = str(e)
                logger.error(f"❌ Compose up failed: {e}")
                result["steps"]["start_services"] = {"success": False, "error": str(e)}
                raise  # Re-raise to skip health checks and go to cleanup
           
            result["steps"]["start_services"] = {
                "success": True,
                "services_started": target_services,
                "options": up_options
            }
            result["services_tested"] = target_services
            logger.info(f"✅ Started {len(target_services)} services")
        else:
            # Dry run simulation
            compose_config = read_compose_file(compose_file, env_file)
            available_services = list(compose_config.get('services', {}).keys())
            target_services = services or available_services
            result["services_tested"] = target_services
            logger.info("🚀 Step 3: Service start skipped (dry run)")
       
        # Step 4: Health checks (single phase with total timeout)
        if not dry_run:
            logger.info("🏥 Step 4: Performing health checks...")
            health_success, health_details = _perform_health_checks(
                compose_file=compose_file,
                services=target_services,
                timeout=health_timeout,
                interval=health_interval,
                logger=logger,
                env_file=env_file
            )
           
            result["steps"]["health_check"] = health_details
            result["health_status"] = health_details.get("service_status", {})
           
            # Identify failing services (any not 'healthy')
            failing_services = [
                svc for svc, status in health_details.get("service_status", {}).items()
                if status.get("overall_status") != "healthy"
            ]
            result["failing_services"] = failing_services
           
            if health_success:
                logger.info("✅ All services healthy!")
                result["success"] = True
            else:
                logger.error(f"❌ Health checks failed for {len(failing_services)} services: {failing_services}")
                result["success"] = False
               
                # Step 5: Capture detailed logs for failing services
                if capture_logs and failing_services:
                    logger.info("📋 Step 5: Capturing logs for failing services...")
                    logs = _capture_failing_service_logs(
                        compose_file=compose_file,
                        failing_services=failing_services,
                        tail=log_tail,
                        project_name=project_name,
                        logger=logger
                    )
                    result["logs_captured"] = logs
                    result["steps"]["log_capture"] = {
                        "status": "captured",
                        "services": list(logs.keys())
                    }
                   
                    # Log the most critical errors
                    for service, log_data in logs.items():
                        if log_data.get('error_logs'):
                            logger.error(f"🔴 {service} error logs (last {log_tail} lines):")
                            for line in log_data['error_logs'][-10:]:
                                logger.error(f" {line}")
        else:
            logger.info("🏥 Step 4: Health checks skipped (dry run)")
            result["success"] = True  # Assume success in dry run
       
        # Step 6: Bring down services (unless keep_compose_up=True)
        if not dry_run and not keep_compose_up:
            logger.info("🛑 Step 6: Stopping services...")
            try:
                down_result = compose_down(compose_file, project_name=project_name)
                result["steps"]["cleanup"] = {"status": "success"}
                logger.info("✅ Services stopped")
            except Exception as e:
                logger.warning(f"⚠️ Service cleanup failed: {e}")
                result["steps"]["cleanup"] = {"status": "failed", "error": str(e)}
        elif keep_compose_up and not dry_run:
            logger.info("🛑 Step 6: Skipping service cleanup (keep_compose_up=True)")
            result["steps"]["cleanup"] = {"status": "skipped", "reason": "keep_compose_up=True"}
        elif dry_run:
            logger.info("🛑 Step 6: Service cleanup skipped (dry run)")
       
        # Calculate duration
        result["duration"] = (dt_ops.current_datetime() - start_time).total_seconds()
       
        if result["success"]:
            if keep_compose_up:
                logger.info(f"🎉 Test {test_id} completed successfully in {result['duration']:.1f}s! Services kept running.")
            else:
                logger.info(f"🎉 Test {test_id} completed successfully in {result['duration']:.1f}s!")
        else:
            logger.error(f"💥 Test {test_id} failed in {result['duration']:.1f}s!")
       
        return result
       
    except Exception as e:
        # Failure handling
        result["duration"] = (dt_ops.current_datetime() - start_time).total_seconds()
        result["error"] = str(e)
       
        logger.error(f"💥 Test {test_id} failed: {e}")
       
        # Only try to cleanup on failure if keep_compose_up=False
        if not dry_run and not keep_compose_up:
            try:
                logger.info("🛑 Emergency cleanup...")
                compose_down(compose_file, project_name=project_name)
                result["steps"]["emergency_cleanup"] = {"status": "success"}
            except Exception as cleanup_error:
                logger.error(f"💥 Emergency cleanup failed: {cleanup_error}")
                result["steps"]["emergency_cleanup"] = {"status": "failed", "error": str(cleanup_error)}
       
        return result
    
def build_compose(
    compose_file: str,
    # Environment configuration
    env_file: str = '.env',
    update_version: bool = False,  # Now optional, default False
    version_source: str = 'git',  # 'git', 'branch', 'commit'
    
    # Build configuration
    services: Optional[List[str]] = None,
    no_cache: bool = False,
    pull: bool = False,  # Force pull all base images
    pull_missing: bool = True,  # NEW: Pull only missing images for services without build
    
    # Cleanup
    cleanup_intermediate: bool = True,
    
    # Additional options
    project_name: Optional[str] = None,
    dry_run: bool = False,
    logger: Optional[logger] = None
    
) -> Dict[str, Any]:
    """
    Build Docker Compose services with optional version management.
    
    Steps:
    0. Pre-build validation
    1. Update version in .env file (if enabled)
    2. Validate compose file and environment
    3. Pull base images (if enabled)
    4. Build services
    5. Cleanup intermediate images (if enabled)
    
    Returns: Build results with version information
    """
    logger = logger or DEFAULT_LOGGER
    build_id = str(uuid.uuid4())[:8]
    
    result = {
        "build_id": build_id,
        "success": False,
        "steps": {},
        "version_updated": False,
        "new_version": None,
        "services_built": [],
        "images_pulled": [],
        "error": None,
        "duration": 0.0
    }
    
    start_time = dt_ops.current_datetime()
    
    try:
        logger.info(f"🔨 Starting build {build_id}")
        logger.info(f"   Compose: {compose_file}")
        logger.info(f"   Version update: {update_version} (source: {version_source})")
        logger.info(f"   Pull mode: {'force all' if pull else 'missing only' if pull_missing else 'none'}")
        
        # Step 0: Pre-build validation
        logger.info("📋 Step 1: Validating configuration...")
        if not files.file_exists(compose_file):
            raise DockerOpsError(f"Compose file not found: {compose_file}")
        
        if not files.file_exists(env_file):
            logger.warning(f"Environment file not found: {env_file}")
        
        # Step 1: Update version in .env file (optional)
        new_version = None
        if update_version and not dry_run:
            logger.info("🔧 Step 2: Updating version...")
            new_version = _update_env_version(
                env_file=env_file,
                source=version_source,
                logger=logger
            )
            
            if new_version:
                result["version_updated"] = True
                result["new_version"] = new_version
                logger.info(f"✅ Version updated to: {new_version}")
                # Reload environment to get updated version
                envs.import_env_to_system(get_env_compose(env_file))
            else:
                logger.info("ℹ️ Version update skipped - using existing version")
        elif dry_run and update_version:
            logger.info("🔧 Step 2: Version update skipped (dry run)")
        else:
            logger.info("🔧 Step 2: Version update disabled")
        
        # Step 2:  Get available services and their configurations
        compose_config = read_compose_file(compose_file, env_file)
        available_services = list(compose_config.get('services', {}).keys())
        
        if services:
            invalid_services = [svc for svc in services if svc not in available_services]
            if invalid_services:
                raise DockerOpsError(f"Invalid services: {invalid_services}")
        
        target_services = services or available_services
        logger.info(f"✅ Validation passed - Building {len(target_services)} services")
        result["steps"]["validation"] = {"status": "passed", "services": target_services}
        
        
        
        # Step 3: Pull base images based on mode
        if (pull or pull_missing) and not dry_run:
            logger.info("⬇️ Step 3: Pulling base images...")
            
            if pull:
                # Force pull all images (original behavior)
                logger.info("   Mode: Force pull all images")
                try:
                    pull_results = compose_pull(compose_file, project_name=project_name)
                    successful_pulls = sum(1 for success in pull_results.values() if success)
                    logger.info(f"✅ Pulled {successful_pulls}/{len(pull_results)} base images")
                    result["steps"]["pull"] = {
                        "mode": "force_all",
                        "successful": successful_pulls, 
                        "total": len(pull_results)
                    }
                    result["images_pulled"] = list(pull_results.keys())
                except Exception as pull_error:
                    logger.warning(f"⚠️ Base image pull failed: {pull_error}")
                    # Continue with build even if pull fails
            
            elif pull_missing:
                # Intelligent pull: only pull images for services without build section
                logger.info("   Mode: Pull missing images for non-build services")
                services_to_pull = []
                images_pulled = []
                
                # Identify services that don't have build configuration
                for service_name in target_services:
                    service_config = compose_config['services'][service_name]
                    
                    # If service doesn't have build section, we need to pull its image
                    if not _service_has_build(service_config):
                        services_to_pull.append(service_name)
                
                if services_to_pull:
                    logger.info(f"   Found {len(services_to_pull)} non-build services to check: {', '.join(services_to_pull)}")
                    
                    # Check which images are missing
                    missing_images = _check_missing_images(
                        compose_file, 
                        services_to_pull, 
                        project_name, 
                        logger,
                        env_file
                    )
                    
                    if missing_images:
                        logger.info(f"   Pulling {len(missing_images)} missing images...")
                        for service in missing_images:
                            try:
                                pull_result = compose_pull(
                                    compose_file, 
                                    services=[service], 
                                    project_name=project_name
                                )
                                
                                if pull_result.get(service, False):
                                    logger.info(f"   ✅ Pulled image for {service}")
                                    images_pulled.append(service)
                                else:
                                    logger.warning(f"   ⚠️ Failed to pull image for {service}")
                            except Exception as e:
                                logger.warning(f"   ⚠️ Error pulling image for {service}: {e}")
                        
                        result["steps"]["pull"] = {
                            "mode": "missing_only",
                            "services_checked": services_to_pull,
                            "missing_found": missing_images,
                            "pulled_successfully": images_pulled,
                            "total": len(missing_images)
                        }
                        result["images_pulled"] = images_pulled
                    else:
                        logger.info("   ✅ All non-build service images are already available locally")
                        result["steps"]["pull"] = {
                            "mode": "missing_only",
                            "services_checked": services_to_pull,
                            "missing_found": [],
                            "status": "no_pull_needed"
                        }
                else:
                    logger.info("   ℹ️ All services have build configuration - no images to pull")
                    result["steps"]["pull"] = {
                        "mode": "missing_only",
                        "services_checked": [],
                        "status": "all_services_have_build"
                    }
        
        elif dry_run and (pull or pull_missing):
            logger.info("⬇️ Step 3: Image pull skipped (dry run)")
            result["steps"]["pull"] = {"mode": "dry_run", "would_pull": pull or pull_missing}
        
        # Step 4: Build services
        logger.info("🔨 Step 4: Building services...")
        if not dry_run:
            # Determine which services to build (those with build configuration)
            services_to_build = []
            for service_name in target_services:
                service_config = compose_config['services'][service_name]
                if _service_has_build(service_config):
                    services_to_build.append(service_name)
            
            if services_to_build:
                logger.info(f"   Building {len(services_to_build)} services with build configuration...")
                
                build_result = compose_build(
                    compose_file=compose_file,
                    services=services_to_build,  # Only build services that need building
                    no_cache=no_cache,
                    project_name=project_name,
                    logger=logger
                )
                
                # Convert build_result to list of built services
                built_services = list(build_result.keys()) if isinstance(build_result, dict) else services_to_build
                
                result["steps"]["build"] = {
                    "success": True,
                    "services_built": built_services,
                    "services_with_build": services_to_build,
                    "details": build_result
                }
                result["services_built"] = built_services
                logger.info(f"✅ Built {len(built_services)} services successfully")
            else:
                logger.info("ℹ️ No services with build configuration - build step skipped")
                result["steps"]["build"] = {
                    "success": True,
                    "services_built": [],
                    "status": "no_build_required"
                }
                result["services_built"] = []
        else:
            # Dry run - simulate build
            result["steps"]["build"] = {
                "success": True,
                "services_built": target_services,
                "dry_run": True
            }
            result["services_built"] = target_services
            logger.info("🔨 Step 4: Build skipped (dry run)")
        
        # Step 5: Cleanup intermediate images
        if cleanup_intermediate and not dry_run:
            logger.info("🧹 Step 5: Cleaning up intermediate images...")
            try:
                cleanup_result = _cleanup_intermediate_images(logger)
                result["steps"]["cleanup"] = cleanup_result
                logger.info("✅ Cleanup completed")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Cleanup failed: {cleanup_error}")
                result["steps"]["cleanup"] = {"success": False, "error": str(cleanup_error)}
        elif dry_run:
            logger.info("🧹 Step 5: Cleanup skipped (dry run)")
        
        # Success!
        result["success"] = True
        result["duration"] = (dt_ops.current_datetime() - start_time).total_seconds()
        
        logger.info(f"🎉 Build {build_id} completed successfully!")
        logger.info(f"   Duration: {result['duration']:.1f}s")
        logger.info(f"   Services built: {len(result['services_built'])}")
        logger.info(f"   Images pulled: {len(result.get('images_pulled', []))}")
        if new_version:
            logger.info(f"   Version: {new_version}")
        
        return result
        
    except Exception as e:
        # Failure handling
        result["duration"] = (dt_ops.current_datetime() - start_time).total_seconds()
        result["error"] = str(e)
        
        logger.error(f"💥 Build {build_id} failed: {e}")
        return result


# Enhanced Deployment workflow
# Enhanced Deployment workflow
def deploy_compose(
    compose_file: str,
    # Environment configuration
    env_file: str = '.env',
    update_version: bool = False,
    version_source: str = 'git',
    env_update_keys: Optional[List[str]] = None,
    
    # Deployment strategy
    deployment_strategy: str = 'rolling',
    pull_images: bool = True,
    health_check: bool = True,
    health_timeout: int = 300,
    
    # Rollback configuration
    auto_rollback: bool = True,
    rollback_on_health_failure: bool = True,
    max_rollback_attempts: int = 3,
    
    # Backup configuration
    backup_enabled: bool = True,
    backup_dir: str = './backups_deploy',
    backup_images: bool = True,
    
    # Cleanup configuration
    keep_image_versions: int = 3,
    cleanup_old_backups: bool = True,
    keep_backup_versions: int = 5,
    
    # Additional options
    project_name: Optional[str] = None,
    dry_run: bool = False,
    logger: Optional[logger] = None
    
) -> Dict[str, Any]:
    """
    Enhanced deployment workflow with git tag versioning and robust rollback.
    
    Steps:
    1. Validate configuration
    2. Create backup (compose + images + env)
    3. Update environment from git/system
    4. Pull new images
    5. Deploy with selected strategy
    6. Health check with automatic rollback
    7. Cleanup old resources
    
    Returns: Detailed deployment result
    """
    logger = logger or DEFAULT_LOGGER
    deployment_id = str(uuid.uuid4())[:8]
    
    result = {
        "deployment_id": deployment_id,
        "success": False,
        "steps": {},
        "version_updated": False,
        "new_version": None,
        "rollback_performed": False,
        "error": None,
        "duration": 0.0
    }
    
    # Track deployment state for rollback
    deployment_state = {
        "backup_created": False,
        "env_updated": False,
        "images_pulled": False,
        "services_started": False,
        "backup_path": None,
        "env_backup_path": None,
        "original_env_content": None,
        "updated_env_keys": [],
        "previous_version": None,
        "new_version": None
    }
    
    start_time = dt_ops.current_datetime()
    
    try:
        logger.info(f"🚀 Starting deployment {deployment_id}")
        logger.info(f"   Compose: {compose_file}")
        logger.info(f"   Strategy: {deployment_strategy}")
        logger.info(f"   Version update: {update_version} (source: {version_source})")
        logger.info(f"   Env keys to update: {env_update_keys if env_update_keys is not None else 'auto'}")
        
        # Step 1: Pre-deployment validation
        logger.info("📋 Step 1: Validating configuration...")
        validation_errors = _validate_compose_preconditions(compose_file, env_file, logger)
        if validation_errors:
            logger.error(f"❌ Validation failed: {validation_errors}")
            raise DockerOpsError(f"Pre-deployment validation failed: {validation_errors}")
        logger.info("✅ Validation passed")
        result["steps"]["validation"] = {"status": "passed"}
        
        # Step 2: Create comprehensive backup
        if backup_enabled and not dry_run:
            logger.info("💾 Step 2: Creating backup...")
            
            # Read current version before backup
            if files.file_exists(env_file):
                current_env = envs.load_env_file(env_file)
                version_keys = ['CI_COMMIT_TAG', 'GIT_TAG', 'VERSION', 'APP_VERSION', 'IMAGE_TAG']
                for key in version_keys:
                    if key in current_env and current_env[key]:
                        deployment_state["previous_version"] = current_env[key]
                        break
            
            backup_path = backup_compose(
                compose_file=compose_file,
                backup_dir=backup_dir,
                include_images=backup_images,
                project_name=project_name,
                env_file=env_file
            )
            deployment_state["backup_created"] = True
            deployment_state["backup_path"] = backup_path
            
            # Backup environment file separately for rollback
            if files.file_exists(env_file):
                #timestamp = dt_ops.current_datetime().strftime("%Y%m%d_%H%M%S")
                #env_backup_file = f"{env_file}.backup.{timestamp}"
                env_backup_file = f"{env_file}.backup"

                files.safe_copy(env_file, env_backup_file)  # Fixed: use safe_copy, not safe_copy
                deployment_state["env_backup_path"] = env_backup_file
                
                # Store original content for rollback
                with open(env_file, 'r') as f:
                    deployment_state["original_env_content"] = f.read()
            
            logger.info(f"✅ Backup created: {backup_path}")
            result["steps"]["backup"] = {
                "path": backup_path, 
                "images_included": backup_images,
                "env_backup": env_backup_file
            }
        elif dry_run:
            logger.info("💾 Step 2: Backup creation skipped (dry run)")
        
        # Step 3: Update environment from git and system
        new_version = None
        should_update_env = update_version or (env_update_keys is not None)
        
        if should_update_env and not dry_run:
            logger.info("🔧 Step 3: Updating environment...")
            
            # Update version if enabled
            if update_version:
                new_version = _update_env_version(
                    env_file=env_file,
                    source=version_source,
                    logger=logger
                )
                
                if new_version:
                    result["version_updated"] = True
                    result["new_version"] = new_version
                    deployment_state["new_version"] = new_version
                    deployment_state["env_updated"] = True
                    deployment_state["updated_env_keys"].append('VERSION')
                    logger.info(f"✅ Version updated to: {new_version}")
                else:
                    logger.info("ℹ️ Version update skipped")
            
            # Update additional environment keys from system
            if env_update_keys is not None:
                updated_keys = _update_env_from_system(env_file, env_update_keys, logger)
                
                if updated_keys:
                    deployment_state["env_updated"] = True
                    deployment_state["updated_env_keys"].extend(updated_keys)
                    logger.info(f"✅ Updated {len(updated_keys)} env vars: {updated_keys}")
            
            # Reload environment if updated
            if deployment_state["env_updated"]:
                envs.import_env_to_system(get_env_compose(env_file))
                
            result["steps"]["environment_update"] = {
                "status": "success" if deployment_state["env_updated"] else "skipped",
                "updated_keys": deployment_state["updated_env_keys"],
                "new_version": new_version,
                "previous_version": deployment_state["previous_version"]
            }
        elif dry_run and should_update_env:
            logger.info("🔧 Step 3: Environment update skipped (dry run)")
        else:
            logger.info("🔧 Step 3: Environment update disabled")
        
        # Step 4: Pull new images
        if pull_images and not dry_run:
            logger.info("⬇️ Step 4: Pulling new images...")
            pull_results = compose_pull(compose_file, project_name=project_name, env_file=env_file)
            deployment_state['images_pulled'] = True
            result["steps"]["pull"] = pull_results
            
            successful_pulls = [svc for svc, success in pull_results.items() if success]
            failed_pulls = [svc for svc, success in pull_results.items() if not success]
            
            if successful_pulls:
                logger.info(f"✅ Pulled {len(successful_pulls)} images successfully")
            if failed_pulls:
                logger.warning(f"⚠️ Failed to pull images for: {failed_pulls}")
                logger.warning("Continuing with existing images")
        elif dry_run and pull_images:
            logger.info("⬇️ Step 4: Image pull skipped (dry run)")
        
        # Step 5: Deploy using selected strategy
        logger.info("🚀 Step 5: Deploying services...")
        deploy_result = _execute_deployment_strategy(
            compose_file=compose_file,
            env_file=env_file,
            strategy=deployment_strategy,
            project_name=project_name,
            dry_run=dry_run,
            logger=logger
        )
        
        if not dry_run:
            deployment_state["services_started"] = True
            result["steps"]["deploy"] = deploy_result
            
            if deploy_result.get('success'):
                logger.info("✅ Services deployed successfully")
            else:
                logger.error(f"❌ Deployment failed: {deploy_result.get('error', 'Unknown error')}")
        elif dry_run:
            logger.info("🚀 Step 5: Deployment skipped (dry run)")
        
        # Step 6: Health checks with automatic rollback
        if health_check and not dry_run:
            logger.info("🏥 Step 6: Performing health checks...")
            health_success = wait_for_healthy(
                compose_file=compose_file,
                env_file=env_file,
                services=None,
                timeout=health_timeout,
                logger=logger
            )
            
            if health_success:
                result["steps"]["health_check"] = {"status": "healthy", "duration": health_timeout}
                logger.info("✅ All services healthy!")
            else:
                result["steps"]["health_check"] = {"status": "failed", "duration": health_timeout}
                logger.error("❌ Health checks failed!")
                
                if auto_rollback and rollback_on_health_failure:
                    logger.error("🔄 Initiating rollback...")
                    rollback_success = _perform_rollback(
                        deployment_state=deployment_state,
                        compose_file=compose_file,
                        env_file=env_file,
                        project_name=project_name,
                        max_attempts=max_rollback_attempts,
                        logger=logger
                    )
                    
                    result["rollback_performed"] = rollback_success
                    
                    if rollback_success:
                        logger.info("✅ Rollback completed successfully")
                        # Verify rollback health
                        rollback_health = wait_for_healthy(
                            compose_file=compose_file,
                            env_file=env_file,
                            timeout=health_timeout // 2,
                        )
                        result["steps"]["rollback_verification"] = {
                            "status": "healthy" if rollback_health else "unhealthy"
                        }
                    else:
                        logger.error("💥 Rollback failed!")
                        raise DockerOpsError("Deployment failed and rollback also failed")
                
                raise HealthCheckFailed("Services failed health checks after deployment")
        elif dry_run and health_check:
            logger.info("🏥 Step 6: Health checks skipped (dry run)")
        
        # Step 7: Cleanup and retention
        if not dry_run:
            logger.info("🧹 Step 7: Cleaning up old resources...")
            cleanup_results = _perform_post_deployment_cleanup(
                compose_file=compose_file,
                keep_image_versions=keep_image_versions,
                cleanup_old_backups=cleanup_old_backups,
                backup_dir=backup_dir,
                keep_backup_versions=keep_backup_versions,
                logger=logger,
                env_file=env_file,

            )
            result["steps"]["cleanup"] = cleanup_results
            
            # Save version information
            if new_version:
                _save_version_history(env_file, new_version, backup_dir, logger)
            
            logger.info("✅ Cleanup completed")
        elif dry_run:
            logger.info("🧹 Step 7: Cleanup skipped (dry run)")
        
        # Success!
        result["success"] = True
        result["duration"] = (dt_ops.current_datetime() - start_time).total_seconds()
        
        logger.info(f"🎉 Deployment {deployment_id} completed successfully!")
        logger.info(f"   Duration: {result['duration']:.1f}s")
        logger.info(f"   Env updates: {len(deployment_state['updated_env_keys'])}")
        if new_version:
            logger.info(f"   Version: {deployment_state['previous_version']} → {new_version}")
        
        return result
        
    except Exception as e:
        # Failure handling
        result["duration"] = (dt_ops.current_datetime() - start_time).total_seconds()
        result["error"] = str(e)
        
        logger.error(f"💥 Deployment {deployment_id} failed: {e}")
        
        # Automatic rollback on any failure
        if auto_rollback and not dry_run:
            logger.info("🔄 Automatic rollback triggered due to failure...")
            try:
                rollback_success = _perform_rollback(
                    deployment_state=deployment_state,
                    compose_file=compose_file,
                    env_file=env_file,
                    project_name=project_name,
                    max_attempts=max_rollback_attempts,
                    logger=logger
                )
                result["rollback_performed"] = rollback_success
                
                if rollback_success:
                    logger.info("✅ Automatic rollback completed")
                else:
                    logger.error("💥 Automatic rollback failed!")
            except Exception as rollback_error:
                logger.error(f"💥 Rollback procedure failed: {rollback_error}")
                result["rollback_error"] = str(rollback_error)
        
        return result


def _execute_deployment_strategy(
    compose_file: str,
    env_file: str,
    strategy: str,
    project_name: Optional[str],
    dry_run: bool,
    logger: logger
) -> Dict[str, Any]:
    """Execute deployment using selected strategy"""
    
    if dry_run:
        logger.info(f"Dry-run: Would deploy using {strategy} strategy")
        return {"strategy": strategy, "dry_run": True}
    
    try:
        if strategy == 'rolling':
            logger.info("Using rolling deployment strategy...")
            down_success = compose_down(compose_file, project_name=project_name, env_file=env_file)
            up_success = compose_up(compose_file, detach=True, project_name=project_name, env_file=env_file)
            return {"strategy": "rolling", "down_success": down_success, "up_success": up_success, "success": down_success and up_success}
        
        elif strategy == 'recreate':
            logger.info("Using recreate deployment strategy...")
            down_success = compose_down(compose_file, remove_volumes=True, project_name=project_name, env_file=env_file)
            up_success = compose_up(compose_file, detach=True, project_name=project_name, env_file=env_file)
            return {"strategy": "recreate", "down_success": down_success, "up_success": up_success, "success": down_success and up_success}
        
        elif strategy == 'blue-green':
            logger.warning("Blue-green deployment requires additional setup, using rolling instead")
            return _execute_deployment_strategy(compose_file, env_file, 'rolling', project_name, dry_run, logger)
        
        else:
            logger.warning(f"Unknown strategy {strategy}, using rolling")
            return _execute_deployment_strategy(compose_file, env_file, 'rolling', project_name, dry_run, logger)
    except Exception as e:
        logger.error(f"Deployment strategy failed: {e}")
        return {"strategy": strategy, "success": False, "error": str(e)}


def _perform_rollback(
    deployment_state: Dict[str, Any],
    compose_file: str,
    env_file: str,
    project_name: Optional[str],
    max_attempts: int,
    logger: logger
) -> bool:
    """Perform comprehensive rollback"""
    
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"Rollback attempt {attempt}/{max_attempts}...")
            
            rollback_actions = []
            
            # 1. Rollback environment if it was updated
            if deployment_state.get("env_updated"):
                if deployment_state.get("env_backup_path") and files.file_exists(deployment_state["env_backup_path"]):
                    files.safe_copy(deployment_state["env_backup_path"], env_file)
                    rollback_actions.append("environment")
                    logger.info(f"Restored environment from: {deployment_state['env_backup_path']}")
                    
                    # Reload environment
                    envs.import_env_to_system(get_env_compose(env_file))
                elif deployment_state.get("original_env_content"):
                    with open(env_file, 'w') as f:
                        f.write(deployment_state["original_env_content"])
                    rollback_actions.append("environment")
                    logger.info("Restored environment from memory backup")
            
            # 2. Rollback services using backup
            if deployment_state.get("backup_created") and deployment_state.get("backup_path"):
                try:
                    # Stop current services
                    compose_down(compose_file, project_name=project_name, env_file=env_file)
                    
                    # Restore from backup
                    restore_compose(
                        backup_path=deployment_state["backup_path"],
                        restore_dir=Path(compose_file).parent,
                        load_images=True,
                        project_name=project_name,
                        env_file=env_file
                    )
                    rollback_actions.append("services")
                    logger.info(f"Restored services from backup: {deployment_state['backup_path']}")
                except Exception as restore_error:
                    logger.error(f"Service restoration failed: {restore_error}")
                    # Continue with other rollback actions
            
            # 3. Alternative: Simple compose restart
            if not rollback_actions and deployment_state.get("services_started"):
                compose_down(compose_file, project_name=project_name, env_file=env_file)
                compose_up(compose_file, project_name=project_name, env_file=env_file)
                rollback_actions.append("services_restart")
                logger.info("Restarted services as fallback")
            
            if rollback_actions:
                logger.info(f"Rollback completed: {rollback_actions}")
                return True
            else:
                logger.warning("No rollback actions were performed")
                
        except Exception as e:
            logger.error(f"Rollback attempt {attempt} failed: {e}")
            if attempt < max_attempts:
                logger.info("Waiting before retry...")
                time.sleep(5)  # Wait before retry
    
    logger.error(f"All {max_attempts} rollback attempts failed")
    return False


def _update_env_from_system(
    env_file: str,
    keys: List[str],
    logger: logger
) -> List[str]:
    """
    Update environment file with values from system environment.
    
    Args:
        env_file: Path to environment file
        keys: List of keys to update from system environment
             If empty list: no updates
             If None: update all version-related keys
    
    Returns:
        List of updated keys
    """
    if not files.file_exists(env_file):
        logger.warning(f"Env file not found: {env_file}")
        return []
    
    # If keys is None, update common version keys
    if keys is None:
        keys = ['CI_COMMIT_TAG', 'GIT_TAG', 'VERSION', 'APP_VERSION', 'IMAGE_TAG']
    elif len(keys) == 0:  # Empty list means no updates
        return []
    
    try:
        # Read current environment
        current_env = envs.load_env_file(env_file)
        updated_keys = []
        
        # Update specified keys from system environment
        for key in keys:
            if key in os.environ and os.environ[key]:
                old_value = current_env.get(key, '')
                new_value = os.environ[key]
                
                if old_value != new_value:
                    current_env[key] = new_value
                    updated_keys.append(key)
                    logger.debug(f"Updated {key}: {old_value} → {new_value}")
        
        # Write back if updates were made
        if updated_keys:
            envs.write_env_file(current_env, env_file)
            return updated_keys
        else:
            logger.info("ℹ️ No environment keys needed updating")
            return []
            
    except Exception as e:
        logger.error(f"Failed to update environment from system: {e}")
        return []


def _validate_compose_preconditions(
    compose_file: str,
    env_file: str,
    logger: logger
) -> List[str]:
    """Validate preconditions for compose deployment."""
    errors = []
    
    if not files.file_exists(compose_file):
        errors.append(f"Compose file not found: {compose_file}")
    
    # env_file is optional, just warn if not found
    if env_file and not files.file_exists(env_file):
        logger.warning(f"Environment file not found: {env_file}")
    
    return errors


def _save_version_history(
    env_file: str,
    current_version: str,
    backup_dir: str,
    logger: logger
) -> None:
    """Save version history for tracking deployments."""
    try:
        # Create version history directory
        version_dir = os.path.join(backup_dir, 'versions')
        os.makedirs(version_dir, exist_ok=True)
        
        # Create version record
        timestamp = int(time.time())
        version_file = os.path.join(version_dir, f"deploy_{current_version}_{timestamp}.json")
        
        version_data = {
            "version": current_version,
            "timestamp": dt_ops.current_datetime().isoformat(),
            "unix_timestamp": timestamp,
            "env_file": os.path.abspath(env_file),
            "type": "deployment"
        }
        
        with open(version_file, 'w') as f:
            json.dump(version_data, f, indent=2)
        
        logger.debug(f"Version history saved: {version_file}")
        
    except Exception as e:
        logger.warning(f"Could not save version history: {e}")


def _check_services_running(
    compose_file: str,
    project_name: Optional[str],
    env_file: str,
    logger: logger
) -> bool:
    """Check if all services in the compose file are running."""
    try:
        result = compose_ps(compose_file, project_name=project_name, env_file=env_file)
        if isinstance(result, list):
            # Check if all services are in "running" state
            for service_info in result:
                if not service_info.get('running', False):
                    return False
            return True
        return False
    except Exception as e:
        logger.warning(f"Could not check service status: {e}")
        return False

def _perform_post_deployment_cleanup(
    compose_file: str,
    keep_image_versions: int,
    cleanup_old_backups: bool,
    backup_dir: str,
    keep_backup_versions: int,
    logger: logger,
    env_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Cleanup old resources after successful deployment"""
    cleanup_results = {}
    
    try:
        # Cleanup old images
        removed_images = cleanup_old_images(keep_count=keep_image_versions)
        cleanup_results["images_removed"] = removed_images
        logger.info(f"Cleaned up {len(removed_images)} old images")
        
        # Cleanup old backups
        if cleanup_old_backups:
            removed_backups = _cleanup_old_backups(backup_dir, keep=keep_backup_versions)
            cleanup_results["backups_removed"] = removed_backups
            logger.info(f"Cleaned up {len(removed_backups)} old backups")
    
    except Exception as e:
        logger.warning(f"Cleanup operations partially failed: {e}")
        cleanup_results["cleanup_errors"] = str(e)
    
    return cleanup_results

def _cleanup_old_backups(backup_dir: str, keep: int = 5) -> List[str]:
    """Remove old backup files, keeping only the most recent ones"""
    try:
        import glob
        backup_files = sorted(
            glob.glob(f"{backup_dir}/*.tar*"), 
            key=os.path.getmtime, 
            reverse=True
        )
        
        removed = []
        for old_backup in backup_files[keep:]:
            try:
                os.remove(old_backup)
                removed.append(Path(old_backup).name)
            except Exception as e:
                logger.warning(f"Failed to remove backup {old_backup}: {e}")
        
        return removed
    except Exception as e:
        logger.warning(f"Backup cleanup failed: {e}")
        return []

# Additional helper functions
def restore_compose(
    backup_path: str,
    restore_dir: str,
    load_images: bool = True,
    project_name: Optional[str] = None,
    env_file: Optional[str] = None,
) -> bool:
    """Restore compose project from backup"""
    try:
        restore_dir = Path(restore_dir)
        restore_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract backup
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            with tarfile.open(backup_path, 'r') as tar:
                tar.extractall(temp_path)
            
            # Find compose file
            compose_files = list(temp_path.rglob("docker-compose*.yml"))
            if not compose_files:
                compose_files = list(temp_path.rglob("*.yml"))
            
            if compose_files:
                compose_file = compose_files[0]
                # Copy to restore directory
                target_compose = restore_dir / compose_file.name
                files.copy(str(compose_file), str(target_compose))
                
                # Load images if requested
                if load_images:
                    images_dir = temp_path / "images"
                    if images_dir.exists():
                        for image_file in images_dir.glob("*.tar"):
                            load_image_from_file(str(image_file))
                
                # Start services
                return compose_up(str(target_compose), project_name=project_name,env_file=env_file)
        
        return False
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False

# Enhanced backup function
def backup_compose(
    compose_file: str,
    backup_dir: str,
    include_images: bool = False,
    project_name: Optional[str] = None,
    env_file: Optional[str] = None
) -> str:
    """Create comprehensive backup of compose project"""
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = dt_ops.current_datetime().strftime("%Y%m%d_%H%M%S")
    project = project_name or Path(compose_file).stem
    backup_name = f"{project}_backup_{timestamp}"
    backup_path = backup_dir / f"{backup_name}.tar.gz"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Backup compose file and related files
        compose_dir = Path(compose_file).parent
        for file in compose_dir.glob("docker-compose*.yml"):
            files.copy(str(file), str(temp_path / file.name))
        
        # Backup environment files
        env_files = find_env_files(compose_file, env_file)
        env_dir = temp_path / "env"
        env_dir.mkdir(exist_ok=True)
        for env_file in env_files:
            files.copy(env_file, str(env_dir / Path(env_file).name))
        
        # Backup images
        if include_images:
            images_dir = temp_path / "images"
            images_dir.mkdir(exist_ok=True)
            services = get_services_from_compose(compose_file , env_file)
            
            for service in services:
                image_name = get_service_image(compose_file, service)
                if image_name:
                    image_path = images_dir / f"{service}.tar"
                    save_image_to_file(image_name, str(image_path))
        
        # Create archive
        with tarfile.open(backup_path, 'w:gz') as tar:
            tar.add(temp_path, arcname=backup_name)
    
    logger.info(f"Backup created: {backup_path}")
    return str(backup_path)

# Bulk operations
def bulk_compose_operation(compose_files: List[str], operation: Callable, 
                          max_workers: int = 4, **kwargs) -> Dict[str, Any]:
    """Perform operation on multiple compose files in parallel"""
    results = {}
    
    def process_compose(compose_file):
        try:
            return compose_file, operation(compose_file, **kwargs)
        except Exception as e:
            return compose_file, {"error": str(e)}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(process_compose, file): file 
            for file in compose_files
        }
        
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                results[file] = future.result()[1]
            except Exception as e:
                results[file] = {"error": str(e)}
    
    return results

# Utility functions
def get_compose_status(compose_file: str, env_file: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive status of compose project"""
    containers = compose_ps(compose_file)
    services = get_services_from_compose(compose_file , env_file)
    
    status = {
        "compose_file": compose_file,
        "services_defined": services,
        "containers_running": [],
        "health_status": {}
    }
    
    for container in containers:
        status["containers_running"].append({
            "service": container.service,
            "name": container.name,
            "image": container.image,
            "status": container.status
        })
        
        if container.service:
            status["health_status"][container.service] = check_service_health(
                compose_file, container.service
            )
    
    return status

def cleanup_old_images(keep_count: int = 3, dry_run: bool = False) -> List[str]:
    """Clean up old Docker images"""
    removed = []
    
    try:
        # Get all images
        result = run_docker_command(["docker", "images", "--format", "{{.ID}}|{{.Repository}}|{{.Tag}}|{{.CreatedAt}}"])
        
        images = []
        for line in result.stdout.strip().splitlines():
            if line.strip():
                parts = line.split('|', 3)
                if len(parts) == 4:
                    images.append({
                        'id': parts[0],
                        'repository': parts[1],
                        'tag': parts[2],
                        'created': parts[3]
                    })
        
        # Group by repository and keep only latest
        repos = {}
        for img in images:
            repo = img['repository']
            if repo not in repos:
                repos[repo] = []
            repos[repo].append(img)
        
        for repo, repo_images in repos.items():
            # Sort by creation date (newest first)
            repo_images.sort(key=lambda x: x['created'], reverse=True)
            
            # Remove old images
            for old_img in repo_images[keep_count:]:
                if dry_run:
                    logger.info(f"Would remove: {old_img['repository']}:{old_img['tag']}")
                else:
                    remove_result = run_docker_command(["docker", "rmi", old_img['id']])
                    if remove_result.rc == 0:
                        removed.append(f"{old_img['repository']}:{old_img['tag']}")
    
    except Exception as e:
        logger.error(f"Image cleanup failed: {e}")
    
    return removed

# ==================== AUTHENTICATION ====================
def docker_login(
    registry: str, 
    username: str, 
    password: str, 
    email: Optional[str] = None,
    logger: Optional[logger] = None
) -> bool:
    """
    Login to Docker registry.
    
    Args:
        registry: Registry URL (e.g., docker.io, ghcr.io)
        username: Registry username
        password: Registry password/token
        email: Optional email
        logger: Custom logger
        
    Returns:
        Success status
    """
    logger = logger or DEFAULT_LOGGER
    cmd = ['docker', 'login', registry, '-u', username, '-p', password]
    if email:
        cmd.extend(['--email', email])  # Rare, mostly for old Docker Hub
    #if reauth:
        #cmd.append('--reauth')  # Optional: Force reauth if needed
    
    try:
        result = systems.run(cmd, capture=True)
        logger.info(f"✅ Docker CLI login successful for {registry}")
        logger.debug(f"Output: {result.stdout}")
        return True
    except Exception as e:
        logger.error(f"❌ Docker CLI login error: {e}")
    client = get_docker_client()
    if client:
        try:
            client.login(
                username=username,
                password=password,
                registry=registry,
                email=email
            )
            logger.info(f"Successfully logged into {registry}")
            return True
        except DockerException as e:
            logger.error(f"SDK login failed: {e}")
    
    # CLI fallback
    cmd = ["docker", "login", registry, "--username", username, "--password-stdin"]
    result = run_docker_command(cmd, capture=True, input_text=password)
    
    if result.rc == 0:
        logger.info(f"CLI login successful to {registry}")
        return True
    else:
        logger.error(f"Login failed: {result.stderr}")
        return False

# ==================== CONTAINER SHELL ACCESS ====================
def run_container_shell(
    container_id: str,
    shell: str = "bash",
    command: Optional[str] = None,
    user: Optional[str] = None,
    workdir: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> ExecResult:
    """
    Run interactive shell in container.
    
    Args:
        container_id: Container ID or name
        shell: Shell to use (bash, sh, powershell, cmd)
        command: Optional command to execute in shell
        user: Optional user to run as
        workdir: Optional working directory
        env: Optional environment variables
        
    Returns:
        ExecResult with command output
    """
    # Determine shell command based on shell type
    shell_commands = {
        "bash": ["/bin/bash", "-c"],
        "sh": ["/bin/sh", "-c"], 
        "powershell": ["powershell", "-Command"],
        "cmd": ["cmd", "/c"]
    }
    
    if shell not in shell_commands:
        raise DockerOpsError(f"Unsupported shell: {shell}. Available: {list(shell_commands.keys())}")
    
    shell_cmd = shell_commands[shell]
    
    # Build command
    if command:
        full_cmd = shell_cmd + [command]
    else:
        # Interactive mode - just start the shell
        full_cmd = shell_cmd[0:1]  # Just the shell executable
    
    # Build docker exec command
    cmd = ["docker", "exec", "-i"]
    
    if user:
        cmd.extend(["-u", user])
    
    if workdir:
        cmd.extend(["-w", workdir])
    
    if env:
        for k, v in env.items():
            cmd.extend(["-e", f"{k}={v}"])
    
    # Add TTY for interactive sessions if no command provided
    if not command:
        cmd.append("-t")
    
    cmd.append(container_id)
    cmd.extend(full_cmd)
    
    return run_docker_command(cmd, capture=bool(command))

# ==================== CONTAINER MANAGEMENT ====================
def container_commit(
    container_id: str,
    repository: str,
    tag: str = "latest",
    message: Optional[str] = None,
    author: Optional[str] = None,
    changes: Optional[List[str]] = None
) -> bool:
    """
    Commit container to new image.
    
    Args:
        container_id: Container to commit
        repository: Repository name for new image
        tag: Image tag
        message: Commit message
        author: Author information
        changes: Dockerfile instructions to apply
        
    Returns:
        Success status
    """
    client = get_docker_client()
    if client:
        try:
            container = client.containers.get(container_id)
            container.commit(
                repository=repository,
                tag=tag,
                message=message,
                author=author,
                changes=changes
            )
            return True
        except DockerException:
            pass
    
    # CLI fallback
    cmd = ["docker", "commit"]
    if message:
        cmd.extend(["-m", message])
    if author:
        cmd.extend(["--author", author])
    if changes:
        for change in changes:
            cmd.extend(["--change", change])
    cmd.extend([container_id, f"{repository}:{tag}"])
    
    result = run_docker_command(cmd)
    return result.rc == 0

def container_kill(
    container_id: str,
    signal: str = "SIGKILL"
) -> bool:
    """
    Kill container with specified signal.
    
    Args:
        container_id: Container to kill
        signal: Signal to send (SIGKILL, SIGTERM, etc.)
        
    Returns:
        Success status
    """
    client = get_docker_client()
    if client:
        try:
            container = client.containers.get(container_id)
            container.kill(signal=signal)
            return True
        except DockerException:
            pass
    
    # CLI fallback
    result = run_docker_command(["docker", "kill", "-s", signal, container_id])
    return result.rc == 0

def container_remove(
    container_id: str,
    force: bool = False,
    remove_volumes: bool = False
) -> bool:
    """
    Remove container.
    
    Args:
        container_id: Container to remove
        force: Force removal if running
        remove_volumes: Remove associated volumes
        
    Returns:
        Success status
    """
    client = get_docker_client()
    if client:
        try:
            container = client.containers.get(container_id)
            container.remove(force=force, v=remove_volumes)
            return True
        except DockerException:
            pass
    
    # CLI fallback
    cmd = ["docker", "rm"]
    if force:
        cmd.append("-f")
    if remove_volumes:
        cmd.append("-v")
    cmd.append(container_id)
    
    result = run_docker_command(cmd)
    return result.rc == 0

def container_restart(
    container_id: str,
    timeout: int = 10
) -> bool:
    """
    Restart container.
    
    Args:
        container_id: Container to restart
        timeout: Timeout before killing container
        
    Returns:
        Success status
    """
    client = get_docker_client()
    if client:
        try:
            container = client.containers.get(container_id)
            container.restart(timeout=timeout)
            return True
        except DockerException:
            pass
    
    # CLI fallback
    result = run_docker_command(["docker", "restart", "-t", str(timeout), container_id])
    return result.rc == 0

# ==================== IMAGE MANAGEMENT ====================
def image_tag(
    source_image: str,
    target_image: str,
    force: bool = False
) -> bool:
    """
    Tag an image with new name/tag.
    
    Args:
        source_image: Source image name:tag
        target_image: Target image name:tag
        force: Force tag even if target exists
        
    Returns:
        Success status
    """
    client = get_docker_client()
    if client:
        try:
            image = client.images.get(source_image)
            image.tag(target_image, force=force)
            return True
        except DockerException:
            pass
    
    # CLI fallback
    cmd = ["docker", "tag", source_image, target_image]
    if force:
        # Docker CLI doesn't have force flag for tag, we'll remove existing first
        run_docker_command(["docker", "rmi", target_image])
    
    result = run_docker_command(cmd)
    return result.rc == 0

# ==================== PRUNE OPERATIONS ====================
def prune_system(
    all_resources: bool = True,
    volumes: bool = False,
    filters: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Prune unused Docker resources.
    
    Args:
        all_resources: Prune containers, images, networks
        volumes: Also prune volumes (be careful!)
        filters: Prune filters
        
    Returns:
        Prune results summary
    """
    result = {}
    
    if all_resources:
        # Prune containers
        cmd = ["docker", "container", "prune", "-f"]
        if filters:
            for k, v in filters.items():
                cmd.extend(["--filter", f"{k}={v}"])
        container_result = run_docker_command(cmd)
        result["containers"] = container_result.stdout
        
        # Prune images
        cmd = ["docker", "image", "prune", "-f"]
        if filters:
            for k, v in filters.items():
                cmd.extend(["--filter", f"{k}={v}"])
        image_result = run_docker_command(cmd)
        result["images"] = image_result.stdout
        
        # Prune networks
        cmd = ["docker", "network", "prune", "-f"]
        if filters:
            for k, v in filters.items():
                cmd.extend(["--filter", f"{k}={v}"])
        network_result = run_docker_command(cmd)
        result["networks"] = network_result.stdout
    
    if volumes:
        cmd = ["docker", "volume", "prune", "-f"]
        if filters:
            for k, v in filters.items():
                cmd.extend(["--filter", f"{k}={v}"])
        volume_result = run_docker_command(cmd)
        result["volumes"] = volume_result.stdout
    
    return result

# ==================== NETWORK MANAGEMENT ====================
def create_network(
    name: str,
    driver: str = "bridge",
    attachable: bool = True,
    labels: Optional[Dict[str, str]] = None,
    options: Optional[Dict[str, str]] = None
) -> bool:
    """
    Create Docker network.
    
    Args:
        name: Network name
        driver: Network driver (bridge, overlay, etc.)
        attachable: Whether containers can connect later
        labels: Network labels
        options: Driver-specific options
        
    Returns:
        Success status
    """
    client = get_docker_client()
    if client:
        try:
            client.networks.create(
                name=name,
                driver=driver,
                attachable=attachable,
                labels=labels or {},
                options=options or {}
            )
            return True
        except DockerException:
            pass
    
    # CLI fallback
    cmd = ["docker", "network", "create"]
    if driver != "bridge":
        cmd.extend(["--driver", driver])
    if attachable:
        cmd.append("--attachable")
    if labels:
        for k, v in labels.items():
            cmd.extend(["--label", f"{k}={v}"])
    if options:
        for k, v in options.items():
            cmd.extend(["--opt", f"{k}={v}"])
    cmd.append(name)
    
    result = run_docker_command(cmd)
    return result.rc == 0

def ensure_network(
    name: str,
    driver: str = "bridge",
    attachable: bool = True,
    labels: Optional[Dict[str, str]] = None
) -> bool:
    """
    Ensure network exists, create if missing.
    
    Args:
        name: Network name
        driver: Network driver
        attachable: Whether network is attachable
        labels: Network labels
        
    Returns:
        True if network exists or was created
    """
    client = get_docker_client()
    
    # Check if network exists
    if client:
        try:
            client.networks.get(name)
            return True  # Network exists
        except DockerException:
            pass  # Network doesn't exist
    
    # CLI check
    result = run_docker_command(["docker", "network", "ls", "--format", "{{.Name}}"])
    if name in result.stdout.splitlines():
        return True
    
    # Create network
    return create_network(name, driver, attachable, labels)

# ==================== VOLUME MANAGEMENT ====================
def create_volume(
    name: str,
    driver: str = "local",
    labels: Optional[Dict[str, str]] = None,
    options: Optional[Dict[str, str]] = None
) -> bool:
    """
    Create Docker volume.
    
    Args:
        name: Volume name
        driver: Volume driver
        labels: Volume labels
        options: Driver-specific options
        
    Returns:
        Success status
    """
    client = get_docker_client()
    if client:
        try:
            client.volumes.create(
                name=name,
                driver=driver,
                labels=labels or {},
                driver_opts=options or {}
            )
            return True
        except DockerException:
            pass
    
    # CLI fallback
    cmd = ["docker", "volume", "create"]
    if driver != "local":
        cmd.extend(["--driver", driver])
    if labels:
        for k, v in labels.items():
            cmd.extend(["--label", f"{k}={v}"])
    if options:
        for k, v in options.items():
            cmd.extend(["--opt", f"{k}={v}"])
    cmd.append(name)
    
    result = run_docker_command(cmd)
    return result.rc == 0

def ensure_volume(
    name: str,
    driver: str = "local",
    labels: Optional[Dict[str, str]] = None
) -> bool:
    """
    Ensure volume exists, create if missing.
    
    Args:
        name: Volume name
        driver: Volume driver
        labels: Volume labels
        
    Returns:
        True if volume exists or was created
    """
    client = get_docker_client()
    
    # Check if volume exists
    if client:
        try:
            client.volumes.get(name)
            return True  # Volume exists
        except DockerException:
            pass  # Volume doesn't exist
    
    # CLI check
    result = run_docker_command(["docker", "volume", "ls", "--format", "{{.Name}}"])
    if name in result.stdout.splitlines():
        return True
    
    # Create volume
    return create_volume(name, driver, labels)

# ==================== CONFLICT DETECTION ====================
def check_conflicts(
    compose_file: str,
    check_ports: bool = True,
    check_networks: bool = True,
    check_volumes: bool = False,
    project_name: Optional[str] = None,
    env_file: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Check for potential conflicts with existing Docker resources.
    
    Args:
        compose_file: Compose file to check
        check_ports: Check for port conflicts
        check_networks: Check for network conflicts  
        check_volumes: Check for volume conflicts
        project_name: Project name for scoping
        
    Returns:
        Dictionary of conflicts by type
    """
    conflicts = {
        "port_conflicts": [],
        "network_conflicts": [], 
        "volume_conflicts": [],
        "container_conflicts": []
    }
    
    # Read compose configuration
    compose_config = read_compose_file(compose_file, env_file)
    services = compose_config.get('services', {})
    
    # Get all running containers
    all_containers = list_containers(all=False)
    
    # Check port conflicts
    if check_ports:
        used_ports = _get_used_ports(all_containers)
        for service_name, service_config in services.items():
            service_ports = service_config.get('ports', [])
            for port_mapping in service_ports:
                host_port = _extract_host_port(port_mapping)
                if host_port and host_port in used_ports:
                    conflicts["port_conflicts"].append({
                        "service": service_name,
                        "port": host_port,
                        "conflicting_container": used_ports[host_port]
                    })
    
    # Check network conflicts
    if check_networks:
        compose_networks = compose_config.get('networks', {})
        existing_networks = _get_existing_networks()
        
        for network_name, network_config in compose_networks.items():
            # Skip external networks - they are expected to exist
            if _get_network_external_status(network_config):
                continue
                
            if network_name in existing_networks:
                conflicts["network_conflicts"].append({
                    "network": network_name,
                    "existing": True,
                    "external": False  # Mark as not external
                })
    
    # Check volume conflicts (if enabled)
    if check_volumes:
        compose_volumes = compose_config.get('volumes', {})
        existing_volumes = _get_existing_volumes()  # You'll need to implement this
        
        for volume_name, volume_config in compose_volumes.items():
            # Skip external volumes - they are expected to exist
            if _get_volume_external_status(volume_config):
                continue
                
            if volume_name in existing_volumes:
                conflicts["volume_conflicts"].append({
                    "volume": volume_name,
                    "existing": True,
                    "external": False
                })
    
    # Check container name conflicts
    for service_name, service_config in services.items():
        container_name = service_config.get('container_name')
        if container_name:
            for container in all_containers:
                if container.name == container_name or container.name == f"/{container_name}":
                    conflicts["container_conflicts"].append({
                        "service": service_name,
                        "container_name": container_name,
                        "conflicting_container": container.id
                    })
    
    return conflicts

def _get_used_ports(containers: List[ContainerInfo]) -> Dict[int, str]:
    """Get used host ports from containers with conflicting container IDs."""
    used_ports = {}
    for container in containers:
        # Assuming ContainerInfo has ports as dict like {'80/tcp': [{'HostPort': '80'}]}
        for container_port, host_bindings in container.ports.items():
            if host_bindings:
                for binding in host_bindings:
                    host_port = int(binding.get('HostPort', 0))
                    if host_port:
                        used_ports[host_port] = container.id  # Use container ID
    return used_ports

def _extract_host_port(port_mapping: Union[str, Dict]) -> Optional[int]:
    """Extract host port from port mapping"""
    if isinstance(port_mapping, str):
        # Format: "host:container" or "host:container/protocol"
        parts = port_mapping.split(':')
        if len(parts) >= 2:
            return int(parts[0])
    elif isinstance(port_mapping, dict):
        return port_mapping.get('published')
    return None

def _get_existing_networks() -> List[str]:
    """Get list of existing Docker networks"""
    result = run_docker_command(["docker", "network", "ls", "--format", "{{.Name}}"])
    return result.stdout.splitlines()

def resolve_conflicts(
    compose_file: str,
    remove_conflicting_containers: bool = False,
    remove_conflicting_networks: bool = False,
    remove_conflicting_volumes: bool = False,
    force: bool = False,
    project_name: Optional[str] = None,
    env_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Detect and resolve conflicts for compose deployment.
    """
    conflicts = check_conflicts(
        compose_file,
        project_name=project_name,
        env_file=env_file,
        check_volumes=remove_conflicting_volumes
    )
   
    resolution = {
        "conflicts_found": conflicts,
        "resolved": [],
        "errors": [],
        "skipped_external": []
    }
   
    # Resolve container conflicts (by name)
    for conflict in conflicts.get("container_conflicts", []):
        container_id = conflict["conflicting_container"]
        try:
            if remove_conflicting_containers:
                if container_remove(container_id, force=force):
                    resolution["resolved"].append(f"container:{container_id}")
                else:
                    resolution["errors"].append(f"Failed to remove container {container_id}")
        except Exception as e:
            resolution["errors"].append(str(e))
   
    # Resolve port conflicts (by removing conflicting containers)
    for conflict in conflicts.get("port_conflicts", []):
        container_id = conflict["conflicting_container"]
        try:
            if remove_conflicting_containers:
                if container_remove(container_id, force=force):
                    resolution["resolved"].append(f"port_conflict_container:{container_id}")
                else:
                    resolution["errors"].append(f"Failed to remove container {container_id} for port conflict")
        except Exception as e:
            resolution["errors"].append(str(e))
   
    # Resolve network conflicts (only non-external)
    for conflict in conflicts.get("network_conflicts", []):
        network_name = conflict["network"]
        is_external = conflict.get("external", False)
       
        if is_external:
            resolution["skipped_external"].append(f"network:{network_name}")
            continue
           
        try:
            if remove_conflicting_networks:
                if network_remove(network_name):
                    resolution["resolved"].append(f"network:{network_name}")
                else:
                    resolution["errors"].append(f"Failed to remove network {network_name}")
        except Exception as e:
            resolution["errors"].append(str(e))
   
    # Resolve volume conflicts (only non-external)
    for conflict in conflicts.get("volume_conflicts", []):
        volume_name = conflict["volume"]
        is_external = conflict.get("external", False)
       
        if is_external:
            resolution["skipped_external"].append(f"volume:{volume_name}")
            continue
           
        try:
            if remove_conflicting_volumes:
                if volume_remove(volume_name):
                    resolution["resolved"].append(f"volume:{volume_name}")
                else:
                    resolution["errors"].append(f"Failed to remove volume {volume_name}")
        except Exception as e:
            resolution["errors"].append(str(e))
   
    return resolution

# ==================== COMPOSE ENHANCEMENTS ====================
def _get_network_external_status(network_config):
    """Check if a network is marked as external"""
    if isinstance(network_config, dict):
        return network_config.get('external', False)
    return False

def _get_volume_external_status(volume_config):
    """Check if a volume is marked as external"""
    if isinstance(volume_config, dict):
        return volume_config.get('external', False)
    return False

def compose_up_with_conflict_resolution(
    compose_file: str,
    resolve_conflicts: bool = True,
    remove_conflicting_containers: bool = True,
    remove_conflicting_networks: bool = False,  # Add this
    remove_conflicting_volumes: bool = False,   # Add this
    project_name: Optional[str] = None,
    **kwargs
) -> bool:
    """
    Compose up with automatic conflict resolution.
    
    Args:
        compose_file: Compose file
        resolve_conflicts: Enable conflict resolution
        remove_conflicting_containers: Remove conflicting containers
        remove_conflicting_networks: Remove conflicting networks (non-external only)
        remove_conflicting_volumes: Remove conflicting volumes (non-external only)
        project_name: Project name
        **kwargs: Additional compose_up arguments
        
    Returns:
        Success status
    """
    if resolve_conflicts:
        logger.info("Checking for conflicts...")
        resolution = resolve_conflicts(
            compose_file,
            remove_conflicting_containers=remove_conflicting_containers,
            remove_conflicting_networks=remove_conflicting_networks,
            remove_conflicting_volumes=remove_conflicting_volumes,
            force=True,
            project_name=project_name,
            env_file=env_file
        )
        
        if resolution["resolved"]:
            logger.info(f"Resolved conflicts: {resolution['resolved']}")
        if resolution["skipped_external"]:
            logger.info(f"Skipped external resources: {resolution['skipped_external']}")
        if resolution["errors"]:
            logger.warning(f"Conflict resolution errors: {resolution['errors']}")
    
    return compose_up(compose_file, project_name=project_name, **kwargs)


def _get_existing_volumes():
    """Get list of existing Docker volumes"""
    try:
        result = subprocess.run(
            ["docker", "volume", "ls", "-q"],
            capture_output=True,
            text=True,
            check=True
        )
        return set(result.stdout.strip().split('\n'))
    except subprocess.CalledProcessError:
        return set()

def network_remove(network_name):
    """Remove a Docker network"""
    try:
        subprocess.run(
            ["docker", "network", "rm", network_name],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def volume_remove(volume_name):
    """Remove a Docker volume"""
    try:
        subprocess.run(
            ["docker", "volume", "rm", volume_name],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

# Main execution for testing
if __name__ == "__main__":
    # Example usage
    compose_file = "docker-compose.yml"
    env_file= get_env_compose(compose_file)
    
    if files.file_exists(compose_file):
        status = get_compose_status(compose_file , env_file)
        logger.info(json.dumps(status, indent=2))
    else:
        logger.error("No docker-compose.yml found")

# Complete __all__ exports
__all__ = [
    # High Level Functions
    # Use these For building you Scripts !
    "deploy_compose","build_compose", "test_compose","push_compose"

    
    
    # Core
    "get_docker_client", "run_docker_command", "run_compose_command",
    # Images
    "pull_image", "push_image", "build_image", "save_image_to_file", "load_image_from_file",
    # Containers
    "list_containers", "get_container_logs", "exec_in_container", "parse_log_line",
    # Compose files
    "read_compose_file", "write_compose_file", "validate_compose_file",
    "get_services_from_compose", "get_service_image", "find_env_files",
    # Compose operations
    "compose_up", "compose_down", "compose_restart", "compose_ps",
    "compose_logs", "compose_pull", "compose_build", "parse_compose_log_line","compose_build_with_env",
    # Health
    "check_service_health", "wait_for_healthy", "check_health_from_compose_ps" , "health_check_docker_compose" , "wait_for_healthy_simple" ,
    # Backup & restore
    "backup_compose", "restore_compose",
    # Utilities
    "get_compose_status", "cleanup_old_images",
    # Data classes
    "ExecResult", "LogLine", "ContainerInfo",
    # Exceptions
    "DockerOpsError", "ComposeConflictError", "HealthCheckFailed",
     # New authentication
    "docker_login",
    # New container operations  
    "run_container_shell","container_commit", "container_kill","container_remove","container_restart",
    # New image operations
    "image_tag",
    # New prune operations
    "prune_system",
    # New network/volume operations
    "create_network","ensure_network", "create_volume","ensure_volume",
    # New conflict detection
    "check_conflicts","resolve_conflicts","compose_up_with_conflict_resolution",

    # Help
    "help"
]

def help(function_name: Optional[str] = None) -> str:
    """
    DockerOps - Functional Docker Compose Operations Library
    
    Quick help: help() for overview, help('function_name') for details, help('category') for groups
     
     
    categories = {
        "core": ["get_docker_client", "run_docker_command", "run_compose_command"],
        "images": ["pull_image", "push_image", "build_image", "save_image_to_file", "load_image_from_file"],
        "containers": ["list_containers", "get_container_logs", "exec_in_container"],
        "compose_files": ["read_compose_file", "write_compose_file", "validate_compose_file", "get_services_from_compose"],
        "compose_ops": ["compose_up", "compose_down", "compose_ps", "compose_logs", "compose_pull", "compose_build"],
        "health": [
            "check_service_health", 
            "wait_for_healthy", 
            "check_health_from_compose_ps",
            "health_check_docker_compose", 
            "wait_for_healthy_simple"
        ],
        "backup": ["backup_compose", "restore_compose"],
        "deployment": ["deploy_compose"],
        "utils": ["get_compose_status", "cleanup_old_images"],
        "authentication": ["docker_login"],
        "container_ops": [
            "run_container_shell", "container_commit", "container_kill", 
            "container_remove", "container_restart"
        ],
        "image_ops": ["image_tag"],
        "prune_ops": ["prune_system"],
        "network_volume": [
            "create_network", "ensure_network", "create_volume", "ensure_volume"
        ],
        "conflict": [
            "check_conflicts", "resolve_conflicts", "compose_up_with_conflict_resolution"
        ]
    }
    
    function_short_help = {
        # High Level Functions - NEW SECTION
        "deploy_compose": "Enhanced deployment with rollback & env management -> Dict[deployment_result]",
        "build_compose": "Build services with version management & cleanup -> Dict[build_result]",
        "test_compose": "Test services with health checks & detailed logging -> Dict[test_result]",
        "push_compose": "Push images with auth handling & version management -> Dict[push_result]",
            
        # Core
        "Compose Detection": "Automatically uses 'docker compose' (modern) or 'docker-compose' (legacy)",
        "get_docker_client": "Get Docker client with CLI fallback -> DockerClient|None",
        "run_docker_command": "Run docker command -> ExecResult(rc,stdout,stderr)",
        "run_compose_command": "Run docker-compose command -> ExecResult",
        
        # Images
        "pull_image": "Pull image with retry logic -> bool",
        "push_image": "Push image to registry -> bool", 
        "build_image": "Build image from context -> bool",
        "save_image_to_file": "Save image to tar file -> bool",
        "load_image_from_file": "Load image from tar file -> bool",
        
        # Containers
        "list_containers": "List containers with filters -> List[ContainerInfo]",
        "get_container_logs": "Get container logs -> Iterator[LogLine]",
        "exec_in_container": "Execute command in container -> ExecResult",
        "parse_log_line": "Parse log line -> LogLine",
        
        # Compose files
        "read_compose_file": "Read compose file -> Dict",
        "write_compose_file": "Write compose file -> None", 
        "validate_compose_file": "Validate compose file -> List[str] (errors)",
        "get_services_from_compose": "Get service names -> List[str]",
        "get_service_image": "Get image for service -> str|None",
        "find_env_files": "Find env files in compose -> List[str]",
        
        # Compose operations
        "compose_up": "Start compose services -> bool",
        "compose_down": "Stop compose services -> bool",
        "compose_restart": "Restart compose services -> bool",
        "compose_ps": "Get compose status -> List[ContainerInfo]",
        "compose_logs": "Get compose logs -> Iterator[LogLine]", 
        "compose_pull": "Pull compose images -> Dict[service->bool]",
        "compose_build": "Build compose images -> Dict[service->bool]",
        "parse_compose_log_line": "Parse compose log -> LogLine",
        
        # Health - UPDATED WITH NEW FUNCTIONS
        "check_service_health": "Check individual service health -> Dict[healthy,details,error]",
        "wait_for_healthy": "Wait for services to become healthy (reliable) -> bool",
        "check_health_from_compose_ps": "Direct health check via JSON parsing -> Dict[healthy,services,details]",
        "health_check_docker_compose": "Simple health check using status parsing -> bool",
        "wait_for_healthy_simple": "Simple health wait using JSON parsing -> bool",
        
        # Backup
        "backup_compose": "Backup compose project -> str (backup_path)",
        "restore_compose": "Restore from backup -> bool",
        
        # Deployment
        "deploy_compose": "Deploy with rollback & env updates -> Dict[deployment_result]",
        
        # Utilities
        "get_compose_status": "Get comprehensive status -> Dict",
        "cleanup_old_images": "Cleanup old images -> List[removed_tags]",
        
        # Authentication
        "docker_login": "Login to Docker registry -> bool",
        
        # Container operations
        "run_container_shell": "Run interactive shell in container -> ExecResult",
        "container_commit": "Commit container to image -> bool", 
        "container_kill": "Kill container with signal -> bool",
        "container_remove": "Remove container -> bool",
        "container_restart": "Restart container -> bool",
        
        # Image operations
        "image_tag": "Tag image with new name -> bool",
        
        # Prune operations
        "prune_system": "Prune unused Docker resources -> Dict",
        
        # Network/Volume operations
        "create_network": "Create Docker network -> bool",
        "ensure_network": "Ensure network exists -> bool", 
        "create_volume": "Create Docker volume -> bool",
        "ensure_volume": "Ensure volume exists -> bool",
        
        # Conflict detection
        "check_conflicts": "Check for deployment conflicts -> Dict",
        "resolve_conflicts": "Resolve deployment conflicts -> Dict",
        "compose_up_with_conflict_resolution": "Compose up with conflict resolution -> bool",
    }
    
    # Function detailed help
    function_details = {
        
        "deploy_compose":
deploy_compose(compose_file: str, env_file: str = '.env', env_new_file: Optional[str] = '.env.new', 
               env_update_keys: Optional[List[str]] = None, deployment_strategy: str = 'rolling', 
               pull_images: bool = True, health_check: bool = True, health_timeout: int = 300,
               auto_rollback: bool = True, rollback_on_health_failure: bool = True, 
               max_rollback_attempts: int = 3, backup_enabled: bool = False, 
               backup_dir: str = 'backups_deploy', backup_images: bool = True,
               keep_image_versions: int = 3, cleanup_old_backups: bool = True, 
               keep_backup_versions: int = 5, project_name: Optional[str] = None,
               dry_run: bool = False, logger: Optional[logger] = None) -> Dict[str, Any]

Enhanced deployment workflow with robust rollback and environment management.

Steps:
1. Validate environment files and compose configuration
2. Create comprehensive backup (compose + images)
3. Update environment variables with backup
4. Pull new images
5. Deploy with selected strategy
6. Health check with automatic rollback on failure
7. Cleanup old images and backups

Returns: Detailed deployment result with rollback capability

Example:
    result = deploy_compose('docker-compose.yml', deployment_strategy='rolling')
    if result['success']:
        print(f"Deployment {result['deployment_id']} completed!")
         ,

    "build_compose":  
build_compose(compose_file: str, env_file: str = '.env', update_version: bool = False,
              version_source: str = 'git', services: Optional[List[str]] = None,
              no_cache: bool = False, pull: bool = True, cleanup_intermediate: bool = True,
              project_name: Optional[str] = None, dry_run: bool = False,
              logger: Optional[logger] = None) -> Dict[str, Any]

Build Docker Compose services with optional version management and cleanup.

Steps:
1. Validate compose file and environment
2. Update version in .env file (if enabled)
3. Pull base images (if enabled)
4. Build services
5. Cleanup intermediate images (if enabled)

Returns: Build results with version information

Example:
    result = build_compose('docker-compose.yml', update_version=True)
    if result['success']:
        print(f"Built {len(result['services_built'])} services, version: {result['new_version']}")
         ,

    "test_compose":  
test_compose(compose_file: str, env_file: str = '.env', update_version: bool = False,
             version_source: str = 'git', services: Optional[List[str]] = None,
             health_timeout: int = 300, health_retries: int = 3, health_interval: int = 10,
             capture_logs: bool = True, log_tail: int = 100, pull_missing: bool = True,
             no_build: bool = True, no_pull: bool = True, project_name: Optional[str] = None,
             dry_run: bool = False, logger: Optional[logger] = None) -> Dict[str, Any]

Test Docker Compose services with comprehensive health checks and logging.

Steps:
1. Update version (if enabled)
2. Check for conflicts
3. Start services with --no-build and --no-pull
4. Perform health checks with retries
5. Capture detailed logs for failing services
6. Bring down services

Returns: Detailed test results with logs

Example:
    result = test_compose('docker-compose.yml', health_timeout=60)
    if result['success']:
        print("All services passed health checks!")
    else:
        print(f"Failed services: {result['failing_services']}")
        print(f"Logs: {result['logs_captured']}")
         ,

    "push_compose":  
push_compose(compose_file: str, env_file: str = '.env', update_version: bool = False,
             version_source: str = 'git', services: Optional[List[str]] = None,
             push_all: bool = True, registry_timeout: int = 300, interactive_login: bool = True,
             login_timeout: int = 300, save_credentials: bool = True,
             project_name: Optional[str] = None, dry_run: bool = False,
             logger: Optional[logger] = None) -> Dict[str, Any]

Push Docker Compose images to registry with authentication handling.

Steps:
1. Update version (if enabled)
2. Check registry authentication
3. Handle login interactively if needed
4. Push images to registry
5. Verify push success

Returns: Push results with authentication status

Example:
    result = push_compose('docker-compose.yml', interactive_login=True)
    if result['success']:
        print(f"Pushed {len(result['images_pushed'])} images successfully")
         ,
        
        "check_service_health":  
check_service_health(compose_file: str, service: str, check_command: Optional[List[str]] = None, timeout: int = 30) -> Dict[str, Any]

Check individual service health using reliable JSON parsing from docker compose ps.

Args:
    compose_file: Path to docker-compose.yml
    service: Service name to check
    check_command: Optional custom health check command
    timeout: Command timeout in seconds

Returns:
    Dict with keys: 'healthy' (bool), 'details' (str), 'error' (str), 'status' (str)

Example:
    health = check_service_health('docker-compose.yml', 'web')
    if health['healthy']:
        print(f"Service is healthy: {health['details']}")
         ,
        
        "wait_for_healthy":  
wait_for_healthy(compose_file: str, services: Optional[List[str]] = None, timeout: int = 300, interval: int = 5) -> bool

Wait for services to become healthy using reliable health checks.

Args:
    compose_file: Path to docker-compose.yml
    services: List of services to check (None for all services)
    timeout: Maximum wait time in seconds
    interval: Check interval in seconds

Returns:
    True if all services became healthy, False if timeout

Example:
    success = wait_for_healthy('docker-compose.yml', timeout=60)
    if success:
        print("All services are healthy!")
         ,
        
        "check_health_from_compose_ps":  
check_health_from_compose_ps(compose_file: str) -> Dict[str, Any]

Direct health check by parsing 'docker compose ps --format json' output.
Most reliable method for health detection.

Args:
    compose_file: Path to docker-compose.yml

Returns:
    Dict with keys: 'healthy' (bool), 'services' (dict), 'details' (str), 'error' (str)

Example:
    result = check_health_from_compose_ps('docker-compose.yml')
    if result['healthy']:
        print(f"All {len(result['services'])} services healthy")
         ,
        
        "health_check_docker_compose":  
health_check_docker_compose(compose_file: str) -> bool

Simple health check that uses docker compose ps to check status.

Args:
    compose_file: Path to docker-compose.yml

Returns:
    True if all services are healthy, False otherwise

Example:
    if health_check_docker_compose('docker-compose.yml'):
        print("System is healthy")
         ,
        
        "wait_for_healthy_simple":  
wait_for_healthy_simple(compose_file: str, timeout: int = 300) -> bool

Simple, reliable health wait using direct JSON parsing.

Args:
    compose_file: Path to docker-compose.yml
    timeout: Maximum wait time in seconds

Returns:
    True if all services became healthy, False if timeout

Example:
    success = wait_for_healthy_simple('docker-compose.yml', timeout=120)
    if success:
        print("Deployment health check passed")
           
        }  
    """
    print(help.__doc__)