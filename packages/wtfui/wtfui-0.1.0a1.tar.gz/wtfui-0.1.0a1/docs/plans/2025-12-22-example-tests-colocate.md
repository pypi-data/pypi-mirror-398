# Move Examples to Top-Level and Colocate Tests

> **Execution:** Use `/dev-workflow:execute-plan docs/plans/2025-12-22-example-tests-colocate.md` to implement task-by-task.

**Goal:** Relocate example apps from `src/pyfuse/examples/` to `src/examples/` (top-level package), then move tests inside each example's `tests/` subdirectory. Each example becomes a standalone project.

**Architecture:** Examples become a separate top-level package (`examples.*` instead of `pyfuse.examples.*`). The CLI demo command will be updated to find examples via a new path. Each example app will contain its own `tests/` directory with colocated tests.

**Tech Stack:** Python 3.14+, pytest 8.0.0+

---

## Task Group 1: Move Examples to Top-Level (must be first)

### Task 1: Relocate examples directory and update imports

**Files:**
- Move: `src/pyfuse/examples/` → `src/examples/`
- Modify: `src/pyfuse/cli/demo.py` (update path resolution)
- Modify: `src/examples/**/*.py` (update internal imports)
- Modify: `tests/examples/**/*.py` (update imports)
- Modify: `pyproject.toml` (add examples to packages)

**Step 1: Move the examples directory** (1 min)

```bash
git mv src/pyfuse/examples src/examples
```

**Step 2: Update pyproject.toml packages** (2 min)

In pyproject.toml, find the `[tool.hatch.build.targets.wheel]` section and add `examples` to packages. Also update `[project]` section's package discovery if needed.

Find and update:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/pyfuse"]
```
to:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/pyfuse", "src/examples"]
```

**Step 3: Update CLI demo.py to find examples** (3 min)

In `src/pyfuse/cli/demo.py`, update `get_examples_dir()` function:

```python
def get_examples_dir() -> Path:
    """Get the examples directory path.

    Works for both:
    - Development: running from repo with `uv run pyfuse demo`
    - Production: pip-installed package
    """
    # Try to find examples package directly
    try:
        import examples
        return Path(examples.__file__).parent
    except ImportError:
        # Fallback for development - check relative to pyfuse package
        package_root = Path(pyfuse.__file__).parent.parent
        return package_root / "examples"
```

**Step 4: Update all imports in example files** (5 min)

Update internal imports within examples from `pyfuse.examples.*` to `examples.*`:

In `src/examples/console/app.py`:
```python
# Change from:
from pyfuse.examples.console.components.dashboard import Dashboard
from pyfuse.examples.console.state import SystemState
# To:
from examples.console.components.dashboard import Dashboard
from examples.console.state import SystemState
```

In `src/examples/console/components/__init__.py`:
```python
# Change from:
from pyfuse.examples.console.components.dashboard import Dashboard
from pyfuse.examples.console.components.process_list import ProcessList
from pyfuse.examples.console.components.progress_bar import ProgressBar
# To:
from examples.console.components.dashboard import Dashboard
from examples.console.components.process_list import ProcessList
from examples.console.components.progress_bar import ProgressBar
```

In `src/examples/console/components/dashboard.py`:
```python
# Change from:
from pyfuse.examples.console.components.process_list import ProcessList
from pyfuse.examples.console.components.progress_bar import ProgressBar
from pyfuse.examples.console.state import SystemState
# To:
from examples.console.components.process_list import ProcessList
from examples.console.components.progress_bar import ProgressBar
from examples.console.state import SystemState
```

In `src/examples/console/components/process_list.py`:
```python
# Change from:
from pyfuse.examples.console.state import SystemState
# To:
from examples.console.state import SystemState
```

**Step 5: Update all test imports** (5 min)

Update all files in `tests/examples/` to import from `examples.*` instead of `pyfuse.examples.*`:

Pattern to replace in all test files:
- `from pyfuse.examples.` → `from examples.`
- `import pyfuse.examples.` → `import examples.`

**Step 6: Update examples __init__.py** (1 min)

Update `src/examples/__init__.py`:
```python
"""Bundled example applications for pyfuse demo command."""
```

**Step 7: Verify imports work** (30 sec)

```bash
uv run python -c "from examples.todo.app import TodoApp; print('OK')"
```

Expected: `OK`

**Step 8: Run tests to verify nothing broke** (1 min)

```bash
uv run pytest tests/examples/ -v --tb=short
```

Expected: All tests pass.

**Step 9: Commit** (30 sec)

```bash
git add -A
git commit -m "refactor(examples): relocate to top-level src/examples package"
```

---

## Task Group 2: Update pytest configuration

### Task 2: Update pytest testpaths for new structure

**Files:**
- Modify: `pyproject.toml:122-128`

**Step 1: Read current pytest configuration** (1 min)

Read lines 120-160 of pyproject.toml to see current testpaths and coverage settings.

**Step 2: Update testpaths array** (2 min)

Change `testpaths = ["tests"]` to include example test directories:

```toml
testpaths = [
    "tests",
    "src/examples/todo/tests",
    "src/examples/console/tests",
    "src/examples/chat/tests",
    "src/examples/dashboard/tests",
]
```

**Step 3: Update coverage omit pattern** (2 min)

Find the coverage omit line and update it from:
```toml
omit = ["tests/*", "src/pyfuse/examples/*"]
```
to:
```toml
omit = ["tests/*"]
```

**Step 4: Verify pytest can parse config** (30 sec)

```bash
uv run pytest --collect-only --ignore=tests 2>&1 | head -20
```

Expected: No configuration errors.

**Step 5: Commit** (30 sec)

```bash
git add pyproject.toml
git commit -m "build(pytest): update testpaths for relocated examples"
```

---

## Task Group 3: Todo App Tests (parallel with Groups 4, 5, 6)

### Task 3: Create todo app tests directory and move tests

**Files:**
- Create: `src/examples/todo/tests/__init__.py`
- Create: `src/examples/todo/tests/conftest.py`
- Move: `tests/examples/test_todo_app.py` → `src/examples/todo/tests/test_app.py`
- Move: `tests/examples/test_todo_storage.py` → `src/examples/todo/tests/test_storage.py`
- Move: `tests/examples/test_todo_validation.py` → `src/examples/todo/tests/test_validation.py`

**Step 1: Create tests directory with __init__.py** (1 min)

```bash
mkdir -p src/examples/todo/tests
touch src/examples/todo/tests/__init__.py
```

**Step 2: Create conftest.py for todo tests** (2 min)

Create `src/examples/todo/tests/conftest.py`:

```python
"""Pytest configuration for todo app tests."""

import pytest

from pyfuse.core.scheduler import get_scheduler


@pytest.fixture(autouse=True)
def reset_scheduler_state():
    """Reset the scheduler state before each test."""
    scheduler = get_scheduler()
    scheduler._effects.clear()
    scheduler._pending.clear()
    scheduler._current_effect = None
    yield
    scheduler._effects.clear()
    scheduler._pending.clear()
    scheduler._current_effect = None
```

**Step 3: Move test files** (2 min)

```bash
git mv tests/examples/test_todo_app.py src/examples/todo/tests/test_app.py
git mv tests/examples/test_todo_storage.py src/examples/todo/tests/test_storage.py
git mv tests/examples/test_todo_validation.py src/examples/todo/tests/test_validation.py
```

**Step 4: Update imports in moved tests** (2 min)

In each moved test file, update imports from `from pyfuse.examples.todo.*` to `from examples.todo.*`.

**Step 5: Run todo tests to verify they pass** (30 sec)

```bash
uv run pytest src/examples/todo/tests/ -v
```

Expected: All tests pass.

**Step 6: Commit** (30 sec)

```bash
git add -A
git commit -m "refactor(examples/todo): move tests inside todo app"
```

---

## Task Group 4: Console App Tests (parallel with Groups 3, 5, 6)

### Task 4: Create console app tests directory and move tests

**Files:**
- Create: `src/examples/console/tests/__init__.py`
- Create: `src/examples/console/tests/conftest.py`
- Move: `tests/examples/console/*.py` → `src/examples/console/tests/`
- Move: `tests/examples/test_inline_counter.py` → `src/examples/console/tests/test_inline_counter.py`
- Move: `tests/examples/test_llm_chat.py` → `src/examples/console/tests/test_llm_chat.py`
- Move: `tests/examples/test_console_dashboard.py` → `src/examples/console/tests/test_console_dashboard.py`

**Step 1: Create tests directory with __init__.py** (1 min)

```bash
mkdir -p src/examples/console/tests
touch src/examples/console/tests/__init__.py
```

**Step 2: Create conftest.py for console tests** (2 min)

Create `src/examples/console/tests/conftest.py`:

```python
"""Pytest configuration for console app tests."""

import pytest

from pyfuse.core.scheduler import get_scheduler


@pytest.fixture(autouse=True)
def reset_scheduler_state():
    """Reset the scheduler state before each test."""
    scheduler = get_scheduler()
    scheduler._effects.clear()
    scheduler._pending.clear()
    scheduler._current_effect = None
    yield
    scheduler._effects.clear()
    scheduler._pending.clear()
    scheduler._current_effect = None
```

**Step 3: Move all console test files** (3 min)

```bash
git mv tests/examples/console/test_app.py src/examples/console/tests/test_app.py
git mv tests/examples/console/test_state.py src/examples/console/tests/test_state.py
git mv tests/examples/console/test_dashboard.py src/examples/console/tests/test_dashboard.py
git mv tests/examples/console/test_dashboard_positions.py src/examples/console/tests/test_dashboard_positions.py
git mv tests/examples/console/test_dashboard_with_psutil.py src/examples/console/tests/test_dashboard_with_psutil.py
git mv tests/examples/console/test_process_list.py src/examples/console/tests/test_process_list.py
git mv tests/examples/console/test_progress_bar.py src/examples/console/tests/test_progress_bar.py
git mv tests/examples/console/test_integration.py src/examples/console/tests/test_integration.py
git mv tests/examples/test_inline_counter.py src/examples/console/tests/test_inline_counter.py
git mv tests/examples/test_llm_chat.py src/examples/console/tests/test_llm_chat.py
git mv tests/examples/test_console_dashboard.py src/examples/console/tests/test_console_dashboard.py
```

**Step 4: Remove empty console directory** (30 sec)

```bash
rmdir tests/examples/console 2>/dev/null || rm -rf tests/examples/console
```

**Step 5: Update imports in moved tests** (3 min)

In each moved test file, update imports from `from pyfuse.examples.console.*` to `from examples.console.*`.

**Step 6: Run console tests to verify they pass** (30 sec)

```bash
uv run pytest src/examples/console/tests/ -v
```

Expected: All tests pass.

**Step 7: Commit** (30 sec)

```bash
git add -A
git commit -m "refactor(examples/console): move tests inside console app"
```

---

## Task Group 5: Chat App Tests (parallel with Groups 3, 4, 6)

### Task 5: Create chat app tests directory and move tests

**Files:**
- Create: `src/examples/chat/tests/__init__.py`
- Create: `src/examples/chat/tests/conftest.py`
- Move: `tests/examples/test_chat_rpc.py` → `src/examples/chat/tests/test_rpc.py`

**Step 1: Create tests directory with __init__.py** (1 min)

```bash
mkdir -p src/examples/chat/tests
touch src/examples/chat/tests/__init__.py
```

**Step 2: Create conftest.py for chat tests** (2 min)

Create `src/examples/chat/tests/conftest.py`:

```python
"""Pytest configuration for chat app tests."""

import pytest

from pyfuse.core.scheduler import get_scheduler


@pytest.fixture(autouse=True)
def reset_scheduler_state():
    """Reset the scheduler state before each test."""
    scheduler = get_scheduler()
    scheduler._effects.clear()
    scheduler._pending.clear()
    scheduler._current_effect = None
    yield
    scheduler._effects.clear()
    scheduler._pending.clear()
    scheduler._current_effect = None
```

**Step 3: Move test_chat_rpc.py** (1 min)

```bash
git mv tests/examples/test_chat_rpc.py src/examples/chat/tests/test_rpc.py
```

**Step 4: Update imports in moved test** (1 min)

Update imports from `from pyfuse.examples.chat.*` to `from examples.chat.*`.

**Step 5: Run chat tests to verify they pass** (30 sec)

```bash
uv run pytest src/examples/chat/tests/ -v
```

Expected: All tests pass.

**Step 6: Commit** (30 sec)

```bash
git add -A
git commit -m "refactor(examples/chat): move tests inside chat app"
```

---

## Task Group 6: Dashboard App Tests (parallel with Groups 3, 4, 5)

### Task 6: Create dashboard app tests directory and move tests

**Files:**
- Create: `src/examples/dashboard/tests/__init__.py`
- Create: `src/examples/dashboard/tests/conftest.py`
- Move: `tests/examples/test_dashboard_components.py` → `src/examples/dashboard/tests/test_components.py`

**Step 1: Create tests directory with __init__.py** (1 min)

```bash
mkdir -p src/examples/dashboard/tests
touch src/examples/dashboard/tests/__init__.py
```

**Step 2: Create conftest.py for dashboard tests** (2 min)

Create `src/examples/dashboard/tests/conftest.py`:

```python
"""Pytest configuration for dashboard app tests."""

import pytest

from pyfuse.core.scheduler import get_scheduler


@pytest.fixture(autouse=True)
def reset_scheduler_state():
    """Reset the scheduler state before each test."""
    scheduler = get_scheduler()
    scheduler._effects.clear()
    scheduler._pending.clear()
    scheduler._current_effect = None
    yield
    scheduler._effects.clear()
    scheduler._pending.clear()
    scheduler._current_effect = None
```

**Step 3: Move test_dashboard_components.py** (1 min)

```bash
git mv tests/examples/test_dashboard_components.py src/examples/dashboard/tests/test_components.py
```

**Step 4: Update imports in moved test** (1 min)

Update imports from `from pyfuse.examples.dashboard.*` to `from examples.dashboard.*`.

**Step 5: Run dashboard tests to verify they pass** (30 sec)

```bash
uv run pytest src/examples/dashboard/tests/ -v
```

Expected: All tests pass.

**Step 6: Commit** (30 sec)

```bash
git add -A
git commit -m "refactor(examples/dashboard): move tests inside dashboard app"
```

---

## Task Group 7: Cleanup (depends on Groups 3-6)

### Task 7: Remove empty tests/examples directory and verify full test suite

**Files:**
- Delete: `tests/examples/` directory (should be empty)

**Step 1: Verify tests/examples is empty** (30 sec)

```bash
ls -la tests/examples/ 2>/dev/null || echo "Directory already removed"
```

Expected: Directory should be empty or already removed.

**Step 2: Remove tests/examples directory** (30 sec)

```bash
rm -rf tests/examples/
```

**Step 3: Run full test suite to verify nothing broke** (2 min)

```bash
uv run pytest --ignore=tests/e2e -v --tb=short
```

Expected: All tests pass. Test count should be the same as before migration.

**Step 4: Run make test-fast to verify CI-like execution** (1 min)

```bash
make test-fast
```

Expected: All tests pass.

**Step 5: Commit cleanup** (30 sec)

```bash
git add -A
git commit -m "refactor(tests): remove empty tests/examples directory"
```

---

## Task Group 8: Final (depends on Group 7)

### Task 8: Code Review

Dispatch code-reviewer agent to review all changes made during this plan execution.

---

## Parallel Execution Groups

| Task Group | Tasks | Rationale |
|------------|-------|-----------|
| Group 1 | Task 1 | Must relocate examples first |
| Group 2 | Task 2 | Config update after relocation |
| Groups 3-6 | Tasks 3, 4, 5, 6 | Independent example apps, no file overlap |
| Group 7 | Task 7 | Cleanup depends on all moves completing |
| Group 8 | Task 8 | Code review after all changes |
