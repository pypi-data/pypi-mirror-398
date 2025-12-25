"""Tests for E2E test utilities.

These tests verify that the test utility functions work correctly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from . import add_django_settings, add_django_settings_from_startproject


# Mark all tests in this module as e2e (skipped by default, use --run-e2e to include)
pytestmark = pytest.mark.e2e_skipped_by_default


class TestAddDjangoSettings:
    """Tests for add_django_settings utility."""

    def test_creates_minimal_settings(self, tmp_path: Path):
        """Test that add_django_settings creates minimal settings."""
        add_django_settings(tmp_path, "myproject")

        settings_dir = tmp_path / "myproject"
        assert settings_dir.exists()
        assert (settings_dir / "__init__.py").exists()
        assert (settings_dir / "settings.py").exists()

        settings_content = (settings_dir / "settings.py").read_text()
        assert "INSTALLED_APPS" in settings_content
        assert "django.contrib.admin" in settings_content

    def test_creates_custom_installed_apps(self, tmp_path: Path):
        """Test that add_django_settings accepts custom INSTALLED_APPS."""
        add_django_settings(tmp_path, "myproject", installed_apps=["django.contrib.auth", "myapp"])

        settings_content = (tmp_path / "myproject" / "settings.py").read_text()
        assert "django.contrib.auth" in settings_content
        assert "myapp" in settings_content
        assert "django.contrib.admin" not in settings_content


class TestAddDjangoSettingsFromStartproject:
    """Tests for add_django_settings_from_startproject utility."""

    def test_creates_realistic_settings(self, tmp_path: Path):
        """Test that add_django_settings_from_startproject creates realistic Django settings."""
        add_django_settings_from_startproject(tmp_path, "myproject")

        settings_dir = tmp_path / "myproject"
        assert settings_dir.exists()
        assert (settings_dir / "__init__.py").exists()
        assert (settings_dir / "settings.py").exists()
        assert (settings_dir / "urls.py").exists()
        assert (settings_dir / "wsgi.py").exists()
        assert (settings_dir / "asgi.py").exists()

        settings_content = (settings_dir / "settings.py").read_text()
        # Real startproject generates all of these:
        assert "SECRET_KEY" in settings_content
        assert "DEBUG" in settings_content
        assert "INSTALLED_APPS" in settings_content
        assert "MIDDLEWARE" in settings_content
        assert "ROOT_URLCONF" in settings_content
        assert "TEMPLATES" in settings_content
        assert "DATABASES" in settings_content
        assert "AUTH_PASSWORD_VALIDATORS" in settings_content
        assert "LANGUAGE_CODE" in settings_content
        assert "TIME_ZONE" in settings_content
        assert "STATIC_URL" in settings_content

    def test_creates_manage_py(self, tmp_path: Path):
        """Test that startproject also creates manage.py in the project root."""
        add_django_settings_from_startproject(tmp_path, "myproject")

        manage_py = tmp_path / "manage.py"
        assert manage_py.exists()
        content = manage_py.read_text()
        assert "django" in content
        assert "myproject.settings" in content

    def test_custom_package_name(self, tmp_path: Path):
        """Test that custom package names work."""
        add_django_settings_from_startproject(tmp_path, "customproject")

        settings_dir = tmp_path / "customproject"
        assert settings_dir.exists()
        assert (settings_dir / "settings.py").exists()

        settings_content = (settings_dir / "settings.py").read_text()
        # Django's startproject uses the package name in WSGI_APPLICATION
        assert "customproject.wsgi.application" in settings_content
