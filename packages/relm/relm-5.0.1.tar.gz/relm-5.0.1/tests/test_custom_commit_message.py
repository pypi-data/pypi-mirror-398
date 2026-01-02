
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from relm.release import perform_release
from relm.core import Project

class TestCustomCommitMessage(unittest.TestCase):
    def setUp(self):
        self.project = Project(
            name="test-project",
            version="1.0.0",
            path=Path("/tmp/test_project"),
            description="Test project"
        )

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
    def test_perform_release_custom_message(self, mock_console, mock_push, mock_tag, mock_commit, mock_add,
                                          mock_run_tests, mock_update_tests, mock_update_file, mock_bump,
                                          mock_is_clean, mock_tag_exists, mock_fetch):
        # Setup mocks for a successful release flow
        mock_is_clean.return_value = True
        mock_tag_exists.side_effect = [True, False] # Already tagged? Yes. New tag exists? No.
        mocked_new_version = "5.0.1" # This will be the mocked new version
        mock_bump.return_value = mocked_new_version
        mock_update_file.return_value = True
        mock_update_tests.return_value = []
        mock_run_tests.return_value = True

        # Define custom message template
        custom_template = "chore(release): bump to version {version}"

        # Call perform_release with the new argument
        perform_release(self.project, "major", yes_mode=True, commit_template=custom_template)

        # Verify git_commit was called with the formatted message
        expected_message = f"chore(release): bump to version {mocked_new_version}"
        mock_commit.assert_called_with(self.project.path, expected_message)

if __name__ == "__main__":
    unittest.main()
