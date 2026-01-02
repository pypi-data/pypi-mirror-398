import shutil
from pathlib import Path
from typing import List
from .core import Project

def clean_project(project: Project) -> List[Path]:
    """
    Recursively remove build artifacts from a project.

    Targets:
    - dist/ (at project root)
    - build/ (at project root)
    - __pycache__/ (recursive)
    """
    cleaned_paths = []

    # 1. Clean root level artifacts
    root_artifacts = ["dist", "build"]
    for artifact in root_artifacts:
        artifact_path = project.path / artifact
        if artifact_path.exists() and artifact_path.is_dir():
            shutil.rmtree(artifact_path)
            cleaned_paths.append(artifact_path)

    # 2. Recursive clean of __pycache__
    for path in project.path.rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path)
            cleaned_paths.append(path)

    return cleaned_paths
