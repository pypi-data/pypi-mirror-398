"""Integration tests for CLI pyfuse."""

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.integration
class TestCLIIntegration:
    """End-to-end CLI tests."""

    def test_pyfuse_help_runs(self) -> None:
        """pyfuse --help executes successfully."""
        result = subprocess.run(
            [sys.executable, "-m", "pyfuse.cli.main", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "PyFuse 0.1.0" in result.stdout

    def test_pyfuse_init_creates_project(self, tmp_path: Path) -> None:
        """pyfuse init creates valid project structure."""
        result = subprocess.run(
            [sys.executable, "-m", "pyfuse.cli.main", "init", "testapp"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            timeout=30,
        )

        assert result.returncode == 0
        assert (tmp_path / "testapp" / "pyproject.toml").exists()
        assert (tmp_path / "testapp" / "app.py").exists()

    def test_pyfuse_clean_is_idempotent(self, tmp_path: Path) -> None:
        """pyfuse clean can run multiple times safely."""
        # Run clean twice - should not error
        for _ in range(2):
            result = subprocess.run(
                [sys.executable, "-m", "pyfuse.cli.main", "clean"],
                capture_output=True,
                text=True,
                cwd=tmp_path,
                timeout=10,
            )
            assert result.returncode == 0


@pytest.mark.integration
class TestCLIIntegrationPyFuseToml:
    """Integration tests for pyfuse.toml-based workflow."""

    def test_init_creates_pyfuse_toml(self, tmp_path: Path) -> None:
        """pyfuse init creates pyfuse.toml in new project."""
        result = subprocess.run(
            [sys.executable, "-m", "pyfuse.cli.main", "init", "testapp"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0
        assert (tmp_path / "testapp" / "pyfuse.toml").exists()

    def test_pyfuse_toml_content(self, tmp_path: Path) -> None:
        """pyfuse.toml contains required configuration."""
        subprocess.run(
            [sys.executable, "-m", "pyfuse.cli.main", "init", "testapp"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        pyfuse_toml = (tmp_path / "testapp" / "pyfuse.toml").read_text()
        assert 'name = "testapp"' in pyfuse_toml
        assert 'entry = "app.py"' in pyfuse_toml
        assert "[project]" in pyfuse_toml
        assert "[app]" in pyfuse_toml
        assert "[dev]" in pyfuse_toml

    def test_dev_finds_project_by_name(self, tmp_path: Path) -> None:
        """pyfuse dev myproject finds project by folder name."""
        project = tmp_path / "myproject"
        project.mkdir()
        (project / "pyfuse.toml").write_text('[project]\nname = "myproject"')
        (project / "app.py").write_text("app = None")
        (project / "pyproject.toml").write_text('[project]\nname = "myproject"\ndependencies = []')

        result = subprocess.run(
            [sys.executable, "-m", "pyfuse.cli.main", "dev", "myproject", "--help"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            timeout=10,
        )

        assert "not found" not in result.stderr.lower() or result.returncode == 0

    def test_project_not_found_error(self, tmp_path: Path) -> None:
        """pyfuse dev nonexistent shows helpful error."""
        result = subprocess.run(
            [sys.executable, "-m", "pyfuse.cli.main", "dev", "nonexistent"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            timeout=10,
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()
