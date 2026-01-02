import argparse
import sys
from argparse import Namespace, _SubParsersAction
from pathlib import Path
from rich.console import Console
from ..core import find_projects, sort_projects_by_dependency
from ..release import perform_release

def register(subparsers: _SubParsersAction, base_parser: argparse.ArgumentParser):
    """Register the release command."""
    release_parser = subparsers.add_parser("release", help="Release a new version of a project", parents=[base_parser])
    release_parser.add_argument("project_name", help="Name of the project to release (must match pyproject.toml name)")
    release_parser.add_argument("type", choices=["major", "minor", "patch", "alpha", "beta", "rc", "release"], default="patch", nargs="?", help="Type of version bump")
    release_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompts (assume yes)")
    release_parser.add_argument("-m", "--message", default="release: bump version to {version}", help="Custom commit message template (e.g., 'chore: release {version}')")
    release_parser.set_defaults(func=execute)

def execute(args: Namespace, console: Console):
    """Execute the release command."""
    root_path = Path(args.path).resolve()
    all_projects = find_projects(
        root_path,
        recursive=getattr(args, "recursive", False),
        max_depth=getattr(args, "depth", 2)
    )

    target_projects = []
    check_changes_flag = False

    if args.project_name == "all":
        try:
            target_projects = sort_projects_by_dependency(all_projects)
        except ValueError as e:
            console.print(f"[red]Dependency sorting failed: {e}[/red]")
            sys.exit(1)

        check_changes_flag = True
        console.print(f"[bold]Running Bulk Release on {len(target_projects)} projects...[/bold]")
    else:
        # Find single project
        target = next((p for p in all_projects if p.name == args.project_name), None)
        if not target:
            console.print(f"[red]Project '{args.project_name}' not found in {root_path}[/red]")
            sys.exit(1)
        target_projects = [target]

    # Execute releases
    results = {"released": [], "skipped": [], "failed": []}

    for project in target_projects:
        # Skip template/meta repos if needed, but git_has_changes handles most logic
        try:
            success = perform_release(
                project,
                args.type,
                yes_mode=args.yes,
                check_changes=check_changes_flag,
                commit_template=args.message
            )
            if success:
                results["released"].append(project.name)
            else:
                results["skipped"].append(project.name)
        except Exception as e:
            console.print(f"[red]Critical error releasing {project.name}: {e}[/red]")
            results["failed"].append(project.name)

    # Summary
    if args.project_name == "all":
        console.rule("Bulk Release Summary")
        console.print(f"[green]Released: {len(results['released'])}[/green] {results['released']}")
        console.print(f"[yellow]Skipped:  {len(results['skipped'])}[/yellow]")
        if results["failed"]:
            console.print(f"[red]Failed:   {len(results['failed'])}[/red] {results['failed']}")
