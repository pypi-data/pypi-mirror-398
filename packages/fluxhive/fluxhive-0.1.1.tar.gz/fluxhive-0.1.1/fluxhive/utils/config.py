"""
Helpers for loading and persisting agent configuration.
"""

from __future__ import annotations

import os
import sys
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import uuid

from .crypto import (
    generate_key_pair,
    load_private_key,
    save_private_key,
    get_public_key_pem,
)
# Note: This uses digital signature (not encryption):
# - Private key signs (signs) the agent_id
# - Public key verifies (verifies) the signature


try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for 3.10
    import tomli as tomllib  # type: ignore[no-redef]


CONFIG_ENV_VAR = "FLUXHIVE_CONFIG"
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "fluxhive"
SYSTEM_CONFIG_DIR = Path("/etc/fluxhive")

# UUID namespace for generating stable agent IDs based on host identifiers
# This is a fixed namespace UUID (generated once and never changed)
_AGENT_ID_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _get_host_unique_id() -> str:
    """
    Get a unique identifier for the current host.
    
    This function attempts to get a stable, host-specific identifier using:
    1. Linux: /etc/machine-id (most reliable)
    2. Windows: Machine GUID from registry
    3. macOS: System UUID from IORegistry
    4. Fallback: MAC address + hostname
    
    Returns:
        A string identifier unique to this host
    """
    system = platform.system()
    
    # Linux: Use /etc/machine-id (most reliable)
    if system == "Linux":
        try:
            machine_id_path = Path("/etc/machine-id")
            if machine_id_path.exists():
                machine_id = machine_id_path.read_text(encoding="utf-8").strip()
                if machine_id:
                    return f"linux-machine-id-{machine_id}"
        except Exception:
            pass
    
    # Windows: Try to get Machine GUID from registry
    elif system == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography"
            )
            machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
            if machine_guid:
                return f"windows-machine-guid-{machine_guid}"
        except Exception:
            pass
    
    # macOS: Try to get System UUID
    elif system == "Darwin":
        try:
            import subprocess
            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if '"IOPlatformUUID"' in line or '"IOPlatformSerialNumber"' in line:
                        # Extract UUID or serial number
                        parts = line.split('"')
                        if len(parts) >= 4:
                            uuid_or_serial = parts[3]
                            if uuid_or_serial:
                                return f"macos-system-{uuid_or_serial}"
        except Exception:
            pass
    
    # Fallback: Use MAC address + hostname
    try:
        mac = uuid.getnode()
        hostname = platform.node()
        if mac and hostname:
            return f"host-{hostname}-mac-{mac:012x}"
        elif mac:
            return f"mac-{mac:012x}"
        elif hostname:
            return f"host-{hostname}"
    except Exception:
        pass
    
    # Last resort: return a fixed string (should rarely happen)
    return "unknown-host"


def _generate_host_based_agent_id() -> str:
    """
    Generate an agent ID based on host unique identifier and a random component.

    - Allows the same host to have multiple unique agent_ids (by random part)
    - Different hosts will always get different base agent_ids
    - Used when you want to run multiple agents on the same host

    Returns:
        A UUID string.
    """
    host_id = _get_host_unique_id()
    # Add randomness so that multiple agent_ids can exist on the same host
    random_bytes = uuid.uuid4().bytes
    # Compose the input for UUID5 as: host_id + random
    base_string = f"{host_id}:{random_bytes.hex()}"
    agent_uuid = uuid.uuid5(_AGENT_ID_NAMESPACE, base_string)
    return str(agent_uuid)


def get_or_create_agent_key_pair(key_dir: Optional[Path] = None) -> tuple[str, str]:
    """
    Get or create the agent's key pair for identity verification.
    
    This function uses digital signature (not encryption):
    - Private key: signs the agent_id to prove identity
    - Public key: verifies the signature on the server side
    
    This function:
    1. Tries to load an existing private key from disk
    2. If not found, generates a new key pair and saves it
    3. Returns the private key object and public key PEM string
    
    Args:
        key_dir: Directory where to store/load the key. If None, uses get_config_dir()
                to get the same directory as config files.
        
    Returns:
        Tuple of (private_key_object, public_key_pem_string)
    """
    private_key_path = get_config_dir(key_dir) / "agent_private_key.pem"
    
    # Try to load existing key
    private_key = load_private_key(private_key_path)
    
    if private_key is None:
        # Generate new key pair
        private_key, public_key = generate_key_pair()
        save_private_key(private_key, private_key_path)
        public_key_pem = get_public_key_pem(public_key)
        return private_key, public_key_pem
    
    # Load existing key and get public key
    public_key = private_key.public_key()
    public_key_pem = get_public_key_pem(public_key)
    
    return private_key, public_key_pem


def _get_default_label() -> str:
    """Get default label from computer hostname."""
    try:
        return platform.node()
    except Exception:
        return "unknown"


@dataclass
class AgentConfig:
    """Runtime settings required to connect to the control plane."""

    agent_id: str
    control_base_url: str
    api_key: str
    log_dir: str = ".agent_logs"
    max_parallel: int = 2
    event_buffer: int = 512
    label: Optional[str] = None


def _extract_dir(path_str: str) -> Path:
    """Extract directory from a path string (handles both file and directory paths)."""
    path = Path(path_str).expanduser()
    if path.suffix == ".toml" or path.name == "config.toml":
        return path.parent
    return path


def _get_config_candidates(explicit: Optional[str] = None) -> list[Path]:
    """Get candidate config directories in priority order."""
    candidates = []
    if explicit:
        candidates.append(_extract_dir(explicit))
    env_value = os.environ.get(CONFIG_ENV_VAR)
    if env_value:
        candidates.append(_extract_dir(env_value))
    candidates.append(DEFAULT_CONFIG_DIR)
    candidates.append(SYSTEM_CONFIG_DIR)
    return candidates


def get_config_dir(explicit: Optional[str] = None) -> Path:
    """
    Get the first existing configuration directory, or create the first candidate if none exist.
    
    Priority order:
    1. Explicit path (if provided)
    2. Environment variable path (FLUXHIVE_CONFIG)
    3. User config directory (~/.config/fluxhive)
    4. System config directory (/etc/fluxhive)
    
    Returns:
        The first existing directory path, or the first candidate directory (created if needed)
    """
    candidates = _get_config_candidates(explicit)
    
    # Try to find the first existing directory
    for candidate_dir in candidates:
        if candidate_dir.exists() and candidate_dir.is_dir():
            return candidate_dir
    
    # If none exist, use the first candidate and create it
    target_dir = candidates[0]
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def load_config(path: Optional[str] = None) -> AgentConfig:
    """
    Load configuration from disk, searching common paths unless overridden.
    """
  
    config_file = get_config_dir(path) / "config.toml"
    if config_file.is_file():
        data = tomllib.loads(config_file.read_text(encoding="utf-8"))
        try:
            return AgentConfig(
                api_key=data["api_key"],
                agent_id=data["agent_id"],
                control_base_url=data["control_base_url"],
                log_dir=data.get("log_dir", ".agent_logs"),
                max_parallel=int(data.get("max_parallel", 2)),
                event_buffer=int(data.get("event_buffer", 512)),
                label=data.get("label") or _get_default_label(),
            )
        except KeyError as exc:
            raise KeyError(f"Missing mandatory config key: {exc} in {config_file}") from exc
    raise FileNotFoundError(
        f"Agent config not found. Provide --config or set {CONFIG_ENV_VAR}. Config file: {config_file}"
    )


def dump_config(config: AgentConfig, path: Optional[str] = None) -> Path:
    """
    Persist configuration to disk.
    """
    target = get_config_dir(path) / "config.toml"
    contents = [
        f'api_key = "{config.api_key}"',
        f'agent_id = "{config.agent_id}"',
        f'control_base_url = "{config.control_base_url}"',
        f'log_dir = "{config.log_dir}"',
        f"max_parallel = {int(config.max_parallel)}",
        f"event_buffer = {int(config.event_buffer)}",
        f'label = "{config.label}"',
        "",
    ]
    target.write_text("\n".join(contents), encoding="utf-8")
    try:
        os.chmod(target, 0o600)
    except PermissionError:  # pragma: no cover - Windows
        pass
    return target


def apply_overrides(config: AgentConfig, *, args: Optional[object] = None) -> AgentConfig:
    """
    Produce a new config with argparse overrides applied (if provided).
    """

    if not args:
        return config
    api_key = getattr(args, "api_key", None) or config.api_key
    agent_id = getattr(args, "agent_id", None) or config.agent_id
    control_base_url = getattr(args, "control_base_url", None) or config.control_base_url
    log_dir = getattr(args, "log_dir", None) or config.log_dir
    max_parallel = getattr(args, "max_parallel", None) or config.max_parallel
    event_buffer = getattr(args, "event_buffer", None) or config.event_buffer
    label = getattr(args, "label", None) or config.label
    return AgentConfig(
        api_key=api_key,
        agent_id=agent_id,
        control_base_url=control_base_url,
        log_dir=log_dir,
        max_parallel=int(max_parallel),
        event_buffer=int(event_buffer),
        label=label,
    )


# Mapping from user-friendly keys to config fields
KEY_MAPPING = {
    "api_key": "api_key",
    "agent_id": "agent_id",
    "control_base_url": "control_base_url",
    "log_dir": "log_dir",
    "max_parallel": "max_parallel",
    "event_buffer": "event_buffer",
    "label": "label",
}

FIELD_MAPPING = {
    "api_key": "api_key",
    "control_base_url": "control_base_url",
    "log_dir": "log_dir",
    "max_parallel": "max_parallel",
    "event_buffer": "event_buffer",
    "label": "label",
}


def get_config_value(key: str, path: Optional[str] = None) -> Optional[str]:
    """
    Get a configuration value by key (supports both user-friendly keys and direct keys).
    """
    try:
        config = load_config(path)
    except FileNotFoundError:
        return None
    
    field_name = KEY_MAPPING.get(key, key)
    if hasattr(config, field_name):
        value = getattr(config, field_name)
        return str(value) if value is not None else None
    return None


def set_config_value(key: str, value: str, global_: bool = False, path: Optional[str] = None) -> Path:
    """
    Set a configuration value by key (supports both user-friendly keys and direct keys).
    """
    field_name = KEY_MAPPING.get(key, key)
    
    # Load existing config or create new one
    try:
        config = load_config(path)
    except FileNotFoundError:
        # Create a minimal config with defaults
        # Use host-based agent_id for stable identification
        config = AgentConfig(
            api_key="",  # Will be set by user
            agent_id=_generate_host_based_agent_id(),
            control_base_url="https://fluxhive.wangzixi.top",
            label=_get_default_label(),
        )
    
    # Update the field
    if hasattr(config, field_name):
        # Handle type conversion for numeric fields
        if field_name in ("max_parallel", "event_buffer"):
            setattr(config, field_name, int(value))
        else:
            setattr(config, field_name, value)
    else:
        raise ValueError(f"Unknown configuration key: {key}")
    
    # Determine target path
    if global_ or path is None:
        target_path = None  # Will use default
    else:
        target_path = path
    
    return dump_config(config, target_path)

