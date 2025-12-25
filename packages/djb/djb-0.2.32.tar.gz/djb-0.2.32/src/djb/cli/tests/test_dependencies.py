"""Tests for djb dependencies command."""

from __future__ import annotations

from click.testing import CliRunner

from djb.cli.djb import djb_cli


class TestDjbDependencies:
    """Tests for djb dependencies command."""

    def test_dependencies_help(self, tmp_path, monkeypatch):
        """Test that dependencies --help works."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\ndependencies = ["djb"]\n'
        )

        runner = CliRunner()
        result = runner.invoke(djb_cli, ["dependencies", "--help"])
        assert result.exit_code == 0
        assert "Refresh dependencies" in result.output
        assert "--bump" in result.output

    def test_dependencies_requires_scope(self, tmp_path, monkeypatch):
        """Test that dependencies requires --frontend or --backend."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\ndependencies = ["djb"]\n'
        )

        runner = CliRunner()
        result = runner.invoke(djb_cli, ["dependencies"])
        assert result.exit_code == 1
        assert "Specify --frontend and/or --backend" in result.output
