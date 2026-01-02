# src/relm/versioning.py

import re
from pathlib import Path
from typing import Tuple, List, Optional, Union

# Regex for parsing version strings like "1.0.0", "1.0.0-alpha.1", "1.0.0-rc.2"
# Supports standard SemVer-ish format: major.minor.patch[-pre.n]
VERSION_PATTERN = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<pre_type>[a-zA-Z]+)\.(?P<pre_num>\d+))?$"
)

class Version:
    def __init__(self, major: int, minor: int, patch: int, pre_type: Optional[str] = None, pre_num: Optional[int] = None):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.pre_type = pre_type
        self.pre_num = pre_num

    def __str__(self):
        v = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_type and self.pre_num is not None:
            v += f"-{self.pre_type}.{self.pre_num}"
        return v

    def bump(self, part: str) -> "Version":
        major, minor, patch = self.major, self.minor, self.patch
        pre_type, pre_num = self.pre_type, self.pre_num

        if part in ["major", "minor", "patch"]:
            # Standard semantic versioning bumps reset pre-release information.
            pre_type = None
            pre_num = None

            if part == 'major':
                major += 1
                minor = 0
                patch = 0
            elif part == 'minor':
                minor += 1
                patch = 0
            elif part == 'patch':
                patch += 1

        elif part in ["alpha", "beta", "rc"]:
            # Prerelease logic
            # If we are not in a pre-release, we bump patch and add prerelease
            if not pre_type:
                patch += 1
                pre_type = part
                pre_num = 1
            else:
                if pre_type == part:
                    # Same prerelease type, increment number
                    if pre_num is None: pre_num = 1
                    pre_num += 1
                else:
                    # Changing prerelease type (e.g. alpha -> beta)
                    # Keep same version numbers, just change type and reset num
                    pre_type = part
                    pre_num = 1

        elif part == "release":
            # Strip pre-release info, keeping the same major.minor.patch numbers.
            # E.g. 1.0.1-rc.1 -> 1.0.1
            pre_type = None
            pre_num = None

        else:
             raise ValueError(f"Invalid bump part: {part}")

        return Version(major, minor, patch, pre_type, pre_num)

def parse_version_object(version: str) -> Version:
    match = VERSION_PATTERN.match(version)
    if not match:
        # Fallback for simple cases like "0.1" -> "0.1.0"
        if re.match(r"^\d+\.\d+$", version):
            version += ".0"
            match = VERSION_PATTERN.match(version)

    if not match:
        raise ValueError(f"Invalid version format: {version}")

    data = match.groupdict()
    return Version(
        int(data['major']),
        int(data['minor']),
        int(data['patch']),
        data.get('pre_type'),
        int(data['pre_num']) if data.get('pre_num') else None
    )

def parse_version(version: str) -> Tuple[int, int, int]:
    """
    Legacy support for parse_version. Returns (major, minor, patch).
    """
    v = parse_version_object(version)
    return v.major, v.minor, v.patch

def bump_version_string(version: str, part: str) -> str:
    """
    Bumps the version string based on the part.
    Supported parts: major, minor, patch, alpha, beta, rc, release
    """
    v = parse_version_object(version)
    new_v = v.bump(part)
    return str(new_v)

def update_file_content(path: Path, old_version: str, new_version: str) -> bool:
    """
    Replaces occurrences of old_version with new_version in the file at path.
    Returns True if changes were made.
    """
    if not path.exists():
        return False
        
    try:
        content = path.read_text(encoding="utf-8")
        
        new_content = content
        
        # Pattern for pyproject.toml: version = "1.0.0"
        toml_pattern = re.compile(rf'version\s*=\s*"{re.escape(old_version)}"')
        if toml_pattern.search(content):
            new_content = toml_pattern.sub(f'version = "{new_version}"', new_content)
            
        # Pattern for __init__.py: __version__ = "1.0.0"
        init_pattern = re.compile(rf'__version__\s*=\s*"{re.escape(old_version)}"')
        if init_pattern.search(content):
            new_content = init_pattern.sub(f'__version__ = "{new_version}"', new_content)
            
        if new_content != content:
            path.write_text(new_content, encoding="utf-8")
            return True
            
    except Exception as e:
        print(f"Error updating {path}: {e}")
        return False
        
    return False

def update_version_tests(project_path: Path, old_version: str, new_version: str) -> List[str]:
    """
    Scans the 'tests' directory for files containing the old version string
    in an assertion context and updates them. returns list of updated files.
    """
    updated_files = []
    tests_dir = project_path / "tests"
    if not tests_dir.exists():
        return updated_files

    for test_file in tests_dir.rglob("*.py"):
        # Skip this file to prevent modifying its own version assertion tests
        if test_file.name == "test_versioning.py":
            continue
            
        try:
            content = test_file.read_text(encoding="utf-8")
            if old_version in content:
                # Check if it's surrounded by quotes to avoid partial matches
                if f'"{old_version}"' in content:
                    new_content = content.replace(f'"{old_version}"', f'"{new_version}"')
                    test_file.write_text(new_content, encoding="utf-8")
                    updated_files.append(str(test_file.relative_to(project_path)))
                elif f"'{old_version}'" in content:
                    new_content = content.replace(f"'{old_version}'", f"'{new_version}'")
                    test_file.write_text(new_content, encoding="utf-8")
                    updated_files.append(str(test_file.relative_to(project_path)))
        except Exception:
            pass
            
    return updated_files
