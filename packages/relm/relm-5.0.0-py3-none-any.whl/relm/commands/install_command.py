import argparse
import sys
from argparse import Namespace, _SubParsersAction
from pathlib import Path
from rich.console import Console
from ..core import find_projects, sort_projects_by_dependency
from ..install import install_project

def register(subparsers: _SubParsersAction, base_parser: argparse.ArgumentParser):
    """Register the install command."""
    install_parser = subparsers.add_parser("install", help="Install projects into the current environment", parents=[base_parser])
    install_parser.add_argument("project_name", help="Name of the project to install or 'all'")
    install_parser.add_argument("--no-editable", action="store_true", help="Install in standard mode instead of editable")
    install_parser.set_defaults(func=execute)

def execute(args: Namespace, console: Console):
    """Execute the install command."""
    root_path = Path(args.path).resolve()
    all_projects = find_projects(
        root_path,
        recursive=getattr(args, "recursive", False),
        max_depth=getattr(args, "depth", 2)
    )
    target_projects = []

    if args.project_name == "all":
        try:
            target_projects = sort_projects_by_dependency(all_projects)
            if getattr(args, "from_root", False):
                target_projects = [p for p in target_projects if p.path.resolve() != root_path.resolve()]
        except ValueError as e:
            console.print(f"[red]Dependency sorting failed: {e}[/red]")
            sys.exit(1)
    else:
        # 1. Try path-based matching
        target_dir = (root_path / args.project_name).resolve()
        if target_dir.exists() and target_dir.is_dir():
            target_projects = [
                p for p in all_projects 
                if p.path.resolve() == target_dir or target_dir in p.path.resolve().parents
            ]
            if target_projects:
                try:
                    target_projects = sort_projects_by_dependency(target_projects)
                except ValueError as e:
                    console.print(f"[red]Dependency sorting failed: {e}[/red]")
                    sys.exit(1)
                console.print(f"[bold]Targeting {len(target_projects)} projects in folder: [cyan]{args.project_name}[/cyan][/bold]")

        # 2. Try exact name match
        if not target_projects:
            target = next((p for p in all_projects if p.name == args.project_name), None)
            if not target:
                console.print(f"[red]Project or folder '{args.project_name}' not found in {root_path}[/red]")
                sys.exit(1)
            target_projects = [target]

    results = {"installed": [], "failed": []}
    editable_mode = not args.no_editable

    if getattr(args, "parallel", False):
        from ..runner import execute_in_parallel
        
        def cmd_provider(p):
            # We need to construct the pip install command manually for parallel runner
            # since install_project uses subprocess directly.
            mode = "-e" if editable_mode else ""
            return [sys.executable, "-m", "pip", "install", mode, "."]

        results_data = execute_in_parallel(
            target_projects,
            command_provider=cmd_provider,
            max_workers=args.jobs,
            fail_fast=True # Always fail-fast for installation dependencies
        )
        
        for res in results_data:
            if res["success"]:
                results["installed"].append(res["name"])
            else:
                results["failed"].append(res["name"])
                console.rule(f"[red]Install FAILED for: {res['name']}[/red]")
                if res["stdout"]: console.print(res["stdout"])
                if res["stderr"]: console.print(res["stderr"], style="red")
    else:
        for project in target_projects:
            success = install_project(project, editable=editable_mode)
            if success:
                results["installed"].append(project.name)
            else:
                results["failed"].append(project.name)

    if args.project_name == "all":
        console.rule("Bulk Install Summary")
        console.print(f"[green]Installed: {len(results['installed'])}[/green] {results['installed']}")
        if results["failed"]:
            console.print(f"[red]Failed:    {len(results['failed'])}[/red] {results['failed']}")
