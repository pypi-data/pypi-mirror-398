import argparse
import os
from argparse import Namespace, _SubParsersAction
from pathlib import Path
from rich.console import Console

def register(subparsers: _SubParsersAction, base_parser: argparse.ArgumentParser):
    """Register the create command."""
    create_parser = subparsers.add_parser("create", help="Create a new Python project", parents=[base_parser])
    create_parser.add_argument("name", help="Name of the new project")

def execute(args: Namespace, console: Console):
    """Execute the create command."""
    project_name = args.name
    # If path is provided, use it. Otherwise use CWD.
    base_path = Path(args.path) if args.path else Path.cwd()
    project_dir = base_path / project_name

    if project_dir.exists():
        console.print(f"[red]Error: Directory {project_dir} already exists.[/red]")
        return

    console.print(f"[green]Creating project {project_name} at {project_dir}...[/green]")

    # Create directories
    (project_dir / "src" / project_name).mkdir(parents=True)
    (project_dir / "tests").mkdir(parents=True)

    # Create files
    create_pyproject_toml(project_dir, project_name)
    create_readme(project_dir, project_name)
    create_gitignore(project_dir)
    (project_dir / "src" / project_name / "__init__.py").touch()
    (project_dir / "tests" / "__init__.py").touch()

    console.print(f"[bold green]Project {project_name} created successfully! 🚀[/bold green]")

def create_pyproject_toml(path: Path, name: str):
    content = f"""[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "0.1.0"
description = "A new project created with relm"
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Programming Language :: Python :: 3",
]
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest",
]
"""
    (path / "pyproject.toml").write_text(content)

def create_readme(path: Path, name: str):
    content = f"""# {name}

A new project created with [relm](https://github.com/relm-tool/relm).
"""
    (path / "README.md").write_text(content)

def create_gitignore(path: Path):
    content = """
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
"""
    (path / ".gitignore").write_text(content)
