"""Command-line interface for py_logex."""

from . import __version__
import yaml
import sys
import argparse
from pathlib import Path
from typing import Optional

from .config import get_config_manager
from .defaults import get_default_yaml
from .utils import get_script_name


def cmd_config_show(args) -> int:
    """Show current configuration file location."""
    try:
        config_manager = get_config_manager()
        config_path = config_manager.discover_config()

        print(f"Configuration file: {config_path}")
        print(f"Exists: {config_path.exists()}")

        if config_path.exists():
            print(f"\nConfiguration content:")
            print("-" * 60)
            with open(config_path, "r") as f:
                print(f.read())
            print("-" * 60)

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_config_init(args) -> int:
    """Initialize new configuration file."""
    try:
        output_path = Path(args.output) if args.output else Path.cwd() / "logging.yaml"

        # Check if file already exists
        if output_path.exists() and not args.force:
            print(
                f"Error: {output_path} already exists. Use --force to overwrite.",
                file=sys.stderr,
            )
            return 1

        # Create config file
        script_name = args.name or get_script_name()
        config_content = get_default_yaml(script_name)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write(config_content)

        print(f"Created configuration file: {output_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_config_validate(args) -> int:
    """Validate configuration file."""
    try:
        config_path = Path(args.config) if args.config else None

        if config_path is None:
            config_manager = get_config_manager()
            config_path = config_manager.discover_config()

        print(f"Validating: {config_path}")

        # Try to load YAML
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        if config is None:
            print("Warning: Configuration file is empty", file=sys.stderr)
            return 1

        # Basic validation
        required_sections = ["logger"]
        missing = [s for s in required_sections if s not in config]

        if missing:
            print(f"Warning: Missing sections: {', '.join(missing)}", file=sys.stderr)
            return 1

        print("✓ Configuration is valid")
        return 0

    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML syntax: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main(argv: Optional[list] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="py_logex - Simple, powerful logging with exception handling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(dest="subcommand")

    # config show
    show_parser = config_subparsers.add_parser(
        "show", help="Show current configuration"
    )
    show_parser.set_defaults(func=cmd_config_show)

    # config init
    init_parser = config_subparsers.add_parser(
        "init", help="Initialize new configuration file"
    )
    init_parser.add_argument(
        "-o", "--output", help="Output path (default: ./logging.yaml)"
    )
    init_parser.add_argument("-n", "--name", help="Script name for log file")
    init_parser.add_argument(
        "-f", "--force", action="store_true", help="Overwrite existing file"
    )
    init_parser.set_defaults(func=cmd_config_init)

    # config validate
    validate_parser = config_subparsers.add_parser(
        "validate", help="Validate configuration file"
    )
    validate_parser.add_argument("-c", "--config", help="Config file to validate")
    validate_parser.set_defaults(func=cmd_config_validate)

    # Version command
    version_parser = subparsers.add_parser("version", help="Show version")

    args = parser.parse_args(argv)

    # Handle version
    if args.command == "version":
        print(f"py_logex version {__version__}")
        return 0

    # Handle no command
    if args.command is None:
        parser.print_help()
        return 0

    # Handle config without subcommand
    if args.command == "config" and args.subcommand is None:
        config_parser.print_help()
        return 0

    # Execute subcommand
    if hasattr(args, "func"):
        return args.func(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
