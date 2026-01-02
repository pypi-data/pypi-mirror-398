"""
Unified CLI entry point for FlowHive agent.
Supports 'config' and 'run' subcommands, similar to git.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from urllib.parse import urljoin

# Add the agent directory to sys.path to ensure imports work
# This handles direct script execution (development mode)
# When installed via pip, fluxhive will be in site-packages and this won't interfere
AGENT_ROOT = Path(__file__).resolve().parents[2]  # Go up to agent/ directory (from cli/fluxhive.py -> fluxhive/ -> agent/)
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from fluxhive.utils.config import (
    FIELD_MAPPING,
    apply_overrides,
    get_config_dir,
    get_config_value,
    load_config,
    set_config_value,
)
from fluxhive.core.control_plane import (
    ControlPlaneClient,
    ControlPlaneConfig,
    ControlPlaneEventPublisher,
    TaskLogStreamer,
    TaskStatusReporter,
)
from fluxhive.core.manager import TaskManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="FlowHive Agent - Distributed task execution agent",
        prog="fluxhive",
        epilog="""Examples:
  # List all configuration
  fluxhive config
  
  # Set API key
  fluxhive config api_key your-api-key-here
  
  # Set control server URL
  fluxhive config control_base_url https://fluxhive.wangzixi.top
  
  # Run agent with default config
  fluxhive run
  
  # Run agent with custom config file
  fluxhive run --config /path/to/config.toml
  
  # Run agent with debug logging
  fluxhive run --log-level DEBUG

For more information, visit: https://pypi.org/project/fluxhive-agent/
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # config subcommand
    config_parser = subparsers.add_parser(
        "config",
        help="Get and set configuration options",
        description="""Manage FlowHive agent configuration.

Configuration Keys:
  api_key             - API key for authentication (required)
  agent_id            - Unique identifier for this agent
  control_base_url    - Control server base URL
  log_dir             - Directory for agent logs
  max_parallel        - Maximum parallel tasks (default: 2)
  event_buffer        - Event buffer size (default: 512)
  label               - Human-readable label for this agent

Authentication:
  API Key authentication is required. Set 'api_key' to authenticate.
        """,
        epilog="""Examples:
  # List all configuration
  fluxhive config
  
  # Get a specific value
  fluxhive config api_key
  
  # Set a value
  fluxhive config api_key your-api-key-here
  
  # Set value in specific config file
  fluxhive config --config /path/to/config.toml control_base_url https://control.fluxhive.io
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    config_parser.add_argument(
        "--global",
        dest="global_",
        action="store_true",
        help="Use global config file (~/.config/fluxhive-agent/config.toml)"
    )
    config_parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to config file"
    )
    config_parser.add_argument(
        "key",
        nargs="?",
        help="Configuration key to get or set"
    )
    config_parser.add_argument(
        "value",
        nargs="?",
        help="Configuration value to set (omit to get current value)"
    )
    
    # run subcommand
    run_parser = subparsers.add_parser(
        "run",
        help="Run FlowHive agent and connect to Control Server",
        description="""Start the FlowHive agent and connect to the Control Server.

The agent will:
  1. Load configuration from file or environment
  2. Authenticate with the Control Server
  3. Listen for and execute tasks
  4. Report task status and stream logs

Configuration Priority (highest to lowest):
  1. Command-line arguments
  2. Config file specified by --config
  3. Config file from FLUXHIVE_CONFIG environment variable
  4. Default config file (~/.config/fluxhive-agent/config.toml)
  5. System config file (/etc/fluxhive-agent/config.toml)
        """,
        epilog="""Examples:
  # Run with default configuration
  fluxhive run
  
  # Run with custom config file
  fluxhive run --config /path/to/config.toml
  
  # Run with debug logging
  fluxhive run --log-level DEBUG
  
  # Override control server URL
  fluxhive run --control-base-url https://custom-server.example.com
  
  # Run with API key override
  fluxhive run --api-key your-api-key-here
  
  # Run with custom agent ID and max parallel tasks
  fluxhive run --agent-id my-agent-001 --max-parallel 4
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    run_parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to agent config file"
    )
    run_parser.add_argument(
        "--agent-id",
        metavar="ID",
        help="Override agent ID from config"
    )
    run_parser.add_argument(
        "--api-key",
        metavar="KEY",
        help="Override API key from config"
    )
    run_parser.add_argument(
        "--control-base-url",
        metavar="URL",
        help="Override Control Server base URL (e.g., https://control.fluxhive.io)"
    )
    run_parser.add_argument(
        "--log-dir",
        metavar="DIR",
        help="Override log directory from config"
    )
    run_parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    run_parser.add_argument(
        "--max-parallel",
        type=int,
        metavar="N",
        help="Override maximum parallel tasks from config"
    )
    run_parser.add_argument(
        "--event-buffer",
        type=int,
        metavar="SIZE",
        help="Override event buffer size from config"
    )
    
    return parser


def to_ws_url(base_url: str, agent_id: str) -> str:
    url = base_url.rstrip("/")
    if url.startswith("https://"):
        url = "wss://" + url[len("https://") :]
    elif url.startswith("http://"):
        url = "ws://" + url[len("http://") :]
    # Use /api/v1 directly since agents connect to backend without proxy
    return urljoin(f"{url}/", f"api/ws/agents/{agent_id}")


def cmd_config(args: argparse.Namespace) -> int:
    """Handle config subcommand."""
    config_path = args.config if args.config else None
    
    if args.key is None:
        # List all config
        try:
            # Find which config file was actually loaded
            config_dir = get_config_dir(config_path)
            config_file = config_dir / "config.toml"
            loaded_path = config_file if config_file.is_file() else None
            
            if not loaded_path:
                print("No configuration found.", file=sys.stderr)
                print("\nTo create a new configuration, set values using:", file=sys.stderr)
                print("  fluxhive config api_key <your-api-key>", file=sys.stderr)
                print("  fluxhive config control_base_url <url>", file=sys.stderr)
                return 1
            else:
                print(f"Configuration file: {loaded_path}")
                
            config = load_config(config_path)
            # Build config dictionary with user-friendly keys
            config_dict = {}
            for attr in vars(config):
                key = FIELD_MAPPING.get(attr, attr)
                value = getattr(config, attr)
                if value is not None:
                    config_dict[key] = str(value)
                
            print("Current configuration:")
            for key, value in sorted(config_dict.items()):
                # Mask sensitive values in display
                # if key in ("user.password", "api_key"):
                #     masked_value = "*" *  8 if value else "(not set)"
                #     print(f"  {key:20s} = {masked_value}")
                # else:
                #     print(f"  {key:20s} = {value}")
                print(f"  {key:20s} = {value}")
            return 0
        except FileNotFoundError:
            print("No configuration found.", file=sys.stderr)
            print("\nTo create a new configuration, set values using:", file=sys.stderr)
            print("  fluxhive config api_key <your-api-key>", file=sys.stderr)
            print("  fluxhive config control_base_url <url>", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error reading configuration: {e}", file=sys.stderr)
            return 1
    
    if args.value is None:
        # Get config value
        try:
            value = get_config_value(args.key, config_path)
            if value is None:
                print(f"Error: Key '{args.key}' not found.", file=sys.stderr)
                print(f"\nAvailable keys:", file=sys.stderr)
                print("  api_key, agent_id, control_base_url", file=sys.stderr)
                print("  log_dir, max_parallel, event_buffer, label", file=sys.stderr)
                print(f"\nUse 'fluxhive config' to list all current values.", file=sys.stderr)
                return 1
            print(value)
            return 0
        except Exception as e:
            print(f"Error reading configuration: {e}", file=sys.stderr)
            return 1
    
    # Set config value
    try:
        target = set_config_value(args.key, args.value, global_=args.global_, path=config_path)
        print(f"✓ Set {args.key} = {args.value}")
        if not args.config:
            print(f"✓ Configuration written to: {target}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(f"\nValid configuration keys:", file=sys.stderr)
        print("  api_key, agent_id, control_base_url", file=sys.stderr)
        print("  log_dir, max_parallel, event_buffer, label", file=sys.stderr)
        return 1
    except PermissionError as e:
        print(f"Error: Permission denied writing to config file.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error setting configuration: {e}", file=sys.stderr)
        print(f"\nPlease check:", file=sys.stderr)
        print(f"  - The config file path is valid", file=sys.stderr)
        print(f"  - You have write permissions", file=sys.stderr)
        print(f"  - The value format is correct", file=sys.stderr)
        return 1


async def async_run(args: argparse.Namespace) -> None:
    """Handle run subcommand."""
    try:
        base_config = load_config(args.config)
    except FileNotFoundError as exc:
        print(f"Error: Configuration file not found.", file=sys.stderr)
        print(f"Details: {exc}", file=sys.stderr)
        print(f"\nTo create a configuration file, run:", file=sys.stderr)
        print(f"  fluxhive config api_key <your-api-key>", file=sys.stderr)
        print(f"  fluxhive config control_base_url <url>", file=sys.stderr)
        print(f"\nOr specify a config file:", file=sys.stderr)
        print(f"  fluxhive run --config /path/to/config.toml", file=sys.stderr)
        sys.exit(1)
    except KeyError as exc:
        print(f"Error: Invalid configuration file.", file=sys.stderr)
        print(f"Details: {exc}", file=sys.stderr)
        print(f"\nRequired fields: agent_id, control_base_url, api_key", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Error: Failed to load configuration.", file=sys.stderr)
        print(f"Details: {exc}", file=sys.stderr)
        sys.exit(1)
    
    config = apply_overrides(base_config, args=args)
    
    # Validate required fields
    if not config.agent_id:
        print(f"Error: agent_id is required.", file=sys.stderr)
        print(f"Set it using: fluxhive config agent_id <id>", file=sys.stderr)
        sys.exit(1)
    
    if not config.control_base_url:
        print(f"Error: control_base_url is required.", file=sys.stderr)
        print(f"Set it using: fluxhive config control_base_url <url>", file=sys.stderr)
        sys.exit(1)
    
    # Check authentication: api_key is required
    if not config.api_key:
        print(f"Error: Missing required authentication configuration.", file=sys.stderr)
        print(f"Missing: api_key", file=sys.stderr)
        print(f"\nYou must configure API key authentication:", file=sys.stderr)
        print(f"  fluxhive config api_key <your-api-key>", file=sys.stderr)
        sys.exit(1)
    print(f"✓ Using API key authentication")
    
    print(f"✓ Agent ID: {config.agent_id}")
    print(f"✓ Control Server: {config.control_base_url}")
    print(f"✓ Max parallel tasks: {config.max_parallel}")
    if config.label:
        print(f"✓ Agent label: {config.label}")
    print(f"\nStarting agent...")
    
    ws_url = to_ws_url(config.control_base_url, config.agent_id)
    loop = asyncio.get_running_loop()
    outbound: asyncio.Queue = asyncio.Queue(maxsize=config.event_buffer)
    publisher = ControlPlaneEventPublisher(loop, outbound)
    status_hook = TaskStatusReporter(publisher)
    log_streamer = TaskLogStreamer(publisher)
    
    manager = TaskManager(
        log_dir=config.log_dir,
        max_parallel=config.max_parallel,
        status_hook=status_hook,
        log_streamer=log_streamer,
    )
    
    client = ControlPlaneClient(
        ControlPlaneConfig(
            ws_url=ws_url,
            agent_id=config.agent_id,
            api_key=config.api_key,
            label=config.label,
        ),
        task_manager=manager,
        outbound_queue=outbound,
    )
    
    try:
        await client.run_forever()
    except ConnectionError as exc:
        print(f"\nError: Failed to connect to Control Server.", file=sys.stderr)
        print(f"Details: {exc}", file=sys.stderr)
        print(f"\nPlease check:", file=sys.stderr)
        print(f"  - Control Server URL is correct: {config.control_base_url}", file=sys.stderr)
        print(f"  - Control Server is running and accessible", file=sys.stderr)
        print(f"  - Network connectivity", file=sys.stderr)
        print(f"  - Firewall settings", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"\nError: Agent encountered an unexpected error.", file=sys.stderr)
        print(f"Details: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("\nShutting down agent...")
        manager.shutdown()
        print("✓ Agent stopped.")


def cmd_run(args: argparse.Namespace) -> int:
    """Handle run subcommand (synchronous wrapper)."""
    try:
        asyncio.run(async_run(args))
    except KeyboardInterrupt:
        print("\n\n✓ Agent stopped by user (Ctrl+C)")
        return 0
    except Exception as exc:
        print(f"\nFatal error: {exc}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = build_parser()
    
    # Handle no arguments - show help
    if len(sys.argv) == 1:
        parser.print_help()
        print("\nQuick Start:")
        print("  1. Configure authentication:")
        print("     fluxhive config api_key <your-api-key>")
        print("\n  2. Set control server URL:")
        print("     fluxhive config control_base_url https://control.fluxhive.io")
        print("\n  3. Run the agent:")
        print("     fluxhive run")
        return 1
    
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # argparse calls sys.exit on error, we catch it to return proper exit code
        return e.code if isinstance(e.code, int) else 1
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "config":
        return cmd_config(args)
    elif args.command == "run":
        log_level = getattr(logging, args.log_level, logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        return cmd_run(args)
    else:
        print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

