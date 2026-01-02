import json
import subprocess
from typing import Tuple
from rich.console import Console
from .core import Project
from .git_ops import git_tag_exists

console = Console()

def verify_project_release(project: Project) -> Tuple[bool, str]:
    """
    Verifies if the locally defined version of the project is available on PyPI.
    Returns (success: bool, message: str).
    """
    local_version = project.version
    tag_name = f"v{local_version}"
    
    # 1. Check if local tag exists (Strict check as requested)
    if not git_tag_exists(project.path, tag_name):
        return False, f"Local git tag '{tag_name}' does not exist. Was the release command run?"

    # 2. Query PyPI using pip
    try:
        # We run with --json to get machine readable output
        result = subprocess.run(
            [
                "pip", 
                "index", 
                "versions", 
                project.name, 
                "--json"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        data = json.loads(result.stdout)
        available_versions = data.get("versions", [])
        
        if local_version in available_versions:
            return True, f"Version {local_version} is verified on PyPI."
        else:
            return False, f"Version {local_version} not found on PyPI. Latest is {data.get('latest', 'unknown')}."

    except subprocess.CalledProcessError:
        return False, f"Failed to query PyPI for '{project.name}'. Package might not be published yet."
    except json.JSONDecodeError:
        return False, "Failed to parse pip output."
    except Exception as e:
        return False, f"Unexpected error: {e}"
