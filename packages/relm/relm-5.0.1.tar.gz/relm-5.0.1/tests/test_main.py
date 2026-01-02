# tests/test_main.py

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
from relm.main import main, list_projects
from relm.core import Project
from relm.commands import list_command

class TestMain(unittest.TestCase):
    def _create_mock_args(self, **kwargs):
        args = MagicMock()
        # Set defaults for common args
        args.path = "."
        args.recursive = False
        args.depth = 2
        args.parallel = False
        args.jobs = None
        args.from_root = False
        for k, v in kwargs.items():
            setattr(args, k, v)
        return (args, [])

    @patch("relm.commands.list_command.find_projects")
    @patch("relm.main.console")
    def test_list_projects(self, mock_console, mock_find_projects):
        mock_find_projects.return_value = [
            Project("proj1", "5.0.1", Path("path/to/proj1"), "desc1"),
            Project("proj2", "5.0.1", Path("path/to/proj2"), None)
        ]

        list_projects(Path("."))

        mock_console.print.assert_called()
        args, _ = mock_console.print.call_args
        self.assertTrue(hasattr(args[0], "rows")) # It's a Table object

    @patch("relm.commands.list_command.find_projects")
    @patch("relm.main.console")
    def test_list_projects_empty(self, mock_console, mock_find_projects):
        mock_find_projects.return_value = []
        list_projects(Path("."))
        mock_console.print.assert_called_with("[yellow]No projects found in this directory.[/yellow]")

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.list_command.execute")
    def test_main_list(self, mock_list_execute, mock_parse_known_args):
        mock_parse_known_args.return_value = self._create_mock_args(command="list", func=mock_list_execute)
        main()
        mock_list_execute.assert_called()

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.release_command.find_projects")
    @patch("relm.commands.release_command.perform_release")
    @patch("relm.main.console")
    def test_main_release_single_success(self, mock_console, mock_perform_release, mock_find_projects, mock_parse_known_args):
        from relm.commands.release_command import execute as release_execute

        mock_parse_known_args.return_value = self._create_mock_args(
            command="release",
            project_name="proj1",
            type="patch",
            yes=True,
            message="release: bump version to {version}",
            func=release_execute
        )
        project = Project("proj1", "5.0.1", Path("."), "desc")
        mock_find_projects.return_value = [project]
        mock_perform_release.return_value = True

        main()

        mock_perform_release.assert_called_with(
            project,
            "patch",
            yes_mode=True,
            check_changes=False,
            commit_template="release: bump version to {version}"
        )

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.release_command.find_projects")
    @patch("relm.main.console")
    def test_main_release_project_not_found(self, mock_console, mock_find_projects, mock_parse_known_args):
        from relm.commands.release_command import execute as release_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="release",
            project_name="nonexistent",
            type="patch",
            yes=True,
            func=release_execute
        )
        mock_find_projects.return_value = []

        with self.assertRaises(SystemExit):
            main()

        mock_console.print.assert_called()

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.release_command.find_projects")
    @patch("relm.commands.release_command.perform_release")
    @patch("relm.main.console")
    def test_main_release_all(self, mock_console, mock_perform_release, mock_find_projects, mock_parse_known_args):
        from relm.commands.release_command import execute as release_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="release",
            project_name="all",
            type="patch",
            yes=True,
            message="release: bump version to {version}",
            func=release_execute
        )
        p1 = Project("proj1", "5.0.1", Path("."), "desc")
        p2 = Project("proj2", "5.0.1", Path("."), "desc")
        mock_find_projects.return_value = [p1, p2]
        mock_perform_release.return_value = True

        main()

        self.assertEqual(mock_perform_release.call_count, 2)

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.release_command.find_projects")
    @patch("relm.commands.release_command.perform_release")
    @patch("relm.main.console")
    def test_main_release_all_exception(self, mock_console, mock_perform_release, mock_find_projects, mock_parse_known_args):
        from relm.commands.release_command import execute as release_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="release",
            project_name="all",
            type="patch",
            yes=True,
            message="release: bump version to {version}",
            func=release_execute
        )
        p1 = Project("proj1", "5.0.1", Path("."), "desc")
        mock_find_projects.return_value = [p1]
        mock_perform_release.side_effect = Exception("error")

        main()

        mock_console.print.assert_called()

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.run_command.find_projects")
    @patch("relm.commands.run_command.run_project_command")
    @patch("relm.main.console")
    def test_main_run_all(self, mock_console, mock_run_cmd, mock_find_projects, mock_parse_known_args):
        from relm.commands.run_command import execute as run_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="run",
            command_string="echo hello",
            project_name="all",
            fail_fast=False,
            func=run_execute
        )
        p1 = Project("proj1", "5.0.1", Path("."), "desc")
        p2 = Project("proj2", "5.0.1", Path("."), "desc")
        mock_find_projects.return_value = [p1, p2]
        mock_run_cmd.return_value = True

        main()

        self.assertEqual(mock_run_cmd.call_count, 2)

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.run_command.find_projects")
    @patch("relm.commands.run_command.run_project_command")
    @patch("relm.main.console")
    def test_main_run_fail_fast(self, mock_console, mock_run_cmd, mock_find_projects, mock_parse_known_args):
        from relm.commands.run_command import execute as run_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="run",
            command_string="echo hello",
            project_name="all",
            fail_fast=True,
            func=run_execute
        )
        p1 = Project("proj1", "5.0.1", Path("."), "desc")
        p2 = Project("proj2", "5.0.1", Path("."), "desc")
        mock_find_projects.return_value = [p1, p2]
        mock_run_cmd.return_value = False

        with self.assertRaises(SystemExit):
            main()

        self.assertEqual(mock_run_cmd.call_count, 1)

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.run_command.find_projects")
    @patch("relm.commands.run_command.run_project_command")
    @patch("relm.main.console")
    def test_main_run_single_success(self, mock_console, mock_run_cmd, mock_find_projects, mock_parse_known_args):
        from relm.commands.run_command import execute as run_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="run",
            command_string="echo hello",
            project_name="proj1",
            fail_fast=False,
            func=run_execute
        )
        p1 = Project("proj1", "5.0.1", Path("."), "desc")
        mock_find_projects.return_value = [p1]
        mock_run_cmd.return_value = True

        main()

        mock_run_cmd.assert_called_once()

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.run_command.find_projects")
    @patch("relm.main.console")
    def test_main_run_project_not_found(self, mock_console, mock_find_projects, mock_parse_known_args):
        from relm.commands.run_command import execute as run_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="run",
            command_string="echo hello",
            project_name="nonexistent",
            fail_fast=False,
            func=run_execute
        )
        mock_find_projects.return_value = []

        with self.assertRaises(SystemExit):
            main()

        root_path = Path(".").resolve()
        mock_console.print.assert_any_call(f"[red]Project or folder 'nonexistent' not found in {root_path}[/red]")

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.install_command.find_projects")
    @patch("relm.commands.install_command.install_project")
    @patch("relm.main.console")
    def test_main_install_all(self, mock_console, mock_install, mock_find_projects, mock_parse_known_args):
        from relm.commands.install_command import execute as install_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="install",
            project_name="all",
            no_editable=False,
            func=install_execute
        )
        p1 = Project("proj1", "5.0.1", Path("."), "desc")
        p2 = Project("proj2", "5.0.1", Path("."), "desc")
        mock_find_projects.return_value = [p1, p2]
        mock_install.return_value = True

        main()

        self.assertEqual(mock_install.call_count, 2)

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.install_command.find_projects")
    @patch("relm.commands.install_command.install_project")
    @patch("relm.main.console")
    def test_main_install_single_success(self, mock_console, mock_install, mock_find_projects, mock_parse_known_args):
        from relm.commands.install_command import execute as install_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="install",
            project_name="proj1",
            no_editable=False,
            func=install_execute
        )
        p1 = Project("proj1", "5.0.1", Path("."), "desc")
        mock_find_projects.return_value = [p1]
        mock_install.return_value = True

        main()

        mock_install.assert_called_once()

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.install_command.find_projects")
    @patch("relm.main.console")
    def test_main_install_project_not_found(self, mock_console, mock_find_projects, mock_parse_known_args):
        from relm.commands.install_command import execute as install_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="install",
            project_name="nonexistent",
            no_editable=False,
            func=install_execute
        )
        mock_find_projects.return_value = []

        with self.assertRaises(SystemExit):
            main()

        root_path = Path(".").resolve()
        mock_console.print.assert_any_call(f"[red]Project or folder 'nonexistent' not found in {root_path}[/red]")

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.status_command.find_projects")
    @patch("relm.commands.status_command.get_current_branch")
    @patch("relm.commands.status_command.is_git_clean")
    @patch("relm.main.console")
    def test_main_status_all(self, mock_console, mock_is_clean, mock_get_branch, mock_find_projects, mock_parse_known_args):
        from relm.commands.status_command import execute as status_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="status",
            project_name="all",
            func=status_execute
        )
        p1 = Project("proj1", "5.0.1", Path("."), "desc")
        mock_find_projects.return_value = [p1]
        mock_get_branch.return_value = "main"
        mock_is_clean.return_value = True

        main()

        mock_console.print.assert_called()

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.status_command.find_projects")
    @patch("relm.commands.status_command.get_current_branch")
    @patch("relm.commands.status_command.is_git_clean")
    @patch("relm.main.console")
    def test_main_status_single(self, mock_console, mock_is_clean, mock_get_branch, mock_find_projects, mock_parse_known_args):
        from relm.commands.status_command import execute as status_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="status",
            project_name="proj1",
            func=status_execute
        )
        p1 = Project("proj1", "5.0.1", Path("."), "desc")
        mock_find_projects.return_value = [p1]
        mock_get_branch.return_value = "main"
        mock_is_clean.return_value = True

        main()

        mock_console.print.assert_called()

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.status_command.find_projects")
    @patch("relm.main.console")
    def test_main_status_project_not_found(self, mock_console, mock_find_projects, mock_parse_known_args):
        from relm.commands.status_command import execute as status_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="status",
            project_name="nonexistent",
            func=status_execute
        )
        mock_find_projects.return_value = []

        with self.assertRaises(SystemExit):
            main()

        root_path = Path(".").resolve()
        mock_console.print.assert_any_call(f"[red]Project or folder 'nonexistent' not found in {root_path}[/red]")

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.main.Console.input")
    @patch("relm.main.console")
    def test_main_safety_check(self, mock_console, mock_input, mock_parse_known_args):
        mock_parse_known_args.return_value = self._create_mock_args(
            command="list",
            path="/",
            yes=False
        )
        mock_input.return_value = "n"

        with self.assertRaises(SystemExit):
            main()

        root_path = Path("/").resolve()
        mock_console.print.assert_any_call(f"[bold red]\u26a0\ufe0f  Safety Warning: You are running relm in the system root ({root_path}).[/bold red]")

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.list_command.execute")
    @patch("relm.main.console")
    def test_main_safety_check_yes(self, mock_console, mock_list_execute, mock_parse_known_args):
        mock_parse_known_args.return_value = self._create_mock_args(
            command="list",
            path="/",
            yes=True,
            func=mock_list_execute
        )

        main()

        mock_list_execute.assert_called()

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.verify_command.find_projects")
    @patch("relm.commands.verify_command.verify_project_release")
    @patch("relm.main.console")
    def test_main_verify_all(self, mock_console, mock_verify, mock_find_projects, mock_parse_known_args):
        from relm.commands.verify_command import execute as verify_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="verify",
            project_name="all",
            func=verify_execute
        )
        p1 = Project("proj1", "5.0.1", Path("."), "desc")
        p2 = Project("proj2", "5.0.1", Path("."), "desc")
        mock_find_projects.return_value = [p1, p2]
        mock_verify.return_value = (True, "Verified")

        main()

        self.assertEqual(mock_verify.call_count, 2)

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.clean_command.find_projects")
    @patch("relm.commands.clean_command.clean_project")
    @patch("relm.main.console")
    def test_main_clean_all(self, mock_console, mock_clean_project, mock_find_projects, mock_parse_known_args):
        from relm.commands.clean_command import execute as clean_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="clean",
            project_name="all",
            func=clean_execute
        )
        p1 = Project("proj1", "5.0.1", Path("."), "desc")
        p2 = Project("proj2", "5.0.1", Path("Proj2"), "desc")
        mock_find_projects.return_value = [p1, p2]
        mock_clean_project.return_value = ["dist/"]

        main()

        self.assertEqual(mock_clean_project.call_count, 2)

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.clean_command.find_projects")
    @patch("relm.commands.clean_command.clean_project")
    @patch("relm.main.console")
    def test_main_clean_single(self, mock_console, mock_clean_project, mock_find_projects, mock_parse_known_args):
        from relm.commands.clean_command import execute as clean_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="clean",
            project_name="proj1",
            func=clean_execute
        )
        p1 = Project("proj1", "5.0.1", Path("."), "desc")
        mock_find_projects.return_value = [p1]
        mock_clean_project.return_value = ["dist/"]

        main()

        mock_clean_project.assert_called_once()

    @patch("argparse.ArgumentParser.parse_known_args")
    @patch("relm.commands.clean_command.find_projects")
    @patch("relm.main.console")
    def test_main_clean_project_not_found(self, mock_console, mock_find_projects, mock_parse_known_args):
        from relm.commands.clean_command import execute as clean_execute
        mock_parse_known_args.return_value = self._create_mock_args(
            command="clean",
            project_name="nonexistent",
            func=clean_execute
        )
        mock_find_projects.return_value = []

        with self.assertRaises(SystemExit):
            main()

        root_path = Path(".").resolve()
        mock_console.print.assert_any_call(f"[red]Project or folder 'nonexistent' not found in {root_path}[/red]")

if __name__ == "__main__":
    unittest.main()