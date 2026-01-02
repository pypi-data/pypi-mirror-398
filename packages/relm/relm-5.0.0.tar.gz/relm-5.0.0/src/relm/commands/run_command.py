import argparse
import sys
from argparse import Namespace, _SubParsersAction
from pathlib import Path
from rich.console import Console
from ..core import find_projects, sort_projects_by_dependency
from ..runner import run_project_command

def register(subparsers: _SubParsersAction, base_parser: argparse.ArgumentParser):
    """Register the run command."""
    run_parser = subparsers.add_parser("run", help="Run a shell command across projects", parents=[base_parser])
    run_parser.add_argument("command_string", help="The shell command to execute")
    run_parser.add_argument("project_name", nargs="?", default="all", help="Name of the project to run on or 'all'")
    run_parser.add_argument("--fail-fast", action="store_true", help="Stop execution if a command fails")
    run_parser.set_defaults(func=execute)

def execute(args: Namespace, console: Console):
    """Execute the run command."""
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
        # 1. Try path-based matching (e.g. relm run "ls" packages)
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

    results = {"success": [], "failed": []}
    use_from_root = getattr(args, "from_root", False)
    cwd = root_path if use_from_root else None

    if getattr(args, "parallel", False):
        from ..runner import execute_in_parallel
        
        def cmd_provider(p):
            return args.command_string

        results_data = execute_in_parallel(
            target_projects,
            command_provider=cmd_provider,
            max_workers=args.jobs,
            fail_fast=args.fail_fast,
            cwd=cwd
        )
        
        for res in results_data:
            if res["success"]:
                results["success"].append(res["name"])
            else:
                results["failed"].append(res["name"])
                console.rule(f"[red]Output for FAILED project: {res['name']}[/red]")
                if res["stdout"]: console.print(res["stdout"])
                if res["stderr"]: console.print(res["stderr"], style="red")
    else:
        for project in target_projects:
            console.rule(f"Running on {project.name}")
            success = run_project_command(cwd or project.path, args.command_string)
            if success:
                results["success"].append(project.name)
            else:
                results["failed"].append(project.name)
                if args.fail_fast:
                    console.print(f"[red]Fail-fast enabled. Stopping execution.[/red]")
                    break

    console.rule("Execution Summary")
    if results["success"]:
        console.print(f"[green]Success: {len(results['success'])}[/green] {results['success']}")
    if results["failed"]:
        console.print(f"[red]Failed:  {len(results['failed'])}[/red] {results['failed']}")
        sys.exit(1)
