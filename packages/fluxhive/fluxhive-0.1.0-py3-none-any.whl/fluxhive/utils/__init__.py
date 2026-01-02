"""Utility modules for FlowHive agent."""

from .config import (
    AgentConfig,
    apply_overrides,
    dump_config,
    get_config_dir,
    get_config_value,
    get_or_create_agent_key_pair,
    load_config,
    set_config_value,
)
from .crypto import (
    generate_key_pair,
    get_public_key_fingerprint,
    get_public_key_pem,
    load_private_key,
    load_public_key_from_pem,
    save_private_key,
    sign_agent_id,
    verify_signature,
)
from .shell import PersistentShell

__all__ = [
    # Config
    "AgentConfig",
    "apply_overrides",
    "dump_config",
    "get_config_dir",
    "get_config_value",
    "get_or_create_agent_key_pair",
    "load_config",
    "set_config_value",
    # Crypto
    "generate_key_pair",
    "get_public_key_fingerprint",
    "get_public_key_pem",
    "load_private_key",
    "load_public_key_from_pem",
    "save_private_key",
    "sign_agent_id",
    "verify_signature",
    # Shell
    "PersistentShell",
]
