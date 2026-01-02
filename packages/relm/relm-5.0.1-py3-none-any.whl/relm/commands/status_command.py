import argparse
import sys
from argparse import Namespace, _SubParsersAction
from pathlib import Path
from rich.console import Console
from rich.table import Table
from ..core import find_projects
from ..git_ops import is_git_clean, get_current_branch

def register(subparsers: _SubParsersAction, base_parser: argparse.ArgumentParser):
    """Register the status command."""
    status_parser = subparsers.add_parser("status", help="Check git status of projects", parents=[base_parser])
    status_parser.add_argument("project_name", help="Name of the project to check or 'all'", nargs="?", default="all")
    status_parser.set_defaults(func=execute)

def execute(args: Namespace, console: Console):
    """Execute the status command."""
    root_path = Path(args.path).resolve()
    all_projects = find_projects(
        root_path,
        recursive=getattr(args, "recursive", False),
        max_depth=getattr(args, "depth", 2)
    )
    target_projects = []

    if args.project_name == "all":
        target_projects = all_projects
    else:
        # 1. Try path-based matching
        target_dir = (root_path / args.project_name).resolve()
        if target_dir.exists() and target_dir.is_dir():
            target_projects = [
                p for p in all_projects 
                if p.path.resolve() == target_dir or target_dir in p.path.resolve().parents
            ]
            if target_projects:
                console.print(f"[bold]Targeting {len(target_projects)} projects in folder: [cyan]{args.project_name}[/cyan][/bold]")

        # 2. Try exact name match
        if not target_projects:
            target = next((p for p in all_projects if p.name == args.project_name), None)
            if not target:
                console.print(f"[red]Project or folder '{args.project_name}' not found in {root_path}[/red]")
                sys.exit(1)
            target_projects = [target]

    table = Table(title=f"Git Status for {len(target_projects)} Projects")
    table.add_column("Project", style="cyan", no_wrap=True)
    table.add_column("Version", style="magenta")
    table.add_column("Branch", style="blue")
    table.add_column("Status", style="bold")

    for project in target_projects:
        branch = get_current_branch(project.path)
        is_clean = is_git_clean(project.path)

        status_str = "[green]Clean[/green]" if is_clean else "[red]Dirty[/red]"
        # Check for potential conflict markers if dirty (simple heuristic) or just leave as Dirty

        table.add_row(
            project.name,
            project.version,
            branch,
            status_str
        )

    console.print(table)
