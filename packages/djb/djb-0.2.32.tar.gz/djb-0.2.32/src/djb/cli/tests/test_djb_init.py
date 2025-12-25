"""Tests for djb init command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import djb
import pytest

from djb.cli.djb import djb_cli
from djb.cli.init import _add_djb_to_installed_apps
from djb.cli.secrets import _get_template
from djb.config import PROJECT, load_config
from djb.secrets import (
    SECRETS_ENVIRONMENTS,
    SecretsManager,
    create_sops_config,
    generate_age_key,
    init_or_upgrade_secrets,
    parse_sops_config,
)
from djb.secrets.init import PROJECT_SECRETS_ENVIRONMENTS
from djb.secrets.init import _get_encrypted_recipients


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run to avoid actual command execution."""
    with patch("djb.cli.init.subprocess.run") as mock:
        # Default: commands succeed
        mock.return_value = Mock(returncode=0, stdout=b"", stderr=b"")
        yield mock


@pytest.fixture(autouse=True)
def mock_configure_all_fields():
    """Mock _configure_all_fields to avoid interactive prompts in tests."""
    mock_result = {
        "name": "Test User",
        "email": "test@example.com",
        "project_name": "test-project",
        "hostname": "test-project.com",
        "log_level": "info",
    }
    with patch("djb.cli.init._configure_all_fields", return_value=mock_result):
        yield


@pytest.fixture(autouse=True)
def mock_sync_identity_to_git():
    """Mock _sync_identity_to_git to avoid git config calls in tests."""
    with patch("djb.cli.init._sync_identity_to_git"):
        yield


@pytest.fixture(autouse=True)
def disable_gpg_protection():
    """Disable GPG protection to avoid pinentry prompts in tests.

    GPG requires an interactive pinentry for decryption, which fails in
    automated test environments. By marking GPG as unavailable, we skip
    the GPG-protection code path entirely.
    """
    with (
        patch("djb.secrets.init.check_gpg_installed", return_value=False),
        patch("djb.secrets.protected.check_gpg_installed", return_value=False),
    ):
        yield


@pytest.fixture(autouse=True)
def mock_gitignore_update():
    """Mock _update_gitignore_for_project_config to avoid modifying actual .gitignore."""
    with patch("djb.cli.init._update_gitignore_for_project_config", return_value=False):
        yield


@pytest.fixture
def project_dir(tmp_path):
    """Create a minimal project directory with pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "test-project"\n')
    return tmp_path


class TestDjbInit:
    """Tests for djb init command."""

    def test_init_help(self, runner):
        """Test that init --help works."""
        result = runner.invoke(djb_cli, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize djb development environment" in result.output
        assert "--skip-brew" in result.output
        assert "--skip-python" in result.output
        assert "--skip-frontend" in result.output
        assert "--skip-secrets" in result.output
        assert "--skip-hooks" in result.output

    def test_init_skip_all(self, runner, mock_subprocess_run, tmp_path):
        """Test init with all skips - should complete without errors."""
        # Create minimal pyproject.toml in temp dir
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-project"\n')

        result = runner.invoke(
            djb_cli,
            [
                "--project-dir",
                str(tmp_path),
                "init",
                "--skip-brew",
                "--skip-python",
                "--skip-frontend",
                "--skip-db",
                "--skip-migrations",
                "--skip-seed",
                "--skip-secrets",
                "--skip-hooks",
            ],
        )
        assert result.exit_code == 0
        # With all skips, no subprocess calls should be made
        assert (
            mock_subprocess_run.call_count == 0
        ), f"Unexpected subprocess calls: {mock_subprocess_run.call_args_list}"

    def test_init_homebrew_check_on_macos(self, runner, mock_subprocess_run):
        """Test that init checks for Homebrew on macOS."""
        with patch("djb.cli.init.sys.platform", "darwin"):
            # Mock brew not found
            def run_side_effect(cmd, *args, **kwargs):
                if cmd == ["which", "brew"]:
                    return Mock(returncode=1)
                return Mock(returncode=0, stdout=b"", stderr=b"")

            mock_subprocess_run.side_effect = run_side_effect

            result = runner.invoke(
                djb_cli,
                ["init", "--skip-python", "--skip-frontend", "--skip-secrets"],
            )

            assert result.exit_code == 1

    def test_init_skips_homebrew_on_windows(self, runner, mock_subprocess_run, tmp_path):
        """Test that init skips Homebrew on Windows (unsupported platform)."""
        # Create minimal pyproject.toml in temp dir
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-project"\n')

        with patch("djb.cli.init.sys.platform", "win32"):
            result = runner.invoke(
                djb_cli,
                [
                    "--project-dir",
                    str(tmp_path),
                    "init",
                    "--skip-python",
                    "--skip-frontend",
                    "--skip-db",
                    "--skip-secrets",
                    "--skip-hooks",
                ],
            )

            assert result.exit_code == 0
            # On Windows, no brew commands should be called
            # Check actual command args, not string representation (avoids matching env vars)
            brew_calls = [c for c in mock_subprocess_run.call_args_list if c[0][0][0] == "brew"]
            assert len(brew_calls) == 0

    def test_init_installs_age_when_missing(self, runner, mock_subprocess_run):
        """Test that init installs age when not present."""
        with patch("djb.cli.init.sys.platform", "darwin"):

            def run_side_effect(cmd, *args, **kwargs):
                # brew exists, age doesn't
                if cmd == ["which", "brew"]:
                    return Mock(returncode=0)
                if cmd == ["brew", "list", "age"]:
                    return Mock(returncode=1)  # Not installed
                return Mock(returncode=0, stdout=b"", stderr=b"")

            mock_subprocess_run.side_effect = run_side_effect

            result = runner.invoke(
                djb_cli,
                ["init", "--skip-python", "--skip-frontend", "--skip-secrets"],
            )

            assert result.exit_code == 0
            # Check that brew install age was called
            install_calls = [
                c
                for c in mock_subprocess_run.call_args_list
                if "brew" in str(c) and "install" in str(c) and "age" in str(c)
            ]
            assert len(install_calls) > 0

    def test_init_skips_age_when_present(self, runner, mock_subprocess_run):
        """Test that init skips installing age when already present."""
        with patch("djb.cli.init.sys.platform", "darwin"):

            def run_side_effect(cmd, *args, **kwargs):
                # brew and age both exist
                if cmd == ["which", "brew"]:
                    return Mock(returncode=0)
                if cmd == ["brew", "list", "age"]:
                    return Mock(returncode=0)  # Already installed
                return Mock(returncode=0, stdout=b"", stderr=b"")

            mock_subprocess_run.side_effect = run_side_effect

            result = runner.invoke(
                djb_cli,
                ["init", "--skip-python", "--skip-frontend", "--skip-secrets"],
            )

            assert result.exit_code == 0
            # Verify that brew install age was NOT called (since it's already installed)
            install_age_calls = [
                c
                for c in mock_subprocess_run.call_args_list
                if "brew" in str(c) and "install" in str(c) and "age" in str(c)
            ]
            assert len(install_age_calls) == 0

    def test_init_python_dependencies(self, runner, mock_subprocess_run, project_dir):
        """Test that init runs uv sync for Python dependencies."""
        result = runner.invoke(
            djb_cli,
            [
                "--project-dir",
                str(project_dir),
                "init",
                "--skip-brew",
                "--skip-frontend",
                "--skip-secrets",
            ],
        )

        assert result.exit_code == 0
        # Check that uv sync was called
        uv_calls = [
            c for c in mock_subprocess_run.call_args_list if "uv" in str(c) and "sync" in str(c)
        ]
        assert len(uv_calls) > 0

    def test_init_frontend_dependencies(self, runner, mock_subprocess_run, project_dir):
        """Test that init runs bun install for frontend dependencies."""
        # Create frontend directory
        frontend_dir = project_dir / "frontend"
        frontend_dir.mkdir()

        result = runner.invoke(
            djb_cli,
            [
                "--project-dir",
                str(project_dir),
                "init",
                "--skip-brew",
                "--skip-python",
                "--skip-secrets",
            ],
        )

        assert result.exit_code == 0
        # Check that bun install was called
        bun_calls = [
            c for c in mock_subprocess_run.call_args_list if "bun" in str(c) and "install" in str(c)
        ]
        assert len(bun_calls) > 0

    def test_init_skips_frontend_when_directory_missing(
        self, runner, mock_subprocess_run, project_dir
    ):
        """Test that init skips frontend when directory doesn't exist."""
        result = runner.invoke(
            djb_cli,
            [
                "--project-dir",
                str(project_dir),
                "init",
                "--skip-brew",
                "--skip-python",
                "--skip-secrets",
            ],
        )

        assert result.exit_code == 0
        # Verify that bun install was NOT called (since frontend dir doesn't exist)
        bun_calls = [
            c for c in mock_subprocess_run.call_args_list if "bun" in str(c) and "install" in str(c)
        ]
        assert len(bun_calls) == 0

    def test_init_secrets_creates_missing_environments(
        self, runner, mock_subprocess_run, project_dir
    ):
        """Test that init creates secrets files for missing environments."""
        # Mock secrets to avoid actual encryption (patch where it's used, not defined)
        with patch("djb.cli.init.init_or_upgrade_secrets") as mock_secrets:
            mock_secrets.return_value = type(
                "SecretsStatus",
                (),
                {"initialized": ["dev", "staging"], "upgraded": [], "up_to_date": []},
            )()

            result = runner.invoke(
                djb_cli,
                [
                    "--project-dir",
                    str(project_dir),
                    "init",
                    "--skip-brew",
                    "--skip-python",
                    "--skip-frontend",
                    "--skip-hooks",
                ],
            )

            assert result.exit_code == 0
            assert "Created secrets" in result.output
            mock_secrets.assert_called_once()

    def test_init_secrets_upgrades_existing(self, runner, mock_subprocess_run, project_dir):
        """Test that init upgrades existing secrets with new template keys."""
        with patch("djb.cli.init.init_or_upgrade_secrets") as mock_secrets:
            mock_secrets.return_value = type(
                "SecretsStatus",
                (),
                {"initialized": [], "upgraded": ["dev"], "up_to_date": ["staging"]},
            )()

            result = runner.invoke(
                djb_cli,
                [
                    "--project-dir",
                    str(project_dir),
                    "init",
                    "--skip-brew",
                    "--skip-python",
                    "--skip-frontend",
                    "--skip-hooks",
                ],
            )

            assert result.exit_code == 0
            assert "Upgraded secrets" in result.output
            mock_secrets.assert_called_once()

    def test_init_secrets_already_up_to_date(self, runner, mock_subprocess_run, project_dir):
        """Test that init reports when all secrets are up to date."""
        with patch("djb.cli.init.init_or_upgrade_secrets") as mock_secrets:
            mock_secrets.return_value = type(
                "SecretsStatus",
                (),
                {"initialized": [], "upgraded": [], "up_to_date": ["dev", "staging", "production"]},
            )()

            result = runner.invoke(
                djb_cli,
                [
                    "--project-dir",
                    str(project_dir),
                    "init",
                    "--skip-brew",
                    "--skip-python",
                    "--skip-frontend",
                    "--skip-hooks",
                ],
            )

            assert result.exit_code == 0
            assert "already up to date" in result.output
            mock_secrets.assert_called_once()

    def test_init_with_project_dir(self, runner, mock_subprocess_run, project_dir):
        """Test that init respects --project-dir option."""
        result = runner.invoke(
            djb_cli,
            [
                "--project-dir",
                str(project_dir),
                "init",
                "--skip-brew",
                "--skip-frontend",
                "--skip-secrets",
            ],
        )

        assert result.exit_code == 0
        # Verify uv sync was called with correct cwd
        uv_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if len(c.args) > 0 and "uv" in str(c.args[0])
        ]
        assert any(c.kwargs.get("cwd") == project_dir for c in uv_calls)

    def test_init_idempotent(self, runner, mock_subprocess_run):
        """Test that running init multiple times is safe (idempotent)."""
        with patch("djb.cli.init.sys.platform", "darwin"):

            def run_side_effect(cmd, *args, **kwargs):
                # Everything already installed
                return Mock(returncode=0, stdout=b"", stderr=b"")

            mock_subprocess_run.side_effect = run_side_effect

            # Run init twice
            result1 = runner.invoke(
                djb_cli,
                ["init", "--skip-python", "--skip-frontend", "--skip-secrets"],
            )

            # Reset config between CLI invocations so configure() can be called again
            djb.reset_config()

            result2 = runner.invoke(
                djb_cli,
                ["init", "--skip-python", "--skip-frontend", "--skip-secrets"],
            )

            # Both runs should succeed (idempotent)
            assert result1.exit_code == 0
            assert result2.exit_code == 0

    def test_init_produces_no_empty_lines(self, runner, mock_subprocess_run):
        """Test that init output contains actual content, not just blank lines.

        Regression test: Previously, when the default log level was 'note' (25) and
        actual messages used logger.info() (level 20), no messages were displayed.
        Only empty logger.note() spacer calls were output as blank lines.
        """
        result = runner.invoke(
            djb_cli,
            [
                "init",
                "--skip-brew",
                "--skip-python",
                "--skip-frontend",
                "--skip-secrets",
                "--skip-hooks",
            ],
        )
        assert result.exit_code == 0

        # Split output into lines and check for meaningful content
        lines = result.output.strip().split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        # Should have multiple lines of actual content (not just blank spacers)
        assert (
            len(non_empty_lines) >= 5
        ), f"Expected at least 5 non-empty lines, got {len(non_empty_lines)}"

        # Should contain recognizable messages
        output_text = result.output
        assert "Initializing" in output_text or "initialization" in output_text.lower()
        assert "complete" in output_text.lower() or "skip" in output_text.lower()

    def test_init_adds_djb_to_installed_apps(self, runner, mock_subprocess_run, project_dir):
        """Test that djb init adds djb to INSTALLED_APPS when not present."""
        # Create a Django project structure
        django_project = project_dir / "myproject"
        django_project.mkdir()
        (django_project / "__init__.py").write_text("")
        settings_path = django_project / "settings.py"
        settings_path.write_text(
            """
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "myproject.app1",
]
"""
        )

        result = runner.invoke(
            djb_cli,
            [
                "--project-dir",
                str(project_dir),
                "init",
                "--skip-brew",
                "--skip-python",
                "--skip-frontend",
                "--skip-secrets",
                "--skip-hooks",
            ],
        )

        assert result.exit_code == 0
        assert "Added djb to INSTALLED_APPS" in result.output

        # Verify djb was added to settings.py
        content = settings_path.read_text()
        assert '"djb"' in content

    def test_init_skips_djb_when_already_in_installed_apps(
        self, runner, mock_subprocess_run, project_dir
    ):
        """Test that djb init skips adding djb when already in INSTALLED_APPS."""
        # Create a Django project structure with djb already present
        django_project = project_dir / "myproject"
        django_project.mkdir()
        (django_project / "__init__.py").write_text("")
        settings_path = django_project / "settings.py"
        original_content = """
INSTALLED_APPS = [
    "django.contrib.admin",
    "djb",
    "myproject.app1",
]
"""
        settings_path.write_text(original_content)

        result = runner.invoke(
            djb_cli,
            [
                "--project-dir",
                str(project_dir),
                "init",
                "--skip-brew",
                "--skip-python",
                "--skip-frontend",
                "--skip-secrets",
                "--skip-hooks",
            ],
        )

        assert result.exit_code == 0
        assert "djb already in INSTALLED_APPS" in result.output

        # Verify settings.py was not modified
        assert settings_path.read_text() == original_content


class TestInitOrUpgradeSecrets:
    """Tests for init_or_upgrade_secrets function."""

    def test_creates_all_environments_when_none_exist(self, runner, project_dir):
        """Test that all environments are created when none exist."""
        key_path = project_dir / ".age" / "keys.txt"
        # Patch get_default_key_path everywhere it's imported (modules cache their imports).
        # GPG protection is disabled by the autouse disable_gpg_protection fixture.
        with (
            patch("djb.secrets.core.get_default_key_path", return_value=key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=key_path),
            patch("djb.secrets.init.get_default_key_path", return_value=key_path),
        ):
            result = runner.invoke(
                djb_cli,
                [
                    "--project-dir",
                    str(project_dir),
                    "init",
                    "--skip-brew",
                    "--skip-python",
                    "--skip-frontend",
                    "--skip-hooks",
                ],
            )

        assert result.exit_code == 0
        assert "Created secrets" in result.output

        # Verify files were created
        secrets_dir = project_dir / "secrets"
        for env in SECRETS_ENVIRONMENTS:
            assert (secrets_dir / f"{env}.yaml").exists()

    def test_upgrades_existing_secrets_with_missing_keys(self, runner, project_dir):
        """Test that existing secrets get upgraded with new template keys."""
        # Set up age key
        key_path = project_dir / ".age" / "keys.txt"
        key_path.parent.mkdir(parents=True)
        public_key, _ = generate_age_key(key_path)

        # Create secrets dir with partial secrets (missing superuser key)
        secrets_dir = project_dir / "secrets"
        secrets_dir.mkdir()
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=key_path)

        # Create dev secrets without superuser key
        manager.save_secrets(
            "dev",
            {"django_secret_key": "test-key", "db_credentials": {"host": "localhost"}},
            [public_key],
        )

        # Patch get_default_key_path everywhere it's imported (modules cache their imports).
        # GPG protection is disabled by the autouse disable_gpg_protection fixture.
        with (
            patch("djb.secrets.core.get_default_key_path", return_value=key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=key_path),
            patch("djb.secrets.init.get_default_key_path", return_value=key_path),
        ):
            result = runner.invoke(
                djb_cli,
                [
                    "--project-dir",
                    str(project_dir),
                    "init",
                    "--skip-brew",
                    "--skip-python",
                    "--skip-frontend",
                    "--skip-hooks",
                ],
            )

        assert result.exit_code == 0
        # dev should be upgraded (missing superuser), others should be initialized
        assert "Upgraded secrets" in result.output or "Created secrets" in result.output

        # Verify dev now has superuser key
        dev_secrets = manager.load_secrets("dev")
        assert "superuser" in dev_secrets

    def test_reports_up_to_date_when_no_changes_needed(self, runner, project_dir):
        """Test that secrets are reported as up to date when complete."""
        # Set up age key
        key_path = project_dir / ".age" / "keys.txt"
        key_path.parent.mkdir(parents=True)
        public_key, _ = generate_age_key(key_path)

        # Create secrets dir with complete secrets
        secrets_dir = project_dir / "secrets"
        secrets_dir.mkdir()
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=key_path)

        # Create complete secrets for all environments
        for env in SECRETS_ENVIRONMENTS:
            template = _get_template(env)
            manager.save_secrets(env, template, [public_key])

        # Patch get_default_key_path everywhere it's imported (modules cache their imports).
        # GPG protection is disabled by the autouse disable_gpg_protection fixture.
        with (
            patch("djb.secrets.core.get_default_key_path", return_value=key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=key_path),
            patch("djb.secrets.init.get_default_key_path", return_value=key_path),
        ):
            result = runner.invoke(
                djb_cli,
                [
                    "--project-dir",
                    str(project_dir),
                    "init",
                    "--skip-brew",
                    "--skip-python",
                    "--skip-frontend",
                    "--skip-hooks",
                ],
            )

        assert result.exit_code == 0
        # All should be up to date
        assert "already up to date" in result.output


class TestAddDjbToInstalledApps:
    """Tests for _add_djb_to_installed_apps function."""

    def test_adds_djb_after_last_django_app(self, tmp_path):
        """Test that djb is added after the last django.* app (including django_components)."""
        # Create a Django project structure
        project_dir = tmp_path / "myproject"
        project_dir.mkdir()
        (project_dir / "__init__.py").write_text("")
        settings_path = project_dir / "settings.py"
        settings_path.write_text(
            """
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django_components",
    "myproject.app1",
]
"""
        )

        result = _add_djb_to_installed_apps(tmp_path)
        assert result is True

        content = settings_path.read_text()
        lines = content.split("\n")

        # Find indices
        djb_line_idx = None
        django_components_idx = None
        for i, line in enumerate(lines):
            if '"djb"' in line:
                djb_line_idx = i
            if "django_components" in line:
                django_components_idx = i

        assert djb_line_idx is not None, "djb should be in INSTALLED_APPS"
        assert django_components_idx is not None
        assert (
            djb_line_idx == django_components_idx + 1
        ), "djb should be right after django_components"

    def test_skips_if_djb_already_present(self, tmp_path):
        """Test that djb is not added if already in INSTALLED_APPS."""
        project_dir = tmp_path / "myproject"
        project_dir.mkdir()
        (project_dir / "__init__.py").write_text("")
        settings_path = project_dir / "settings.py"
        original_content = """
INSTALLED_APPS = [
    "django.contrib.admin",
    "djb",
    "myproject.app1",
]
"""
        settings_path.write_text(original_content)

        result = _add_djb_to_installed_apps(tmp_path)
        assert result is False

        # Content should be unchanged
        assert settings_path.read_text() == original_content

    def test_handles_single_quotes(self, tmp_path):
        """Test that djb detection works with single quotes."""
        project_dir = tmp_path / "myproject"
        project_dir.mkdir()
        (project_dir / "__init__.py").write_text("")
        settings_path = project_dir / "settings.py"
        settings_path.write_text(
            """
INSTALLED_APPS = [
    'django.contrib.admin',
    'djb',
]
"""
        )

        result = _add_djb_to_installed_apps(tmp_path)
        assert result is False  # Already present

    def test_preserves_indentation(self, tmp_path):
        """Test that the added line uses correct indentation."""
        project_dir = tmp_path / "myproject"
        project_dir.mkdir()
        (project_dir / "__init__.py").write_text("")
        settings_path = project_dir / "settings.py"
        settings_path.write_text(
            """
INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
]
"""
        )

        _add_djb_to_installed_apps(tmp_path)

        content = settings_path.read_text()
        # djb should have 8 spaces of indentation (matching the other apps)
        assert '        "djb",' in content

    def test_returns_false_when_no_settings_found(self, tmp_path):
        """Test that it returns False when no settings.py is found."""
        result = _add_djb_to_installed_apps(tmp_path)
        assert result is False

    def test_skips_directories_without_init(self, tmp_path):
        """Test that directories without __init__.py are skipped."""
        # Create a directory with settings.py but no __init__.py
        project_dir = tmp_path / "not_a_package"
        project_dir.mkdir()
        (project_dir / "settings.py").write_text('INSTALLED_APPS = ["django.contrib.admin"]')

        result = _add_djb_to_installed_apps(tmp_path)
        assert result is False


class TestTeamMembershipChanges:
    """Tests for team membership change detection in init_or_upgrade_secrets."""

    def test_bob_first_user_creates_secrets_with_his_key(self, tmp_path):
        """Test that when Bob is the first user, secrets are encrypted for him.

        Scenario: Brand new project, Bob is the first developer. No .sops.yaml,
        no secrets files exist. Bob runs djb init and secrets should be created
        encrypted for Bob.
        """
        # Brand new project - no secrets directory yet
        secrets_dir = tmp_path / "secrets"
        # Don't create it - init_or_upgrade_secrets should create it

        # Create Bob's key
        bob_key_path = tmp_path / ".age" / "keys.txt"
        bob_key_path.parent.mkdir(parents=True)
        bob_public_key, _ = generate_age_key(bob_key_path)

        # Bob is the first user - runs djb init
        # Patch get_default_key_path in both modules (they have separate imports)
        with (
            patch("djb.secrets.init.get_default_key_path", return_value=bob_key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=bob_key_path),
            patch("djb.secrets.init.logger"),
        ):
            status = init_or_upgrade_secrets(tmp_path, email="bob@example.com")

        # All environments should be initialized (created)
        assert set(status.initialized) == set(SECRETS_ENVIRONMENTS)
        assert status.upgraded == []
        assert status.up_to_date == []

        # Verify .sops.yaml was created with Bob's key
        recipients = parse_sops_config(secrets_dir)
        assert bob_public_key in recipients
        assert recipients[bob_public_key] == "bob@example.com"

        # Verify all secrets files are encrypted for Bob
        for env in SECRETS_ENVIRONMENTS:
            secrets_file = secrets_dir / f"{env}.yaml"
            assert secrets_file.exists(), f"{env}.yaml should exist"
            file_recipients = _get_encrypted_recipients(secrets_file)
            assert bob_public_key in file_recipients, f"{env}.yaml should be encrypted for Bob"

    def test_bob_joins_no_warning_about_self(self, tmp_path):
        """Test that Bob joining doesn't see a warning about himself being added.

        Scenario: Bob runs djb init for the first time. His key is added to .sops.yaml.
        He should NOT see "New team member added: bob@example.com" about himself.
        """
        # Alice has already set up the project
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        # Create Alice's key
        alice_key_path = tmp_path / ".age" / "alice_keys.txt"
        alice_key_path.parent.mkdir(parents=True)
        alice_public_key, _ = generate_age_key(alice_key_path)

        # Alice created .sops.yaml with her key
        create_sops_config(secrets_dir, {alice_public_key: "alice@example.com"})

        # Alice created encrypted secrets (only project secrets - dev.yaml is gitignored)
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        for env in PROJECT_SECRETS_ENVIRONMENTS:
            manager.save_secrets(env, {"django_secret_key": "test"}, [alice_public_key])

        # Now Bob joins - create Bob's key
        bob_key_path = tmp_path / ".age" / "bob_keys.txt"
        bob_public_key, _ = generate_age_key(bob_key_path)

        # Bob pulls Alice's .sops.yaml (still has only Alice's key)
        # Bob runs djb init - his key should be added to .sops.yaml
        # Patch get_default_key_path in both modules (they have separate imports)
        with (
            patch("djb.secrets.init.get_default_key_path", return_value=bob_key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=bob_key_path),
            patch("djb.secrets.init.logger") as mock_logger,
        ):
            init_or_upgrade_secrets(tmp_path, email="bob@example.com")

            # Bob should NOT see warning about himself being added
            warning_calls = [
                call
                for call in mock_logger.warning.call_args_list
                if "bob@example.com" in str(call)
            ]
            assert len(warning_calls) == 0, "Bob should not see warning about himself"

            # Bob's key should be added to .sops.yaml
            recipients = parse_sops_config(secrets_dir)
            assert bob_public_key in recipients
            assert recipients[bob_public_key] == "bob@example.com"

    def test_alice_sees_warning_when_bob_added(self, tmp_path):
        """Test that Alice sees a warning when Bob's key appears in .sops.yaml.

        Scenario: Bob ran djb init and pushed his .sops.yaml changes. Alice pulls and
        runs djb init. She should see "New team member added: bob@example.com".
        """
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        # Create Alice's key
        alice_key_path = tmp_path / ".age" / "keys.txt"
        alice_key_path.parent.mkdir(parents=True)
        alice_public_key, _ = generate_age_key(alice_key_path)

        # Create Bob's key (simulating Bob who already joined)
        bob_key_path = tmp_path / ".age" / "bob_keys.txt"
        bob_public_key, _ = generate_age_key(bob_key_path)

        # .sops.yaml has BOTH Alice and Bob (Bob pushed his changes, Alice pulled)
        create_sops_config(
            secrets_dir,
            {
                alice_public_key: "alice@example.com",
                bob_public_key: "bob@example.com",
            },
        )

        # But encrypted files only have Alice's key (not yet re-encrypted for Bob)
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        for env in SECRETS_ENVIRONMENTS:
            manager.save_secrets(env, {"django_secret_key": "test"}, [alice_public_key])

        # Alice runs djb init
        # Patch get_default_key_path in both modules (they have separate imports)
        with (
            patch("djb.secrets.init.get_default_key_path", return_value=alice_key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=alice_key_path),
            patch("djb.secrets.init.logger") as mock_logger,
        ):
            init_or_upgrade_secrets(tmp_path, email="alice@example.com")

            # Alice should see warning about Bob being added
            warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
            bob_warning = any("bob@example.com" in call for call in warning_calls)
            assert bob_warning, f"Expected warning about bob@example.com, got: {warning_calls}"

    def test_alice_reencrypts_for_bob(self, tmp_path):
        """Test that Alice re-encrypts project secrets when Bob is added.

        After Alice sees the warning, project secrets (staging/production) should
        be re-encrypted for both. Dev secrets remain user-only.
        """
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        # Create Alice's key
        alice_key_path = tmp_path / ".age" / "keys.txt"
        alice_key_path.parent.mkdir(parents=True)
        alice_public_key, _ = generate_age_key(alice_key_path)

        # Create Bob's key
        bob_key_path = tmp_path / ".age" / "bob_keys.txt"
        bob_public_key, _ = generate_age_key(bob_key_path)

        # .sops.yaml has both Alice and Bob
        create_sops_config(
            secrets_dir,
            {
                alice_public_key: "alice@example.com",
                bob_public_key: "bob@example.com",
            },
        )

        # Encrypted files only have Alice's key
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        for env in SECRETS_ENVIRONMENTS:
            manager.save_secrets(env, {"django_secret_key": "test"}, [alice_public_key])

        # Verify staging is only encrypted for Alice initially
        staging_recipients = _get_encrypted_recipients(secrets_dir / "staging.yaml")
        assert alice_public_key in staging_recipients
        assert bob_public_key not in staging_recipients

        # Alice runs djb init (mock logger to avoid test isolation issues)
        # Patch get_default_key_path in both modules (they have separate imports)
        with (
            patch("djb.secrets.init.get_default_key_path", return_value=alice_key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=alice_key_path),
            patch("djb.secrets.init.logger"),
        ):
            init_or_upgrade_secrets(tmp_path, email="alice@example.com")

        # After re-encryption, project secrets should be encrypted for both
        staging_recipients = _get_encrypted_recipients(secrets_dir / "staging.yaml")
        assert alice_public_key in staging_recipients, "Alice should still be a recipient"
        assert bob_public_key in staging_recipients, "Bob should now be a recipient"

        # Dev secrets remain user-only (not re-encrypted for Bob)
        dev_recipients = _get_encrypted_recipients(secrets_dir / "dev.yaml")
        assert alice_public_key in dev_recipients, "Alice should still be a recipient for dev"
        assert (
            bob_public_key not in dev_recipients
        ), "Bob should NOT be a recipient for dev (user secret)"

    def test_warning_when_team_member_removed(self, tmp_path):
        """Test that a warning is shown when a team member is removed.

        Scenario: Carol was removed from the team. Someone runs djb init and should
        see "Team member removed: age1..." warning.
        """
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        # Create Alice's key
        alice_key_path = tmp_path / ".age" / "keys.txt"
        alice_key_path.parent.mkdir(parents=True)
        alice_public_key, _ = generate_age_key(alice_key_path)

        # Create Carol's key (she's being removed)
        carol_key_path = tmp_path / ".age" / "carol_keys.txt"
        carol_public_key, _ = generate_age_key(carol_key_path)

        # .sops.yaml only has Alice (Carol was removed)
        create_sops_config(
            secrets_dir,
            {
                alice_public_key: "alice@example.com",
            },
        )

        # But encrypted project files still have both Alice and Carol
        # (dev.yaml is per-user and gitignored, so it wouldn't have Carol's key)
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        for env in PROJECT_SECRETS_ENVIRONMENTS:
            manager.save_secrets(
                env, {"django_secret_key": "test"}, [alice_public_key, carol_public_key]
            )

        # Alice runs djb init
        # Patch get_default_key_path in both modules (they have separate imports)
        with (
            patch("djb.secrets.init.get_default_key_path", return_value=alice_key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=alice_key_path),
            patch("djb.secrets.init.logger") as mock_logger,
        ):
            init_or_upgrade_secrets(tmp_path, email="alice@example.com")

            # Should see warning about Carol being removed (truncated key)
            warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
            removed_warning = any("removed" in call.lower() for call in warning_calls)
            assert removed_warning, f"Expected 'removed' warning, got: {warning_calls}"

    def test_reencrypts_after_member_removed(self, tmp_path):
        """Test that secrets are re-encrypted after a team member is removed."""
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        # Create Alice's key
        alice_key_path = tmp_path / ".age" / "keys.txt"
        alice_key_path.parent.mkdir(parents=True)
        alice_public_key, _ = generate_age_key(alice_key_path)

        # Create Carol's key (being removed)
        carol_key_path = tmp_path / ".age" / "carol_keys.txt"
        carol_public_key, _ = generate_age_key(carol_key_path)

        # .sops.yaml only has Alice
        create_sops_config(
            secrets_dir,
            {
                alice_public_key: "alice@example.com",
            },
        )

        # Encrypted project files have both Alice and Carol
        # (dev.yaml is per-user and gitignored, so it wouldn't have Carol's key)
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        for env in PROJECT_SECRETS_ENVIRONMENTS:
            manager.save_secrets(
                env, {"django_secret_key": "test"}, [alice_public_key, carol_public_key]
            )

        # Verify Carol is currently a recipient of project secrets
        staging_recipients = _get_encrypted_recipients(secrets_dir / "staging.yaml")
        assert carol_public_key in staging_recipients

        # Alice runs djb init (mock logger to avoid test isolation issues)
        # Patch get_default_key_path in both modules (they have separate imports)
        with (
            patch("djb.secrets.init.get_default_key_path", return_value=alice_key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=alice_key_path),
            patch("djb.secrets.init.logger"),
        ):
            init_or_upgrade_secrets(tmp_path, email="alice@example.com")

        # After re-encryption, Carol should be removed from project secrets
        staging_recipients = _get_encrypted_recipients(secrets_dir / "staging.yaml")
        assert alice_public_key in staging_recipients, "Alice should still be a recipient"
        assert carol_public_key not in staging_recipients, "Carol should no longer be a recipient"

    def test_no_warning_or_reencrypt_when_team_unchanged(self, tmp_path):
        """Test that no warnings or re-encryption happens when team is unchanged."""
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        # Create Alice's key
        alice_key_path = tmp_path / ".age" / "keys.txt"
        alice_key_path.parent.mkdir(parents=True)
        alice_public_key, _ = generate_age_key(alice_key_path)

        # .sops.yaml has Alice
        create_sops_config(
            secrets_dir,
            {
                alice_public_key: "alice@example.com",
            },
        )

        # Encrypted files also have Alice (in sync)
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        for env in SECRETS_ENVIRONMENTS:
            manager.save_secrets(env, {"django_secret_key": "test"}, [alice_public_key])

        # Alice runs djb init
        # Patch get_default_key_path in both modules (they have separate imports)
        with (
            patch("djb.secrets.init.get_default_key_path", return_value=alice_key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=alice_key_path),
            patch("djb.secrets.init.logger") as mock_logger,
            patch("djb.secrets.init.rotate_keys") as mock_rotate,
        ):
            init_or_upgrade_secrets(tmp_path, email="alice@example.com")

            # No warnings about team changes
            warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
            team_warnings = [c for c in warning_calls if "member" in c.lower()]
            assert len(team_warnings) == 0, f"Expected no team warnings, got: {team_warnings}"

            # rotate_keys should not be called
            assert mock_rotate.call_count == 0, "No re-encryption should happen"

    def test_bob_cannot_reencrypt_for_alice(self, tmp_path):
        """Test that Bob cannot re-encrypt when he joins (chicken-and-egg).

        When Bob joins, files aren't encrypted for him yet, so he can't decrypt
        to re-encrypt. The re-encryption should fail gracefully.
        """
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        # Create Alice's key
        alice_key_path = tmp_path / ".age" / "alice_keys.txt"
        alice_key_path.parent.mkdir(parents=True)
        alice_public_key, _ = generate_age_key(alice_key_path)

        # Create Bob's key
        bob_key_path = tmp_path / ".age" / "keys.txt"
        bob_public_key, _ = generate_age_key(bob_key_path)

        # .sops.yaml has Alice AND a third person (Charlie) who was just added
        charlie_key_path = tmp_path / ".age" / "charlie_keys.txt"
        charlie_public_key, _ = generate_age_key(charlie_key_path)

        create_sops_config(
            secrets_dir,
            {
                alice_public_key: "alice@example.com",
                bob_public_key: "bob@example.com",
                charlie_public_key: "charlie@example.com",
            },
        )

        # Files are encrypted ONLY for Alice (Bob can't decrypt)
        # Only project secrets are shared - dev.yaml is gitignored
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=alice_key_path)
        for env in PROJECT_SECRETS_ENVIRONMENTS:
            manager.save_secrets(env, {"django_secret_key": "test"}, [alice_public_key])

        # Bob runs djb init - he sees Charlie was added but can't re-encrypt
        # Patch get_default_key_path in both modules (they have separate imports)
        with (
            patch("djb.secrets.init.get_default_key_path", return_value=bob_key_path),
            patch("djb.secrets.protected.get_default_key_path", return_value=bob_key_path),
            patch("djb.secrets.init.logger") as mock_logger,
        ):
            # Should not raise, but should warn about failure
            init_or_upgrade_secrets(tmp_path, email="bob@example.com")

            # Should see warning about Charlie being added
            warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
            charlie_warning = any("charlie@example.com" in call for call in warning_calls)
            assert charlie_warning, f"Expected warning about charlie@example.com: {warning_calls}"

            # Should see warning about re-encryption failure
            failure_warning = any("Failed to re-encrypt" in call for call in warning_calls)
            assert failure_warning, f"Expected re-encryption failure warning: {warning_calls}"

            # Should see helpful message
            info_calls = [str(call) for call in mock_logger.info.call_args_list]
            help_msg = any("Ask a team member" in call for call in info_calls)
            assert help_msg, f"Expected helpful message about asking team member: {info_calls}"
