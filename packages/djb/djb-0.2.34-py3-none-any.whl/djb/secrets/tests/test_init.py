"""Tests for djb.secrets.init module."""

from __future__ import annotations

import string
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from djb.secrets.init import (
    _deep_merge_missing,
    _generate_secret_key,
    _get_encrypted_recipients,
    _get_template,
)


class TestGetEncryptedRecipients:
    """Tests for _get_encrypted_recipients."""

    def test_returns_empty_set_for_nonexistent_file(self, tmp_path: Path):
        """Test returns empty set when file doesn't exist."""
        result = _get_encrypted_recipients(tmp_path / "nonexistent.yaml")
        assert result == set()

    def test_returns_recipients_from_sops_metadata(self, tmp_path: Path):
        """Test extracts recipients from SOPS metadata in encrypted file."""
        secrets_file = tmp_path / "staging.yaml"
        sops_content = {
            "django_secret_key": "ENC[encrypted...]",
            "sops": {
                "age": [
                    {"recipient": "age1abc123"},
                    {"recipient": "age1def456"},
                ],
                "lastmodified": "2024-01-01T00:00:00Z",
            },
        }
        secrets_file.write_text(yaml.dump(sops_content))

        result = _get_encrypted_recipients(secrets_file)
        assert result == {"age1abc123", "age1def456"}

    def test_returns_empty_set_for_invalid_yaml(self, tmp_path: Path):
        """Test returns empty set when file has invalid YAML."""
        secrets_file = tmp_path / "staging.yaml"
        secrets_file.write_text("invalid: yaml: content")

        result = _get_encrypted_recipients(secrets_file)
        assert result == set()

    def test_returns_empty_set_when_no_sops_section(self, tmp_path: Path):
        """Test returns empty set when file has no sops metadata."""
        secrets_file = tmp_path / "staging.yaml"
        secrets_file.write_text(yaml.dump({"django_secret_key": "value"}))

        result = _get_encrypted_recipients(secrets_file)
        assert result == set()

    def test_returns_empty_set_when_no_age_section(self, tmp_path: Path):
        """Test returns empty set when sops section has no age key."""
        secrets_file = tmp_path / "staging.yaml"
        secrets_file.write_text(yaml.dump({"sops": {"lastmodified": "2024-01-01"}}))

        result = _get_encrypted_recipients(secrets_file)
        assert result == set()


class TestGenerateSecretKey:
    """Tests for _generate_secret_key."""

    def test_generates_key_with_default_length(self):
        """Test generates 50 character key by default."""
        key = _generate_secret_key()
        assert len(key) == 50

    def test_generates_key_with_custom_length(self):
        """Test generates key with specified length."""
        key = _generate_secret_key(length=100)
        assert len(key) == 100

    def test_generates_unique_keys(self):
        """Test generates different keys each time."""
        keys = [_generate_secret_key() for _ in range(10)]
        assert len(set(keys)) == 10  # All unique

    def test_uses_valid_characters(self):
        """Test key only contains expected character set."""
        valid_chars = set(string.ascii_letters + string.digits + "!@#$%^&*(-_=+)")
        key = _generate_secret_key(length=1000)  # Large sample
        assert all(c in valid_chars for c in key)


class TestGetTemplate:
    """Tests for _get_template."""

    def test_dev_template_has_auto_generated_values(self):
        """Test dev template has auto-generated values, not placeholders."""
        template = _get_template("dev")

        # Should have real values, not CHANGE-ME placeholders
        assert "CHANGE-ME" not in template["django_secret_key"]
        assert len(template["django_secret_key"]) == 50

        # Should have db_credentials
        assert "db_credentials" in template
        assert template["db_credentials"]["host"] == "localhost"
        assert template["db_credentials"]["port"] == 5432

        # Should have superuser
        assert "superuser" in template
        assert template["superuser"]["username"] == "admin"

    def test_dev_template_uses_project_name_for_db(self):
        """Test dev template uses project name for database name."""
        template = _get_template("dev", project_name="myproject")

        assert template["db_credentials"]["username"] == "myproject"
        assert template["db_credentials"]["database"] == "myproject"

    def test_staging_template_has_placeholders(self):
        """Test staging template has CHANGE-ME placeholders."""
        template = _get_template("staging")

        assert "CHANGE-ME-STAGING-KEY" in template["django_secret_key"]
        assert "db_credentials" in template
        assert "CHANGE-ME-STAGING-PASSWORD" in template["db_credentials"]["password"]
        assert "CHANGE-ME-STAGING-PASSWORD" in template["superuser"]["password"]

    def test_production_template_has_no_db_credentials(self):
        """Test production template doesn't include db_credentials (Heroku provides)."""
        template = _get_template("production")

        assert "CHANGE-ME-PRODUCTION-KEY" in template["django_secret_key"]
        assert "db_credentials" not in template  # Heroku provides DATABASE_URL
        assert "superuser" in template
        assert "CHANGE-ME-PRODUCTION-PASSWORD" in template["superuser"]["password"]


class TestDeepMergeMissing:
    """Tests for _deep_merge_missing."""

    def test_adds_missing_top_level_keys(self):
        """Test adds keys from template that are missing in existing."""
        existing = {"key1": "value1"}
        template = {"key1": "template1", "key2": "value2"}

        result, added = _deep_merge_missing(existing, template)

        assert result == {"key1": "value1", "key2": "value2"}
        assert added == ["key2"]

    def test_preserves_existing_values(self):
        """Test doesn't overwrite existing values."""
        existing = {"key1": "existing_value"}
        template = {"key1": "template_value"}

        result, added = _deep_merge_missing(existing, template)

        assert result["key1"] == "existing_value"
        assert added == []

    def test_merges_nested_dicts(self):
        """Test recursively merges nested dictionaries."""
        existing = {
            "db_credentials": {
                "username": "myuser",
            }
        }
        template = {
            "db_credentials": {
                "username": "default_user",
                "password": "default_pass",
                "host": "localhost",
            }
        }

        result, added = _deep_merge_missing(existing, template)

        assert result["db_credentials"]["username"] == "myuser"  # Preserved
        assert result["db_credentials"]["password"] == "default_pass"  # Added
        assert result["db_credentials"]["host"] == "localhost"  # Added
        assert "db_credentials.password" in added
        assert "db_credentials.host" in added

    def test_returns_empty_added_when_all_present(self):
        """Test returns empty list when existing has all template keys."""
        existing = {"key1": "val1", "key2": "val2"}
        template = {"key1": "t1", "key2": "t2"}

        result, added = _deep_merge_missing(existing, template)

        assert added == []
        assert result == existing

    def test_does_not_modify_original_dict(self):
        """Test doesn't mutate the original existing dict."""
        existing = {"key1": "value1"}
        template = {"key2": "value2"}
        original_existing = dict(existing)

        _deep_merge_missing(existing, template)

        assert existing == original_existing

    def test_handles_deeply_nested_structures(self):
        """Test handles multiple levels of nesting."""
        existing = {"level1": {"level2": {"existing_key": "value"}}}
        template = {"level1": {"level2": {"existing_key": "x", "new_key": "y"}}}

        result, added = _deep_merge_missing(existing, template)

        assert result["level1"]["level2"]["existing_key"] == "value"  # Preserved
        assert result["level1"]["level2"]["new_key"] == "y"  # Added
        assert "level1.level2.new_key" in added
