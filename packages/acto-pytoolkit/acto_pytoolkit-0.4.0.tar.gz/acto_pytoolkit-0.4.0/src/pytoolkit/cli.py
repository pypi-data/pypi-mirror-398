import argparse
from typing import Callable, Optional

from .config_loader import ConfigLoader
from .env import get_environment
from .logger import get_logger

_COMMANDS: dict[str, Callable[[argparse.Namespace], int]] = {}


def command(name: Optional[str] = None) -> Callable:
    """Decorator that registers a function as a CLI command.

    The wrapped function must accept a single `argparse.Namespace` and return
    an integer exit code.
    """

    def decorator(func: Callable[[argparse.Namespace], int]) -> Callable[[argparse.Namespace], int]:
        cmd_name = name or func.__name__
        _COMMANDS[cmd_name] = func
        return func

    return decorator


def build_parser() -> argparse.ArgumentParser:
    """Build an argument parser with a sub command for each registered command."""
    parser = argparse.ArgumentParser(
        prog="pytoolkit", description="pytoolkit command line interface"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, func in _COMMANDS.items():
        subparser = subparsers.add_parser(name, help=func.__doc__ or "")
        configure = getattr(func, "configure_parser", None)
        if callable(configure):
            configure(subparser)

    return parser


def run_cli() -> int:
    """Entry point for running the CLI."""
    parser = build_parser()
    args = parser.parse_args()
    cmd_name = args.command
    func = _COMMANDS.get(cmd_name)
    if not func:
        parser.error(f"Unknown command: {cmd_name}")
    return func(args)


logger = get_logger("pytoolkit.cli")


@command("info")
def info_cmd(args: argparse.Namespace) -> int:
    """Show basic information about the installed package."""
    logger.info("pytoolkit CLI is available and working.")
    return 0


@command("env")
def env_cmd(args: argparse.Namespace) -> int:
    """Print the current application environment."""
    env = get_environment()
    logger.info("Environment: %s", env.name)
    return 0


@command("config-example")
def config_example_cmd(args: argparse.Namespace) -> int:
    """Show a small configuration example from .env and config.json if available."""
    config = ConfigLoader(env_file=".env", json_file="config.json", prefix="APP_")
    logger.info("Loaded configuration keys: %s", list(config.as_dict().keys()))
    return 0
