"""Unit tests for djb.secrets.gpg module."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from djb.secrets.gpg import (
    GpgError,
    check_gpg_installed,
    generate_gpg_key,
    get_default_gpg_email,
    get_gpg_home,
    get_gpg_key_id,
    gpg_decrypt_file,
    gpg_encrypt_file,
    has_gpg_secret_key,
    init_gpg_agent_config,
    is_gpg_encrypted,
    setup_gpg_tty,
)


class TestCheckGpgInstalled:
    """Tests for check_gpg_installed."""

    def test_gpg_installed(self):
        """Test returns True when gpg is available."""
        with patch("shutil.which", return_value="/usr/bin/gpg"):
            assert check_gpg_installed() is True

    def test_gpg_not_installed(self):
        """Test returns False when gpg is not available."""
        with patch("shutil.which", return_value=None):
            assert check_gpg_installed() is False


class TestSetupGpgTty:
    """Tests for setup_gpg_tty."""

    def test_sets_gpg_tty_from_tty_command(self, mock_subprocess_result):
        """Test GPG_TTY is set from tty command output."""
        mock_result = mock_subprocess_result(stdout="/dev/ttys001\n")

        with patch("subprocess.run", return_value=mock_result):
            env = setup_gpg_tty()
            assert env["GPG_TTY"] == "/dev/ttys001"

    def test_falls_back_to_dev_tty_on_error(self):
        """Test falls back to /dev/tty when tty command fails."""
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "tty")):
            with patch.dict("os.environ", {}, clear=True):
                env = setup_gpg_tty()
                assert env["GPG_TTY"] == "/dev/tty"

    def test_preserves_existing_gpg_tty(self):
        """Test preserves existing GPG_TTY if set."""
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "tty")):
            with patch.dict("os.environ", {"GPG_TTY": "/dev/pts/0"}):
                env = setup_gpg_tty()
                assert env["GPG_TTY"] == "/dev/pts/0"


class TestIsGpgEncrypted:
    """Tests for is_gpg_encrypted."""

    def test_returns_false_for_nonexistent_file(self, tmp_path: Path):
        """Test returns False when file doesn't exist."""
        assert is_gpg_encrypted(tmp_path / "nonexistent.gpg") is False

    def test_returns_true_for_gpg_file(self, tmp_path: Path, mock_subprocess_result):
        """Test returns True when gpg --list-packets finds encryption markers."""
        test_file = tmp_path / "test.gpg"
        test_file.write_text("fake gpg content")

        # Must include GPG packet markers in output for is_gpg_encrypted to return True
        mock_result = mock_subprocess_result(
            returncode=0, stdout=":pubkey enc packet:\n", stderr=""
        )

        with patch("subprocess.run", return_value=mock_result):
            assert is_gpg_encrypted(test_file) is True

    def test_returns_false_for_plain_file(self, tmp_path: Path, mock_subprocess_result):
        """Test returns False when gpg --list-packets fails."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("plain text")

        mock_result = mock_subprocess_result(returncode=1)

        with patch("subprocess.run", return_value=mock_result):
            assert is_gpg_encrypted(test_file) is False

    def test_returns_false_on_gpg_error(self, tmp_path: Path):
        """Test returns False when gpg command fails."""
        test_file = tmp_path / "test.gpg"
        test_file.write_text("content")

        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert is_gpg_encrypted(test_file) is False


class TestGpgEncryptFile:
    """Tests for gpg_encrypt_file."""

    def test_encrypts_file_successfully(self, tmp_path: Path, mock_subprocess_result):
        """Test successful encryption."""
        input_file = tmp_path / "secret.txt"
        input_file.write_text("secret data")
        output_file = tmp_path / "secret.txt.gpg"

        mock_result = mock_subprocess_result(returncode=0)

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            with patch("djb.secrets.gpg.setup_gpg_tty", return_value={"GPG_TTY": "/dev/tty"}):
                with patch(
                    "djb.secrets.gpg.get_default_gpg_email",
                    return_value="test@example.com",
                ):
                    # Create the temp file that would be created by gpg
                    temp_file = output_file.with_suffix(".gpg.tmp")
                    temp_file.write_text("encrypted")

                    result = gpg_encrypt_file(input_file, output_file)

                    assert result == output_file
                    mock_run.assert_called_once()
                    call_args = mock_run.call_args
                    assert "gpg" in call_args[0][0]
                    assert "--encrypt" in call_args[0][0]

    def test_raises_on_encryption_failure(self, tmp_path: Path, mock_subprocess_result):
        """Test raises GpgError on encryption failure."""
        input_file = tmp_path / "secret.txt"
        input_file.write_text("secret data")
        output_file = tmp_path / "secret.txt.gpg"

        mock_result = mock_subprocess_result(returncode=1, stderr="encryption failed")

        with patch("subprocess.run", return_value=mock_result):
            with patch("djb.secrets.gpg.setup_gpg_tty", return_value={"GPG_TTY": "/dev/tty"}):
                with patch(
                    "djb.secrets.gpg.get_default_gpg_email",
                    return_value="test@example.com",
                ):
                    with pytest.raises(GpgError, match="encryption failed"):
                        gpg_encrypt_file(input_file, output_file)

    def test_uses_armor_by_default(self, tmp_path: Path, mock_subprocess_result):
        """Test uses ASCII armor by default."""
        input_file = tmp_path / "secret.txt"
        input_file.write_text("secret data")
        output_file = tmp_path / "secret.txt.gpg"

        mock_result = mock_subprocess_result(returncode=0)

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            with patch("djb.secrets.gpg.setup_gpg_tty", return_value={"GPG_TTY": "/dev/tty"}):
                with patch(
                    "djb.secrets.gpg.get_default_gpg_email",
                    return_value="test@example.com",
                ):
                    temp_file = output_file.with_suffix(".gpg.tmp")
                    temp_file.write_text("encrypted")

                    gpg_encrypt_file(input_file, output_file)

                    call_args = mock_run.call_args[0][0]
                    assert "--armor" in call_args


class TestGpgDecryptFile:
    """Tests for gpg_decrypt_file."""

    def test_decrypts_file_successfully(self, tmp_path: Path, mock_subprocess_result):
        """Test successful decryption to file."""
        input_file = tmp_path / "secret.txt.gpg"
        input_file.write_text("encrypted data")
        output_file = tmp_path / "secret.txt"

        mock_result = mock_subprocess_result(returncode=0, stdout="")

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            with patch("djb.secrets.gpg.setup_gpg_tty", return_value={"GPG_TTY": "/dev/tty"}):
                # Create output file that would be created by gpg
                output_file.write_text("decrypted")

                gpg_decrypt_file(input_file, output_file)

                mock_run.assert_called_once()
                call_args = mock_run.call_args
                assert "gpg" in call_args[0][0]
                assert "--decrypt" in call_args[0][0]

    def test_returns_content_without_output_path(self, tmp_path: Path, mock_subprocess_result):
        """Test returns decrypted content when no output path specified."""
        input_file = tmp_path / "secret.txt.gpg"
        input_file.write_text("encrypted data")

        mock_result = mock_subprocess_result(returncode=0, stdout="decrypted content")

        with patch("subprocess.run", return_value=mock_result):
            with patch("djb.secrets.gpg.setup_gpg_tty", return_value={"GPG_TTY": "/dev/tty"}):
                result = gpg_decrypt_file(input_file)
                assert result == "decrypted content"

    def test_raises_on_decryption_failure(self, tmp_path: Path, mock_subprocess_result):
        """Test raises GpgError on decryption failure."""
        input_file = tmp_path / "secret.txt.gpg"
        input_file.write_text("encrypted data")

        mock_result = mock_subprocess_result(returncode=1, stderr="decryption failed")

        with patch("subprocess.run", return_value=mock_result):
            with patch("djb.secrets.gpg.setup_gpg_tty", return_value={"GPG_TTY": "/dev/tty"}):
                with pytest.raises(GpgError, match="decryption failed"):
                    gpg_decrypt_file(input_file)


class TestGetGpgKeyId:
    """Tests for get_gpg_key_id."""

    def test_returns_key_id_when_found(self, mock_subprocess_result):
        """Test returns key ID when GPG key exists for email."""
        mock_result = mock_subprocess_result(
            returncode=0, stdout="sec:u:4096:1:ABCDEF1234567890:1234567890::u:::scESC:::\n"
        )

        with patch("subprocess.run", return_value=mock_result):
            result = get_gpg_key_id("test@example.com")
            assert result == "ABCDEF1234567890"

    def test_returns_none_when_not_found(self, mock_subprocess_result):
        """Test returns None when no key found for email."""
        mock_result = mock_subprocess_result(
            returncode=2, stdout=""
        )  # GPG returns 2 when no key found

        with patch("subprocess.run", return_value=mock_result):
            result = get_gpg_key_id("unknown@example.com")
            assert result is None

    def test_returns_none_on_error(self):
        """Test returns None when GPG command fails."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = get_gpg_key_id("test@example.com")
            assert result is None

    def test_returns_none_on_timeout(self):
        """Test returns None when GPG command times out."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("gpg", 60)):
            result = get_gpg_key_id("test@example.com")
            assert result is None


class TestGetDefaultGpgEmail:
    """Tests for get_default_gpg_email."""

    def test_returns_email_when_key_exists(self, mock_subprocess_result):
        """Test extracts email from GPG UID.

        GPG --with-colons output format for uid line (field 10 is the UID):
        uid:validity:::::::::userid:comment:...
        """
        # Field 10 (index 9) contains the UID
        mock_result = mock_subprocess_result(
            returncode=0,
            stdout=(
                "sec:u:4096:1:ABCD1234:1234567890::u:::scESC:::\n"
                "uid:u::::1234567890::0123456789ABCDEF:0:Test User <test@example.com>:\n"
            ),
        )

        with patch("subprocess.run", return_value=mock_result):
            result = get_default_gpg_email()
            assert result == "test@example.com"

    def test_returns_none_when_no_keys(self, mock_subprocess_result):
        """Test returns None when no GPG keys exist."""
        mock_result = mock_subprocess_result(returncode=0, stdout="")

        with patch("subprocess.run", return_value=mock_result):
            result = get_default_gpg_email()
            assert result is None

    def test_returns_none_on_error(self):
        """Test returns None when GPG command fails."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = get_default_gpg_email()
            assert result is None


class TestHasGpgSecretKey:
    """Tests for has_gpg_secret_key."""

    def test_returns_true_when_secret_key_exists(self, mock_subprocess_result):
        """Test returns True when at least one secret key exists."""
        mock_result = mock_subprocess_result(
            returncode=0, stdout="sec:u:4096:1:ABCD1234:1234567890::u:::scESC:::\n"
        )

        with patch("subprocess.run", return_value=mock_result):
            assert has_gpg_secret_key() is True

    def test_returns_false_when_no_secret_keys(self, mock_subprocess_result):
        """Test returns False when no secret keys exist."""
        mock_result = mock_subprocess_result(returncode=0, stdout="")

        with patch("subprocess.run", return_value=mock_result):
            assert has_gpg_secret_key() is False

    def test_returns_false_on_error(self):
        """Test returns False when GPG command fails."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert has_gpg_secret_key() is False


class TestGetGpgHome:
    """Tests for get_gpg_home."""

    def test_returns_gnupghome_env_var(self):
        """Test returns GNUPGHOME if set."""
        with patch.dict("os.environ", {"GNUPGHOME": "/custom/gnupg"}):
            result = get_gpg_home()
            assert result == Path("/custom/gnupg")

    def test_returns_default_when_no_env_var(self):
        """Test returns ~/.gnupg when GNUPGHOME not set."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("os.environ.get", return_value=None):
                result = get_gpg_home()
                assert result == Path.home() / ".gnupg"


class TestInitGpgAgentConfig:
    """Tests for init_gpg_agent_config."""

    def test_creates_config_when_missing(self, tmp_path: Path):
        """Test creates gpg-agent.conf when it doesn't exist."""
        gnupg_home = tmp_path / ".gnupg"

        with patch("djb.secrets.gpg.get_gpg_home", return_value=gnupg_home):
            with patch("subprocess.run"):  # Mock gpgconf reload
                result = init_gpg_agent_config()

                assert result is True
                config_path = gnupg_home / "gpg-agent.conf"
                assert config_path.exists()
                content = config_path.read_text()
                assert "default-cache-ttl 28800" in content

    def test_skips_when_config_exists(self, tmp_path: Path):
        """Test doesn't overwrite existing config."""
        gnupg_home = tmp_path / ".gnupg"
        gnupg_home.mkdir()
        config_path = gnupg_home / "gpg-agent.conf"
        config_path.write_text("# custom config\n")

        with patch("djb.secrets.gpg.get_gpg_home", return_value=gnupg_home):
            result = init_gpg_agent_config()

            assert result is False
            assert config_path.read_text() == "# custom config\n"


class TestGenerateGpgKey:
    """Tests for generate_gpg_key."""

    def test_generates_key_successfully(self, mock_subprocess_result):
        """Test successful GPG key generation."""
        mock_result = mock_subprocess_result(returncode=0)

        with patch("subprocess.run", return_value=mock_result):
            with patch("djb.secrets.gpg.setup_gpg_tty", return_value={"GPG_TTY": "/dev/tty"}):
                result = generate_gpg_key("Test User", "test@example.com")
                assert result is True

    def test_raises_on_failure(self, mock_subprocess_result):
        """Test raises GpgError on key generation failure."""
        mock_result = mock_subprocess_result(returncode=1, stderr="key generation failed")

        with patch("subprocess.run", return_value=mock_result):
            with patch("djb.secrets.gpg.setup_gpg_tty", return_value={"GPG_TTY": "/dev/tty"}):
                with pytest.raises(GpgError, match="Failed to generate GPG key"):
                    generate_gpg_key("Test User", "test@example.com")

    def test_raises_on_timeout(self):
        """Test raises GpgError on timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("gpg", 120)):
            with patch("djb.secrets.gpg.setup_gpg_tty", return_value={"GPG_TTY": "/dev/tty"}):
                with pytest.raises(GpgError, match="timed out"):
                    generate_gpg_key("Test User", "test@example.com")
