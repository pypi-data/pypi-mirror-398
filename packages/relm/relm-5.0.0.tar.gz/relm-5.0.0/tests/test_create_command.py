
import unittest
from unittest.mock import MagicMock, patch
from argparse import Namespace
from pathlib import Path
from pyfakefs.fake_filesystem_unittest import TestCase
# This import is expected to fail initially
from relm.commands import create_command

class TestCreateCommand(TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.console = MagicMock()
        self.cwd = Path("/workspace")
        self.fs.create_dir(self.cwd)
        self.args = Namespace(name="myproj", path=None)

    def test_create_project_structure(self):
        with patch("pathlib.Path.cwd", return_value=self.cwd):
            create_command.execute(self.args, self.console)

        project_path = self.cwd / "myproj"
        self.assertTrue(project_path.exists())
        self.assertTrue((project_path / "pyproject.toml").exists())
        self.assertTrue((project_path / "README.md").exists())
        self.assertTrue((project_path / ".gitignore").exists())
        self.assertTrue((project_path / "src" / "myproj" / "__init__.py").exists())
        self.assertTrue((project_path / "tests" / "__init__.py").exists())

        content = (project_path / "pyproject.toml").read_text()
        self.assertIn('name = "myproj"', content)
        self.assertIn('version = "0.1.0"', content)

    def test_create_project_exists(self):
        (self.cwd / "existing").mkdir()
        self.args.name = "existing"

        with patch("pathlib.Path.cwd", return_value=self.cwd):
            create_command.execute(self.args, self.console)

        # Should print error and not overwrite or create subdirs if logic correct
        self.console.print.assert_called()
        # Verify error message
        calls = self.console.print.call_args_list
        # The last call or one of the calls should contain "already exists"
        messages = [str(args[0]) for args, kwargs in calls]
        self.assertTrue(any("already exists" in msg for msg in messages))
