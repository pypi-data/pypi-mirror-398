<div align="center">
  <img src="https://raw.githubusercontent.com/dhruv13x/relm/main/relm_logo.png" alt="relm logo" width="200"/>
</div>

<div align="center">

<!-- Package Info -->
[![PyPI version](https://img.shields.io/pypi/v/relm.svg)](https://pypi.org/project/relm/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
![Wheel](https://img.shields.io/pypi/wheel/relm.svg)
[![Release](https://img.shields.io/badge/release-PyPI-blue)](https://pypi.org/project/relm/)

<!-- Build & Quality -->
[![Build status](https://github.com/dhruv13x/relm/actions/workflows/publish.yml/badge.svg)](https://github.com/dhruv13x/relm/actions/workflows/publish.yml)
[![Codecov](https://codecov.io/gh/dhruv13x/relm/graph/badge.svg)](https://codecov.io/gh/dhruv13x/relm)
[![Test Coverage](https://img.shields.io/badge/coverage-85%25%2B-brightgreen.svg)](https://github.com/dhruv13x/relm/actions/workflows/test.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/badge/linting-ruff-yellow.svg)](https://github.com/astral-sh/ruff)

<!-- Usage -->
![Downloads](https://img.shields.io/pypi/dm/relm.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

# relm

**The Monorepo Manager for Python.** "Batteries Included" CLI for managing your Python mono-repo or multi-project workspace. Automate versioning, git tagging, PyPI releases, and local environment setup with a single tool.

---

## ⚡ Quick Start (The "5-Minute Rule")

### Prerequisites
*   **Python 3.8+**
*   **Docker** (Optional, for containerized workflows)
*   **Git** (Required for version control operations)

### Installation
Install globally with `pipx` (recommended) or `pip`:
```bash
# Recommended
pipx install relm

# Alternative
pip install relm
```

### Run
Start managing your workspace instantly:
```bash
# Discover projects in the current directory
relm list
```

### Demo
Copy-paste this snippet to see `relm` in action (assumes you have a Python project structure):

```bash
# 1. List all projects and their current versions
relm list

# 2. Check git status across the entire workspace
relm status all

# 3. Install all projects in editable mode
relm install all

# 4. Run tests across all projects (stops on first failure)
relm run "pytest" all --fail-fast

# 5. Release a patch version for a specific library
relm release my-library patch
```

---

## ✨ Features (The "Why")

### Core
*   **Automated Discovery**: Recursively scans and identifies Python projects (`pyproject.toml`) in your workspace.
*   **Smart Versioning**: Semantically bumps versions (`major`, `minor`, `patch`, `alpha`, `beta`, `rc`) and updates files automatically.
*   **Zero-Config Git Ops**: Auto-stages, commits, tags, and pushes releases with standardized messages.

### Performance & Workflow
*   **Bulk Operations**: **Install, Test, or Release ALL projects** with a single command.
*   **Dependency Awareness**: **Topologically sorts projects** to ensure correct build order (build `lib-a` before `app-b`).
*   **"Changed Since" Detection**: Filter operations to only target projects modified since a specific git reference (`--since`).
*   **Workspace Cleaning**: Instantly wipe `dist/`, `build/`, and `__pycache__` artifacts with `relm clean`.

### Automation & Security
*   **Automated Changelog**: **Parses Conventional Commits** to auto-generate `CHANGELOG.md`.
*   **PyPI Publishing**: seamless build and upload workflow.
*   **PyPI Verification**: Verify local tags match PyPI releases with `relm verify`.
*   **Safety Checks**: Prevents accidental execution in system roots.

---

## 🛠️ Configuration (The "How")

`relm` is configured via a `.relm.toml` file in your workspace root and CLI arguments.

### Environment Variables
`relm` primarily uses `.relm.toml` for configuration, but respects standard tool variables:

| Name | Description | Default | Required |
| :--- | :--- | :--- | :--- |
| `TWINE_USERNAME` | Username for PyPI upload (used by internal tools) | None | For Release |
| `TWINE_PASSWORD` | Password/Token for PyPI upload | None | For Release |

### CLI Arguments

**Global Options**
| Flag | Description |
| :--- | :--- |
| `--path` | Root directory to scan for projects (default: `.`) |

**Commands**
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `list` | `--since <ref>` | List projects (optionally filtered by changes since git ref). |
| `status` | `project_name` | Show git branch and dirty status. |
| `install` | `project_name`, `--no-editable` | Install projects (default: editable). |
| `run` | `command`, `project_name`, `--fail-fast` | Execute shell command in project directories. |
| `release` | `project`, `type`, `-y`, `-m` | Bump version, tag, and publish. Type: `major`, `minor`, `patch`, etc. |
| `clean` | `project_name` | Remove build artifacts. |
| `create` | `name`, `path` | Scaffold a new project. |
| `verify` | `project_name` | Verify PyPI release availability. |
| `gc` | N/A | Run `git gc` on all projects. |

---

## 🏗️ Architecture

`relm` uses a modular architecture designed for maintainability and separation of concerns.

### Directory Tree
```text
src/relm/
├── commands/           # 🔌 Pluggable Command Modules
│   ├── list_command.py
│   ├── release_command.py
│   └── ...
├── core.py             # 🧠 Project Model & Dependency Graph
├── config.py           # ⚙️ Configuration Loader (.relm.toml)
├── git_ops.py          # 🐙 Git Wrapper
├── release.py          # 🚀 Release Workflow Engine
├── versioning.py       # 🏷️ SemVer Logic
├── changelog.py        # 📝 Changelog Generator
├── main.py             # 🏁 CLI Entry Point
└── banner.py           # 🎨 ASCII Art
```

### Data Flow
1.  **Discovery**: `main.py` bootstraps and calls `core.py` to recursively find `pyproject.toml` files.
2.  **Graph Construction**: Projects are parsed into `Project` objects; dependencies are mapped.
3.  **Topological Sort**: For bulk operations (`install`, `run`), projects are ordered so dependencies are processed first.
4.  **Execution**: The appropriate `command` module is invoked, orchestrating `git_ops`, `subprocess` calls, or file manipulations.

---

## 🐞 Troubleshooting

### Common Issues
| Error Message | Possible Cause | Solution |
| :--- | :--- | :--- |
| `Project 'xyz' not found` | The project is not in the scan path. | Ensure `--path` is correct and `pyproject.toml` exists. |
| `Git repository is not clean` | Uncommitted changes exist. | Commit or stash changes before releasing. |
| `Circular dependency detected` | Projects depend on each other. | Refactor dependencies to be acyclic. |
| `Running in system root` | Executing from `/` or similar. | Navigate to your workspace folder or use `--path`. |

### Debug Mode
`relm` uses `rich` for output. While there is no dedicated `--debug` flag, exceptions are printed with tracebacks on failure.
Check `pyproject.toml` for `log_cli = true` to enable verbose logging during test runs (`relm run "pytest"`).

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Dev Setup
1.  Clone the repo.
2.  Install dependencies: `pip install .[dev]`.
3.  Run tests: `pytest`.
4.  Linting: `ruff check .` and `black .`.

---

## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md) for the full vision.

*   [x] Bulk Release Support
*   [x] Task Runner (`relm run`)
*   [x] Project Status (`relm status`)
*   [x] Pre-release Version Support (`alpha`, `beta`, `rc`)
*   [x] Automated Changelog Generation
*   [x] Configuration File Support (`.relm.toml`)
*   [x] Dependency Graph Awareness
*   [ ] Parallel execution for `run` and `install`
*   [ ] Interactive mode for project selection
*   [ ] Docker container support
*   [ ] CI/CD Integration templates
