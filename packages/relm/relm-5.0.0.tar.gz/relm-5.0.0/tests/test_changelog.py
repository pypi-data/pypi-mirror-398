import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from relm.changelog import parse_commits, generate_changelog_content, update_changelog_file, generate_changelog
from relm.git_ops import get_commit_log

def test_parse_commits():
    raw_commits = [
        "feat: add new feature",
        "fix: fix bug",
        "docs: update readme",
        "chore: clean up",
        "feat(core): add core feature",
        "invalid commit message",
        "refactor: improve code structure"
    ]

    parsed = parse_commits(raw_commits)

    assert "Features" in parsed
    assert "Bug Fixes" in parsed
    assert "Documentation" in parsed
    assert "Other Changes" in parsed # chore, refactor, etc if configured, or just mapped

    assert "add new feature" in parsed["Features"]
    assert "**core:** add core feature" in parsed["Features"] # Scope handling
    assert "fix bug" in parsed["Bug Fixes"]
    assert "update readme" in parsed["Documentation"]

def test_generate_changelog_content():
    commits_map = {
        "Features": ["add new feature", "add core feature"],
        "Bug Fixes": ["fix bug"],
        "Documentation": ["update readme"]
    }

    content = generate_changelog_content("1.2.0", "2023-10-27", commits_map)

    assert "## [1.2.0] - 2023-10-27" in content
    assert "### Features" in content
    assert "- add new feature" in content
    assert "- add core feature" in content
    assert "### Bug Fixes" in content
    assert "- fix bug" in content
    assert "### Documentation" in content
    assert "- update readme" in content

def test_update_changelog_file(tmp_path):
    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.write_text("# Changelog\n\n## [1.1.0] - 2023-10-01\n- Old entry")

    new_entry = "## [1.2.0] - 2023-10-27\n### Features\n- New thing\n"

    update_changelog_file(changelog_path, new_entry)

    content = changelog_path.read_text()
    assert content.startswith("# Changelog\n\n## [1.2.0] - 2023-10-27")
    assert "## [1.1.0] - 2023-10-01" in content

def test_update_changelog_file_empty(tmp_path):
    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.touch()

    new_entry = "## [1.2.0] - 2023-10-27\n### Features\n- New thing\n"

    update_changelog_file(changelog_path, new_entry)

    content = changelog_path.read_text()
    assert content.startswith("# Changelog\n\n## [1.2.0] - 2023-10-27")

def test_update_changelog_file_no_file(tmp_path):
    changelog_path = tmp_path / "CHANGELOG.md"
    # File does not exist

    new_entry = "## [1.2.0] - 2023-10-27\n### Features\n- New thing\n"

    update_changelog_file(changelog_path, new_entry)

    content = changelog_path.read_text()
    assert content.startswith("# Changelog\n\n## [1.2.0] - 2023-10-27")

def test_update_changelog_file_existing_version(tmp_path):
    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.write_text("# Changelog\n\n## [1.2.0] - 2023-10-27\n- Old entry")

    new_entry = "## [1.2.0] - 2023-10-27\n### Features\n- New thing\n"

    update_changelog_file(changelog_path, new_entry)

    content = changelog_path.read_text()
    # Should remain unchanged
    assert content == "# Changelog\n\n## [1.2.0] - 2023-10-27\n- Old entry"

def test_update_changelog_file_header_only_stripped(tmp_path):
    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.write_text("# Changelog")

    new_entry = "## [1.2.0] - 2023-10-27\n### Features\n- New thing\n"

    update_changelog_file(changelog_path, new_entry)

    content = changelog_path.read_text()
    assert content == "# Changelog\n\n" + new_entry

def test_update_changelog_file_header_with_newlines(tmp_path):
    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.write_text("# Changelog\n\n")

    new_entry = "## [1.2.0] - 2023-10-27\n### Features\n- New thing\n"

    update_changelog_file(changelog_path, new_entry)

    content = changelog_path.read_text()
    # Should use the path that just appends header + entry because strip() == "# Changelog"
    assert content == "# Changelog\n\n" + new_entry

def test_update_changelog_file_header_with_intro_text(tmp_path):
    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.write_text("# Changelog\n\nIntro text here.\n")

    new_entry = "## [1.2.0] - 2023-10-27\n### Features\n- New thing\n"

    update_changelog_file(changelog_path, new_entry)

    content = changelog_path.read_text()
    # logic: starts with header, strip() != header.
    # new_content = header + new_entry + "\n" + rest
    # rest = "Intro text here.\n"
    expected = "# Changelog\n\n" + new_entry + "\n" + "Intro text here.\n"
    assert content == expected

def test_update_changelog_file_weird_format(tmp_path):
    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.write_text("# Changelog\nSome random text\n")

    new_entry = "## [1.2.0] - 2023-10-27\n### Features\n- New thing\n"

    update_changelog_file(changelog_path, new_entry)

    content = changelog_path.read_text()
    # logic: else: lines = splitlines() ...
    # lines = ["# Changelog", "Some random text"]
    # new_content = "# Changelog" + "\n\n" + new_entry + "\n" + "Some random text"
    expected = "# Changelog\n\n" + new_entry + "\n" + "Some random text"
    assert content == expected

def test_update_changelog_file_no_changelog_header(tmp_path):
    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.write_text("## Some other header\n- Content")

    new_entry = "## [1.2.0] - 2023-10-27\n"

    update_changelog_file(changelog_path, new_entry)

    content = changelog_path.read_text()
    # logic: else: new_content = header + new_entry + "\n" + current_content
    # header = "# Changelog\n\n"
    expected = "# Changelog\n\n" + new_entry + "\n" + "## Some other header\n- Content"
    assert content == expected

@patch("relm.changelog.get_commit_log")
def test_generate_changelog_integration(mock_get_log, tmp_path):
    # Setup
    mock_get_log.return_value = [
        "feat: amazing feature",
        "fix: critical bug"
    ]
    project_path = tmp_path

    # Execution
    content = generate_changelog(project_path, "1.2.0")

    # Verification
    assert "## [1.2.0]" in content
    assert "- amazing feature" in content
    assert "- critical bug" in content
