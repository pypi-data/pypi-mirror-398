import argparse
import sys
from argparse import Namespace, _SubParsersAction
from pathlib import Path
from rich.console import Console
from rich.table import Table
from ..core import find_projects
from ..verify import verify_project_release

def register(subparsers: _SubParsersAction, base_parser: argparse.ArgumentParser):
    """Register the verify command."""
    verify_parser = subparsers.add_parser("verify", help="Verify if the local release is available on PyPI", parents=[base_parser])
    verify_parser.add_argument("project_name", help="Name of the project to verify or 'all'", nargs="?", default="all")
    verify_parser.set_defaults(func=execute)

def execute(args: Namespace, console: Console):
    """Execute the verify command."""
    root_path = Path(args.path).resolve()
    all_projects = find_projects(
        root_path,
        recursive=getattr(args, "recursive", False),
        max_depth=getattr(args, "depth", 2)
    )
    target_projects = []

    if args.project_name == "all":
        target_projects = all_projects
        if getattr(args, "from_root", False):
            target_projects = [p for p in target_projects if p.path.resolve() != root_path.resolve()]
        console.print(f"[bold]Verifying PyPI availability for {len(target_projects)} projects...[/bold]")
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

    results = {"verified": [], "failed": []}

    table = Table(title=f"PyPI Verification Status for {len(target_projects)} Projects")
    table.add_column("Project", style="cyan", no_wrap=True)
    table.add_column("Version", style="magenta")
    table.add_column("Status", style="bold")
    table.add_column("Details")

    with console.status(f"[bold green]Verifying {len(target_projects)} projects...[/bold green]"):
        for project in target_projects:
            success, message = verify_project_release(project)
            if success:
                results["verified"].append(project.name)
                status_str = "[green]Verified[/green]"
            else:
                results["failed"].append(project.name)
                status_str = "[red]Failed[/red]"

            table.add_row(
                project.name,
                project.version,
                status_str,
                message
            )

    console.print(table)

    if args.project_name == "all":
        console.rule("Verification Summary")
        console.print(f"[green]Verified: {len(results['verified'])}[/green]")
        if results["failed"]:
            console.print(f"[red]Failed:   {len(results['failed'])}[/red]")
