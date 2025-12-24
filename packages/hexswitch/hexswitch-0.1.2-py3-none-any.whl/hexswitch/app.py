"""Main application entry point for HexSwitch."""

import argparse
from pathlib import Path
import sys

from hexswitch import __version__
from hexswitch.runtime import Runtime
from hexswitch.shared.config import (
    DEFAULT_CONFIG_PATH,
    ConfigError,
    get_example_config,
    load_config,
    validate_config,
)
from hexswitch.shared.config.config import build_execution_plan
from hexswitch.shared.logging import get_logger, setup_logging

logger = get_logger(__name__)

TAGLINE = "Hexagonal runtime switchboard for config-driven microservices"


def cmd_version() -> int:
    """Handle 'version' command.

    Returns:
        Exit code (0 for success).
    """
    print(f"HexSwitch {__version__}")
    print(TAGLINE)
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Handle 'init' command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    config_path = Path(args.config or DEFAULT_CONFIG_PATH)

    if config_path.exists() and not args.force:
        logger.error(f"Configuration file already exists: {config_path}")
        logger.error("Use --force to overwrite")
        return 1

    try:
        example_config = get_example_config()
        config_path.write_text(example_config, encoding="utf-8")
        logger.info(f"Created example configuration: {config_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to create configuration file: {e}")
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Handle 'validate' command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for validation error).
    """
    config_path = args.config or DEFAULT_CONFIG_PATH

    try:
        config = load_config(config_path)
        validate_config(config)
        logger.info(f"Configuration is valid: {config_path}")
        return 0
    except ConfigError as e:
        logger.error(f"Validation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    """Handle 'run' command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for validation error, 2 for runtime failure).
    """
    config_path = args.config or DEFAULT_CONFIG_PATH

    # Load and validate config
    try:
        config = load_config(config_path)
        validate_config(config)
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        return 1

    # Build execution plan
    plan = build_execution_plan(config)

    if args.dry_run:
        # Dry-run mode: print execution plan
        logger.info(f"Execution plan for service '{plan['service']}':")
        logger.info(f"  Inbound adapters: {len(plan['inbound_adapters'])}")
        for adapter in plan["inbound_adapters"]:
            logger.info(f"    - {adapter['name']}")
        logger.info(f"  Outbound adapters: {len(plan['outbound_adapters'])}")
        for adapter in plan["outbound_adapters"]:
            logger.info(f"    - {adapter['name']}")
        logger.info("Ready to start runtime")
        return 0

    # Run mode: start runtime
    try:
        logger.info(f"Starting HexSwitch runtime with config: {config_path}")
        runtime = Runtime(config)
        runtime.start()
        try:
            # Keep running until interrupted
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            runtime.stop()
        return 0
    except Exception as e:
        logger.error(f"Runtime failure: {e}")
        return 2


def main() -> int:
    """Main entry point for HexSwitch CLI.

    Returns:
        Exit code (0 for success, 1 for validation error, 2 for runtime failure).
    """
    parser = argparse.ArgumentParser(
        description="HexSwitch - Hexagonal runtime switchboard for config-driven microservices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help=f"Path to configuration file (default: {DEFAULT_CONFIG_PATH})",
    )

    # Backwards compatibility: --version flag
    parser.add_argument(
        "--version",
        action="version",
        version=f"HexSwitch {__version__}",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # version command
    subparsers.add_parser("version", help="Show version and tagline")

    # init command
    init_parser = subparsers.add_parser("init", help="Create example configuration")
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing configuration file",
    )

    # validate command
    subparsers.add_parser("validate", help="Validate configuration")

    # run command
    run_parser = subparsers.add_parser("run", help="Start runtime")
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print execution plan without starting runtime",
    )

    args = parser.parse_args()

    # Set up logging (must be done before any logger calls)
    setup_logging(level=args.log_level, service_name="hexswitch")

    # Handle commands
    if args.command == "version" or args.command is None:
        # If no command specified, show version (backwards compatibility)
        return cmd_version()
    elif args.command == "init":
        return cmd_init(args)
    elif args.command == "validate":
        return cmd_validate(args)
    elif args.command == "run":
        return cmd_run(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
