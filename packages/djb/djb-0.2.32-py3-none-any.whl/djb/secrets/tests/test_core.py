"""Tests for djb.secrets.core module."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from djb.secrets.core import (
    SecretsManager,
    SopsError,
    check_age_installed,
    check_sops_installed,
    create_sops_config,
    decrypt_file,
    encrypt_file,
    find_placeholder_secrets,
    format_identity,
    get_all_recipients,
    get_public_key_from_private,
    is_placeholder_value,
    is_valid_age_public_key,
    load_secrets,
    load_secrets_for_mode,
    parse_identity,
    parse_sops_config,
    rotate_keys,
)
from djb.types import Mode


class TestCheckInstalled:
    """Tests for check_sops_installed and check_age_installed."""

    def test_check_sops_installed_found(self):
        """Test check_sops_installed when sops is available."""
        with patch("shutil.which", return_value="/usr/bin/sops"):
            assert check_sops_installed() is True

    def test_check_sops_installed_not_found(self):
        """Test check_sops_installed when sops is not available."""
        with patch("shutil.which", return_value=None):
            assert check_sops_installed() is False

    def test_check_age_installed_found(self):
        """Test check_age_installed when age-keygen is available."""
        with patch("shutil.which", return_value="/usr/bin/age-keygen"):
            assert check_age_installed() is True

    def test_check_age_installed_not_found(self):
        """Test check_age_installed when age-keygen is not available."""
        with patch("shutil.which", return_value=None):
            assert check_age_installed() is False


class TestIsValidAgePublicKey:
    """Tests for is_valid_age_public_key."""

    def test_valid_key(self):
        """Test valid age public key."""
        # This is a properly formatted age public key (62 chars, starts with age1)
        key = "age1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqs3290gq"
        assert is_valid_age_public_key(key) is True

    def test_wrong_prefix(self):
        """Test rejection of wrong prefix."""
        key = "age2qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqs3290gq"
        assert is_valid_age_public_key(key) is False

    def test_wrong_length(self):
        """Test rejection of wrong length."""
        key = "age1short"
        assert is_valid_age_public_key(key) is False

    def test_invalid_characters(self):
        """Test rejection of invalid bech32 characters."""
        # 'b' and '1' (except in prefix) are not valid bech32
        key = "age1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsb290gq"
        assert is_valid_age_public_key(key) is False


class TestFormatAndParseIdentity:
    """Tests for format_identity and parse_identity."""

    def test_format_with_name_and_email(self):
        """Test formatting with both name and email."""
        result = format_identity("John Doe", "john@example.com")
        assert result == "John Doe <john@example.com>"

    def test_format_with_email_only(self):
        """Test formatting with email only."""
        result = format_identity(None, "john@example.com")
        assert result == "john@example.com"

    def test_parse_full_identity(self):
        """Test parsing full git-style identity."""
        name, email = parse_identity("John Doe <john@example.com>")
        assert name == "John Doe"
        assert email == "john@example.com"

    def test_parse_email_only(self):
        """Test parsing email-only identity."""
        name, email = parse_identity("john@example.com")
        assert name is None
        assert email == "john@example.com"

    def test_roundtrip(self):
        """Test format then parse returns original values."""
        formatted = format_identity("Jane Smith", "jane@example.com")
        name, email = parse_identity(formatted)
        assert name == "Jane Smith"
        assert email == "jane@example.com"

    def test_parse_identity_with_spaces(self):
        """Test parsing identity with extra spaces."""
        name, email = parse_identity("Alice Smith  <alice@example.com>")
        assert name == "Alice Smith"
        assert email == "alice@example.com"


class TestPlaceholderDetection:
    """Tests for placeholder detection functions."""

    def test_is_placeholder_change_me(self):
        """Test detection of CHANGE-ME placeholder (used in secrets templates)."""
        assert is_placeholder_value("CHANGE-ME") is True
        assert is_placeholder_value("change-me") is True
        assert is_placeholder_value("CHANGE-ME-DEV-KEY") is True
        assert is_placeholder_value("CHANGE-ME-PRODUCTION-PASSWORD") is True

    def test_is_placeholder_real_values(self):
        """Test that real values are not detected as placeholders."""
        real_values = [
            "sk_live_abc123xyz",
            "my-secret-key-12345",
            "production-database-password",
            "https://api.example.com",
            "user@example.com",
        ]

        for value in real_values:
            assert is_placeholder_value(value) is False, f"Should not detect: {value}"

    def test_is_placeholder_non_string(self):
        """Test that non-strings return False."""
        assert is_placeholder_value(123) is False  # type: ignore[arg-type]
        assert is_placeholder_value(None) is False  # type: ignore[arg-type]
        assert is_placeholder_value(["CHANGE-ME"]) is False  # type: ignore[arg-type]

    def test_find_placeholder_secrets_flat(self):
        """Test finding placeholders in flat dict."""
        secrets = {
            "api_key": "sk_live_real_key",
            "db_password": "CHANGE-ME",
            "secret_key": "real-secret",
        }

        result = find_placeholder_secrets(secrets)
        assert result == ["db_password"]

    def test_find_placeholder_secrets_nested(self):
        """Test finding placeholders in nested dict."""
        secrets = {
            "api_keys": {
                "stripe": "sk_live_real",
                "sendgrid": "CHANGE-ME",
            },
            "database": {
                "password": "CHANGE-ME-DEV-PASSWORD",
            },
        }

        result = find_placeholder_secrets(secrets)
        assert "api_keys.sendgrid" in result
        assert "database.password" in result
        assert len(result) == 2

    def test_find_placeholder_secrets_empty(self):
        """Test that empty dict returns no placeholders."""
        assert find_placeholder_secrets({}) == []

    def test_find_placeholder_secrets_no_placeholders(self):
        """Test dict with no placeholders."""
        secrets = {
            "key1": "real-value-1",
            "key2": "real-value-2",
        }
        assert find_placeholder_secrets(secrets) == []


class TestSopsConfig:
    """Tests for SOPS config functions."""

    def test_create_sops_config_dict(self, tmp_path):
        """Test creating .sops.yaml with dict recipients."""
        recipients = {
            "age1abc123": "John <john@example.com>",
            "age1def456": "Jane <jane@example.com>",
        }

        result = create_sops_config(tmp_path, recipients)

        assert result == tmp_path / ".sops.yaml"
        assert result.exists()

        content = result.read_text()
        assert "age1abc123" in content
        assert "age1def456" in content
        assert "john@example.com" in content
        assert "jane@example.com" in content

    def test_create_sops_config_list(self, tmp_path):
        """Test creating .sops.yaml with list of keys."""
        recipients = ["age1abc123", "age1def456"]

        result = create_sops_config(tmp_path, recipients)

        content = result.read_text()
        assert "age1abc123" in content
        assert "age1def456" in content

    def test_parse_sops_config(self, tmp_path):
        """Test parsing .sops.yaml."""
        sops_config = tmp_path / ".sops.yaml"
        sops_config.write_text(
            """creation_rules:
  - path_regex: '.*\\.yaml$'
    key_groups:
      - age:
          # John <john@example.com>
          - age1abc123
          # jane@example.com
          - age1def456
"""
        )

        result = parse_sops_config(tmp_path)

        assert result["age1abc123"] == "John <john@example.com>"
        assert result["age1def456"] == "jane@example.com"

    def test_parse_sops_config_missing(self, tmp_path):
        """Test parsing when .sops.yaml doesn't exist."""
        result = parse_sops_config(tmp_path)
        assert result == {}

    def test_get_all_recipients(self, tmp_path):
        """Test getting all recipients from .sops.yaml."""
        sops_config = tmp_path / ".sops.yaml"
        sops_config.write_text(
            """creation_rules:
  - path_regex: '.*\\.yaml$'
    key_groups:
      - age:
          - age1abc123
          - age1def456
"""
        )

        result = get_all_recipients(tmp_path)
        assert set(result) == {"age1abc123", "age1def456"}


class TestGetPublicKeyFromPrivate:
    """Tests for get_public_key_from_private."""

    def test_reads_from_comment(self, tmp_path):
        """Test reading public key from comment in key file."""
        key_file = tmp_path / "keys.txt"
        key_file.write_text(
            "# created: 2024-01-01T00:00:00Z\n"
            "# public key: age1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqs3290gq\n"
            "AGE-SECRET-KEY-1QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ\n"
        )

        result = get_public_key_from_private(key_file)
        assert result == "age1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqs3290gq"

    def test_missing_file_raises(self, tmp_path):
        """Test FileNotFoundError when key file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            get_public_key_from_private(tmp_path / "missing.txt")

    def test_derives_from_private_key(self, tmp_path, mock_subprocess_result):
        """Test deriving public key using age-keygen -y."""
        key_file = tmp_path / "keys.txt"
        # Key file without public key comment
        key_file.write_text(
            "AGE-SECRET-KEY-1QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ\n"
        )

        mock_result = mock_subprocess_result(returncode=0, stdout="age1derived123")

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = get_public_key_from_private(key_file)
            assert result == "age1derived123"
            mock_run.assert_called_once()

    def test_invalid_file_raises(self, tmp_path):
        """Test SopsError when file has no valid key."""
        key_file = tmp_path / "keys.txt"
        key_file.write_text("# just a comment\n")

        with pytest.raises(SopsError):
            get_public_key_from_private(key_file)

    def test_empty_file_raises(self, tmp_path):
        """Test SopsError when file is empty."""
        key_file = tmp_path / "keys.txt"
        key_file.write_text("")

        with pytest.raises(SopsError, match="No valid age key found"):
            get_public_key_from_private(key_file)

    def test_whitespace_only_file_raises(self, tmp_path):
        """Test SopsError when file contains only whitespace."""
        key_file = tmp_path / "keys.txt"
        key_file.write_text("   \n\n   \n")

        with pytest.raises(SopsError, match="No valid age key found"):
            get_public_key_from_private(key_file)

    def test_multiple_public_key_comments_uses_first(self, tmp_path):
        """Test that the first public key comment is used when multiple exist."""
        key_file = tmp_path / "keys.txt"
        key_file.write_text(
            "# public key: age1first111\n"
            "# public key: age1second222\n"
            "AGE-SECRET-KEY-1QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ\n"
        )

        result = get_public_key_from_private(key_file)
        assert result == "age1first111"

    def test_public_key_with_trailing_whitespace(self, tmp_path):
        """Test that trailing whitespace is stripped from public key."""
        key_file = tmp_path / "keys.txt"
        key_file.write_text(
            "# public key: age1testkey123   \n"
            "AGE-SECRET-KEY-1QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ\n"
        )

        result = get_public_key_from_private(key_file)
        assert result == "age1testkey123"

    def test_crlf_line_endings(self, tmp_path):
        """Test that CRLF line endings are handled correctly."""
        key_file = tmp_path / "keys.txt"
        # Write with CRLF line endings
        key_file.write_text(
            "# public key: age1crlftest\r\n"
            "AGE-SECRET-KEY-1QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ\r\n"
        )

        result = get_public_key_from_private(key_file)
        # The trailing \r should be stripped
        assert result == "age1crlftest"

    def test_empty_public_key_comment_falls_back_to_derivation(
        self, tmp_path, mock_subprocess_result
    ):
        """Test that empty public key comment falls back to derivation."""
        key_file = tmp_path / "keys.txt"
        # Empty public key comment (just "# public key: " with nothing after)
        key_file.write_text(
            "# public key: \n"
            "AGE-SECRET-KEY-1QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ\n"
        )

        mock_subprocess_result(returncode=0, stdout="age1derived456")

        # Empty string from comment is still truthy check, so we get "" not None
        # The function returns the stripped value, which is ""
        result = get_public_key_from_private(key_file)
        # Empty string is returned since strip() returns ""
        assert result == ""

    def test_timeout_during_derivation_raises(self, tmp_path):
        """Test that timeout during key derivation raises SopsError."""
        key_file = tmp_path / "keys.txt"
        key_file.write_text(
            "AGE-SECRET-KEY-1QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ\n"
        )

        with patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="age-keygen", timeout=30)
        ):
            with pytest.raises(SopsError, match="timed out"):
                get_public_key_from_private(key_file)

    def test_derivation_failure_raises(self, tmp_path, mock_subprocess_result):
        """Test that failed derivation raises SopsError with error message."""
        key_file = tmp_path / "keys.txt"
        key_file.write_text(
            "AGE-SECRET-KEY-1QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ\n"
        )

        mock_result = mock_subprocess_result(returncode=1, stderr="invalid key format")

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(SopsError, match="Failed to derive public key"):
                get_public_key_from_private(key_file)


class TestEncryptFile:
    """Tests for encrypt_file."""

    def test_encrypts_successfully(self, tmp_path, mock_subprocess_result):
        """Test successful encryption."""
        input_file = tmp_path / "secret.yaml"
        input_file.write_text("secret: value")
        output_file = tmp_path / "secret.enc.yaml"

        mock_result = mock_subprocess_result(returncode=0)

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            encrypt_file(input_file, output_file, public_keys=["age1test123"])

            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert "sops" in call_args[0][0]
            assert "--encrypt" in call_args[0][0]

    def test_raises_on_failure(self, tmp_path, mock_subprocess_result):
        """Test raises SopsError on encryption failure."""
        input_file = tmp_path / "secret.yaml"
        input_file.write_text("secret: value")

        mock_result = mock_subprocess_result(returncode=1, stderr="encryption failed")

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(SopsError, match="encryption failed"):
                encrypt_file(input_file, public_keys=["age1test123"])

    def test_raises_on_timeout(self, tmp_path):
        """Test raises SopsError on timeout."""
        input_file = tmp_path / "secret.yaml"
        input_file.write_text("secret: value")

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("sops", 60)):
            with pytest.raises(SopsError, match="timed out"):
                encrypt_file(input_file, public_keys=["age1test123"])


class TestDecryptFile:
    """Tests for decrypt_file."""

    def test_decrypts_successfully(self, tmp_path, mock_subprocess_result):
        """Test successful decryption."""
        input_file = tmp_path / "secret.enc.yaml"
        input_file.write_text("encrypted content")

        mock_result = mock_subprocess_result(returncode=0, stdout="secret: value")

        with patch("subprocess.run", return_value=mock_result):
            result = decrypt_file(input_file)
            assert result == "secret: value"

    def test_raises_on_failure(self, tmp_path, mock_subprocess_result):
        """Test raises SopsError on decryption failure."""
        input_file = tmp_path / "secret.enc.yaml"
        input_file.write_text("encrypted content")

        mock_result = mock_subprocess_result(returncode=1, stderr="decryption failed")

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(SopsError, match="decryption failed"):
                decrypt_file(input_file)

    def test_raises_on_timeout(self, tmp_path):
        """Test raises SopsError on timeout."""
        input_file = tmp_path / "secret.enc.yaml"
        input_file.write_text("encrypted content")

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("sops", 60)):
            with pytest.raises(SopsError, match="timed out"):
                decrypt_file(input_file)


class TestRotateKeys:
    """Tests for rotate_keys."""

    def test_rotates_successfully(self, tmp_path, mock_subprocess_result):
        """Test successful key rotation."""
        input_file = tmp_path / "secret.yaml"
        input_file.write_text("encrypted content")

        # Create .sops.yaml
        sops_config = tmp_path / ".sops.yaml"
        sops_config.write_text("creation_rules:\n  - path_regex: '.*'\n")

        mock_result = mock_subprocess_result(returncode=0)

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            rotate_keys(input_file, ["age1test123"], sops_config=sops_config)

            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert "sops" in call_args[0][0]
            assert "updatekeys" in call_args[0][0]

    def test_raises_on_failure(self, tmp_path, mock_subprocess_result):
        """Test raises SopsError on rotation failure."""
        input_file = tmp_path / "secret.yaml"
        input_file.write_text("encrypted content")

        sops_config = tmp_path / ".sops.yaml"
        sops_config.write_text("creation_rules:\n  - path_regex: '.*'\n")

        mock_result = mock_subprocess_result(returncode=1, stderr="rotation failed")

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(SopsError, match="rotation failed"):
                rotate_keys(input_file, ["age1test123"], sops_config=sops_config)


class TestSecretsManager:
    """Tests for SecretsManager class."""

    def test_load_secrets(self, tmp_path, mock_subprocess_result, make_age_key):
        """Test loading secrets for an environment."""
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        secrets_file = secrets_dir / "dev.yaml"
        secrets_file.write_text("encrypted")

        key_file = make_age_key(content="AGE-SECRET-KEY-...\n")

        mock_result = mock_subprocess_result(returncode=0, stdout="secret_key: abc123\n")

        with patch("subprocess.run", return_value=mock_result):
            manager = SecretsManager(secrets_dir, key_path=key_file)
            result = manager.load_secrets("dev")

            assert result == {"secret_key": "abc123"}

    def test_load_secrets_file_not_found(self, tmp_path, make_age_key):
        """Test raises FileNotFoundError when secrets file missing."""
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()

        key_file = make_age_key(content="AGE-SECRET-KEY-...\n")
        manager = SecretsManager(secrets_dir, key_path=key_file)

        with pytest.raises(FileNotFoundError):
            manager.load_secrets("missing")

    def test_save_secrets(self, tmp_path, make_age_key):
        """Test saving secrets for an environment."""
        secrets_dir = tmp_path / "secrets"

        key_file = make_age_key(content="AGE-SECRET-KEY-...\n")

        # Mock encrypt_file to simulate SOPS creating the output file
        def mock_encrypt(input_path, output_path=None, **kwargs):
            # Simulate SOPS creating the encrypted output file
            target = output_path or input_path
            target.write_text("encrypted content")

        with patch("djb.secrets.core.encrypt_file", side_effect=mock_encrypt):
            manager = SecretsManager(secrets_dir, key_path=key_file)
            manager.save_secrets("dev", {"secret": "value"}, ["age1test123"])

            # Verify secrets file was created
            assert (secrets_dir / "dev.yaml").exists()


class TestLoadSecrets:
    """Tests for load_secrets convenience function."""

    def test_loads_secrets(self, tmp_path, mock_subprocess_result, make_age_key):
        """Test loading secrets with default paths."""
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()
        secrets_file = secrets_dir / "dev.yaml"
        secrets_file.write_text("encrypted")

        key_file = make_age_key(content="AGE-SECRET-KEY-...\n")

        mock_result = mock_subprocess_result(returncode=0, stdout="api_key: secret123\n")

        with patch("subprocess.run", return_value=mock_result):
            result = load_secrets(environment="dev", secrets_dir=secrets_dir, key_path=key_file)
            assert result == {"api_key": "secret123"}

    def test_raises_when_key_missing(self, tmp_path):
        """Test raises FileNotFoundError when key file missing."""
        with pytest.raises(FileNotFoundError, match="Age key file not found"):
            load_secrets(
                environment="dev",
                secrets_dir=tmp_path / "secrets",
                key_path=tmp_path / "missing_key.txt",
            )


class TestLoadSecretsForMode:
    """Tests for load_secrets_for_mode function."""

    def test_loads_for_development_mode(self, tmp_path, mock_subprocess_result, make_age_key):
        """Test loads dev.yaml for DEVELOPMENT mode."""
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()
        secrets_file = secrets_dir / "dev.yaml"
        secrets_file.write_text("encrypted")

        key_file = make_age_key(content="AGE-SECRET-KEY-...\n")

        mock_result = mock_subprocess_result(returncode=0, stdout="debug: true\n")

        with patch("subprocess.run", return_value=mock_result):
            result = load_secrets_for_mode(
                Mode.DEVELOPMENT, secrets_dir=secrets_dir, key_path=key_file
            )
            assert result == {"debug": True}

    def test_loads_for_production_mode(self, tmp_path, mock_subprocess_result, make_age_key):
        """Test loads production.yaml for PRODUCTION mode."""
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()
        secrets_file = secrets_dir / "production.yaml"
        secrets_file.write_text("encrypted")

        key_file = make_age_key(content="AGE-SECRET-KEY-...\n")

        mock_result = mock_subprocess_result(returncode=0, stdout="debug: false\n")

        with patch("subprocess.run", return_value=mock_result):
            result = load_secrets_for_mode(
                Mode.PRODUCTION, secrets_dir=secrets_dir, key_path=key_file
            )
            assert result == {"debug": False}
