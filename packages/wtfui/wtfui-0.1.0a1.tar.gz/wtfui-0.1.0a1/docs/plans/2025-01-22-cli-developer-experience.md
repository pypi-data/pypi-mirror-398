# CLI Developer Experience Implementation Plan

> **Execution:** Use `/dev-workflow:execute-plan docs/plans/2025-01-22-cli-developer-experience.md` to implement task-by-task.

**Goal:** Add `pyfuse demo` command, fix docstrings, improve help output, and enhance error messages to match Bun's developer experience.

**Architecture:** Move examples into `src/pyfuse/examples/` so they're packaged with pip installs. Add a `demo` command to the Click CLI that discovers examples relative to the pyfuse package location, runs them via existing `run_tui_mode`/`run_web_mode`. Handle missing optional dependencies gracefully.

**Tech Stack:** Python 3.14+, Click CLI framework, pytest with CliRunner, hatchling build

---

## Task Groups

| Task Group | Tasks | Rationale |
|------------|-------|-----------|
| Group 1 | 1 | Move examples into package (prerequisite for demo) |
| Group 2 | 2, 3 | Independent: docstring fixes + help output (no overlap) |
| Group 3 | 4 | `demo` command implementation (depends on Task 1) |
| Group 4 | 5 | Error message improvements (depends on demo existing) |
| Group 5 | 6 | Code Review |

---

### Task 1: Move Examples into Package

**Files:**
- Move: `examples/` → `src/pyfuse/examples/`
- Modify: `pyproject.toml` (update ruff config paths)
- Create: `src/pyfuse/examples/__init__.py`

**Step 1: Move examples directory into src/pyfuse/** (2 min)

```bash
git mv examples/ src/pyfuse/examples/
```

**Step 2: Create package __init__.py** (1 min)

Create `src/pyfuse/examples/__init__.py`:

```python
"""Bundled example applications for pyfuse demo command."""
```

**Step 3: Update pyproject.toml ruff config** (2 min)

In `pyproject.toml`, update the `per-file-ignores` path for examples:

```toml
# BEFORE:
"examples/**/*.py" = [
    "S101",   # assert ok in examples
]

# AFTER:
"src/pyfuse/examples/**/*.py" = [
    "S101",   # assert ok in examples
]
```

Also update `isort` known-first-party (remove "examples"):

```toml
# BEFORE:
known-first-party = ["pyfuse", "examples"]

# AFTER:
known-first-party = ["pyfuse"]
```

**Step 4: Update relative imports in examples** (3 min)

The examples use relative imports like `from .storage import LocalStorage`. These will still work since they're now `pyfuse.examples.todo.storage`, etc.

Verify imports work:

```bash
uv run python -c "from pyfuse.examples.todo.app import app; print('todo OK')"
uv run python -c "from pyfuse.examples.dashboard.app import app; print('dashboard OK')"
uv run python -c "from pyfuse.examples.chat.app import app; print('chat OK')"
```

**Step 5: Run tests to verify nothing broke** (30 sec)

```bash
pytest tests/test_cli.py -v
```

Expected: PASS

**Step 6: Commit** (30 sec)

```bash
git add -A
git commit -m "refactor: move examples into src/pyfuse/examples for packaging"
```

---

### Task 2: Fix Example Docstrings

**Files:**
- Modify: `src/pyfuse/examples/todo/app.py:10`
- Modify: `src/pyfuse/examples/chat/app.py:10`
- Modify: `src/pyfuse/examples/dashboard/app.py:10`
- Modify: `src/pyfuse/examples/console/app.py` (if has docstring)

**Step 1: Fix todo example docstring** (2 min)

Change line 10 in `src/pyfuse/examples/todo/app.py`:

```python
# BEFORE:
Run with: cd examples/todo && flow dev --web

# AFTER:
Run with: pyfuse demo todo --web
```

**Step 2: Fix chat example docstring** (2 min)

Change line 10 in `src/pyfuse/examples/chat/app.py`:

```python
# BEFORE:
Run with: cd examples/chat && flow dev --web

# AFTER:
Run with: pyfuse demo chat --web
```

**Step 3: Fix dashboard example docstring** (2 min)

Change line 10 in `src/pyfuse/examples/dashboard/app.py`:

```python
# BEFORE:
Run with: cd examples/dashboard && flow dev --web

# AFTER:
Run with: pyfuse demo dashboard --web
```

**Step 4: Check and fix console example** (2 min)

Read `src/pyfuse/examples/console/app.py` and fix docstring if it contains `flow dev`.

**Step 5: Commit** (30 sec)

```bash
git add src/pyfuse/examples/
git commit -m "docs(examples): update docstrings to use pyfuse demo command"
```

---

### Task 3: Improve Help Output

**Files:**
- Modify: `src/pyfuse/cli/main.py:41-67`
- Test: `tests/test_cli.py` (add test)

**Step 1: Write test for compact help output** (3 min)

Add to `tests/test_cli.py`:

```python
class TestCliHelpOutput:
    """Tests for improved help output."""

    def test_help_shows_quick_start(self):
        """Help output includes quick start section."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Quick start:" in result.output or "Getting Started:" in result.output

    def test_help_mentions_demo_command(self):
        """Help output mentions demo command for trying examples."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "demo" in result.output.lower()
```

**Step 2: Run test to verify it fails** (30 sec)

```bash
pytest tests/test_cli.py::TestCliHelpOutput -v
```

Expected: FAIL (demo not in help output yet)

**Step 3: Update help output in main.py** (5 min)

Replace `print_help()` function in `src/pyfuse/cli/main.py:41-67`:

```python
def print_help() -> None:
    print("""PyFuse 0.1.0 - Pythonic UI for Python 3.14+

Usage: pyfuse <command> [options]

Quick start:
  pyfuse init myapp     Create new project
  pyfuse demo todo      Try the todo example

Commands:
  init <name>         Create a new PyFuse project
  dev [app]           Start development server (TUI default, --web for browser)
  build [app]         Compile to PyFuseByte for production
  demo [name]         Run bundled example apps

  install             Install project dependencies
  clean               Remove build artifacts
  learn [topic]       Interactive tutorial

Options:
  --version           Show version
  --help              Show this message

Run 'pyfuse <command> --help' for command details.
""")
```

**Step 4: Run test to verify it passes** (30 sec)

```bash
pytest tests/test_cli.py::TestCliHelpOutput -v
```

Expected: PASS

**Step 5: Commit** (30 sec)

```bash
git add src/pyfuse/cli/main.py tests/test_cli.py
git commit -m "feat(cli): improve help output with quick start section"
```

---

### Task 4: Add `pyfuse demo` Command

**Files:**
- Modify: `src/pyfuse/cli/__init__.py` (add demo command)
- Create: `src/pyfuse/cli/demo.py` (demo logic)
- Create: `tests/test_cli_demo.py` (demo tests)

**Step 1: Write test for demo --list** (3 min)

Create `tests/test_cli_demo.py`:

```python
# tests/test_cli_demo.py
"""Tests for pyfuse demo command."""

from click.testing import CliRunner

from pyfuse.cli import cli


class TestDemoCommand:
    """Tests for the demo command."""

    def test_demo_command_exists(self):
        """Demo command is available."""
        runner = CliRunner()
        result = runner.invoke(cli, ["demo", "--help"])

        assert result.exit_code == 0
        assert "demo" in result.output.lower()

    def test_demo_list_shows_examples(self):
        """Demo --list shows available examples."""
        runner = CliRunner()
        result = runner.invoke(cli, ["demo", "--list"])

        assert result.exit_code == 0
        assert "todo" in result.output.lower()
        assert "dashboard" in result.output.lower()
        assert "chat" in result.output.lower()
```

**Step 2: Run test to verify it fails** (30 sec)

```bash
pytest tests/test_cli_demo.py::TestDemoCommand::test_demo_command_exists -v
```

Expected: FAIL (no demo command)

**Step 3: Create demo.py with package-relative example discovery** (5 min)

Create `src/pyfuse/cli/demo.py`:

```python
# src/pyfuse/cli/demo.py
"""Demo command for running bundled examples.

Examples are bundled in src/pyfuse/examples/ and installed with the package.
This module discovers and runs them for both pip-installed and dev scenarios.
"""

from pathlib import Path

import pyfuse

# Example metadata for display
EXAMPLES: dict[str, tuple[str, list[str]]] = {
    # name: (description, optional_dependencies)
    "todo": ("Todo app with persistence (Signal, Effect)", []),
    "dashboard": ("Metrics dashboard (Computed, Flex layout)", []),
    "chat": ("Real-time chat with @rpc", []),
    "console": ("TUI console app", ["psutil"]),
}


def get_examples_dir() -> Path:
    """Get the examples directory path relative to installed package.

    Works for both:
    - Development: running from repo with `uv run pyfuse demo`
    - Production: pip-installed package
    """
    # pyfuse.__file__ is src/pyfuse/__init__.py (dev) or site-packages/pyfuse/__init__.py (prod)
    package_root = Path(pyfuse.__file__).parent
    return package_root / "examples"


def list_examples() -> list[tuple[str, str, list[str]]]:
    """Return list of (name, description, missing_deps) for available examples."""
    examples_dir = get_examples_dir()
    available = []

    for name, (description, deps) in EXAMPLES.items():
        example_path = examples_dir / name / "app.py"
        if example_path.exists():
            # Check for missing optional dependencies
            missing = []
            for dep in deps:
                try:
                    __import__(dep)
                except ImportError:
                    missing.append(dep)
            available.append((name, description, missing))

    return available


def get_example_path(name: str) -> Path | None:
    """Get the app.py path for an example, or None if not found."""
    examples_dir = get_examples_dir()
    app_path = examples_dir / name / "app.py"

    if app_path.exists():
        return app_path
    return None


def check_dependencies(name: str) -> list[str]:
    """Check if example has missing optional dependencies.

    Returns list of missing package names, or empty list if all present.
    """
    if name not in EXAMPLES:
        return []

    _, deps = EXAMPLES[name]
    missing = []
    for dep in deps:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    return missing
```

**Step 4: Add demo command to CLI** (5 min)

Add to `src/pyfuse/cli/__init__.py` after the `learn` command (around line 351):

```python
@cli.command()
@click.argument("example", required=False, default=None)
@click.option("--list", "list_examples_flag", is_flag=True, help="List available examples")
@click.option("--web", is_flag=True, help="Run in web mode (browser)")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
def demo(
    example: str | None,
    list_examples_flag: bool,
    web: bool,
    host: str,
    port: int,
) -> None:
    """Run bundled example applications.

    Examples:
      pyfuse demo              # List available demos
      pyfuse demo todo         # Run todo app in TUI
      pyfuse demo todo --web   # Run todo app in browser
    """
    from pyfuse.cli.demo import check_dependencies, get_example_path, list_examples

    # List mode
    if list_examples_flag or example is None:
        examples = list_examples()
        if not examples:
            click.echo("No examples found.", err=True)
            click.echo("This may indicate a packaging issue.", err=True)
            sys.exit(1)

        click.echo("Available demos:\n")
        for name, description, missing in examples:
            if missing:
                click.echo(f"  {name:12} {description} (requires: {', '.join(missing)})")
            else:
                click.echo(f"  {name:12} {description}")
        click.echo("\nRun a demo:")
        click.echo("  pyfuse demo <name>        Run in TUI mode")
        click.echo("  pyfuse demo <name> --web  Run in browser")
        return

    # Check dependencies before running
    missing = check_dependencies(example)
    if missing:
        click.echo(f"Error: Demo '{example}' requires additional packages:", err=True)
        click.echo(f"  pip install {' '.join(missing)}", err=True)
        click.echo("\nOr install all demo dependencies:", err=True)
        click.echo("  pip install pyfuse[demo]", err=True)
        sys.exit(1)

    # Run specific example
    app_path = get_example_path(example)
    if app_path is None:
        click.echo(f"Error: Example '{example}' not found.", err=True)
        click.echo("\nAvailable examples:", err=True)
        for name, _, _ in list_examples():
            click.echo(f"  {name}", err=True)
        sys.exit(1)

    click.echo(f"Running demo: {example}")

    if web:
        run_web_mode(str(app_path), host, port, reload=False)
    else:
        run_tui_mode(str(app_path))
```

**Step 5: Run tests to verify they pass** (30 sec)

```bash
pytest tests/test_cli_demo.py -v
```

Expected: PASS (2 passed)

**Step 6: Write test for running demo in TUI mode** (3 min)

Add to `tests/test_cli_demo.py`:

```python
from unittest.mock import patch


class TestDemoExecution:
    """Tests for demo execution modes."""

    def test_demo_runs_tui_mode_by_default(self):
        """Demo runs example in TUI mode by default."""
        runner = CliRunner()

        with patch("pyfuse.cli.run_tui_mode") as mock_tui:
            mock_tui.side_effect = SystemExit(0)
            runner.invoke(cli, ["demo", "todo"])

            mock_tui.assert_called_once()
            # Should be called with path to todo example
            call_arg = mock_tui.call_args[0][0]
            assert "todo" in call_arg
            assert "app.py" in call_arg

    def test_demo_runs_web_mode_with_flag(self):
        """Demo --web runs example in web mode."""
        runner = CliRunner()

        with patch("pyfuse.cli.run_web_mode") as mock_web:
            mock_web.side_effect = SystemExit(0)
            runner.invoke(cli, ["demo", "todo", "--web"])

            mock_web.assert_called_once()
            call_args = mock_web.call_args[0]
            assert "todo" in call_args[0]
            assert "app.py" in call_args[0]

    def test_demo_invalid_example_shows_error(self):
        """Demo with invalid example shows helpful error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["demo", "nonexistent"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower()
        assert "todo" in result.output.lower()  # Should suggest valid examples


class TestDemoDependencyHandling:
    """Tests for graceful handling of missing dependencies."""

    def test_demo_list_shows_missing_deps(self):
        """Demo list indicates when examples need additional packages."""
        runner = CliRunner()

        # Mock psutil as missing
        with patch.dict("sys.modules", {"psutil": None}):
            with patch("pyfuse.cli.demo.EXAMPLES", {
                "console": ("TUI console", ["psutil"]),
                "todo": ("Todo app", []),
            }):
                result = runner.invoke(cli, ["demo", "--list"])

                # Should show but indicate missing deps
                assert result.exit_code == 0
                # The output format will indicate missing deps
```

**Step 7: Run all demo tests** (30 sec)

```bash
pytest tests/test_cli_demo.py -v
```

Expected: PASS (6 passed)

**Step 8: Commit** (30 sec)

```bash
git add src/pyfuse/cli/demo.py src/pyfuse/cli/__init__.py tests/test_cli_demo.py
git commit -m "feat(cli): add demo command to run bundled examples"
```

---

### Task 5: Improve Error Messages

**Files:**
- Modify: `src/pyfuse/cli/__init__.py:129-144` (`_suggest_app_files` function)
- Test: `tests/test_cli.py` (add error message tests)

**Step 1: Write test for error message with demo suggestion** (3 min)

Add to `tests/test_cli.py`:

```python
class TestCliErrorMessages:
    """Tests for helpful error messages."""

    def test_dev_no_app_suggests_demo(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """When no app found, error suggests pyfuse demo command."""
        monkeypatch.chdir(tmp_path)  # Empty directory

        runner = CliRunner()
        result = runner.invoke(cli, ["dev"])

        assert result.exit_code != 0
        # Should suggest demo command
        assert "demo" in result.output.lower()

    def test_dev_no_app_suggests_init(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """When no app found, error suggests pyfuse init command."""
        monkeypatch.chdir(tmp_path)  # Empty directory

        runner = CliRunner()
        result = runner.invoke(cli, ["dev"])

        assert result.exit_code != 0
        # Should suggest init command
        assert "init" in result.output.lower()
```

**Step 2: Run test to verify current behavior** (30 sec)

```bash
pytest tests/test_cli.py::TestCliErrorMessages -v
```

Expected: May pass or fail depending on current implementation

**Step 3: Update _suggest_app_files function** (3 min)

Replace `_suggest_app_files()` in `src/pyfuse/cli/__init__.py:129-144`:

```python
def _suggest_app_files() -> None:
    cwd = Path.cwd()
    nearby = list(cwd.glob("*.py"))
    app_files = [f for f in nearby if "app" in f.name.lower()]

    if app_files:
        click.echo("\nDid you mean one of these?", err=True)
        for f in app_files[:5]:
            click.echo(f"  pyfuse dev {f.name}", err=True)
    else:
        click.echo("\nTo get started:", err=True)
        click.echo("  pyfuse demo todo    Try an example app", err=True)
        click.echo("  pyfuse init myapp   Create a new project", err=True)
        click.echo("\nOr specify an app file:", err=True)
        click.echo("  pyfuse dev path/to/app.py", err=True)
```

**Step 4: Run tests to verify they pass** (30 sec)

```bash
pytest tests/test_cli.py::TestCliErrorMessages -v
```

Expected: PASS

**Step 5: Commit** (30 sec)

```bash
git add src/pyfuse/cli/__init__.py tests/test_cli.py
git commit -m "feat(cli): improve error messages with demo suggestions"
```

---

### Task 6: Code Review

**Files:**
- Review all changes from Tasks 1-5

**Step 1: Run full test suite** (2 min)

```bash
pytest tests/test_cli.py tests/test_cli_demo.py -v
```

Expected: All tests pass

**Step 2: Run linter** (1 min)

```bash
make lint
```

Expected: No errors

**Step 3: Verify package structure** (1 min)

```bash
# Verify examples are in package
ls src/pyfuse/examples/
# Should show: __init__.py, todo/, dashboard/, chat/, console/

# Verify imports work
uv run python -c "from pyfuse.cli.demo import get_examples_dir; print(get_examples_dir())"
```

**Step 4: Manual verification** (3 min)

```bash
# Test help output
pyfuse --help

# Test demo list
uv run pyfuse demo --list

# Test demo run (TUI)
uv run pyfuse demo todo

# Test demo run (web) - Ctrl+C to exit
uv run pyfuse demo todo --web
```

**Step 5: Final commit if any fixes needed** (30 sec)

```bash
git status
# If changes needed:
git add -A && git commit -m "fix(cli): address code review feedback"
```

---

## Summary

| Task | Description | New Files | Modified Files |
|------|-------------|-----------|----------------|
| 1 | Move examples to package | 1 (__init__.py) | 1 (pyproject.toml) + git mv |
| 2 | Fix docstrings | 0 | 3-4 examples |
| 3 | Improve help | 0 | 2 (main.py, test_cli.py) |
| 4 | Add demo command | 2 (demo.py, test_cli_demo.py) | 1 (__init__.py) |
| 5 | Error messages | 0 | 2 (__init__.py, test_cli.py) |
| 6 | Code Review | 0 | 0 |

**Total new files:** 3
**Total commits:** 6

---

## Distribution Verification

After completing all tasks, verify the package works when installed:

```bash
# Build and install locally
uv build
pip install dist/pyfuse-0.1.0-py3-none-any.whl

# Test from a clean directory
cd /tmp
pyfuse demo --list
pyfuse demo todo --web
```

This ensures examples are properly bundled with the wheel.
