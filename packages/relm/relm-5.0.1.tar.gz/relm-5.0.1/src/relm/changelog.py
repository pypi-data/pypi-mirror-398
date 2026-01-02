from typing import List, Dict
from pathlib import Path
from datetime import datetime
from .git_ops import get_commit_log

def parse_commits(commits: List[str]) -> Dict[str, List[str]]:
    """
    Parses a list of commit messages and groups them by type.
    """
    groups = {
        "Features": [],
        "Bug Fixes": [],
        "Documentation": [],
        "Other Changes": []
    }

    for commit in commits:
        parts = commit.split(":", 1)
        if len(parts) != 2:
            continue

        type_scope = parts[0].strip()
        message = parts[1].strip()

        scope = ""
        commit_type = type_scope

        # Extract type and scope
        if "(" in type_scope and type_scope.endswith(")"):
            commit_type_part = type_scope.split("(", 1)
            commit_type = commit_type_part[0]
            scope = commit_type_part[1][:-1] # remove trailing )

        final_message = f"**{scope}:** {message}" if scope else message

        if commit_type == "feat":
            groups["Features"].append(final_message)
        elif commit_type == "fix":
            groups["Bug Fixes"].append(final_message)
        elif commit_type == "docs":
            groups["Documentation"].append(final_message)
        else:
            groups["Other Changes"].append(final_message)

    return groups

def generate_changelog_content(version: str, date: str, groups: Dict[str, List[str]]) -> str:
    """
    Generates the changelog content for a specific version.
    """
    content = [f"## [{version}] - {date}"]

    for section, messages in groups.items():
        if messages:
            content.append(f"### {section}")
            for msg in messages:
                content.append(f"- {msg}")

    return "\n".join(content) + "\n"

def update_changelog_file(path: Path, new_entry: str):
    """
    Updates the CHANGELOG.md file by prepending the new entry.
    """
    current_content = ""
    if path.exists():
        current_content = path.read_text()

    # Check for idempotency
    # If the new entry version header is already present, we might be re-running.
    # new_entry starts with "## [version] - date"
    version_line = new_entry.splitlines()[0]
    # To be safe, just check if the version tag is in the content?
    # Or strict check? Strict check is safer.
    # Extract version from new_entry
    # "## [1.2.0] - ..."
    if version_line in current_content:
        # Already exists, do nothing or replace?
        # For safety in this tool, we will assume if it exists, we skip or warn.
        # But maybe we want to regenerate it?
        # Let's simple return to avoid duplication for now.
        return

    header = "# Changelog\n\n"

    if not current_content.strip():
        # Empty file
        new_content = header + new_entry
    elif current_content.startswith("# Changelog"):
        # Find the first H2
        if "\n## [" in current_content:
             parts = current_content.split("\n## [", 1)
             new_content = parts[0] + "\n" + new_entry + "\n## [" + parts[1]
        else:
             # Header exists but no entries or non-standard
             if current_content.strip() == "# Changelog":
                 new_content = header + new_entry
             elif current_content.startswith(header):
                 rest = current_content[len(header):]
                 new_content = header + new_entry + "\n" + rest
             else:
                 # It starts with # Changelog but maybe different spacing
                 # Just append after first line?
                 lines = current_content.splitlines()
                 new_content = lines[0] + "\n\n" + new_entry + "\n" + "\n".join(lines[1:])
    else:
        new_content = header + new_entry + "\n" + current_content

    path.write_text(new_content)

def generate_changelog(project_path: Path, version: str) -> str:
    """
    Orchestrates the changelog generation process.
    Returns the generated changelog content.
    """
    commits = get_commit_log(project_path)
    parsed = parse_commits(commits)
    date_str = datetime.now().strftime("%Y-%m-%d")
    content = generate_changelog_content(version, date_str, parsed)

    changelog_path = project_path / "CHANGELOG.md"
    update_changelog_file(changelog_path, content)
    return content
