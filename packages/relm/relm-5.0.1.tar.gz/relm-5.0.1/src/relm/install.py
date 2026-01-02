# src/relm/install.py

import sys
import subprocess
from rich.console import Console
from .core import Project

console = Console()

def install_project(project: Project, editable: bool = True) -> bool:
    """
    Installs the project using pip in the current environment.
    Returns True if successful, False otherwise.
    """
    mode_str = "editable" if editable else "standard"
    console.print(f"[blue]Installing {project.name} in {mode_str} mode...[/blue]")
    
    cmd = [sys.executable, "-m", "pip", "install"]
    if editable:
        cmd.append("-e")
    cmd.append(".")

    try:
        # We allow stdout/stderr to flow to the console so the user sees pip's progress
        subprocess.run(
            cmd,
            cwd=project.path,
            check=True
        )
        console.print(f"[green]Successfully installed {project.name}[/green]")
        return True
    except subprocess.CalledProcessError:
        console.print(f"[red]Failed to install {project.name}[/red]")
        return False
