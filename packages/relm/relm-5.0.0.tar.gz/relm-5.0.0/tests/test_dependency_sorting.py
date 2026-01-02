import pytest
from pathlib import Path
from relm.core import Project, sort_projects_by_dependency, load_project

def test_load_project_with_dependencies(fs):
    """Test that load_project correctly parses dependencies."""
    project_path = Path("/app-a")
    fs.create_dir(project_path)
    fs.create_file(
        project_path / "pyproject.toml",
        contents="""
[project]
name = "app-a"
version = "0.1.0"
dependencies = [
    "lib-b>=1.0.0",
    "requests",
    "lib-c"
]
"""
    )

    project = load_project(project_path)
    assert project is not None
    assert project.name == "app-a"
    assert "lib-b" in project.dependencies
    assert "lib-c" in project.dependencies
    assert "requests" in project.dependencies

def test_topological_sort_simple(fs):
    """
    Test simple linear dependency: A -> B -> C.
    Execution order should be C, B, A.
    """
    p_a = Project(name="A", version="1.0", path=Path("/a"), dependencies=["B"])
    p_b = Project(name="B", version="1.0", path=Path("/b"), dependencies=["C"])
    p_c = Project(name="C", version="1.0", path=Path("/c"), dependencies=[])

    projects = [p_a, p_b, p_c]
    # Shuffle or input in wrong order
    sorted_projects = sort_projects_by_dependency([p_a, p_c, p_b])

    names = [p.name for p in sorted_projects]
    assert names == ["C", "B", "A"]

def test_topological_sort_diamond(fs):
    """
    Test diamond dependency:
      A -> B, A -> C
      B -> D, C -> D
    Execution order: D then (B, C in any order) then A.
    """
    p_a = Project(name="A", version="1.0", path=Path("/a"), dependencies=["B", "C"])
    p_b = Project(name="B", version="1.0", path=Path("/b"), dependencies=["D"])
    p_c = Project(name="C", version="1.0", path=Path("/c"), dependencies=["D"])
    p_d = Project(name="D", version="1.0", path=Path("/d"), dependencies=[])

    projects = [p_a, p_b, p_c, p_d]
    sorted_projects = sort_projects_by_dependency(projects)

    names = [p.name for p in sorted_projects]

    # D must be first
    assert names[0] == "D"
    # A must be last
    assert names[-1] == "A"
    # B and C are in middle
    assert set(names[1:3]) == {"B", "C"}

def test_topological_sort_circular_dependency():

    p_a = Project(name="A", version="1.0", path=Path("/a"), dependencies=["B"])

    p_b = Project(name="B", version="1.0", path=Path("/b"), dependencies=["A"])

    

    # Now it should NOT raise ValueError, but return both projects

    projects = [p_a, p_b]

    sorted_projects = sort_projects_by_dependency(projects)

    

    assert len(sorted_projects) == 2

    names = [p.name for p in sorted_projects]

    assert "A" in names

    assert "B" in names



def test_sort_with_external_dependencies():
    """
    Test that external dependencies (not in the project list) are ignored.
    A -> B
    A -> requests (external)
    B -> numpy (external)
    """
    p_a = Project(name="A", version="1.0", path=Path("/a"), dependencies=["B", "requests"])
    p_b = Project(name="B", version="1.0", path=Path("/b"), dependencies=["numpy"])

    sorted_projects = sort_projects_by_dependency([p_a, p_b])
    names = [p.name for p in sorted_projects]
    assert names == ["B", "A"]
