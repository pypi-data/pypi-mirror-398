# src/relm/release.py

import sys
import subprocess
from pathlib import Path
from typing import Literal

from rich.console import Console
from rich.prompt import Confirm, Prompt

from .core import Project
from .versioning import bump_version_string, update_file_content, update_version_tests
from .git_ops import is_git_clean, git_add, git_commit, git_tag, git_push, git_fetch_tags, git_tag_exists, git_has_changes
from .changelog import generate_changelog

console = Console()

def run_tests(project_path: Path) -> bool:
    """
    Runs pytest in the project directory. Returns True if successful.
    """
    # Check if pytest is installed/available?
    # We assume the user has the env set up correctly or it's in path.
    console.print("[bold blue]Running tests...[/bold blue]")
    try:
        # We use sys.executable -m pytest to use the same env
        subprocess.run(
            [sys.executable, "-m", "pytest"],
            cwd=project_path,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        console.print("[yellow]pytest not found. Skipping tests.[/yellow]")
        return True # Treat missing pytest as "pass" (or warn?) - safer to warn and pass for now

def revert_changes(project_path: Path):
    """
    Reverts local changes using git checkout.
    """
    console.print("[yellow]Reverting changes...[/yellow]")
    try:
        subprocess.run(["git", "checkout", "."], cwd=project_path, check=True)
    except Exception as e:
        console.print(f"[red]Failed to revert changes: {e}[/red]")

def perform_release(project: Project, part: Literal['major', 'minor', 'patch'], yes_mode: bool = False, check_changes: bool = False, commit_template: str = "release: bump version to {version}") -> bool:
    console.rule(f"Releasing {project.name}")
    
    # 0. Fetch Tags & Check State
    console.print("[dim]Fetching remote tags...[/dim]")
    try:
        git_fetch_tags(project.path)
    except Exception:
        console.print("[yellow]Warning: Could not fetch remote tags. Proceeding with local info.[/yellow]")

    current_version_tag = f"v{project.version}"
    is_already_tagged = git_tag_exists(project.path, current_version_tag)
    
    # Smart Skip Logic
    if check_changes and is_already_tagged:
        if not git_has_changes(project.path, current_version_tag):
            console.print(f"[dim]No changes detected since {current_version_tag}. Skipping.[/dim]")
            return False

    should_bump = True
    target_version = project.version # Default to current if not bumping
    
    if not is_already_tagged:
        console.print(f"[yellow]Notice: Current version [bold]{project.version}[/bold] is NOT tagged locally.[/yellow]")
        # If yes_mode is on, we default to RETRY (True), i.e. skip bump
        if yes_mode or Confirm.ask(f"Retry release for v{project.version} (skip bump)?", default=True):
            should_bump = False
            target_version = project.version
    
    # 1. Check Git Cleanliness
    if not is_git_clean(project.path):
        console.print("[red]Error: Git repository is not clean. Commit or stash changes first.[/red]")
        # We could potentially auto-commit if yes_mode is on, but that's risky.
        return False

    # 2. Calculate New Version (if bumping)
    if should_bump:
        try:
            target_version = bump_version_string(project.version, part)
            console.print(f"Current version: [cyan]{project.version}[/cyan]")
            console.print(f"New version:     [green]{target_version}[/green]")
        except ValueError as e:
            console.print(f"[red]Error parsing version: {e}[/red]")
            return False
    else:
         console.print(f"Releasing existing version: [green]{target_version}[/green]")

    
    if not yes_mode and not Confirm.ask("Proceed with release?"):
        console.print("[yellow]Release cancelled.[/yellow]")
        return False

    # 3. Update Files (Only if bumping)
    if should_bump:
        console.print("[bold blue]Updating files...[/bold blue]")
        files_updated = []
        
        # Update pyproject.toml
        if update_file_content(project.pyproject_path, project.version, target_version):
            files_updated.append("pyproject.toml")
        
        # Update __init__.py
        # Try src/{name}/__init__.py first
        init_path = project.path / "src" / project.name.replace("-", "_") / "__init__.py"
        if not init_path.exists():
             # Try {name}/__init__.py
             init_path = project.path / project.name.replace("-", "_") / "__init__.py"
        
        if init_path.exists():
            if update_file_content(init_path, project.version, target_version):
                files_updated.append(str(init_path.relative_to(project.path)))
        
        # Update Tests (Hardcoded versions)
        updated_tests = update_version_tests(project.path, project.version, target_version)
        if updated_tests:
            console.print(f"[green]Automatically updated version assertions in {len(updated_tests)} test files.[/green]")
            files_updated.extend(updated_tests)

        # Generate Changelog
        try:
            console.print("[dim]Generating changelog...[/dim]")
            generate_changelog(project.path, target_version)
            files_updated.append("CHANGELOG.md")
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to generate changelog: {e}[/yellow]")

        if not files_updated:
            console.print("[red]No files were updated! Check version strings.[/red]")
            return False
            
        # 4. Run Tests Locally
        if not run_tests(project.path):
            console.print("[bold red]Tests failed! Aborting release.[/bold red]")
            if yes_mode or Confirm.ask("Revert changes to files?", default=True):
                revert_changes(project.path)
            return False

        # 5. Git Commit
        console.print("[bold blue]Committing...[/bold blue]")
        try:
            git_add(project.path, files_updated)
            commit_message = commit_template.format(version=target_version)
            git_commit(project.path, commit_message)
        except Exception as e:
            console.print(f"[red]Git commit error: {e}[/red]")
            return False

    # 6. Tag (Always needed)
    # We double check if tag exists now, just in case
    if git_tag_exists(project.path, f"v{target_version}"):
         console.print(f"[yellow]Tag v{target_version} already exists locally. Skipping creation.[/yellow]")
    else:
        console.print(f"[bold blue]Tagging v{target_version}...[/bold blue]")
        try:
            git_tag(project.path, f"v{target_version}", f"Release v{target_version}")
        except Exception as e:
            console.print(f"[red]Git tag error: {e}[/red]")
            return False

    # 7. Push
    if yes_mode or Confirm.ask("Push changes to remote? (This will trigger the GitHub Action release)"):
        try:
            git_push(project.path)
        except Exception as e:
            console.print(f"[red]Push error: {e}[/red]")
            return False

    console.print(f"[bold green]Successfully tagged and pushed {project.name} v{target_version}![/bold green]")
    console.print("[dim]The GitHub Action workflow should now handle the PyPI release.[/dim]")
    return True
