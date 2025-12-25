"""End-to-end tests for GPG encryption of age keys.

These tests use real GPG and age commands without mocking.
They properly isolate the test environment to avoid polluting the user's
age keys (GPG symmetric encryption doesn't affect the keyring).

Key isolation techniques:
- Age keys: Generated in tmp_path, never touching user's ~/.age
- GPG symmetric encryption: Uses passphrase via stdin, doesn't affect keyring

Requirements:
- GPG must be installed (brew install gnupg)
- age must be installed (brew install age)
- SOPS must be installed (brew install sops)

Run with: pytest --run-e2e
"""

from __future__ import annotations

from pathlib import Path

import pytest

from djb.secrets import (
    generate_age_key,
    get_public_key_from_private,
    is_gpg_encrypted,
)

from . import (
    age_decrypt,
    age_encrypt,
    assert_gpg_encrypted,
    assert_not_contains_secrets,
    assert_sops_encrypted,
    create_sops_config,
    gpg_decrypt,
    gpg_encrypt,
    sops_decrypt,
    sops_encrypt,
)


# Mark all tests in this module as e2e (skipped by default, use --run-e2e to include)
pytestmark = pytest.mark.e2e_skipped_by_default


@pytest.fixture(autouse=True)
def _require_gpg(require_gpg):
    """Skip tests if GPG is not installed (uses fixture from conftest)."""
    pass


# Note: age_key_dir, test_passphrase fixtures are now provided by conftest.py


class TestGpgEncryption:
    """E2E tests for GPG encryption/decryption."""

    def test_encrypt_and_decrypt_file(self, tmp_path: Path, test_passphrase: str):
        """Test encrypting and decrypting a file with GPG."""
        # Create a test file
        plaintext_file = tmp_path / "secret.txt"
        plaintext_content = "This is a secret message!"
        plaintext_file.write_text(plaintext_content)

        encrypted_file = tmp_path / "secret.txt.gpg"

        # Encrypt the file using shared utility
        result = gpg_encrypt(plaintext_file, encrypted_file, test_passphrase)
        assert result.returncode == 0, f"Encryption failed: {result.stderr}"
        assert encrypted_file.exists()

        # Use shared assertion helpers
        assert_gpg_encrypted(encrypted_file)
        assert_not_contains_secrets(encrypted_file, plaintext_content)

        # Remove original plaintext
        plaintext_file.unlink()

        # Decrypt and verify content using shared utility
        result = gpg_decrypt(encrypted_file, plaintext_file, test_passphrase)
        assert result.returncode == 0, f"Decryption failed: {result.stderr}"

        decrypted_content = plaintext_file.read_text()
        assert decrypted_content == plaintext_content

    def test_decryption_fails_with_wrong_passphrase(self, tmp_path: Path, test_passphrase: str):
        """Test that decryption fails with wrong passphrase."""
        # Create and encrypt a test file
        plaintext_file = tmp_path / "secret.txt"
        plaintext_file.write_text("Secret data!")

        encrypted_file = tmp_path / "secret.txt.gpg"
        result = gpg_encrypt(plaintext_file, encrypted_file, test_passphrase)
        assert result.returncode == 0

        # Try to decrypt with wrong passphrase
        plaintext_file.unlink()
        result = gpg_decrypt(encrypted_file, plaintext_file, "wrong-passphrase")
        # Should fail
        assert result.returncode != 0

    def test_is_gpg_encrypted_nonexistent_file(self, tmp_path: Path):
        """Test is_gpg_encrypted returns False for non-existent file."""
        assert is_gpg_encrypted(tmp_path / "nonexistent.gpg") is False


class TestAgeKeyProtection:
    """E2E tests for protecting age keys with GPG."""

    def test_protect_and_unprotect_age_key(
        self,
        tmp_path: Path,
        age_key_dir: Path,
        test_passphrase: str,
    ):
        """Test full lifecycle: generate key, protect, use, unprotect."""
        # Generate an age key
        key_path = age_key_dir / "keys.txt"
        public_key, private_key = generate_age_key(key_path)

        assert key_path.exists()
        assert public_key.startswith("age1")

        # Save original key content for verification
        original_key_content = key_path.read_text()

        # Protect the key using shared GPG utility
        encrypted_path = key_path.parent / (key_path.name + ".gpg")

        result = gpg_encrypt(key_path, encrypted_path, test_passphrase)
        assert result.returncode == 0, f"GPG encrypt failed: {result.stderr}"

        # Remove plaintext key
        key_path.unlink()

        # Verify state
        assert not key_path.exists()
        assert encrypted_path.exists()

        # Use shared assertion helpers
        assert_gpg_encrypted(encrypted_path)
        assert_not_contains_secrets(encrypted_path, "AGE-SECRET-KEY")

        # Decrypt the key using shared utility
        result = gpg_decrypt(encrypted_path, key_path, test_passphrase)
        assert result.returncode == 0, f"GPG decrypt failed: {result.stderr}"

        # Verify the decrypted key matches the original
        assert key_path.read_text() == original_key_content

        # Verify we can read the public key from the decrypted file
        recovered_public = get_public_key_from_private(key_path)
        assert recovered_public == public_key

    def test_age_key_generation_and_usage(self, age_key_dir: Path, tmp_path: Path):
        """Test that generated age keys work for encryption/decryption."""
        # Generate age key
        key_path = age_key_dir / "keys.txt"
        public_key, _ = generate_age_key(key_path)

        # Create a test file to encrypt
        plaintext = tmp_path / "secret.txt"
        plaintext.write_text("Super secret data!")

        encrypted = tmp_path / "secret.txt.age"

        # Encrypt with age using shared utility
        result = age_encrypt(plaintext, encrypted, public_key)
        assert result.returncode == 0, f"age encrypt failed: {result.stderr}"

        # Decrypt with age using shared utility
        decrypted = tmp_path / "secret.decrypted.txt"
        result = age_decrypt(encrypted, decrypted, key_path)
        assert result.returncode == 0, f"age decrypt failed: {result.stderr}"

        assert decrypted.read_text() == "Super secret data!"


class TestSopsWithProtectedKey:
    """E2E tests for SOPS operations with GPG-protected age keys.

    These tests verify that the protected_age_key context manager
    works correctly with real SOPS encryption/decryption.
    """

    @pytest.fixture
    def sops_secrets_dir(self, tmp_path: Path) -> Path:
        """Create a secrets directory with SOPS config."""
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()
        return secrets_dir

    def test_sops_encrypt_decrypt_with_age_key(
        self,
        age_key_dir: Path,
        sops_secrets_dir: Path,
    ):
        """Test SOPS encryption and decryption using an age key."""
        # Generate age key
        key_path = age_key_dir / "keys.txt"
        public_key, _ = generate_age_key(key_path)

        # Create .sops.yaml config using shared utility
        sops_config = create_sops_config(sops_secrets_dir, public_key)

        # Create a plaintext secrets file
        secrets_file = sops_secrets_dir / "test.yaml"
        secrets_file.write_text("secret_key: my-secret-value\n")

        # Encrypt with SOPS using shared utility
        result = sops_encrypt(secrets_file, sops_config, key_path)
        assert result.returncode == 0, f"SOPS encrypt failed: {result.stderr}"

        # Use shared assertion helpers
        assert_sops_encrypted(secrets_file)
        assert_not_contains_secrets(secrets_file, "my-secret-value")

        # Decrypt with SOPS using shared utility
        result = sops_decrypt(secrets_file, sops_config, key_path)
        assert result.returncode == 0, f"SOPS decrypt failed: {result.stderr}"

        # Verify decrypted content (returned in stdout)
        decrypted_content = result.stdout
        assert "secret_key: my-secret-value" in decrypted_content
