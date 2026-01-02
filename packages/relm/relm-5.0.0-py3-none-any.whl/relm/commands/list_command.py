import argparse
from argparse import Namespace, _SubParsersAction
from pathlib import Path
from rich.console import Console
from rich.table import Table
from ..core import find_projects
from ..git_ops import git_has_changes_since

def register(subparsers: _SubParsersAction, base_parser: argparse.ArgumentParser):
    """Register the list command."""
    list_parser = subparsers.add_parser("list", help="List all discovered projects", parents=[base_parser])
    list_parser.add_argument("--since", help="List only projects changed since the given git ref")
    list_parser.set_defaults(func=execute)

def execute(args: Namespace, console: Console):
    """Execute the list command."""
    root_path = Path(args.path).resolve()
    projects = find_projects(
        root_path, 
        recursive=getattr(args, "recursive", False), 
        max_depth=getattr(args, "depth", 2)
    )

    if args.since:
        projects = [p for p in projects if git_has_changes_since(p.path, args.since)]

    if not projects:
        console.print("[yellow]No projects found in this directory.[/yellow]")
        return

    table = Table(title=f"Found {len(projects)} Projects")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Version", style="magenta")
    table.add_column("Path", style="green")
    table.add_column("Description")

    for project in projects:
        table.add_row(
            project.name,
            project.version,
            str(project.path),
            project.description or ""
        )

    console.print(table)
