
import unittest
from unittest.mock import MagicMock, patch, call
from argparse import Namespace
from pathlib import Path
from relm.commands import list_command

class TestChangedSince(unittest.TestCase):
    def setUp(self):
        self.console = MagicMock()
        self.args = Namespace(path=".", since="HEAD~1")
        self.project1 = MagicMock(name="proj1")
        self.project1.name = "proj1"
        self.project1.version = "1.0.0"
        self.project1.path = Path("/repo/proj1")
        self.project1.description = "Project 1"

        self.project2 = MagicMock(name="proj2")
        self.project2.name = "proj2"
        self.project2.version = "1.0.0"
        self.project2.path = Path("/repo/proj2")
        self.project2.description = "Project 2"

    @patch("relm.commands.list_command.find_projects")
    @patch("relm.commands.list_command.git_has_changes_since", create=True)
    def test_list_since_filters_projects(self, mock_has_changes, mock_find_projects):
        # Setup
        mock_find_projects.return_value = [self.project1, self.project2]

        # proj1 has changes, proj2 does not
        def side_effect(path, ref):
            return path == self.project1.path
        mock_has_changes.side_effect = side_effect

        # Execute
        list_command.execute(self.args, self.console)

        # Verify
        # This assertion is expected to fail first
        mock_has_changes.assert_has_calls([
            call(self.project1.path, "HEAD~1"),
            call(self.project2.path, "HEAD~1")
        ], any_order=True)

        self.assertTrue(self.console.print.called)
        args, _ = self.console.print.call_args
        table = args[0]

        self.assertEqual(table.title, "Found 1 Projects")
