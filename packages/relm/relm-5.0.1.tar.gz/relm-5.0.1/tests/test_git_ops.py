# tests/test_git_ops.py

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import subprocess
from relm.git_ops import (
    run_git_command,
    is_git_clean,
    git_add,
    git_commit,
    git_tag,
    git_push,
    git_fetch_tags,
    git_tag_exists,
    git_has_changes,
    get_current_branch,
    get_commit_log,
    git_has_changes_since
)

class TestGitOps(unittest.TestCase):
    def setUp(self):
        self.path = Path("/tmp/test_repo")

    @patch("subprocess.run")
    def test_run_git_command_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "output\n"
        mock_run.return_value = mock_result

        output = run_git_command(["status"], self.path)

        mock_run.assert_called_with(
            ["git", "status"],
            cwd=self.path,
            capture_output=True,
            text=True,
            check=True
        )
        self.assertEqual(output, "output")

    @patch("subprocess.run")
    def test_run_git_command_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, ["git", "status"])

        with self.assertRaises(subprocess.CalledProcessError):
            run_git_command(["status"], self.path)

    @patch("subprocess.run")
    def test_is_git_clean_true(self, mock_run):
        self.assertTrue(is_git_clean(self.path))
        self.assertEqual(mock_run.call_count, 3)

    @patch("subprocess.run")
    def test_is_git_clean_false(self, mock_run):
        mock_run.side_effect = [None, subprocess.CalledProcessError(1, "cmd")]
        self.assertFalse(is_git_clean(self.path))

    @patch("relm.git_ops.run_git_command")
    def test_git_add(self, mock_run_git):
        git_add(self.path, ["file1", "file2"])
        mock_run_git.assert_called_with(["add", "file1", "file2"], cwd=self.path)

    @patch("relm.git_ops.run_git_command")
    def test_git_commit(self, mock_run_git):
        git_commit(self.path, "commit message")
        mock_run_git.assert_called_with(["commit", "-m", "commit message"], cwd=self.path)

    @patch("relm.git_ops.run_git_command")
    def test_git_tag(self, mock_run_git):
        git_tag(self.path, "v1.0.0", "release v1.0.0")
        mock_run_git.assert_called_with(["tag", "v1.0.0", "-m", "release v1.0.0"], cwd=self.path)

    @patch("relm.git_ops.run_git_command")
    def test_git_tag_no_message(self, mock_run_git):
        git_tag(self.path, "v1.0.0")
        mock_run_git.assert_called_with(["tag", "v1.0.0"], cwd=self.path)

    @patch("relm.git_ops.run_git_command")
    def test_git_push(self, mock_run_git):
        git_push(self.path)
        self.assertEqual(mock_run_git.call_count, 2)
        mock_run_git.assert_any_call(["push"], cwd=self.path)
        mock_run_git.assert_any_call(["push", "--tags"], cwd=self.path)

    @patch("relm.git_ops.run_git_command")
    def test_git_fetch_tags(self, mock_run_git):
        git_fetch_tags(self.path)
        mock_run_git.assert_called_with(["fetch", "--tags"], cwd=self.path)

    @patch("relm.git_ops.run_git_command")
    def test_git_tag_exists_true(self, mock_run_git):
        git_tag_exists(self.path, "v1.0.0")
        mock_run_git.assert_called_with(["rev-parse", "-q", "--verify", "refs/tags/v1.0.0"], cwd=self.path)

    @patch("relm.git_ops.run_git_command")
    def test_git_tag_exists_false(self, mock_run_git):
        mock_run_git.side_effect = subprocess.CalledProcessError(1, "cmd")
        self.assertFalse(git_tag_exists(self.path, "v1.0.0"))

    @patch("subprocess.run")
    def test_git_has_changes_false(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertFalse(git_has_changes(self.path, "v1.0.0"))
        mock_run.assert_called_with(
            ["git", "diff", "--quiet", "v1.0.0", "HEAD", "--", "."],
            cwd=self.path,
            check=True
        )

    @patch("subprocess.run")
    def test_git_has_changes_true(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        self.assertTrue(git_has_changes(self.path, "v1.0.0"))

    @patch("relm.git_ops.run_git_command")
    def test_get_current_branch_success(self, mock_run_git):
        mock_run_git.return_value = "main"
        branch = get_current_branch(self.path)
        self.assertEqual(branch, "main")
        mock_run_git.assert_called_with(["rev-parse", "--abbrev-ref", "HEAD"], cwd=self.path)

    @patch("relm.git_ops.run_git_command")
    def test_get_current_branch_unknown(self, mock_run_git):
        mock_run_git.side_effect = subprocess.CalledProcessError(1, "cmd")
        branch = get_current_branch(self.path)
        self.assertEqual(branch, "unknown")

    @patch("relm.git_ops.run_git_command")
    def test_get_commit_log_success(self, mock_run_git):
        mock_run_git.side_effect = ["v1.0.0", "feat: new feature\nfix: bug fix"]
        log = get_commit_log(self.path)
        self.assertEqual(log, ["feat: new feature", "fix: bug fix"])
        mock_run_git.assert_any_call(["describe", "--tags", "--abbrev=0"], cwd=self.path)
        mock_run_git.assert_any_call(["log", "v1.0.0..HEAD", "--pretty=format:%s"], cwd=self.path)

    @patch("relm.git_ops.run_git_command")
    def test_get_commit_log_no_tags(self, mock_run_git):
        # Simulate 'describe' failing (no tags), then 'log' succeeding
        def side_effect(args, cwd):
            if args[0] == "describe":
                raise subprocess.CalledProcessError(128, "cmd")
            if args[0] == "log":
                return "init\nfeat: first"
            return ""

        mock_run_git.side_effect = side_effect
        log = get_commit_log(self.path)
        self.assertEqual(log, ["init", "feat: first"])

    @patch("relm.git_ops.run_git_command")
    def test_get_commit_log_failure(self, mock_run_git):
         # Simulate 'describe' failing and 'log' failing
        mock_run_git.side_effect = subprocess.CalledProcessError(1, "cmd")
        log = get_commit_log(self.path)
        self.assertEqual(log, [])

    @patch("subprocess.run")
    def test_git_has_changes_since_false(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertFalse(git_has_changes_since(self.path, "main"))
        mock_run.assert_called_with(
            ["git", "diff", "--quiet", "main", "HEAD", "--", "."],
            cwd=self.path,
            check=True
        )

    @patch("subprocess.run")
    def test_git_has_changes_since_true(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        self.assertTrue(git_has_changes_since(self.path, "main"))

if __name__ == "__main__":
    unittest.main()
