from typing import Optional
from .core import Project
from .git_ops import run_git_gc

def gc_project(project: Project) -> bool:
    """
    Run git gc on a project.
    Returns True if successful, False otherwise.
    """
    try:
        run_git_gc(project.path)
        return True
    except Exception:
        # We catch Exception here because run_git_gc might raise CalledProcessError
        # or other errors.
        return False
