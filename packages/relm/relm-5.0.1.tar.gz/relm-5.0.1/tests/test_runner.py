import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from relm.runner import run_project_command, execute_in_parallel, run_project_command_tail
from relm.core import Project

def test_run_project_command_success():
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.poll.return_value = 0
        mock_process.stdout.readline.return_value = ""
        mock_popen.return_value = mock_process
        
        result = run_project_command(Path("/tmp/test"), "echo hello")
        assert result is True

def test_run_project_command_failure_exit_code():
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.poll.return_value = 1
        mock_process.stdout.readline.return_value = ""
        mock_popen.return_value = mock_process
        
        result = run_project_command(Path("/tmp/test"), "exit 1")
        assert result is False

def test_run_project_command_exception():
    with patch("subprocess.Popen", side_effect=Exception("Boom")):
        result = run_project_command(Path("/tmp/test"), "echo hello")
        assert result is False

def test_execute_in_parallel_basic():
    p1 = Project(name="p1", version="1.0", path=Path("/p1"), dependencies=[])
    p2 = Project(name="p2", version="1.0", path=Path("/p2"), dependencies=["p1"])
    projects = [p1, p2]
    
    def provider(p):
        return ["echo", p.name]
        
    with patch("relm.runner.run_project_command_tail") as mock_run:
        mock_run.return_value = {"returncode": 0, "stdout": "done", "stderr": ""}
        
        results = execute_in_parallel(projects, provider)
        
        assert len(results) == 2
        assert mock_run.call_count == 2
        names = [r["name"] for r in results]
        assert "p1" in names
        assert "p2" in names

def test_execute_in_parallel_with_cycle():
    p1 = Project(name="p1", version="1.0", path=Path("/p1"), dependencies=["p2"])
    p2 = Project(name="p2", version="1.0", path=Path("/p2"), dependencies=["p1"])
    projects = [p1, p2]
    
    def provider(p):
        return ["echo", p.name]
        
    with patch("relm.runner.run_project_command_tail") as mock_run:
        mock_run.return_value = {"returncode": 0, "stdout": "done", "stderr": ""}
        
        results = execute_in_parallel(projects, provider)
        
        assert len(results) == 2
        assert mock_run.call_count == 2

def test_execute_in_parallel_fail_fast():
    p1 = Project(name="p1", version="1.0", path=Path("/p1"), dependencies=[])
    p2 = Project(name="p2", version="1.0", path=Path("/p2"), dependencies=["p1"])
    projects = [p1, p2]
    
    def provider(p):
        return ["echo", p.name]
        
    with patch("relm.runner.run_project_command_tail") as mock_run:
        # First one fails
        mock_run.return_value = {"returncode": 1, "stdout": "failed", "stderr": ""}
        
        results = execute_in_parallel(projects, provider, fail_fast=True)
        
        # Should stop after p1 fails
        assert len(results) == 1
        assert results[0]["name"] == "p1"

def test_run_project_command_tail_success():
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        # readline returns one line then empty string to end loop
        mock_process.stdout.readline.side_effect = ["line1\n", ""]
        # poll returns 0 (finished)
        mock_process.poll.return_value = 0
        mock_popen.return_value = mock_process
        
        res = run_project_command_tail(Path("/tmp"), "echo ok")
        assert res["returncode"] == 0
        assert "line1" in res["stdout"]
