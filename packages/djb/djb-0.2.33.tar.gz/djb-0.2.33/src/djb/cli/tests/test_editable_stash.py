"""Tests for djb editable_stash module."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from djb.cli.editable_stash import (
    bust_uv_cache,
    regenerate_uv_lock,
    restore_editable,
    stashed_editable,
)


class TestBustUvCache:
    """Tests for bust_uv_cache function."""

    def test_runs_uv_cache_clean(self):
        """Test runs uv cache clean djb command."""
        with patch("djb.cli.editable_stash.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            bust_uv_cache()

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["uv", "cache", "clean", "djb"]


class TestRegenerateUvLock:
    """Tests for regenerate_uv_lock function."""

    def test_runs_uv_lock_refresh(self, tmp_path):
        """Test runs uv lock --refresh command."""
        with patch("djb.cli.editable_stash.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            result = regenerate_uv_lock(tmp_path)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["uv", "lock", "--refresh"]
        assert mock_run.call_args[1]["cwd"] == tmp_path

    def test_returns_false_on_failure(self, tmp_path):
        """Test returns False when uv lock fails."""
        with patch("djb.cli.editable_stash.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="error")
            result = regenerate_uv_lock(tmp_path, quiet=True)

        assert result is False

    def test_prints_error_when_not_quiet(self, tmp_path):
        """Test prints error message when not in quiet mode."""
        with patch("djb.cli.editable_stash.subprocess.run") as mock_run:
            with patch("djb.cli.editable_stash.logger") as mock_logger:
                mock_run.return_value = Mock(returncode=1, stdout="", stderr="some error")
                regenerate_uv_lock(tmp_path, quiet=False)

        # Should have printed an error via logger
        mock_logger.fail.assert_called()


class TestStashedEditableContextManager:
    """Tests for stashed_editable context manager."""

    def test_yields_true_when_editable(self, tmp_path):
        """Test yields True when djb was in editable mode."""
        with (
            patch("djb.cli.editable_stash.is_djb_editable", return_value=True),
            patch("djb.cli.editable_stash.uninstall_editable_djb") as mock_uninstall,
            patch("djb.cli.editable_stash.install_editable_djb") as mock_install,
        ):
            with stashed_editable(tmp_path, quiet=True) as was_editable:
                assert was_editable is True
                # Inside context: should have called uninstall
                mock_uninstall.assert_called_once_with(tmp_path, quiet=True)
                mock_install.assert_not_called()

            # After context: should have called install
            mock_install.assert_called_once_with(tmp_path, quiet=True)

    def test_yields_false_when_not_editable(self, tmp_path):
        """Test yields False when djb was not in editable mode."""
        with (
            patch("djb.cli.editable_stash.is_djb_editable", return_value=False),
            patch("djb.cli.editable_stash.uninstall_editable_djb") as mock_uninstall,
            patch("djb.cli.editable_stash.install_editable_djb") as mock_install,
        ):
            with stashed_editable(tmp_path, quiet=True) as was_editable:
                assert was_editable is False
                # Should not call uninstall when not editable
                mock_uninstall.assert_not_called()

            # Should not call install when was not editable
            mock_install.assert_not_called()

    def test_restores_on_exception(self, tmp_path):
        """Test context manager restores editable mode even on exception."""
        with (
            patch("djb.cli.editable_stash.is_djb_editable", return_value=True),
            patch("djb.cli.editable_stash.uninstall_editable_djb"),
            patch("djb.cli.editable_stash.install_editable_djb") as mock_install,
        ):
            with pytest.raises(ValueError):
                with stashed_editable(tmp_path, quiet=True):
                    raise ValueError("Test exception")

            # Should still have called install to restore
            mock_install.assert_called_once_with(tmp_path, quiet=True)

    def test_prints_messages_when_not_quiet(self, tmp_path):
        """Test prints status messages when not in quiet mode."""
        with (
            patch("djb.cli.editable_stash.is_djb_editable", return_value=True),
            patch("djb.cli.editable_stash.uninstall_editable_djb"),
            patch("djb.cli.editable_stash.install_editable_djb"),
            patch("djb.cli.editable_stash.logger") as mock_logger,
        ):
            with stashed_editable(tmp_path, quiet=False):
                pass

        # Should have printed messages via logger
        assert mock_logger.info.call_count >= 2


class TestRestoreEditable:
    """Tests for restore_editable function."""

    def test_calls_install_editable_djb(self, tmp_path):
        """Test calls install_editable_djb with correct arguments."""
        with patch("djb.cli.editable_stash.install_editable_djb") as mock_install:
            mock_install.return_value = True
            result = restore_editable(tmp_path, quiet=True)

        assert result is True
        mock_install.assert_called_once_with(tmp_path, quiet=True)

    def test_returns_false_on_failure(self, tmp_path):
        """Test returns False when install fails."""
        with patch("djb.cli.editable_stash.install_editable_djb") as mock_install:
            mock_install.return_value = False
            result = restore_editable(tmp_path)

        assert result is False
