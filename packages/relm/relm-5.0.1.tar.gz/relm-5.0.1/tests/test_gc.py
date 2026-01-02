import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from relm.commands import gc_command
from relm.core import Project
from relm.gc import gc_project
from relm.git_ops import run_git_gc
import argparse

@pytest.fixture
def mock_console():
    return MagicMock()

@pytest.fixture
def mock_project():
    return Project(
        name="test-project",
        version="0.1.0",
        path=Path("/tmp/test-project"),
        description="A test project"
    )

def test_register_command():

    subparsers = MagicMock()

    parser_mock = MagicMock()

    subparsers.add_parser.return_value = parser_mock

    base_parser = MagicMock()

    gc_command.register(subparsers, base_parser)

    subparsers.add_parser.assert_called_once_with("gc", help="Run git gc on project(s)", parents=[base_parser])


    parser_mock.add_argument.assert_called_once_with("project_name", help="Name of the project to gc or 'all'", nargs="?", default="all")
    parser_mock.set_defaults.assert_called_once_with(func=gc_command.execute)

def test_run_git_gc():
    path = Path("/tmp/repo")
    with patch("relm.git_ops.run_git_command") as mock_run_cmd:
        run_git_gc(path)
        mock_run_cmd.assert_called_once_with(["gc"], cwd=path)

def test_gc_project_success(mock_project):
    with patch("relm.gc.run_git_gc") as mock_run_gc:
        result = gc_project(mock_project)
        assert result is True
        mock_run_gc.assert_called_once_with(mock_project.path)

def test_gc_project_failure(mock_project):
    with patch("relm.gc.run_git_gc") as mock_run_gc:
        mock_run_gc.side_effect = Exception("Git error")
        result = gc_project(mock_project)
        assert result is False
        mock_run_gc.assert_called_once_with(mock_project.path)

def test_gc_command_all_success(mock_console):
    args = MagicMock()
    args.path = "."
    args.project_name = "all"

    projects = [
        Project(name="p1", version="1.0", path=Path("/p1")),
        Project(name="p2", version="1.0", path=Path("/p2")),
    ]

    with patch("relm.commands.gc_command.find_projects", return_value=projects), \
         patch("relm.commands.gc_command.gc_project", return_value=True) as mock_gc:

        gc_command.execute(args, mock_console)

        assert mock_gc.call_count == 2
        mock_gc.assert_has_calls([call(projects[0]), call(projects[1])])
        # Verify summary
        mock_console.print.assert_any_call("[bold green]Successfully ran git gc on 2 projects.[/bold green]")

def test_gc_command_single_success(mock_console):
    args = MagicMock()
    args.path = "."
    args.project_name = "p1"

    projects = [
        Project(name="p1", version="1.0", path=Path("/p1")),
        Project(name="p2", version="1.0", path=Path("/p2")),
    ]

    with patch("relm.commands.gc_command.find_projects", return_value=projects), \
         patch("relm.commands.gc_command.gc_project", return_value=True) as mock_gc:

        gc_command.execute(args, mock_console)

        mock_gc.assert_called_once_with(projects[0])
        mock_console.print.assert_any_call("[bold green]Successfully ran git gc on 1 projects.[/bold green]")

def test_gc_command_single_not_found(mock_console):
    args = MagicMock()
    args.path = "."
    args.project_name = "unknown"

    projects = [
        Project(name="p1", version="1.0", path=Path("/p1")),
    ]

    with patch("relm.commands.gc_command.find_projects", return_value=projects):
        with pytest.raises(SystemExit) as exc:
            gc_command.execute(args, mock_console)
        assert exc.value.code == 1
        mock_console.print.assert_any_call(f"[red]Project 'unknown' not found in {Path('.').resolve()}[/red]")

def test_gc_command_mixed_results(mock_console):
    args = MagicMock()
    args.path = "."
    args.project_name = "all"

    projects = [
        Project(name="p1", version="1.0", path=Path("/p1")),
        Project(name="p2", version="1.0", path=Path("/p2")),
    ]

    # p1 succeeds, p2 fails
    with patch("relm.commands.gc_command.find_projects", return_value=projects), \
         patch("relm.commands.gc_command.gc_project", side_effect=[True, False]):

        gc_command.execute(args, mock_console)

        mock_console.print.assert_any_call("[bold red]Completed with failures.[/bold red]")

def test_gc_command_single_failure(mock_console):
    args = MagicMock()
    args.path = "."
    args.project_name = "p1"

    projects = [
        Project(name="p1", version="1.0", path=Path("/p1")),
    ]

    with patch("relm.commands.gc_command.find_projects", return_value=projects), \
         patch("relm.commands.gc_command.gc_project", return_value=False):

        with pytest.raises(SystemExit) as exc:
            gc_command.execute(args, mock_console)
        assert exc.value.code == 1
