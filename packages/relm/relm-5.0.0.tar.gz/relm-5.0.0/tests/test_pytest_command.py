import sys
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from relm.commands.pytest_command import execute
from relm.core import Project

@pytest.fixture
def mock_console():
    return MagicMock()

@pytest.fixture
def mock_projects():
    return [
        Project(name="pkg-a", version="0.1.0", path=Path("/tmp/pkg-a"), dependencies=[]),
        Project(name="pkg-b", version="0.1.0", path=Path("/tmp/pkg-b"), dependencies=["pkg-a"]),
    ]

def test_pytest_command_all_success(mock_console, mock_projects):
    args = Namespace(path="/tmp", project_name="all", fail_fast=False)
    
    with patch("relm.commands.pytest_command.find_projects", return_value=mock_projects) \
         , patch("relm.commands.pytest_command.sort_projects_by_dependency", return_value=mock_projects) \
         , patch("sys.argv", ["relm", "pytest", "all"]) \
         , patch("relm.runner.run_project_command_tail") as mock_run:
        
        mock_run.return_value = {"returncode": 0, "stdout": "Success", "stderr": ""}
        
        execute(args, mock_console)
        
        assert mock_run.call_count == 2

def test_pytest_command_single_project(mock_console, mock_projects):
    args = Namespace(path="/tmp", project_name="pkg-a", fail_fast=False)
    
    # Mocking sys.argv to simulate: relm pytest pkg-a -- -v
    with patch("relm.commands.pytest_command.find_projects", return_value=mock_projects) \
         , patch("sys.argv", ["relm", "pytest", "pkg-a", "--", "-v"]) \
         , patch("relm.runner.run_project_command_tail") as mock_run:
        
        mock_run.return_value = {"returncode": 0, "stdout": "Success", "stderr": ""}
        
        execute(args, mock_console)
        
        assert mock_run.call_count == 1
        cmd = mock_run.call_args[0][1]
        assert "-v" in cmd

def test_pytest_command_fail_fast(mock_console, mock_projects):
    args = Namespace(path="/tmp", project_name="all", fail_fast=True)
    
    with patch("relm.commands.pytest_command.find_projects", return_value=mock_projects) \
         , patch("relm.commands.pytest_command.sort_projects_by_dependency", return_value=mock_projects) \
         , patch("sys.argv", ["relm", "pytest", "all"]) \
         , patch("relm.runner.run_project_command_tail") as mock_run \
         , pytest.raises(SystemExit):
        
        mock_run.return_value = {"returncode": 1, "stdout": "Fail", "stderr": ""}
        execute(args, mock_console)
        # Should stop after first failure because fail_fast is True
        assert mock_run.call_count == 1

def test_pytest_command_parallel(mock_console, mock_projects):
    args = Namespace(path="/tmp", project_name="all", fail_fast=False, parallel=True, jobs=4)
    
    with patch("relm.commands.pytest_command.find_projects", return_value=mock_projects) \
         , patch("relm.commands.pytest_command.sort_projects_by_dependency", return_value=mock_projects) \
         , patch("sys.argv", ["relm", "pytest", "all", "--parallel"]) \
         , patch("relm.commands.pytest_command.execute_in_parallel") as mock_parallel:
        
        mock_parallel.return_value = [
            {"name": "pkg-a", "success": True, "path": Path("/tmp/pkg-a")},
            {"name": "pkg-b", "success": True, "path": Path("/tmp/pkg-b")}
        ]
        
        execute(args, mock_console)
        
        mock_parallel.assert_called_once()
        assert mock_parallel.call_args.kwargs['max_workers'] == 4