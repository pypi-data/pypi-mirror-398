"""Tests for djb.testing.typecheck module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from djb.testing.typecheck import run_typecheck, test_typecheck


class TestRunTypecheck:
    """Tests for run_typecheck function."""

    def test_success(self, tmp_path):
        """Test successful typecheck."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\n')

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "0 errors"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            # Should not raise
            run_typecheck(tmp_path)

            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][0] == ["pyright"]
            assert call_args[1]["cwd"] == tmp_path

    def test_failure_raises_assertion(self, tmp_path):
        """Test typecheck failure raises AssertionError."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\n')

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "error: Cannot find module 'foo'"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(AssertionError) as exc_info:
                run_typecheck(tmp_path)

            assert "Type checking failed" in str(exc_info.value)
            assert "Cannot find module" in str(exc_info.value)

    def test_includes_stderr_in_error(self, tmp_path):
        """Test stderr is included in error message."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\n')

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "pyright: command not found"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(AssertionError) as exc_info:
                run_typecheck(tmp_path)

            assert "stderr" in str(exc_info.value)
            assert "pyright: command not found" in str(exc_info.value)

    def test_auto_finds_project_root(self, tmp_path, monkeypatch):
        """Test run_typecheck finds project root when not provided."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\n')

        monkeypatch.chdir(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            run_typecheck()  # No argument

            call_args = mock_run.call_args
            assert call_args[1]["cwd"] == tmp_path

    def test_accepts_string_path(self, tmp_path):
        """Test run_typecheck accepts string path."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\n')

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            run_typecheck(str(tmp_path))  # String instead of Path

            call_args = mock_run.call_args
            assert call_args[1]["cwd"] == tmp_path


class TestTestTypecheck:
    """Tests for test_typecheck pytest function."""

    def test_is_importable(self):
        """Test that test_typecheck can be imported."""
        assert callable(test_typecheck)

    def test_runs_typecheck(self, tmp_path, monkeypatch):
        """Test test_typecheck runs typecheck."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\n')

        monkeypatch.chdir(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            # Should not raise
            test_typecheck()
