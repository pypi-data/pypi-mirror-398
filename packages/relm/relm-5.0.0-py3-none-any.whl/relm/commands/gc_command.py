import argparse
import sys
from argparse import Namespace, _SubParsersAction
from pathlib import Path
from rich.console import Console
from ..core import find_projects
from ..gc import gc_project

def register(subparsers: _SubParsersAction, base_parser: argparse.ArgumentParser):
    """Register the gc command."""
    gc_parser = subparsers.add_parser("gc", help="Run git gc on project(s)", parents=[base_parser])
    gc_parser.add_argument("project_name", help="Name of the project to gc or 'all'", nargs="?", default="all")
    gc_parser.set_defaults(func=execute)

def execute(args: Namespace, console: Console):
    """Execute the gc command."""
    root_path = Path(args.path).resolve()
    all_projects = find_projects(root_path)
    target_projects = []

    if args.project_name == "all":
        target_projects = all_projects
        console.print(f"[bold]Running git gc for {len(target_projects)} projects...[/bold]")
    else:
        target = next((p for p in all_projects if p.name == args.project_name), None)
        if not target:
            console.print(f"[red]Project '{args.project_name}' not found in {root_path}[/red]")
            sys.exit(1)
        target_projects = [target]

    success_count = 0
    failure_count = 0

    for project in target_projects:
        console.print(f"Running git gc in [bold]{project.path}[/bold]...")
        if gc_project(project):
            console.print(f"[green]Successfully ran git gc for {project.name}[/green]")
            success_count += 1
        else:
            console.print(f"[red]Failed to run git gc for {project.name}[/red]")
            failure_count += 1

    console.rule("GC Summary")
    if failure_count > 0:
        console.print(f"[bold red]Completed with failures.[/bold red]")
        console.print(f"Success: {success_count}, Failures: {failure_count}")
        # Note: We don't exit with 1 here for 'all' as per requirements to "continue",
        # but usually a tool might return non-zero if partial failure.
        # For now, I'll exit 0 as long as the process completed, unless user requested a specific one and it failed.
        if args.project_name != "all" and failure_count > 0:
             sys.exit(1)
    else:
        console.print(f"[bold green]Successfully ran git gc on {success_count} projects.[/bold green]")
