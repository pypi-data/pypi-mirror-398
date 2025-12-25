"""Tests for djb secrets CLI commands and safeguards."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch

import pytest

from djb.cli.secrets import (
    _check_homebrew_installed,
    _check_prerequisites,
    _ensure_prerequisites,
    _install_with_homebrew,
    rotate,
    secrets,
)
from djb.secrets import (
    PROJECT_SECRETS_ENVIRONMENTS,
    SecretsManager,
    load_secrets_for_mode,
    parse_sops_config,
)
from djb.types import Mode


class TestRotateCommandSafeguards:
    """Tests for safeguards in the rotate command."""

    def test_invalid_key_rejected(
        self,
        runner,
        secrets_dir: Path,
        alice_key: tuple[Path, str],
        setup_sops_config: Callable[[dict[str, str]], Path],
    ):
        """Test that adding an invalid key is rejected."""
        alice_key_path, alice_public = alice_key
        setup_sops_config({alice_public: "alice@example.com"})

        # Patch get_default_key_path in both modules (they have separate imports)
        with (
            patch("djb.cli.secrets.get_default_key_path", return_value=alice_key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=alice_key_path),
        ):
            result = runner.invoke(
                rotate,
                [
                    "--add-key",
                    "garbage-not-a-key",
                    "--add-email",
                    "bob@example.com",
                    "--secrets-dir",
                    str(secrets_dir),
                ],
            )

        assert result.exit_code != 0
        assert "Invalid age public key" in result.output

    def test_cannot_remove_last_recipient(
        self,
        runner,
        secrets_dir: Path,
        alice_key: tuple[Path, str],
        setup_sops_config: Callable[[dict[str, str]], Path],
    ):
        """Test that removing the last recipient is prevented."""
        alice_key_path, alice_public = alice_key
        setup_sops_config({alice_public: "alice@example.com"})

        # Patch get_default_key_path in both modules (they have separate imports)
        with (
            patch("djb.cli.secrets.get_default_key_path", return_value=alice_key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=alice_key_path),
        ):
            result = runner.invoke(
                rotate,
                [
                    "--remove-key",
                    "alice@example.com",
                    "--secrets-dir",
                    str(secrets_dir),
                ],
            )

        assert result.exit_code != 0
        assert "Cannot remove the last recipient" in result.output

    def test_can_remove_when_multiple_recipients(
        self,
        runner,
        secrets_dir: Path,
        alice_key: tuple[Path, str],
        bob_key: tuple[Path, str],
        setup_sops_config: Callable[[dict[str, str]], Path],
    ):
        """Test that removing a recipient works when others exist."""
        alice_key_path, alice_public = alice_key
        _, bob_public = bob_key

        setup_sops_config(
            {
                alice_public: "alice@example.com",
                bob_public: "bob@example.com",
            }
        )

        # Create encrypted project secrets for both (dev.yaml is per-user and gitignored)
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        for env in PROJECT_SECRETS_ENVIRONMENTS:
            manager.save_secrets(env, {"django_secret_key": "test"}, [alice_public, bob_public])

        # Patch get_default_key_path in both modules (they have separate imports)
        with (
            patch("djb.cli.secrets.get_default_key_path", return_value=alice_key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=alice_key_path),
        ):
            result = runner.invoke(
                rotate,
                [
                    "--remove-key",
                    "bob@example.com",
                    "--secrets-dir",
                    str(secrets_dir),
                ],
            )

        assert result.exit_code == 0
        assert "Removed key" in result.output

        # Verify Bob was removed from .sops.yaml
        recipients = parse_sops_config(secrets_dir)
        assert alice_public in recipients
        assert bob_public not in recipients

    def test_valid_key_accepted(
        self,
        runner,
        secrets_dir: Path,
        alice_key: tuple[Path, str],
        bob_key: tuple[Path, str],
        setup_sops_config: Callable[[dict[str, str]], Path],
    ):
        """Test that adding a valid key works."""
        alice_key_path, alice_public = alice_key
        _, bob_public = bob_key

        setup_sops_config({alice_public: "alice@example.com"})

        # Create encrypted project secrets (dev.yaml is per-user and gitignored)
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        for env in PROJECT_SECRETS_ENVIRONMENTS:
            manager.save_secrets(env, {"django_secret_key": "test"}, [alice_public])

        # Patch get_default_key_path in both modules (they have separate imports)
        with (
            patch("djb.cli.secrets.get_default_key_path", return_value=alice_key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=alice_key_path),
        ):
            result = runner.invoke(
                rotate,
                [
                    "--add-key",
                    bob_public,
                    "--add-email",
                    "bob@example.com",
                    "--secrets-dir",
                    str(secrets_dir),
                ],
            )

        assert result.exit_code == 0
        assert "Added key for bob@example.com" in result.output

        # Verify Bob was added to .sops.yaml
        recipients = parse_sops_config(secrets_dir)
        assert alice_public in recipients
        assert bob_public in recipients


class TestLoadSecretsForMode:
    """Tests for load_secrets_for_mode() function."""

    def test_development_loads_dev_secrets(
        self,
        secrets_dir: Path,
        alice_key: tuple[Path, str],
        setup_sops_config,
    ):
        """Test that Mode.DEVELOPMENT loads dev.yaml secrets."""
        alice_key_path, alice_public = alice_key
        setup_sops_config({alice_public: "alice@example.com"})

        # Create dev secrets
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        manager.save_secrets("dev", {"env": "development", "api_key": "dev-key"}, [alice_public])

        # Load using Mode.DEVELOPMENT
        secrets = load_secrets_for_mode(
            mode=Mode.DEVELOPMENT,
            secrets_dir=secrets_dir,
            key_path=alice_key_path,
        )

        assert secrets["env"] == "development"
        assert secrets["api_key"] == "dev-key"

    def test_staging_loads_staging_secrets(
        self,
        secrets_dir: Path,
        alice_key: tuple[Path, str],
        setup_sops_config,
    ):
        """Test that Mode.STAGING loads staging.yaml secrets."""
        alice_key_path, alice_public = alice_key
        setup_sops_config({alice_public: "alice@example.com"})

        # Create staging secrets
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        manager.save_secrets(
            "staging", {"env": "staging", "api_key": "staging-key"}, [alice_public]
        )

        # Load using Mode.STAGING
        secrets = load_secrets_for_mode(
            mode=Mode.STAGING,
            secrets_dir=secrets_dir,
            key_path=alice_key_path,
        )

        assert secrets["env"] == "staging"
        assert secrets["api_key"] == "staging-key"

    def test_production_loads_production_secrets(
        self,
        secrets_dir: Path,
        alice_key: tuple[Path, str],
        setup_sops_config,
    ):
        """Test that Mode.PRODUCTION loads production.yaml secrets."""
        alice_key_path, alice_public = alice_key
        setup_sops_config({alice_public: "alice@example.com"})

        # Create production secrets
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        manager.save_secrets(
            "production", {"env": "production", "api_key": "prod-key"}, [alice_public]
        )

        # Load using Mode.PRODUCTION
        secrets = load_secrets_for_mode(
            mode=Mode.PRODUCTION,
            secrets_dir=secrets_dir,
            key_path=alice_key_path,
        )

        assert secrets["env"] == "production"
        assert secrets["api_key"] == "prod-key"


class TestPrerequisiteChecks:
    """Tests for prerequisite checking functions."""

    def test_check_homebrew_installed_when_present(self):
        """Test _check_homebrew_installed returns True when brew exists."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            assert _check_homebrew_installed() is True

    def test_check_homebrew_installed_when_missing(self):
        """Test _check_homebrew_installed returns False when brew missing."""
        with patch("shutil.which", return_value=None):
            assert _check_homebrew_installed() is False

    def test_install_with_homebrew_success(self):
        """Test _install_with_homebrew returns True on success."""
        mock_result = type("Result", (), {"returncode": 0, "stderr": ""})()
        with (
            patch("subprocess.run", return_value=mock_result),
            patch("djb.cli.secrets.logger"),
        ):
            result = _install_with_homebrew("sops")
            assert result is True

    def test_install_with_homebrew_failure(self):
        """Test _install_with_homebrew returns False on failure."""
        mock_result = type("Result", (), {"returncode": 1, "stderr": "error"})()
        with (
            patch("subprocess.run", return_value=mock_result),
            patch("djb.cli.secrets.logger"),
        ):
            result = _install_with_homebrew("sops")
            assert result is False

    def test_install_with_homebrew_exception(self):
        """Test _install_with_homebrew handles exceptions."""
        with (
            patch("subprocess.run", side_effect=OSError("Command failed")),
            patch("djb.cli.secrets.logger"),
        ):
            result = _install_with_homebrew("sops")
            assert result is False

    def test_ensure_prerequisites_all_installed(self):
        """Test _ensure_prerequisites returns True when all tools installed."""
        with (
            patch("djb.cli.secrets.check_sops_installed", return_value=True),
            patch("djb.cli.secrets.check_age_installed", return_value=True),
            patch("djb.cli.secrets.logger"),
        ):
            result = _ensure_prerequisites()
            assert result is True

    def test_ensure_prerequisites_missing_tools_no_homebrew(self):
        """Test _ensure_prerequisites returns False when tools missing and no brew."""
        with (
            patch("djb.cli.secrets.check_sops_installed", return_value=False),
            patch("djb.cli.secrets.check_age_installed", return_value=False),
            patch("djb.cli.secrets._check_homebrew_installed", return_value=False),
            patch("platform.system", return_value="Linux"),
            patch("djb.cli.secrets.logger"),
        ):
            result = _ensure_prerequisites()
            assert result is False

    def test_ensure_prerequisites_auto_install_macos(self):
        """Test _ensure_prerequisites auto-installs on macOS with Homebrew."""
        with (
            patch("djb.cli.secrets.check_sops_installed", return_value=False),
            patch("djb.cli.secrets.check_age_installed", return_value=False),
            patch("djb.cli.secrets._check_homebrew_installed", return_value=True),
            patch("platform.system", return_value="Darwin"),
            patch("djb.cli.secrets._install_with_homebrew", return_value=True) as mock_install,
            patch("djb.cli.secrets.logger"),
        ):
            result = _ensure_prerequisites()
            assert result is True
            # Should have called install for both tools
            assert mock_install.call_count == 2

    def test_ensure_prerequisites_quiet_mode(self):
        """Test _ensure_prerequisites doesn't log when quiet=True."""
        with (
            patch("djb.cli.secrets.check_sops_installed", return_value=True),
            patch("djb.cli.secrets.check_age_installed", return_value=True),
            patch("djb.cli.secrets.logger") as mock_logger,
        ):
            _ensure_prerequisites(quiet=True)
            # Should not call done for installed tools in quiet mode
            mock_logger.done.assert_not_called()

    def test_ensure_prerequisites_macos_no_homebrew(self):
        """Test _ensure_prerequisites on macOS without Homebrew shows install hints."""
        with (
            patch("djb.cli.secrets.check_sops_installed", return_value=False),
            patch("djb.cli.secrets.check_age_installed", return_value=True),
            patch("djb.cli.secrets._check_homebrew_installed", return_value=False),
            patch("platform.system", return_value="Darwin"),
            patch("djb.cli.secrets.logger") as mock_logger,
        ):
            result = _ensure_prerequisites()
            assert result is False
            # Should suggest installing Homebrew first
            mock_logger.info.assert_any_call("  First install Homebrew: https://brew.sh")

    def test_ensure_prerequisites_auto_install_fails(self):
        """Test _ensure_prerequisites returns False when auto-install fails."""
        with (
            patch("djb.cli.secrets.check_sops_installed", return_value=False),
            patch("djb.cli.secrets.check_age_installed", return_value=True),
            patch("djb.cli.secrets._check_homebrew_installed", return_value=True),
            patch("platform.system", return_value="Darwin"),
            patch("djb.cli.secrets._install_with_homebrew", return_value=False),
            patch("djb.cli.secrets.logger"),
        ):
            result = _ensure_prerequisites()
            assert result is False

    def test_check_prerequisites_exits_on_failure(self):
        """Test _check_prerequisites calls sys.exit when prerequisites fail."""
        with (
            patch("djb.cli.secrets._ensure_prerequisites", return_value=False),
            pytest.raises(SystemExit) as exc_info,
        ):
            _check_prerequisites()
        assert exc_info.value.code == 1


class TestSecretsCommandGroup:
    """Tests for the secrets command group."""

    def test_secrets_help(self, runner):
        """Test secrets --help shows available commands."""
        result = runner.invoke(secrets, ["--help"])
        assert result.exit_code == 0
        assert "Manage encrypted secrets" in result.output

    def test_secrets_init_help(self, runner):
        """Test secrets init --help shows options."""
        result = runner.invoke(secrets, ["init", "--help"])
        assert result.exit_code == 0
        assert "--key-path" in result.output
        assert "--secrets-dir" in result.output
        assert "--force" in result.output


class TestListEnvironmentsCommand:
    """Tests for the secrets list command."""

    def test_list_no_secrets_dir(self, runner, tmp_path, monkeypatch):
        """Test list command when secrets directory doesn't exist."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(secrets, ["list"])
        assert result.exit_code == 0
        assert "No secrets directory found" in result.output

    def test_list_empty_secrets_dir(self, runner, tmp_path, monkeypatch):
        """Test list command when secrets directory is empty."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "secrets").mkdir()
        result = runner.invoke(secrets, ["list"])
        assert result.exit_code == 0
        assert "No secret files found" in result.output

    def test_list_with_secrets(self, runner, tmp_path, monkeypatch):
        """Test list command shows available environments."""
        monkeypatch.chdir(tmp_path)
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()
        (secrets_dir / "dev.yaml").write_text("test: value")
        (secrets_dir / "production.yaml").write_text("test: value")
        (secrets_dir / ".sops.yaml").write_text("config: true")  # Should be excluded

        result = runner.invoke(secrets, ["list"])
        assert result.exit_code == 0
        assert "Available environments" in result.output
        assert "dev" in result.output
        assert "production" in result.output
        assert ".sops" not in result.output

    def test_list_custom_secrets_dir(self, runner, tmp_path):
        """Test list command with custom --secrets-dir."""
        custom_dir = tmp_path / "custom_secrets"
        custom_dir.mkdir()
        (custom_dir / "staging.yaml").write_text("test: value")

        result = runner.invoke(secrets, ["list", "--secrets-dir", str(custom_dir)])
        assert result.exit_code == 0
        assert "staging" in result.output


class TestGenerateKeyCommand:
    """Tests for the secrets generate-key command."""

    def test_generate_key_output(self, runner):
        """Test generate-key produces a valid Django secret key."""
        result = runner.invoke(secrets, ["generate-key"])
        assert result.exit_code == 0
        assert "Generated Django secret key" in result.output

    def test_generate_key_unique(self, runner):
        """Test generate-key produces unique keys each time."""
        result1 = runner.invoke(secrets, ["generate-key"])
        result2 = runner.invoke(secrets, ["generate-key"])
        # Extract keys (they should be different)
        assert result1.output != result2.output


class TestExportKeyCommand:
    """Tests for the secrets export-key command."""

    def test_export_key_not_found(self, runner, tmp_path, monkeypatch):
        """Test export-key fails when key doesn't exist."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(secrets, ["export-key"])
        assert result.exit_code == 1
        assert "Age key not found" in result.output

    def test_export_key_success(self, runner, tmp_path):
        """Test export-key outputs the secret key."""
        key_file = tmp_path / "keys.txt"
        key_file.write_text(
            "# created: 2024-01-01\n" "# public key: age1xyz\n" "AGE-SECRET-KEY-1ABCDEFGHIJKLMNOP\n"
        )

        result = runner.invoke(secrets, ["export-key", "--key-path", str(key_file)])
        assert result.exit_code == 0
        assert "AGE-SECRET-KEY-1ABCDEFGHIJKLMNOP" in result.output

    def test_export_key_no_secret_in_file(self, runner, tmp_path):
        """Test export-key fails when file has no secret key."""
        key_file = tmp_path / "keys.txt"
        key_file.write_text("# just comments\n")

        result = runner.invoke(secrets, ["export-key", "--key-path", str(key_file)])
        assert result.exit_code == 1
        assert "No AGE-SECRET-KEY found" in result.output


class TestViewCommand:
    """Tests for the secrets view command."""

    def test_view_all_secrets(
        self,
        runner,
        secrets_dir: Path,
        alice_key: tuple[Path, str],
        setup_sops_config,
    ):
        """Test view command shows all secrets."""
        alice_key_path, alice_public = alice_key
        setup_sops_config({alice_public: "alice@example.com"})

        # Create dev secrets
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        manager.save_secrets("dev", {"api_key": "test-key", "debug": True}, [alice_public])

        result = runner.invoke(
            secrets,
            [
                "view",
                "dev",
                "--key-path",
                str(alice_key_path),
                "--secrets-dir",
                str(secrets_dir),
            ],
        )
        assert result.exit_code == 0
        assert "api_key" in result.output
        assert "test-key" in result.output

    def test_view_specific_key(
        self,
        runner,
        secrets_dir: Path,
        alice_key: tuple[Path, str],
        setup_sops_config,
    ):
        """Test view command with --key option shows single key."""
        alice_key_path, alice_public = alice_key
        setup_sops_config({alice_public: "alice@example.com"})

        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        manager.save_secrets("dev", {"api_key": "my-api-key", "other": "value"}, [alice_public])

        result = runner.invoke(
            secrets,
            [
                "view",
                "dev",
                "--key",
                "api_key",
                "--key-path",
                str(alice_key_path),
                "--secrets-dir",
                str(secrets_dir),
            ],
        )
        assert result.exit_code == 0
        assert "api_key" in result.output
        assert "my-api-key" in result.output
        # Should not show other keys
        assert "other" not in result.output

    def test_view_key_not_found(
        self,
        runner,
        secrets_dir: Path,
        alice_key: tuple[Path, str],
        setup_sops_config,
    ):
        """Test view command fails when key doesn't exist."""
        alice_key_path, alice_public = alice_key
        setup_sops_config({alice_public: "alice@example.com"})

        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        manager.save_secrets("dev", {"existing": "value"}, [alice_public])

        result = runner.invoke(
            secrets,
            [
                "view",
                "dev",
                "--key",
                "nonexistent",
                "--key-path",
                str(alice_key_path),
                "--secrets-dir",
                str(secrets_dir),
            ],
        )
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_view_missing_age_key(self, runner, tmp_path, monkeypatch):
        """Test view command fails when age key doesn't exist."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(secrets, ["view", "dev"])
        assert result.exit_code == 1
        assert "not found" in result.output
