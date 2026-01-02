# tests/test_verify.py

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import subprocess
import json
from relm.verify import verify_project_release
from relm.core import Project

class TestVerify(unittest.TestCase):
    def setUp(self):
        self.project = Project(
            name="test-project",
            version="5.0.1",
            path=Path("/tmp/test_project"),
            description="Test project"
        )

    @patch("relm.verify.git_tag_exists")
    @patch("subprocess.run")
    def test_verify_success(self, mock_run, mock_tag_exists):
        mock_tag_exists.return_value = True
        
        # Mock pip output
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"name": "test-project", "versions": [self.project.version, "0.9.0"]}),
            returncode=0
        )
        
        success, message = verify_project_release(self.project)
        self.assertTrue(success)
        self.assertIn("is verified on PyPI", message)

    @patch("relm.verify.git_tag_exists")
    def test_verify_missing_tag(self, mock_tag_exists):
        mock_tag_exists.return_value = False
        
        success, message = verify_project_release(self.project)
        self.assertFalse(success)
        self.assertIn(f"Local git tag 'v{self.project.version}' does not exist", message)

    @patch("relm.verify.git_tag_exists")
    @patch("subprocess.run")
    def test_verify_version_not_found(self, mock_run, mock_tag_exists):
        mock_tag_exists.return_value = True
        
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"name": "test-project", "versions": ["0.9.0"], "latest": "0.9.0"}),
            returncode=0
        )
        
        success, message = verify_project_release(self.project)
        self.assertFalse(success)
        self.assertIn("not found on PyPI", message)
        self.assertIn("Latest is 0.9.0", message)

    @patch("relm.verify.git_tag_exists")
    @patch("subprocess.run")
    def test_verify_pip_error(self, mock_run, mock_tag_exists):
        mock_tag_exists.return_value = True
        
        mock_run.side_effect = subprocess.CalledProcessError(1, "pip")
        
        success, message = verify_project_release(self.project)
        self.assertFalse(success)
        self.assertIn("Failed to query PyPI", message)

    @patch("relm.verify.git_tag_exists")
    @patch("subprocess.run")
    def test_verify_json_error(self, mock_run, mock_tag_exists):
        mock_tag_exists.return_value = True
        
        mock_run.return_value = MagicMock(
            stdout="Not JSON",
            returncode=0
        )
        
        success, message = verify_project_release(self.project)
        self.assertFalse(success)
        self.assertIn("Failed to parse pip output", message)

if __name__ == "__main__":
    unittest.main()
