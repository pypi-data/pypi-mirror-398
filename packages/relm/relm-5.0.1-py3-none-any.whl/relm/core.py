# src/relm/core.py

import os
import tomllib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set, Dict

@dataclass
class Project:
    name: str
    version: str
    path: Path
    description: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    @property
    def pyproject_path(self) -> Path:
        return self.path / "pyproject.toml"

    def __str__(self) -> str:
        return f"{self.name} (v{self.version}) - {self.path}"

def _parse_package_name(dep_string: str) -> str:
    """
    Extracts the package name from a dependency string.
    E.g., "lib-b>=1.0.0" -> "lib-b"
          "requests[security]" -> "requests"
    """
    # PEP 508 parsing is complex, but for basic sorting we just need the name.
    # Name typically ends at the first non-alphanumeric/hyphen/underscore/dot character
    # that indicates a version specifier or extra.
    match = re.match(r"^([A-Za-z0-9_\-\.]+)", dep_string)
    if match:
        return match.group(1).lower()
    return dep_string.lower()

def load_project(path: Path) -> Optional[Project]:
    """
    Loads a project from a directory if it contains a valid pyproject.toml.
    """
    pyproject_file = path / "pyproject.toml"
    if not pyproject_file.exists():
        return None

    try:
        with open(pyproject_file, "rb") as f:
            data = tomllib.load(f)
        
        project_data = data.get("project", {})
        name = project_data.get("name")
        version = project_data.get("version")
        description = project_data.get("description")
        dependencies = project_data.get("dependencies", [])

        # Also check optional-dependencies (extras) if we want deep dependency awareness?
        # The prompt only mentioned building lib-a before app-b, which usually implies
        # direct dependencies. Let's stick to core dependencies for now to keep it simple.

        if name and version:
            # Normalize dependencies to simple names
            parsed_deps = [_parse_package_name(d) for d in dependencies]

            return Project(
                name=name,
                version=version,
                path=path,
                description=description,
                dependencies=parsed_deps
            )
    except Exception as e:
        # We might want to log this error in a real app
        pass
    
    return None

def find_projects(root_path: Path, recursive: bool = False, max_depth: int = 1) -> List[Project]:
    """
    Scans root_path for valid projects. 
    If recursive is False, only scans root and immediate subdirectories (depth 1).
    If recursive is True, scans up to max_depth.
    """
    projects = []
    if not root_path.exists() or not root_path.is_dir():
        return projects

    IGNORE_DIRS = {
        "node_modules", "venv", ".venv", "env", ".env", "dist", "build", ".git",
        "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", "site-packages"
    }

    root_path = root_path.resolve()

    for root, dirs, files in os.walk(root_path):
        current_path = Path(root).resolve()
        
        try:
            rel_path = current_path.relative_to(root_path)
            current_depth = len(rel_path.parts)
        except ValueError:
            continue

        # Filter directories in-place to prevent recursion into ignored folders
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

        # Stop recursion if we exceed max_depth
        if not recursive and current_depth >= 1:
            dirs[:] = []
            if current_depth > 1:
                continue
        
        if recursive and current_depth >= max_depth:
            dirs[:] = []
        
        if "pyproject.toml" in files:
            project = load_project(current_path)
            if project:
                projects.append(project)

    return sorted(projects, key=lambda p: p.name)

def sort_projects_by_dependency(projects: List[Project]) -> List[Project]:
    """
    Sorts projects topologically based on their dependencies.
    Projects with no dependencies (or only external ones) come first.
    """
    project_map: Dict[str, Project] = {p.name.lower(): p for p in projects}

    # Build graph: node -> list of dependencies (that are in the workspace)
    graph: Dict[str, Set[str]] = {}

    for p in projects:
        p_name = p.name.lower()
        graph[p_name] = set()
        for dep in p.dependencies:
            dep_name = dep.lower()
            if dep_name in project_map:
                graph[p_name].add(dep_name)

    # Kahn's Algorithm
    result = []
    # Find all nodes with no incoming edges (here, no dependencies)
    # Actually for build order: if A depends on B, we need B first.
    # So "incoming edge" depends on how we view the graph.
    # Standard: A -> B means A depends on B.
    # We want B, then A.
    # So we are looking for nodes with out-degree 0 (no dependencies) to be first?
    # No, wait.
    # A -> B.
    # Valid order: B, A.
    # So we output nodes whose dependencies have all been outputted.

    # Let's use standard topo sort where we visit nodes.
    # Or just use the "visit" logic (DFS post-order).

    visited = set()
    temp_marked = set()
    sorted_list = []

    def visit(n: str):
        if n in temp_marked:
            # Instead of raising ValueError, we'll just log a warning and break the cycle
            # This is less "correct" but more "useful" for complex monorepos.
            from rich.console import Console
            Console().print(f"[yellow]⚠️  Warning: Circular dependency detected involving {n}. Sorting may be non-deterministic for this cluster.[/yellow]")
            return
        if n in visited:
            return

        temp_marked.add(n)

        # Visit all dependencies first
        for dep in graph.get(n, []):
            visit(dep)

        temp_marked.remove(n)
        visited.add(n)
        sorted_list.append(n)

    # We need to ensure we visit all nodes.
    # Sort keys to ensure deterministic order for independent chains.
    for name in sorted(project_map.keys()):
        if name not in visited:
            visit(name)

    # Convert back to Project objects
    return [project_map[name] for name in sorted_list]
