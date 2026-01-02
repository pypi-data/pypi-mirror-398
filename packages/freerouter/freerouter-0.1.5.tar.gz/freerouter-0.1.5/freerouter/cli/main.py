#!/usr/bin/env python3
"""
FreeRouter CLI - Command Line Interface

Usage:
    freerouter                  # Start service (interactive)
    freerouter start            # Start service
    freerouter fetch            # Fetch models and generate config
    freerouter list             # List available models
    freerouter logs             # Show service logs (if running in background)
    freerouter init             # Initialize config directory
    freerouter --version        # Show version
"""

import sys
import os
import argparse
import logging
from pathlib import Path

from freerouter.__version__ import __version__
from freerouter.cli.config import ConfigManager
from freerouter.core.fetcher import FreeRouterFetcher
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cmd_init(args):
    """Initialize configuration (interactive)"""
    config_mgr = ConfigManager()

    # Interactive prompts
    print("=" * 60)
    print("FreeRouter Configuration Initialization")
    print("=" * 60)
    print("\nChoose configuration file location:")
    print("1. ~/.config/freerouter/providers.yaml (Recommended, user-level)")
    print("2. ./config/providers.yaml (Current directory, project-level)")

    while True:
        choice = input("\nEnter your choice [1/2] (default: 1): ").strip() or "1"
        if choice in ["1", "2"]:
            break
        print("Invalid option. Please enter 1 or 2")

    use_user_config = (choice == "1")
    config_dir = config_mgr.init_config(interactive=True, use_user_config=use_user_config)

    print(f"\n✓ Configuration initialized: {config_dir / 'providers.yaml'}")
    print(f"✓ All providers are disabled by default (enabled: false)")
    print(f"\nNext steps:")
    print(f"1. Edit {config_dir / 'providers.yaml'} to configure your providers")
    print(f"2. Set enabled: true for the providers you want to use")
    print(f"3. Run 'freerouter fetch' to fetch model list")
    print(f"4. Run 'freerouter start' to start the service")
    print("=" * 60)


def _setup_debug_env(debug_enabled: bool) -> None:
    """
    Setup or clear debug environment variables

    Args:
        debug_enabled: Whether debug mode is enabled
    """
    if debug_enabled:
        # Save and show override if needed
        original_log = os.environ.get('LITELLM_LOG')
        if original_log and original_log != 'DEBUG':
            logger.info(f"Note: Overriding LITELLM_LOG={original_log} → DEBUG")

        # Set debug env vars
        os.environ['LITELLM_LOG'] = 'DEBUG'
        os.environ['FREEROUTER_LOG_RAW'] = 'true'
    else:
        # Clear debug-specific vars to prevent interference
        if 'FREEROUTER_LOG_RAW' in os.environ:
            logger.info("Note: Clearing FREEROUTER_LOG_RAW for normal mode")
            del os.environ['FREEROUTER_LOG_RAW']


def cmd_fetch(args):
    """Fetch models and generate config"""
    config_mgr = ConfigManager()

    # Find provider config
    provider_config = config_mgr.find_provider_config()
    if not provider_config:
        logger.error("No providers.yaml found!")
        logger.info("Run 'freerouter init' to create configuration")
        sys.exit(1)

    # Get output path
    output_config = config_mgr.get_output_config_path()

    logger.info("=" * 60)
    logger.info("FreeRouter - Fetching models and generating config")
    logger.info("=" * 60)
    logger.info(f"Provider config: {provider_config}")
    logger.info(f"Output config: {output_config}")

    # Fetch models
    fetcher = FreeRouterFetcher(config_path=str(output_config))
    fetcher.load_providers_from_yaml(str(provider_config))

    if fetcher.generate_config():
        # Read master_key from config
        master_key = None
        try:
            import yaml
            with open(output_config) as f:
                config = yaml.safe_load(f)
                master_key = config.get("litellm_settings", {}).get("master_key")
        except Exception:
            pass

        logger.info("=" * 60)
        logger.info("✓ Config generation successful!")
        logger.info(f"Generated: {output_config}")
        if master_key:
            logger.info(f"Master Key: {master_key}")
            logger.info("📝 Save this key! Required for API access")
        logger.info("=" * 60)
    else:
        logger.error("✗ Config generation failed!")
        sys.exit(1)


def cmd_start(args):
    """Start FreeRouter service"""
    import os
    import subprocess
    import time

    # Setup debug mode
    debug_mode = hasattr(args, 'debug') and args.debug
    _setup_debug_env(debug_mode)

    if debug_mode:
        logger.info("=" * 60)
        logger.info("🐛 Debug mode enabled")
        logger.info("  - Will regenerate config with debug settings")
        logger.info("  - Raw HTTP requests/responses will be logged")
        logger.info("  - Check logs with: freerouter logs")
        logger.info("=" * 60)

    config_mgr = ConfigManager()

    # Find config
    output_config = config_mgr.get_output_config_path()

    # If debug mode or config doesn't exist, regenerate
    if debug_mode or not output_config.exists():
        if debug_mode:
            logger.info("Regenerating config with debug settings...")

        # Find provider config
        provider_config = config_mgr.find_provider_config()
        if not provider_config:
            logger.error("No providers.yaml found!")
            logger.info("Run 'freerouter init' to create configuration")
            sys.exit(1)

        # Regenerate config
        fetcher = FreeRouterFetcher(config_path=str(output_config))
        fetcher.load_providers_from_yaml(str(provider_config))
        if not fetcher.generate_config():
            logger.error("Failed to generate config")
            sys.exit(1)

        if debug_mode:
            logger.info("✓ Config regenerated with debug settings")

    if not output_config.exists():
        logger.error(f"Config not found: {output_config}")
        logger.info("Run 'freerouter fetch' first to generate config")
        sys.exit(1)

    # IMPORTANT: Remove CONFIG_FILE_PATH env var if exists
    # LiteLLM prioritizes env var over --config flag, which causes confusion
    if 'CONFIG_FILE_PATH' in os.environ:
        logger.warning(f"Removing CONFIG_FILE_PATH env var (was: {os.environ['CONFIG_FILE_PATH']})")
        logger.warning(f"Using freerouter config instead: {output_config}")
        del os.environ['CONFIG_FILE_PATH']

    # Log file path
    log_dir = output_config.parent
    log_file = log_dir / "freerouter.log"
    pid_file = log_dir / "freerouter.pid"

    # Check if already running
    if pid_file.exists():
        with open(pid_file) as f:
            old_pid = f.read().strip()
        try:
            # Check if process is still running
            os.kill(int(old_pid), 0)
            logger.error(f"FreeRouter is already running (PID: {old_pid})")
            logger.info("Use 'freerouter logs' to view logs or kill the process first")
            sys.exit(1)
        except (OSError, ValueError):
            # Process not running, remove stale pid file
            pid_file.unlink()

    port = os.getenv("LITELLM_PORT", "4000")
    host = os.getenv("LITELLM_HOST", "0.0.0.0")

    logger.info("=" * 60)
    logger.info("Starting FreeRouter Service")
    logger.info("=" * 60)
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Config: {output_config}")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 60)

    try:
        cmd = [
            "litellm",
            "--config", str(output_config),
            "--port", str(port),
            "--host", host
        ]

        # Add debug flag if debug mode enabled
        if debug_mode:
            cmd.extend(["--detailed_debug"])

        # Open log file
        log_handle = open(log_file, "a")

        # Prepare environment for subprocess
        env = os.environ.copy()

        # Set HTTPX logging if in debug mode
        if env.get('LITELLM_LOG') == 'DEBUG':
            env['HTTPX_LOG_LEVEL'] = 'DEBUG'

        logger.info(f"LITELLM_LOG level: {env.get('LITELLM_LOG', 'INFO')}")

        # Start process as daemon (detached from parent)
        process = subprocess.Popen(
            cmd,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # Detach from parent process
            bufsize=1,
            env=env  # Pass environment variables to subprocess
        )

        # Write PID file
        with open(pid_file, "w") as f:
            f.write(str(process.pid))

        # Wait and monitor log file for startup success
        startup_success = False
        startup_timeout = 30
        start_time = time.time()

        print("\nWaiting for service to start...")
        time.sleep(2)  # Give it a moment to start writing logs

        # Tail the log file to check for startup
        last_pos = 0
        while time.time() - start_time < startup_timeout:
            try:
                with open(log_file, "r") as f:
                    f.seek(last_pos)
                    new_lines = f.readlines()
                    last_pos = f.tell()

                    for line in new_lines:
                        print(line, end="")

                        if "Uvicorn running on" in line:
                            startup_success = True
                            break

                        if "error" in line.lower() and "failed" in line.lower():
                            logger.error("\nStartup failed! Check logs for details.")
                            process.terminate()
                            pid_file.unlink()
                            sys.exit(1)

                if startup_success:
                    break

                time.sleep(0.5)

            except FileNotFoundError:
                time.sleep(0.5)
                continue

        if startup_success:
            # Read master_key from config
            master_key = None
            try:
                import yaml
                with open(output_config) as f:
                    config = yaml.safe_load(f)
                    master_key = config.get("litellm_settings", {}).get("master_key")
            except Exception:
                pass

            logger.info("\n" + "=" * 60)
            logger.info("✓ FreeRouter started successfully!")
            logger.info(f"  PID: {process.pid}")
            logger.info(f"  URL: http://{host}:{port}")
            logger.info(f"  Logs: {log_file}")
            if master_key:
                logger.info(f"  Master Key: {master_key}")
                logger.info(f"  📝 Save this key! Required for API access")
            logger.info("")
            logger.info("Commands:")
            logger.info("  freerouter logs      - View real-time logs")
            logger.info("  freerouter stop      - Stop the service")
            logger.info("=" * 60)
        else:
            logger.error("\nStartup timeout! The service may still be starting.")
            logger.info(f"Check logs: tail -f {log_file}")
            logger.info(f"If failed, kill process: kill {process.pid}")

    except FileNotFoundError:
        logger.error("litellm not found! Please install: pip install litellm")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        if pid_file.exists():
            pid_file.unlink()
        sys.exit(1)


def cmd_list(args):
    """List available models"""
    import os
    import yaml
    import requests
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from collections import defaultdict

    console = Console()
    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()

    if not output_config.exists():
        logger.error(f"Config not found: {output_config}")
        logger.info("Run 'freerouter fetch' first to generate config")
        sys.exit(1)

    port = os.getenv("LITELLM_PORT", "4000")
    host = os.getenv("LITELLM_HOST", "0.0.0.0")
    url = f"http://localhost:{port}" if host == "0.0.0.0" else f"http://{host}:{port}"

    # Show service status banner and try to get models from API if running
    models = None
    providers_models = None

    if is_service_running():
        log_dir = output_config.parent
        pid_file = log_dir / "freerouter.pid"
        with open(pid_file) as f:
            pid = f.read().strip()

        console.print(f"\n[green]● Service Running[/green] [dim](PID: {pid}, {url})[/dim]")

        # Try to get models from API
        try:
            response = requests.get(f"{url}/v1/models", timeout=2)
            if response.status_code == 200:
                api_data = response.json()
                api_models = api_data.get("data", [])
                if api_models:
                    # Read config to get provider mapping
                    with open(output_config) as f:
                        config = yaml.safe_load(f)
                    config_models = config.get("model_list", [])

                    # Build model_name -> provider mapping from config
                    model_provider_map = {}
                    for config_model in config_models:
                        model_name = config_model.get("model_name", "")
                        litellm_model = config_model.get("litellm_params", {}).get("model", "")
                        provider = litellm_model.split("/")[0] if "/" in litellm_model else "unknown"
                        model_provider_map[model_name] = provider

                    # Convert API response to our format with provider info
                    models = []
                    providers_models = defaultdict(list)
                    for model in api_models:
                        model_id = model.get("id", "")
                        models.append({"model_name": model_id})
                        # Use provider from config, fallback to inferring from name
                        provider = model_provider_map.get(model_id, "unknown")
                        if provider == "unknown" and "/" in model_id:
                            provider = model_id.split("/")[0]
                        providers_models[provider].append(model_id)
                    console.print(f"[dim]  Fetched from API: /v1/models[/dim]")
        except Exception as e:
            logger.debug(f"Failed to fetch from API: {e}")
            # Fall back to config file
            pass
    else:
        console.print(f"\n[yellow]○ Service Not Running[/yellow] [dim](start with: freerouter start)[/dim]")

    # Fall back to reading from config file if API call failed or service not running
    if models is None:
        with open(output_config) as f:
            config = yaml.safe_load(f)

        models = config.get("model_list", [])

    if not models:
        console.print("[yellow]No models configured.[/yellow]")
        return

    # Group models by provider (if not already done by API fetch)
    if providers_models is None:
        providers_models = defaultdict(list)

        for model in models:
            model_name = model.get("model_name", "")
            litellm_model = model.get("litellm_params", {}).get("model", "")
            provider = litellm_model.split("/")[0] if "/" in litellm_model else "unknown"
            providers_models[provider].append(model_name)

    # Display each provider in a separate table
    for provider in sorted(providers_models.keys()):
        models_list = providers_models[provider]

        # Print provider header
        console.print(f"\n[bold cyan]{provider.upper()}[/bold cyan] [dim]({len(models_list)} models)[/dim]")

        # Create table for models
        table = Table(
            show_header=False,
            box=None,
            padding=(0, 1),
            show_edge=False
        )

        # Calculate number of columns based on terminal width
        # Assume average model name length of 40, add 3 columns if wide terminal
        terminal_width = console.width
        if terminal_width >= 160:  # Wide terminal
            num_cols = 3
        elif terminal_width >= 100:  # Medium terminal
            num_cols = 2
        else:  # Narrow terminal
            num_cols = 1

        # Add columns
        for _ in range(num_cols):
            table.add_column(style="white", overflow="fold")

        # Add rows
        for i in range(0, len(models_list), num_cols):
            row = []
            for j in range(num_cols):
                idx = i + j
                if idx < len(models_list):
                    row.append(f"  • {models_list[idx]}")
                else:
                    row.append("")
            table.add_row(*row)

        console.print(table)

    # Summary
    console.print(f"[bold]Total:[/bold] [cyan]{len(models)}[/cyan] models across [cyan]{len(providers_models)}[/cyan] providers\n")


def cmd_stop(args):
    """Stop FreeRouter service"""
    import os
    import time

    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()
    log_dir = output_config.parent
    pid_file = log_dir / "freerouter.pid"

    # Check if service is running
    if not pid_file.exists():
        logger.error("FreeRouter is not running")
        sys.exit(1)

    with open(pid_file) as f:
        pid = f.read().strip()

    try:
        pid_int = int(pid)
        os.kill(pid_int, 0)  # Check if running
    except (OSError, ValueError):
        logger.error(f"FreeRouter process (PID: {pid}) is not running")
        pid_file.unlink()
        sys.exit(1)

    logger.info(f"Stopping FreeRouter service (PID: {pid})...")

    try:
        # Send SIGTERM
        os.kill(pid_int, 15)

        # Wait for process to stop
        for i in range(10):
            try:
                os.kill(pid_int, 0)
                time.sleep(0.5)
            except OSError:
                break

        # Check if stopped
        try:
            os.kill(pid_int, 0)
            logger.error("Failed to stop service gracefully, use: kill -9 {pid}")
            sys.exit(1)
        except OSError:
            pid_file.unlink()
            logger.info("✓ FreeRouter stopped successfully")

    except Exception as e:
        logger.error(f"Failed to stop service: {e}")
        sys.exit(1)


def _format_log_line(line: str) -> str:
    """Format log line for pretty output"""
    import re
    import json

    # Format "POST Request Sent from LiteLLM"
    if "POST Request Sent from LiteLLM:" in line:
        return "\n\033[96m" + "="*70 + "\033[0m\n\033[1;96m🚀 API REQUEST\033[0m\n" + "\033[96m" + "="*70 + "\033[0m\n" + line

    # Format curl command lines
    if line.strip().startswith("curl -X POST"):
        return "\033[93m" + line + "\033[0m"

    # Format RAW RESPONSE
    if "RAW RESPONSE:" in line:
        # Try to extract and format JSON
        try:
            json_match = re.search(r'RAW RESPONSE:\s*(\{.*\})', line, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)

                output = [
                    "\n\033[92m" + "="*70 + "\033[0m",
                    "\033[1;92m📥 API RESPONSE\033[0m",
                    "\033[92m" + "="*70 + "\033[0m"
                ]

                # Model and ID
                if 'model' in data:
                    output.append(f"\033[1mModel:\033[0m {data['model']}")
                if 'id' in data:
                    output.append(f"\033[1mID:\033[0m {data['id']}")

                # Content
                if 'choices' in data and len(data['choices']) > 0:
                    choice = data['choices'][0]
                    if 'message' in choice:
                        content = choice['message'].get('content', '')
                        output.append(f"\n\033[1mContent:\033[0m\n{content}")

                # Usage
                if 'usage' in data:
                    usage = data['usage']
                    output.append(f"\n\033[1mToken Usage:\033[0m")
                    output.append(f"  Prompt: {usage.get('prompt_tokens', 0)}, Completion: {usage.get('completion_tokens', 0)}, Total: {usage.get('total_tokens', 0)}")

                output.append("\033[92m" + "="*70 + "\033[0m\n")
                return "\n".join(output)
        except:
            pass

        return "\n\033[92m" + "="*70 + "\033[0m\n\033[1;92m📥 API RESPONSE\033[0m\n" + "\033[92m" + "="*70 + "\033[0m\n" + line

    # Highlight errors
    if "ERROR" in line or "error" in line.lower():
        return "\033[91m" + line + "\033[0m"

    # Highlight warnings
    if "WARNING" in line or "warning" in line.lower():
        return "\033[93m" + line + "\033[0m"

    # Highlight INFO level for Router
    if "LiteLLM Router:INFO" in line and "200 OK" in line:
        return "\033[92m" + line + "\033[0m"

    return line


def cmd_logs(args):
    """Show service logs in real-time with pretty formatting"""
    import os
    import time
    from .request_log_parser import LogStreamFilter

    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()
    log_dir = output_config.parent
    log_file = log_dir / "freerouter.log"
    pid_file = log_dir / "freerouter.pid"

    # Check if service is running
    if not pid_file.exists():
        logger.error("FreeRouter is not running")
        logger.info("Start it with: freerouter start")
        sys.exit(1)

    with open(pid_file) as f:
        pid = f.read().strip()

    try:
        os.kill(int(pid), 0)
    except (OSError, ValueError):
        logger.error(f"FreeRouter process (PID: {pid}) is not running")
        logger.info("Start it with: freerouter start")
        pid_file.unlink()
        sys.exit(1)

    # Check if log file exists
    if not log_file.exists():
        logger.error(f"Log file not found: {log_file}")
        sys.exit(1)

    requests_only = hasattr(args, 'requests') and args.requests

    if requests_only:
        logger.info(f"Showing API requests/responses from: {log_file}")
        logger.info("Press Ctrl+C to exit\n")
    else:
        logger.info(f"Showing logs from: {log_file}")
        logger.info(f"Service PID: {pid}")
        logger.info("Press Ctrl+C to exit\n")
        logger.info("=" * 60)

    # Tail the log file with formatting
    try:
        with open(log_file, "r") as f:
            # Go to end of file
            f.seek(0, 2)

            # Initialize filter for requests-only mode
            log_filter = LogStreamFilter() if requests_only else None
            buffer = ""  # Buffer for normal mode

            while True:
                line = f.readline()
                if line:
                    if requests_only:
                        # Use LogStreamFilter for request/response filtering
                        output = log_filter.process_line(line)
                        if output:
                            print(output)
                    else:
                        # Normal mode: format all logs
                        buffer += line
                        if line.endswith('\n'):
                            formatted = _format_log_line(buffer)
                            print(formatted, end="")
                            buffer = ""
                else:
                    time.sleep(0.1)

                    # Check if process is still running
                    try:
                        os.kill(int(pid), 0)
                    except (OSError, ValueError):
                        logger.info("\n" + "=" * 60)
                        logger.info("Service stopped")
                        break

    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Stopped viewing logs")
    except Exception as e:
        logger.error(f"Error reading logs: {e}")


def cmd_status(args):
    """Show FreeRouter service status"""
    import os
    import time
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

    console = Console()
    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()
    log_dir = output_config.parent
    pid_file = log_dir / "freerouter.pid"
    log_file = log_dir / "freerouter.log"

    # Check if service is running
    if not pid_file.exists():
        console.print(Panel.fit(
            f"[yellow]○ Not Running[/yellow]\n"
            f"Version: [dim]{__version__}[/dim]\n\n"
            "Start service with: [cyan]freerouter start[/cyan]",
            title="[bold]FreeRouter Service Status[/bold]",
            border_style="yellow"
        ))
        return

    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())

        # Check if process is running
        os.kill(pid, 0)

        # Service is running - create info table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="cyan", width=12)
        table.add_column("Value", style="white")

        table.add_row("Status", "[green]● Running[/green]")
        table.add_row("Version", __version__)
        table.add_row("PID", str(pid))

        # Get service URL
        port = os.getenv("LITELLM_PORT", "4000")
        host = os.getenv("LITELLM_HOST", "0.0.0.0")
        if host == "0.0.0.0":
            display_url = f"http://localhost:{port} [dim](listening on 0.0.0.0)[/dim]"
        else:
            display_url = f"http://{host}:{port}"
        table.add_row("URL", display_url)

        # Config file
        table.add_row("Config", str(output_config))

        # Calculate uptime from PID file creation time
        if pid_file.exists():
            start_time = pid_file.stat().st_mtime
            uptime_seconds = time.time() - start_time
            uptime_str = format_uptime(uptime_seconds)
            table.add_row("Uptime", uptime_str)

        # Count models and get master_key
        if output_config.exists():
            import yaml
            with open(output_config) as f:
                config = yaml.safe_load(f)
            model_count = len(config.get("model_list", []))
            table.add_row("Models", f"{model_count} configured")

            # Get master_key from config
            master_key = config.get("litellm_settings", {}).get("master_key")
            if master_key:
                table.add_row("Master Key", f"[yellow]{master_key}[/yellow]")

        # Log file
        if log_file.exists():
            log_size = log_file.stat().st_size / 1024  # KB
            table.add_row("Log", f"{log_file} ({log_size:.1f} KB)")

        console.print(Panel(
            table,
            title="[bold green]FreeRouter Service Status[/bold green]",
            border_style="green"
        ))

    except (OSError, ValueError):
        # Process not running, but PID file exists (stale)
        console.print(Panel.fit(
            f"[yellow]○ Not Running[/yellow] [dim](stale PID file)[/dim]\n"
            f"Version: [dim]{__version__}[/dim]\n"
            f"PID: [dim]{pid} (not found)[/dim]\n\n"
            "Clean up and start: [cyan]freerouter start[/cyan]",
            title="[bold]FreeRouter Service Status[/bold]",
            border_style="yellow"
        ))
        pid_file.unlink()


def format_uptime(seconds):
    """Format uptime in human readable format"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
    else:
        days = int(seconds / 86400)
        hours = int((seconds % 86400) / 3600)
        return f"{days} day{'s' if days != 1 else ''} {hours} hour{'s' if hours != 1 else ''}"


def backup_config(config_path: Path):
    """
    Backup configuration file with timestamp

    Args:
        config_path: Path to config file to backup
    """
    import datetime
    import shutil

    if not config_path.exists():
        return

    # Create backup with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.parent / f"{config_path.name}.backup.{timestamp}"

    shutil.copy2(config_path, backup_path)

    # Show prominent backup message
    logger.info("=" * 60)
    logger.info(f"✓ Backup created: {backup_path.name}")
    logger.info(f"  Location: {backup_path}")
    logger.info(f"  Restore: freerouter restore {backup_path.name}")
    logger.info("=" * 60)

    # Cleanup old backups (keep only 5 most recent)
    cleanup_old_backups(config_path, keep=5)


def cleanup_old_backups(config_path: Path, keep: int = 5):
    """
    Remove old backup files, keeping only the most recent ones

    Args:
        config_path: Path to config file
        keep: Number of backups to keep
    """
    backup_pattern = f"{config_path.name}.backup.*"
    backup_files = sorted(
        config_path.parent.glob(backup_pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    # Remove old backups
    for old_backup in backup_files[keep:]:
        try:
            old_backup.unlink()
            logger.debug(f"Removed old backup: {old_backup.name}")
        except Exception as e:
            logger.warning(f"Failed to remove old backup {old_backup.name}: {e}")


def is_service_running() -> bool:
    """
    Check if FreeRouter service is currently running

    Returns:
        True if service is running, False otherwise
    """
    import os

    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()
    log_dir = output_config.parent
    pid_file = log_dir / "freerouter.pid"

    if not pid_file.exists():
        return False

    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())

        # Check if process is running
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def cmd_reload(args):
    """
    Reload FreeRouter service

    Modes:
    - Normal: stop + start (restart with existing config)
    - Refresh (-r): fetch + stop + start (refresh from providers)
    - Debug (-d): restart with debug logging
    """
    import time
    import os

    # Setup debug mode
    debug_mode = hasattr(args, 'debug') and args.debug
    _setup_debug_env(debug_mode)

    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()

    logger.info("=" * 60)
    logger.info("Reloading FreeRouter Service")
    if debug_mode:
        logger.info("🐛 Debug mode: ON")
    logger.info("=" * 60)

    # 1. If --refresh or --debug, backup and regenerate config
    if args.refresh or debug_mode:
        logger.info("Refreshing configuration from providers...")

        # Backup existing config
        if output_config.exists():
            backup_config(output_config)

        # Regenerate config
        cmd_fetch(args)
        logger.info("✓ Configuration refreshed")

    # 2. Stop service if running
    if is_service_running():
        logger.info("Stopping service...")
        cmd_stop(args)
        time.sleep(1)  # Wait for clean shutdown
    else:
        logger.info("Service is not running")

    # 3. Start service
    logger.info("Starting service...")
    cmd_start(args)

    logger.info("=" * 60)
    logger.info("✓ Service reloaded successfully")
    logger.info("=" * 60)


def cmd_restore(args):
    """
    Restore configuration from backup

    Args:
        args.backup_file: Backup file name or full path
    """
    import shutil

    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()
    config_dir = output_config.parent

    backup_file = args.backup_file

    # If just a filename, look in config directory
    if not Path(backup_file).is_absolute():
        backup_path = config_dir / backup_file
    else:
        backup_path = Path(backup_file)

    # Check if backup exists
    if not backup_path.exists():
        logger.error(f"Backup file not found: {backup_path}")

        # List available backups
        available_backups = sorted(
            config_dir.glob(f"{output_config.name}.backup.*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if available_backups:
            logger.info("\nAvailable backups:")
            for backup in available_backups:
                mtime = backup.stat().st_mtime
                import datetime
                timestamp = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"  - {backup.name} ({timestamp})")
            logger.info(f"\nUsage: freerouter restore <backup-file>")
        else:
            logger.info("No backups found")

        sys.exit(1)

    # Confirm restore
    logger.info("=" * 60)
    logger.info("Restore Configuration")
    logger.info("=" * 60)
    logger.info(f"From: {backup_path.name}")
    logger.info(f"To:   {output_config}")

    if not args.yes:
        response = input("\nContinue? [y/N]: ").strip().lower()
        if response != 'y':
            logger.info("Restore cancelled")
            sys.exit(0)

    # Backup current config before restoring
    if output_config.exists():
        logger.info("Creating backup of current config...")
        backup_config(output_config)

    # Restore
    try:
        shutil.copy2(backup_path, output_config)
        logger.info("=" * 60)
        logger.info("✓ Configuration restored successfully")
        logger.info("=" * 60)
        logger.info(f"Restored from: {backup_path.name}")
        logger.info("\nTo apply changes, run: freerouter reload")

    except Exception as e:
        logger.error(f"Failed to restore configuration: {e}")
        sys.exit(1)


def cmd_select(args):
    """
    Interactive model selector

    Allows users to select which models to include in config.yaml,
    reducing LiteLLM startup time and memory usage.
    """
    import yaml
    import questionary

    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()

    # Check if config exists
    if not output_config.exists():
        logger.error(f"Config not found: {output_config}")
        logger.info("Run 'freerouter fetch' first to generate config")
        sys.exit(1)

    # Load config
    with open(output_config) as f:
        config = yaml.safe_load(f)

    models = config.get("model_list", [])

    if not models:
        logger.error("No models found in config")
        sys.exit(1)

    # Prepare choices for selection
    choices = []
    for model in models:
        model_name = model.get("model_name", "")
        litellm_model = model.get("litellm_params", {}).get("model", "")
        provider = litellm_model.split("/")[0] if "/" in litellm_model else "unknown"

        # Format: [provider] model_name
        display_name = f"[{provider}] {model_name}"
        choices.append({
            "name": display_name,
            "value": model_name
        })

    logger.info("=" * 60)
    logger.info("FreeRouter - Model Selector")
    logger.info("=" * 60)
    logger.info(f"Total models: {len(models)}")
    logger.info("")
    logger.info("Select the models you want to use:")
    logger.info("  • Use [Space] to select/deselect")
    logger.info("  • Use [↑/↓] to navigate")
    logger.info("  • Press [Enter] to confirm")
    logger.info("=" * 60)

    # Interactive multi-select
    selected_models = questionary.checkbox(
        "Select models to include:",
        choices=choices,
        instruction="Use [Space] to select, [Enter] to confirm"
    ).ask()

    if not selected_models:
        logger.info("No models selected. Operation cancelled.")
        sys.exit(0)

    # Filter config to only include selected models
    filtered_models = [
        model for model in models
        if model.get("model_name") in selected_models
    ]

    # Backup original config
    backup_config(output_config)

    # Write filtered config
    config["model_list"] = filtered_models
    with open(output_config, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Show summary
    logger.info("=" * 60)
    logger.info("✓ Model selection complete!")
    logger.info("=" * 60)
    logger.info(f"Selected: {len(selected_models)} models")
    logger.info(f"Removed: {len(models) - len(selected_models)} models")
    logger.info(f"Config: {output_config}")
    logger.info("")
    logger.info("To apply changes:")
    logger.info("  • If service is running: freerouter reload")
    logger.info("  • If service is stopped: freerouter start")
    logger.info("=" * 60)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="freerouter",
        description="FreeRouter - Free LLM Router Service",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"FreeRouter {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    parser_init = subparsers.add_parser("init", help="Initialize configuration")
    parser_init.set_defaults(func=cmd_init)

    # fetch command
    parser_fetch = subparsers.add_parser("fetch", help="Fetch models and generate config")
    parser_fetch.set_defaults(func=cmd_fetch)

    # start command
    parser_start = subparsers.add_parser("start", help="Start FreeRouter service")
    parser_start.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug mode (shows raw HTTP requests/responses)"
    )
    parser_start.set_defaults(func=cmd_start)

    # list command
    parser_list = subparsers.add_parser("list", help="List available models")
    parser_list.set_defaults(func=cmd_list)

    # stop command
    parser_stop = subparsers.add_parser("stop", help="Stop FreeRouter service")
    parser_stop.set_defaults(func=cmd_stop)

    # logs command
    parser_logs = subparsers.add_parser("logs", help="Show service logs")
    parser_logs.add_argument(
        "-r", "--requests",
        action="store_true",
        help="Show only API requests and responses (filters out debug logs)"
    )
    parser_logs.set_defaults(func=cmd_logs)

    # status command
    parser_status = subparsers.add_parser("status", help="Show service status")
    parser_status.set_defaults(func=cmd_status)

    # reload command
    parser_reload = subparsers.add_parser(
        "reload",
        help="Reload service (restart or refresh config)"
    )
    parser_reload.add_argument(
        "-r", "--refresh",
        action="store_true",
        help="Refresh configuration from providers before reloading"
    )
    parser_reload.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug mode (shows raw HTTP requests/responses)"
    )
    parser_reload.set_defaults(func=cmd_reload)

    # restore command
    parser_restore = subparsers.add_parser(
        "restore",
        help="Restore configuration from backup"
    )
    parser_restore.add_argument(
        "backup_file",
        help="Backup file name (e.g., config.yaml.backup.20251226_120530)"
    )
    parser_restore.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt"
    )
    parser_restore.set_defaults(func=cmd_restore)

    # select command
    parser_select = subparsers.add_parser(
        "select",
        help="Interactive model selector"
    )
    parser_select.set_defaults(func=cmd_select)

    # Parse arguments
    args = parser.parse_args()

    # If no command, default to start
    if not args.command:
        args.command = "start"
        args.func = cmd_start

    # Execute command
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
