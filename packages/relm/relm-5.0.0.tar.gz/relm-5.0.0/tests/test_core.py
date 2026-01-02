# tests/test_core.py

import unittest
from pathlib import Path
from pyfakefs.fake_filesystem_unittest import TestCase
from relm.core import Project, find_projects, load_project


class TestCore(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_project_str(self):
        """
        Tests the __str__ representation of the Project class.
        """
        project = Project(name="test-project", version="1.0", path=Path("/path/to/project"))
        self.assertIn("test-project", str(project))
        self.assertIn("1.0", str(project))

    def test_load_project_invalid_toml(self):
        """
        Tests that load_project returns None for an invalid TOML file.
        """
        self.fs.create_file("invalid/pyproject.toml", contents="invalid toml")
        self.assertIsNone(load_project(Path("invalid")))

    def test_find_projects_non_existent_path(self):
        """
        Tests that find_projects returns an empty list for a non-existent path.
        """
        projects = find_projects(Path("non-existent"))
        self.assertEqual(len(projects), 0)

    def test_find_projects(self):
        # Create a mock file system with multiple projects
        self.fs.create_file("pyproject.toml", contents='''
[project]
name = "root-project"
version = "5.0.0"
''')
        self.fs.create_file("subproject1/pyproject.toml", contents='''
[project]
name = "subproject1"
version = "0.2.0"
''')
        self.fs.create_file("subproject2/pyproject.toml", contents='''
[project]
name = "subproject2"
version = "0.3.0"
''')
        self.fs.create_dir("not-a-project")

        root = Path(".")
        projects = find_projects(root)
        
        # Should find root-project, subproject1, and subproject2
        names = [p.name for p in projects]
        
        self.assertIn("root-project", names)
        self.assertIn("subproject1", names)
        self.assertIn("subproject2", names)
        self.assertEqual(len(projects), 3)

    def test_find_projects_no_projects(self):
        self.fs.create_dir("empty")
        root = Path("empty")
        projects = find_projects(root)
        self.assertEqual(len(projects), 0)

if __name__ == "__main__":
    unittest.main()
