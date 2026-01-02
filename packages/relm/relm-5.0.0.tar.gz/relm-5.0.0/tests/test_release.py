# tests/test_release.py

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import subprocess
from relm.release import perform_release, run_tests, revert_changes
from relm.core import Project

class TestRelease(unittest.TestCase):
    def setUp(self):
        self.project = Project(
            name="test-project",
            version="5.0.0",
            path=Path("/tmp/test_project"),
            description="Test project"
        )

    @patch("subprocess.run")
    @patch("relm.release.console")
    def test_run_tests_success(self, mock_console, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(run_tests(self.project.path))

    @patch("subprocess.run")
    @patch("relm.release.console")
    def test_run_tests_failure(self, mock_console, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "pytest")
        self.assertFalse(run_tests(self.project.path))

    @patch("subprocess.run")
    @patch("relm.release.console")
    def test_run_tests_no_pytest(self, mock_console, mock_run):
        mock_run.side_effect = FileNotFoundError()
        self.assertTrue(run_tests(self.project.path))
        mock_console.print.assert_called_with("[yellow]pytest not found. Skipping tests.[/yellow]")

    @patch("subprocess.run")
    @patch("relm.release.console")
    def test_revert_changes_success(self, mock_console, mock_run):
        revert_changes(self.project.path)
        mock_run.assert_called_with(["git", "checkout", "."], cwd=self.project.path, check=True)

    @patch("subprocess.run")
    @patch("relm.release.console")
    def test_revert_changes_failure(self, mock_console, mock_run):
        mock_run.side_effect = Exception("error")
        revert_changes(self.project.path)
        mock_console.print.assert_any_call("[red]Failed to revert changes: error[/red]")

    @patch("relm.release.git_fetch_tags")
    @patch("relm.release.git_tag_exists")
    @patch("relm.release.git_has_changes")
    @patch("relm.release.console")
    def test_perform_release_smart_skip(self, mock_console, mock_has_changes, mock_tag_exists, mock_fetch):
        mock_tag_exists.return_value = True
        mock_has_changes.return_value = False

        result = perform_release(self.project, "patch", check_changes=True)
        self.assertFalse(result)
        mock_console.print.assert_any_call(f"[dim]No changes detected since v{self.project.version}. Skipping.[/dim]")

    @patch("relm.release.git_fetch_tags")
    @patch("relm.release.git_tag_exists")
    @patch("relm.release.is_git_clean")
    @patch("relm.release.console")
    def test_perform_release_dirty_git(self, mock_console, mock_is_clean, mock_tag_exists, mock_fetch):
        mock_tag_exists.return_value = True # Pretend tagged to avoid prompt logic for now
        mock_is_clean.return_value = False

        result = perform_release(self.project, "patch", yes_mode=True)
        self.assertFalse(result)
        mock_console.print.assert_any_call("[red]Error: Git repository is not clean. Commit or stash changes first.[/red]")

    @patch("relm.release.git_fetch_tags")
    @patch("relm.release.git_tag_exists")
    @patch("relm.release.is_git_clean")
    @patch("relm.release.bump_version_string")
    @patch("relm.release.update_file_content")
    @patch("relm.release.update_version_tests")
    @patch("relm.release.run_tests")
    @patch("relm.release.git_add")
    @patch("relm.release.git_commit")
    @patch("relm.release.git_tag")
    @patch("relm.release.git_push")
    @patch("relm.release.console")
    def test_perform_release_success_bump(self, mock_console, mock_push, mock_tag, mock_commit, mock_add,
                                          mock_run_tests, mock_update_tests, mock_update_file, mock_bump,
                                          mock_is_clean, mock_tag_exists, mock_fetch):
        mock_is_clean.return_value = True
        mock_tag_exists.side_effect = [True, False] # First check: already tagged? Yes (so bump). Second check: new tag exists? No.
        mock_bump.return_value = "5.0.0"
        mock_update_file.return_value = True
        mock_update_tests.return_value = []
        mock_run_tests.return_value = True

        result = perform_release(self.project, "patch", yes_mode=True)
        self.assertTrue(result)

        mock_bump.assert_called_with("5.0.0", "patch")
        mock_commit.assert_called()
        mock_tag.assert_called()
        mock_push.assert_called()

    @patch("relm.release.git_fetch_tags")
    @patch("relm.release.git_tag_exists")
    @patch("relm.release.Confirm.ask")
    @patch("relm.release.is_git_clean")
    @patch("relm.release.git_tag")
    @patch("relm.release.git_push")
    @patch("relm.release.console")
    def test_perform_release_retry_existing(self, mock_console, mock_push, mock_tag, mock_is_clean, mock_confirm, mock_tag_exists, mock_fetch):
        # Case: Not tagged locally, user says Retry (skip bump)
        mock_tag_exists.return_value = False # Not tagged initially, and new tag doesn't exist
        mock_confirm.side_effect = [True, True, True] # Retry? Yes. Proceed? Yes. Push? Yes.
        mock_is_clean.return_value = True

        result = perform_release(self.project, "patch", yes_mode=False)
        self.assertTrue(result)

        # Verify no file updates happen (we can't easily assert on that unless we mock the calls, but we check logic flow)
        mock_tag.assert_called_with(self.project.path, f"v{self.project.version}", f"Release v{self.project.version}")

    @patch("relm.release.git_fetch_tags")
    @patch("relm.release.git_tag_exists")
    @patch("relm.release.is_git_clean")
    @patch("relm.release.bump_version_string")
    @patch("relm.release.update_file_content")
    @patch("relm.release.run_tests")
    @patch("relm.release.revert_changes")
    @patch("relm.release.console")
    def test_perform_release_tests_fail(self, mock_console, mock_revert, mock_run_tests, mock_update_file, mock_bump, mock_is_clean, mock_tag_exists, mock_fetch):
        mock_is_clean.return_value = True
        mock_tag_exists.return_value = True
        mock_bump.return_value = "5.0.0"
        mock_update_file.return_value = True
        mock_run_tests.return_value = False

        result = perform_release(self.project, "patch", yes_mode=True)
        self.assertFalse(result)
        mock_revert.assert_called()

    @patch("relm.release.git_fetch_tags")
    @patch("relm.release.git_tag_exists")
    @patch("relm.release.is_git_clean")
    @patch("relm.release.bump_version_string")
    @patch("relm.release.update_file_content")
    @patch("relm.release.console")
    def test_perform_release_no_files_updated(self, mock_console, mock_update_file, mock_bump, mock_is_clean, mock_tag_exists, mock_fetch):
        mock_is_clean.return_value = True
        mock_tag_exists.return_value = True
        mock_bump.return_value = "5.0.0"
        mock_update_file.return_value = False # No files updated

        result = perform_release(self.project, "patch", yes_mode=True)
        self.assertFalse(result)
        mock_console.print.assert_any_call("[red]No files were updated! Check version strings.[/red]")

    @patch("relm.release.git_fetch_tags")
    @patch("relm.release.console")
    def test_perform_release_fetch_fail(self, mock_console, mock_fetch):
        mock_fetch.side_effect = Exception("Fetch failed")
        # We need to mock subsequent calls to avoid errors
        with patch("relm.release.git_tag_exists", return_value=True), \
             patch("relm.release.is_git_clean", return_value=False):

            perform_release(self.project, "patch", yes_mode=True)
            mock_console.print.assert_any_call("[yellow]Warning: Could not fetch remote tags. Proceeding with local info.[/yellow]")

    @patch("relm.release.git_fetch_tags")
    @patch("relm.release.git_tag_exists")
    @patch("relm.release.is_git_clean")
    @patch("relm.release.bump_version_string")
    @patch("relm.release.console")
    def test_perform_release_bump_error(self, mock_console, mock_bump, mock_is_clean, mock_tag_exists, mock_fetch):
        mock_is_clean.return_value = True
        mock_tag_exists.return_value = True
        mock_bump.side_effect = ValueError("Bad version")

        result = perform_release(self.project, "patch", yes_mode=True)
        self.assertFalse(result)
        mock_console.print.assert_any_call("[red]Error parsing version: Bad version[/red]")

    @patch("relm.release.git_fetch_tags")
    @patch("relm.release.git_tag_exists")
    @patch("relm.release.is_git_clean")
    @patch("relm.release.bump_version_string")
    @patch("relm.release.Confirm.ask")
    @patch("relm.release.console")
    def test_perform_release_cancel(self, mock_console, mock_confirm, mock_bump, mock_is_clean, mock_tag_exists, mock_fetch):
        mock_is_clean.return_value = True
        mock_tag_exists.return_value = True
        mock_bump.return_value = "5.0.0"
        mock_confirm.return_value = False # Cancel

        result = perform_release(self.project, "patch", yes_mode=False)
        self.assertFalse(result)
        mock_console.print.assert_any_call("[yellow]Release cancelled.[/yellow]")

    @patch("relm.release.git_fetch_tags")
    @patch("relm.release.git_tag_exists")
    @patch("relm.release.is_git_clean")
    @patch("relm.release.bump_version_string")
    @patch("relm.release.update_file_content")
    @patch("relm.release.run_tests")
    @patch("relm.release.git_add")
    @patch("relm.release.git_commit")
    @patch("relm.release.console")
    def test_perform_release_commit_fail(self, mock_console, mock_commit, mock_add, mock_run_tests, mock_update_file, mock_bump, mock_is_clean, mock_tag_exists, mock_fetch):
        mock_is_clean.return_value = True
        mock_tag_exists.side_effect = [True, False]
        mock_bump.return_value = "5.0.0"
        mock_update_file.return_value = True
        mock_run_tests.return_value = True
        mock_commit.side_effect = Exception("Commit failed")

        result = perform_release(self.project, "patch", yes_mode=True)
        self.assertFalse(result)
        mock_console.print.assert_any_call("[red]Git commit error: Commit failed[/red]")

    @patch("relm.release.git_fetch_tags")
    @patch("relm.release.git_tag_exists")
    @patch("relm.release.is_git_clean")
    @patch("relm.release.bump_version_string")
    @patch("relm.release.update_file_content")
    @patch("relm.release.run_tests")
    @patch("relm.release.git_add")
    @patch("relm.release.git_commit")
    @patch("relm.release.git_tag")
    @patch("relm.release.console")
    def test_perform_release_tag_fail(self, mock_console, mock_tag, mock_commit, mock_add, mock_run_tests, mock_update_file, mock_bump, mock_is_clean, mock_tag_exists, mock_fetch):
        mock_is_clean.return_value = True
        mock_tag_exists.side_effect = [True, False]
        mock_bump.return_value = "5.0.0"
        mock_update_file.return_value = True
        mock_run_tests.return_value = True
        mock_tag.side_effect = Exception("Tag failed")

        result = perform_release(self.project, "patch", yes_mode=True)
        self.assertFalse(result)
        mock_console.print.assert_any_call("[red]Git tag error: Tag failed[/red]")

    @patch("relm.release.git_fetch_tags")
    @patch("relm.release.git_tag_exists")
    @patch("relm.release.is_git_clean")
    @patch("relm.release.bump_version_string")
    @patch("relm.release.update_file_content")
    @patch("relm.release.run_tests")
    @patch("relm.release.git_add")
    @patch("relm.release.git_commit")
    @patch("relm.release.git_tag")
    @patch("relm.release.git_push")
    @patch("relm.release.console")
    def test_perform_release_push_fail(self, mock_console, mock_push, mock_tag, mock_commit, mock_add, mock_run_tests, mock_update_file, mock_bump, mock_is_clean, mock_tag_exists, mock_fetch):
        mock_is_clean.return_value = True
        mock_tag_exists.side_effect = [True, False]
        mock_bump.return_value = "5.0.0"
        mock_update_file.return_value = True
        mock_run_tests.return_value = True
        mock_push.side_effect = Exception("Push failed")

        result = perform_release(self.project, "patch", yes_mode=True)
        self.assertFalse(result)
        mock_console.print.assert_any_call("[red]Push error: Push failed[/red]")

    @patch("pathlib.Path.exists")
    @patch("relm.release.git_fetch_tags")
    @patch("relm.release.git_tag_exists")
    @patch("relm.release.is_git_clean")
    @patch("relm.release.bump_version_string")
    @patch("relm.release.update_file_content")
    @patch("relm.release.update_version_tests")
    @patch("relm.release.run_tests")
    @patch("relm.release.git_add")
    @patch("relm.release.git_commit")
    @patch("relm.release.git_tag")
    @patch("relm.release.git_push")
    @patch("relm.release.console")
    def test_perform_release_init_in_project_root(self, mock_console, mock_push, mock_tag, mock_commit, mock_add,
                                                  mock_run_tests, mock_update_tests, mock_update_file, mock_bump,
                                                  mock_is_clean, mock_tag_exists, mock_fetch, mock_path_exists):
        mock_is_clean.return_value = True
        mock_tag_exists.side_effect = [True, False]
        mock_bump.return_value = "5.0.0"
        mock_update_file.return_value = True
        mock_update_tests.return_value = []
        mock_run_tests.return_value = True
        # Simulate that __init__.py is in the project root, not src
        mock_path_exists.side_effect = [False, True]

        result = perform_release(self.project, "patch", yes_mode=True)
        self.assertTrue(result)

        # Check that update_file_content was called for the correct __init__.py path
        init_path = self.project.path / "test_project/__init__.py"
        mock_update_file.assert_any_call(init_path, "5.0.0", "5.0.0")


if __name__ == "__main__":
    unittest.main()
