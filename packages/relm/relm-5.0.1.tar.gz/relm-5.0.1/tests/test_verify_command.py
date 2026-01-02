# tests/test_verify_command.py

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from argparse import Namespace
import sys
from relm.commands.verify_command import execute
from relm.core import Project

class TestVerifyCommand(unittest.TestCase):
    def setUp(self):
        self.console = MagicMock()
        self.args = Namespace(path="/tmp/test_root", project_name="all")
        self.root_path = Path("/tmp/test_root").resolve()

        self.project1 = Project(name="proj1", version="1.0.0", path=self.root_path / "proj1", description="")
        self.project2 = Project(name="proj2", version="5.0.1", path=self.root_path / "proj2", description="")

    @patch("relm.commands.verify_command.find_projects")
    @patch("relm.commands.verify_command.verify_project_release")
    def test_verify_all_mixed_results(self, mock_verify, mock_find):
        mock_find.return_value = [self.project1, self.project2]
        # proj1 success, proj2 fail
        mock_verify.side_effect = [(True, "All good"), (False, "Not found")]

        execute(self.args, self.console)

        # Check find_projects called with correct path
        mock_find.assert_called_with(self.root_path, recursive=False, max_depth=2)

        # Check verify calls
        self.assertEqual(mock_verify.call_count, 2)

        # Check console output
        # Header for all
        self.console.print.assert_any_call(f"[bold]Verifying PyPI availability for 2 projects...[/bold]")

        # Summary
        self.console.rule.assert_called_with("Verification Summary")
        self.console.print.assert_any_call("[green]Verified: 1[/green]")
        self.console.print.assert_any_call("[red]Failed:   1[/red]")

    @patch("relm.commands.verify_command.find_projects")
    @patch("relm.commands.verify_command.verify_project_release")
    def test_verify_single_success(self, mock_verify, mock_find):
        self.args.project_name = "proj1"
        mock_find.return_value = [self.project1, self.project2]
        mock_verify.return_value = (True, "All good")

        execute(self.args, self.console)

        mock_verify.assert_called_once_with(self.project1)
        # Should NOT print "Verifying PyPI availability for..." header
        # Should NOT print summary
        self.console.rule.assert_not_called()

    @patch("relm.commands.verify_command.find_projects")
    def test_verify_single_not_found(self, mock_find):
        self.args.project_name = "nonexistent"
        mock_find.return_value = [self.project1]

        with self.assertRaises(SystemExit) as cm:
            execute(self.args, self.console)

        self.assertEqual(cm.exception.code, 1)
        self.console.print.assert_called_with(f"[red]Project or folder 'nonexistent' not found in {self.root_path}[/red]")

    @patch("relm.commands.verify_command.find_projects")
    @patch("relm.commands.verify_command.verify_project_release")
    def test_verify_all_success(self, mock_verify, mock_find):
         mock_find.return_value = [self.project1]
         mock_verify.return_value = (True, "Good")

         execute(self.args, self.console)

         self.console.print.assert_any_call("[green]Verified: 1[/green]")
         # Should not print Failed count if 0
         # But the code says: if results["failed"]: print
         # So we verify that the failure message was NOT called
         # Note: print is called multiple times, so we need to check arguments

         calls = [call.args[0] for call in self.console.print.call_args_list]
         self.assertNotIn("[red]Failed:   0[/red]", calls) # Just making sure
         # Check that no red failure message appeared
         self.assertFalse(any("Failed:" in str(c) for c in calls))

if __name__ == "__main__":
    unittest.main()
