import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from relm.core import Project
from relm.commands import run_command

class TestExecutionOrder(unittest.TestCase):
    @patch("relm.commands.run_command.find_projects")
    @patch("relm.commands.run_command.run_project_command")
    @patch("relm.commands.run_command.Console")
    def test_run_respects_dependencies(self, mock_console_cls, mock_run_cmd, mock_find_projects):
        # Setup: Project A depends on B
        p_a = Project("A", "1.0", Path("/a"), dependencies=["B"])
        p_b = Project("B", "1.0", Path("/b"), dependencies=[])

        # find_projects might return them in any order (e.g., alphabetical A, B)
        mock_find_projects.return_value = [p_a, p_b]

        mock_run_cmd.return_value = True

        # Args
        args = MagicMock()
        args.project_name = "all"
        args.command_string = "echo test"
        args.path = "."
        args.fail_fast = False
        args.parallel = False
        args.from_root = False
        
        console = MagicMock()

        run_command.execute(args, console)

        # Check that run_project_command was called in order: B then A

        calls = mock_run_cmd.call_args_list
        self.assertEqual(len(calls), 2)

        first_call_path = calls[0][0][0]
        second_call_path = calls[1][0][0]

        self.assertEqual(first_call_path, Path("/b"))
        self.assertEqual(second_call_path, Path("/a"))

if __name__ == "__main__":
    unittest.main()