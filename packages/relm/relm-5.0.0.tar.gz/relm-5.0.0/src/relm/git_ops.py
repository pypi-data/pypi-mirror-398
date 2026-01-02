# src/relm/git_ops.py

import subprocess
from pathlib import Path
from typing import List

def run_git_command(args: List[str], cwd: Path) -> str:
    """
    Runs a git command in the specified directory.
    Raises subprocess.CalledProcessError on failure.
    """
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

def is_git_clean(path: Path) -> bool:
    """
    Checks if the git repository is clean (no uncommitted changes).
    """
    try:
        # update-index -q --refresh is good practice before diff-index
        subprocess.run(["git", "update-index", "-q", "--refresh"], cwd=path, check=False)
        # check for unstaged changes
        subprocess.run(["git", "diff-files", "--quiet"], cwd=path, check=True)
        # check for staged changes
        subprocess.run(["git", "diff-index", "--cached", "--quiet", "HEAD", "--"], cwd=path, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def git_add(path: Path, files: List[str]):
    run_git_command(["add"] + files, cwd=path)

def git_commit(path: Path, message: str):
    run_git_command(["commit", "-m", message], cwd=path)

def git_tag(path: Path, tag_name: str, message: str = None):
    args = ["tag", tag_name]
    if message:
        args.extend(["-m", message])
    run_git_command(args, cwd=path)

def git_push(path: Path):
    run_git_command(["push"], cwd=path)
    run_git_command(["push", "--tags"], cwd=path)

def git_fetch_tags(path: Path):
    """
    Fetches tags from the remote to ensure local knowledge is up to date.
    """
    run_git_command(["fetch", "--tags"], cwd=path)

def git_tag_exists(path: Path, tag_name: str) -> bool:
    """
    Checks if a specific tag exists locally.
    """
    try:
        # git rev-parse -q --verify "refs/tags/v1.0.0"
        run_git_command(["rev-parse", "-q", "--verify", f"refs/tags/{tag_name}"], cwd=path)
        return True
    except subprocess.CalledProcessError:
        return False

def git_has_changes(path: Path, tag_name: str) -> bool:
    """
    Checks if there are changes between the given tag and HEAD.
    Returns True if changes exist, False otherwise.
    """
    try:
        # git diff --quiet tag_name HEAD -- .
        # If exit code is 1, there are changes. If 0, no changes.
        # We use check=True which raises error on non-zero... wait.
        # diff --quiet returns 1 if diffs found. So we want to catch the error.
        
        subprocess.run(
            ["git", "diff", "--quiet", tag_name, "HEAD", "--", "."],
            cwd=path,
            check=True
        )
        return False # Exit code 0 means NO differences
    except subprocess.CalledProcessError:
        return True # Exit code 1 means differences exist (or error, but usually diffs)

def get_current_branch(path: Path) -> str:
    """
    Returns the name of the current git branch.
    """
    try:
        return run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], cwd=path)
    except subprocess.CalledProcessError:
        return "unknown"

def get_commit_log(path: Path) -> List[str]:
    """
    Returns the list of commit messages since the last tag.
    """
    try:
        # Get the latest tag
        last_tag = run_git_command(["describe", "--tags", "--abbrev=0"], cwd=path)
        # Get commits between last tag and HEAD
        # Format %s returns just the subject
        log_output = run_git_command(["log", f"{last_tag}..HEAD", "--pretty=format:%s"], cwd=path)
        return log_output.splitlines()
    except subprocess.CalledProcessError:
        # Fallback if no tags exist: return all commits
        try:
            log_output = run_git_command(["log", "--pretty=format:%s"], cwd=path)
            return log_output.splitlines()
        except subprocess.CalledProcessError:
            return []

def git_has_changes_since(path: Path, ref: str) -> bool:
    """
    Checks if there are changes between the given ref and HEAD in the path.
    Returns True if changes exist, False otherwise.
    """
    try:
        subprocess.run(
            ["git", "diff", "--quiet", ref, "HEAD", "--", "."],
            cwd=path,
            check=True
        )
        return False
    except subprocess.CalledProcessError:
        return True

def run_git_gc(path: Path):
    """
    Runs git gc in the specified directory.
    """
    # git gc is verbose on stderr usually, but we want it to just run.
    # We use check=True to raise error if it fails.
    # We allow stdout/stderr to pass through if captured by run_git_command or similar,
    # but here we might want to capture it or just run it.
    # Using run_git_command which captures output.
    # But wait, run_git_command returns stdout. git gc often prints to stderr.
    # Let's use subprocess directly to better control or use run_git_command and ignore output?
    # run_git_command uses capture_output=True.

    run_git_command(["gc"], cwd=path)
