# src/relm/main.py

import argparse
import sys
from pathlib import Path
from rich.console import Console

from .banner import print_logo
from .config import load_config
from .commands import (
    list_command,
    release_command,
    install_command,
    run_command,
    status_command,
    verify_command,
    clean_command,
    create_command,
    gc_command,
    pytest_command,
)

# Export list_projects for backward compatibility if any tests rely on it,
# though we should update tests to use the new structure.
# But looking at tests/test_main.py, it imports list_projects directly.
# So I will keep a wrapper or move the logic back?
# No, "The Golden Rule: Functionality MUST remain identical."
# If I remove `list_projects` from here, tests might break.
# I should probably update the tests to point to the new location, or re-export it.
# Re-exporting is safer for now.

from .commands.list_command import execute as _list_execute
# Adapting old signature to new logic if needed, but wait.
# The tests import `list_projects` and call it with `path`.
# The new `execute` takes `args` and `console`.
# So I cannot simply re-export.
# I will define a compatibility wrapper.

console = Console()

def list_projects(path: Path):
    """
    Deprecated: Use commands.list_command.execute instead.
    Kept for backward compatibility with tests.
    """
    # Create a dummy args object
    args = argparse.Namespace(path=str(path), since=None)
    list_command.execute(args, console)


def main():
    print_logo()

    # Load config early
    # We don't have args yet, so we assume current dir for config search
    # or we can do a partial parse?
    # For now, let's load from CWD
    cwd = Path.cwd()
    config = load_config(cwd)

    # Base parser for shared arguments
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument(
        "--path",
        default=".",
        help="Path to the root directory containing projects (default: current dir)."
    )
    base_parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Recursively scan for projects in subdirectories."
    )
    base_parser.add_argument(
        "--depth", "-d",
        type=int,
        default=2,
        help="Maximum depth to scan when recursive is enabled (default: 2)."
    )
    base_parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run commands in parallel across projects."
    )
    base_parser.add_argument(
        "--jobs", "-j",
        type=int,
        default=None,
        help="Number of parallel jobs (default: number of CPUs)."
    )
    base_parser.add_argument(
        "--from-root",
        action="store_true",
        help="Run commands from the current working directory instead of project directories."
    )

    parser = argparse.ArgumentParser(
        description="Manage releases and versioning for local Python projects.",
        parents=[base_parser]
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # We pass the base_parser to commands if they need to inherit it
    # or just use it in the registration process.
    # However, to allow the flags AFTER the command, the subparser itself needs them.
    # So we define a function to register with inheritance.

    def add_cmd(name, help_text):
        return subparsers.add_parser(name, help=help_text, parents=[base_parser])

    # Each register function now needs to be aware or we just update the register calls.
    # Let's see how register is defined in commands.
    # e.g. list_command.register(subparsers)
    
    # Register commands
    list_command.register(subparsers, base_parser)
    release_command.register(subparsers, base_parser)
    install_command.register(subparsers, base_parser)
    run_command.register(subparsers, base_parser)
    status_command.register(subparsers, base_parser)
    verify_command.register(subparsers, base_parser)
    clean_command.register(subparsers, base_parser)
    create_command.register(subparsers, base_parser)
    gc_command.register(subparsers, base_parser)
    pytest_command.register(subparsers, base_parser)

    args, unknown = parser.parse_known_args()

    # Inject unknown args if we want? No, execute() manually checks sys.argv
    # or we can pass unknown to the command.
    # For now, let's just make sure it doesn't crash.

    # Inject config into args
    # This allows commands to access config via args.config
    setattr(args, "config", config)

    root_path = Path(args.path).resolve()

    # Safety check for root directory
    if root_path == Path(root_path.anchor):
        console.print(f"[bold red]⚠️  Safety Warning: You are running relm in the system root ({root_path}).[/bold red]")
        console.print("[red]This is highly discouraged and may cause performance issues or unintended side effects.[/red]")
        
        # Check if we can skip confirmation (only valid for commands that support -y)
        auto_yes = getattr(args, "yes", False)
        
        if not auto_yes:
             response = console.input("[yellow]Are you sure you want to continue? (y/N): [/yellow]")
             if response.lower() != "y":
                 sys.exit(1)

    if hasattr(args, "func"):
        args.func(args, console)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
