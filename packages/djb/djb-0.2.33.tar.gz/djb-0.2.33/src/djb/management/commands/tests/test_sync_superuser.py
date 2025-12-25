"""Tests for sync_superuser Django management command."""

from __future__ import annotations

import os
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.management import call_command
from django.core.management.base import CommandError, OutputWrapper

from djb.management.commands.sync_superuser import Command


class TestSyncSuperuserCommand:
    """Tests for the sync_superuser management command."""

    def test_add_arguments_registers_options(self):
        """Test that add_arguments registers the expected CLI options."""
        cmd = Command()
        mock_parser = MagicMock()
        cmd.add_arguments(mock_parser)

        # Check that required arguments are added
        calls = mock_parser.add_argument.call_args_list
        arg_names = [call[0][0] for call in calls]

        assert "--environment" in arg_names
        assert "--dry-run" in arg_names

    def test_loads_from_environment_variables(self, tmp_path):
        """Test that credentials are loaded from environment variables when available."""
        cmd = Command()
        stdout = StringIO()
        cmd.stdout = OutputWrapper(stdout)
        cmd.style = MagicMock()
        cmd.style.SUCCESS = lambda x: x

        # Create a mock user that passes isinstance check
        mock_user = MagicMock(spec=AbstractUser)
        mock_user_model = MagicMock()
        mock_user_model.objects.get.return_value = mock_user

        env_copy = {k: v for k, v in os.environ.items() if not k.startswith("SUPERUSER_")}
        env_copy.update(
            {
                "SUPERUSER_USERNAME": "admin",
                "SUPERUSER_EMAIL": "admin@example.com",
                "SUPERUSER_PASSWORD": "secret123",
            }
        )

        with (
            patch.dict(os.environ, env_copy, clear=True),
            patch(
                "djb.management.commands.sync_superuser.get_user_model",
                return_value=mock_user_model,
            ),
        ):
            cmd.handle(environment=None, dry_run=False)

        mock_user_model.objects.get.assert_called_once_with(username="admin")
        mock_user.set_password.assert_called_once_with("secret123")
        mock_user.save.assert_called_once()
        assert mock_user.email == "admin@example.com"
        assert mock_user.is_staff is True
        assert mock_user.is_superuser is True
        assert mock_user.is_active is True

    def test_creates_user_when_not_exists(self):
        """Test that a new user is created when it doesn't exist."""
        cmd = Command()
        stdout = StringIO()
        cmd.stdout = OutputWrapper(stdout)
        cmd.style = MagicMock()
        cmd.style.SUCCESS = lambda x: x

        # Simulate user not found
        mock_user_model = MagicMock()
        mock_user_model.DoesNotExist = Exception
        mock_user_model.objects.get.side_effect = mock_user_model.DoesNotExist

        env_copy = {k: v for k, v in os.environ.items() if not k.startswith("SUPERUSER_")}
        env_copy.update(
            {
                "SUPERUSER_USERNAME": "newadmin",
                "SUPERUSER_EMAIL": "new@example.com",
                "SUPERUSER_PASSWORD": "newpass",
            }
        )

        with (
            patch.dict(os.environ, env_copy, clear=True),
            patch(
                "djb.management.commands.sync_superuser.get_user_model",
                return_value=mock_user_model,
            ),
        ):
            cmd.handle(environment=None, dry_run=False)

        mock_user_model.objects.create_superuser.assert_called_once_with(
            username="newadmin",
            email="new@example.com",
            password="newpass",
        )

    def test_dry_run_does_not_modify(self):
        """Test that dry-run mode doesn't create or update users."""
        cmd = Command()
        stdout = StringIO()
        cmd.stdout = OutputWrapper(stdout)
        cmd.style = MagicMock()
        cmd.style.WARNING = lambda x: f"[WARNING] {x}"

        mock_user_model = MagicMock()

        env_copy = {k: v for k, v in os.environ.items() if not k.startswith("SUPERUSER_")}
        env_copy.update(
            {
                "SUPERUSER_USERNAME": "admin",
                "SUPERUSER_EMAIL": "admin@example.com",
                "SUPERUSER_PASSWORD": "secret",
            }
        )

        with (
            patch.dict(os.environ, env_copy, clear=True),
            patch(
                "djb.management.commands.sync_superuser.get_user_model",
                return_value=mock_user_model,
            ),
        ):
            cmd.handle(environment=None, dry_run=True)

        mock_user_model.objects.get.assert_not_called()
        mock_user_model.objects.create_superuser.assert_not_called()
        assert "[DRY RUN]" in stdout.getvalue()

    def test_loads_from_secrets_when_env_not_set(self, tmp_path):
        """Test that credentials are loaded from secrets when env vars not set."""
        cmd = Command()
        stdout = StringIO()
        cmd.stdout = OutputWrapper(stdout)
        cmd.style = MagicMock()
        cmd.style.SUCCESS = lambda x: x

        mock_user = MagicMock(spec=AbstractUser)
        mock_user_model = MagicMock()
        mock_user_model.objects.get.return_value = mock_user

        mock_secrets = {
            "superuser": {
                "username": "secret_admin",
                "email": "secret@example.com",
                "password": "secret_pass",
            }
        }

        env_without_superuser = {
            k: v for k, v in os.environ.items() if not k.startswith("SUPERUSER_")
        }

        with (
            patch.dict(os.environ, env_without_superuser, clear=True),
            patch("djb.management.commands.sync_superuser.load_secrets", return_value=mock_secrets),
            patch(
                "djb.management.commands.sync_superuser.get_user_model",
                return_value=mock_user_model,
            ),
            patch("django.conf.settings") as mock_settings,
        ):
            mock_settings.BASE_DIR = tmp_path
            cmd.handle(environment="dev", dry_run=False)

        mock_user.set_password.assert_called_once_with("secret_pass")
        assert mock_user.email == "secret@example.com"

    def test_auto_detects_production_on_heroku(self, tmp_path):
        """Test that environment is auto-detected as production on Heroku."""
        cmd = Command()
        stdout = StringIO()
        cmd.stdout = OutputWrapper(stdout)
        cmd.style = MagicMock()
        cmd.style.SUCCESS = lambda x: x

        mock_user = MagicMock(spec=AbstractUser)
        mock_user_model = MagicMock()
        mock_user_model.objects.get.return_value = mock_user

        mock_secrets = {
            "superuser": {
                "username": "admin",
                "email": "admin@example.com",
                "password": "pass",
            }
        }

        env_with_dyno = {"DYNO": "web.1"}

        with (
            patch.dict(os.environ, env_with_dyno, clear=True),
            patch(
                "djb.management.commands.sync_superuser.load_secrets", return_value=mock_secrets
            ) as mock_load,
            patch(
                "djb.management.commands.sync_superuser.get_user_model",
                return_value=mock_user_model,
            ),
            patch("django.conf.settings") as mock_settings,
        ):
            mock_settings.BASE_DIR = tmp_path
            cmd.handle(environment=None, dry_run=False)

        # Should load production secrets
        mock_load.assert_called_once()
        call_kwargs = mock_load.call_args
        assert call_kwargs[1]["environment"] == "production"

    def test_raises_error_when_no_superuser_config(self, tmp_path):
        """Test that error is raised when superuser config is missing."""
        cmd = Command()
        stdout = StringIO()
        cmd.stdout = OutputWrapper(stdout)

        mock_user_model = MagicMock()
        mock_secrets = {}  # No superuser config

        env_without_superuser = {
            k: v for k, v in os.environ.items() if not k.startswith("SUPERUSER_")
        }

        with (
            patch.dict(os.environ, env_without_superuser, clear=True),
            patch("djb.management.commands.sync_superuser.load_secrets", return_value=mock_secrets),
            patch(
                "djb.management.commands.sync_superuser.get_user_model",
                return_value=mock_user_model,
            ),
            patch("django.conf.settings") as mock_settings,
            pytest.raises(CommandError) as exc_info,
        ):
            mock_settings.BASE_DIR = tmp_path
            cmd.handle(environment="dev", dry_run=False)

        assert "No 'superuser' configuration found" in str(exc_info.value)

    def test_raises_error_when_secrets_incomplete(self, tmp_path):
        """Test that error is raised when superuser config is incomplete."""
        cmd = Command()
        stdout = StringIO()
        cmd.stdout = OutputWrapper(stdout)

        mock_user_model = MagicMock()
        # Missing password
        mock_secrets = {
            "superuser": {
                "username": "admin",
                "email": "admin@example.com",
            }
        }

        env_without_superuser = {
            k: v for k, v in os.environ.items() if not k.startswith("SUPERUSER_")
        }

        with (
            patch.dict(os.environ, env_without_superuser, clear=True),
            patch("djb.management.commands.sync_superuser.load_secrets", return_value=mock_secrets),
            patch(
                "djb.management.commands.sync_superuser.get_user_model",
                return_value=mock_user_model,
            ),
            patch("django.conf.settings") as mock_settings,
            pytest.raises(CommandError) as exc_info,
        ):
            mock_settings.BASE_DIR = tmp_path
            cmd.handle(environment="dev", dry_run=False)

        assert "must include" in str(exc_info.value)

    def test_raises_error_when_secrets_load_fails(self, tmp_path):
        """Test that error is raised when secrets cannot be loaded."""
        cmd = Command()
        stdout = StringIO()
        cmd.stdout = OutputWrapper(stdout)

        mock_user_model = MagicMock()

        env_without_superuser = {
            k: v for k, v in os.environ.items() if not k.startswith("SUPERUSER_")
        }

        with (
            patch.dict(os.environ, env_without_superuser, clear=True),
            patch(
                "djb.management.commands.sync_superuser.load_secrets",
                side_effect=FileNotFoundError("Key not found"),
            ),
            patch(
                "djb.management.commands.sync_superuser.get_user_model",
                return_value=mock_user_model,
            ),
            patch("django.conf.settings") as mock_settings,
            pytest.raises(CommandError) as exc_info,
        ):
            mock_settings.BASE_DIR = tmp_path
            cmd.handle(environment="dev", dry_run=False)

        assert "Failed to load secrets" in str(exc_info.value)

    def test_raises_error_when_create_superuser_missing(self):
        """Test that error is raised when manager doesn't have create_superuser."""
        cmd = Command()
        stdout = StringIO()
        cmd.stdout = OutputWrapper(stdout)
        cmd.style = MagicMock()

        # Simulate user not found and no create_superuser method
        mock_user_model = MagicMock()
        mock_user_model.DoesNotExist = Exception
        mock_user_model.objects.get.side_effect = mock_user_model.DoesNotExist
        mock_user_model.objects.create_superuser = None

        env_copy = {k: v for k, v in os.environ.items() if not k.startswith("SUPERUSER_")}
        env_copy.update(
            {
                "SUPERUSER_USERNAME": "admin",
                "SUPERUSER_EMAIL": "admin@example.com",
                "SUPERUSER_PASSWORD": "secret",
            }
        )

        with (
            patch.dict(os.environ, env_copy, clear=True),
            patch(
                "djb.management.commands.sync_superuser.get_user_model",
                return_value=mock_user_model,
            ),
            pytest.raises(CommandError) as exc_info,
        ):
            cmd.handle(environment=None, dry_run=False)

        assert "create_superuser" in str(exc_info.value)

    def test_falls_back_to_environment_env_var(self, tmp_path):
        """Test that ENVIRONMENT env var is used when DYNO is not present."""
        cmd = Command()
        stdout = StringIO()
        cmd.stdout = OutputWrapper(stdout)
        cmd.style = MagicMock()
        cmd.style.SUCCESS = lambda x: x

        mock_user = MagicMock(spec=AbstractUser)
        mock_user_model = MagicMock()
        mock_user_model.objects.get.return_value = mock_user

        mock_secrets = {
            "superuser": {
                "username": "admin",
                "email": "admin@example.com",
                "password": "pass",
            }
        }

        env_with_environment = {"ENVIRONMENT": "staging"}

        with (
            patch.dict(os.environ, env_with_environment, clear=True),
            patch(
                "djb.management.commands.sync_superuser.load_secrets", return_value=mock_secrets
            ) as mock_load,
            patch(
                "djb.management.commands.sync_superuser.get_user_model",
                return_value=mock_user_model,
            ),
            patch("django.conf.settings") as mock_settings,
        ):
            mock_settings.BASE_DIR = tmp_path
            cmd.handle(environment=None, dry_run=False)

        # Should load staging secrets
        mock_load.assert_called_once()
        call_kwargs = mock_load.call_args
        assert call_kwargs[1]["environment"] == "staging"

    def test_raises_error_when_user_not_abstract_user(self):
        """Test that error is raised when user doesn't inherit from AbstractUser."""
        cmd = Command()
        stdout = StringIO()
        cmd.stdout = OutputWrapper(stdout)
        cmd.style = MagicMock()

        # Create a non-AbstractUser user
        class FakeUser:
            pass

        fake_user = FakeUser()

        # Create mock model with proper DoesNotExist that won't be raised
        class MockDoesNotExist(Exception):
            pass

        mock_user_model = MagicMock()
        mock_user_model.__name__ = "FakeUserModel"
        mock_user_model.DoesNotExist = MockDoesNotExist
        mock_user_model.objects.get.return_value = fake_user

        env_copy = {k: v for k, v in os.environ.items() if not k.startswith("SUPERUSER_")}
        env_copy.update(
            {
                "SUPERUSER_USERNAME": "admin",
                "SUPERUSER_EMAIL": "admin@example.com",
                "SUPERUSER_PASSWORD": "secret",
            }
        )

        with (
            patch.dict(os.environ, env_copy, clear=True),
            patch(
                "djb.management.commands.sync_superuser.get_user_model",
                return_value=mock_user_model,
            ),
            pytest.raises(CommandError) as exc_info,
        ):
            cmd.handle(environment=None, dry_run=False)

        assert "must inherit from AbstractUser" in str(exc_info.value)
