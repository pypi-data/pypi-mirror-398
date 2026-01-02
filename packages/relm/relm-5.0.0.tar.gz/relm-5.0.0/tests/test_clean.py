
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from pyfakefs.fake_filesystem_unittest import TestCase
# We will implement this in src/relm/clean.py
from relm.clean import clean_project
from relm.core import Project

class TestClean(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_clean_project_removes_artifacts(self):
        # Setup
        project_path = Path("/projects/myproj")
        self.fs.create_dir(project_path / "dist")
        self.fs.create_dir(project_path / "build")
        self.fs.create_dir(project_path / "src" / "myproj" / "__pycache__")
        self.fs.create_file(project_path / "src" / "myproj" / "main.py")
        self.fs.create_dir(project_path / "src" / "myproj" / "sub" / "__pycache__")

        project = Project("myproj", "1.0.0", project_path, "description")

        # Action
        # We expect clean_project to return a list of removed paths or count, or boolean
        # Let's say it returns a list of removed paths for reporting
        removed_paths = clean_project(project)

        # Assert
        self.assertFalse((project_path / "dist").exists())
        self.assertFalse((project_path / "build").exists())
        self.assertFalse((project_path / "src" / "myproj" / "__pycache__").exists())
        self.assertFalse((project_path / "src" / "myproj" / "sub" / "__pycache__").exists())
        self.assertTrue((project_path / "src" / "myproj" / "main.py").exists())

        self.assertTrue(len(removed_paths) > 0)
        self.assertIn(str(project_path / "dist"), [str(p) for p in removed_paths])

    def test_clean_project_no_artifacts(self):
        # Setup
        project_path = Path("/projects/myproj")
        self.fs.create_file(project_path / "src" / "myproj" / "main.py")

        project = Project("myproj", "1.0.0", project_path, "description")

        # Action
        removed_paths = clean_project(project)

        # Assert
        self.assertEqual(len(removed_paths), 0)
        self.assertTrue((project_path / "src" / "myproj" / "main.py").exists())
