import sys
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from relm.install import install_project
from relm.core import Project

@pytest.fixture
def mock_project():
    return Project(name="test_project", path=Path("/tmp/test_project"), version="0.1.0")

def test_install_project_success_editable(mock_project):
    with patch("subprocess.run") as mock_run:
        result = install_project(mock_project, editable=True)
        assert result is True
        mock_run.assert_called_once_with(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            cwd=mock_project.path,
            check=True
        )

def test_install_project_success_standard(mock_project):
    with patch("subprocess.run") as mock_run:
        result = install_project(mock_project, editable=False)
        assert result is True
        mock_run.assert_called_once_with(
            [sys.executable, "-m", "pip", "install", "."],
            cwd=mock_project.path,
            check=True
        )

def test_install_project_failure(mock_project):
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "pip")):
        result = install_project(mock_project)
        assert result is False
