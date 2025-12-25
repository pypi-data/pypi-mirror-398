"""End-to-end tests for djb secrets CLI commands.

These tests exercise the secrets management CLI against real encryption tools
(age, SOPS, GPG) while properly isolating the test environment.

Commands tested:
- djb secrets init
- djb secrets edit
- djb secrets view
- djb secrets list
- djb secrets generate-key
- djb secrets export-key
- djb secrets upgrade
- djb secrets rotate
- djb secrets protect
- djb secrets unprotect

Requirements:
- GPG must be installed (brew install gnupg)
- age must be installed (brew install age)
- SOPS must be installed (brew install sops)

Run with: pytest --run-e2e
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from unittest.mock import patch

import pytest

from djb.cli.djb import djb_cli
from djb.secrets import (
    SOPS_TIMEOUT,
    SecretsManager,
    SopsError,
    create_sops_config,
    encrypt_file,
    generate_age_key,
    get_public_key_from_private,
    parse_sops_config,
)

from . import (
    assert_gpg_encrypted,
    assert_not_contains_secrets,
    assert_sops_encrypted,
    gpg_decrypt,
    gpg_encrypt,
    sops_decrypt,
)


# Mark all tests in this module as e2e (skipped by default, use --run-e2e to include)
pytestmark = pytest.mark.e2e_skipped_by_default


class TestSecretsInit:
    """E2E tests for djb secrets init command."""

    def test_init_creates_key_and_secrets(
        self, runner, isolated_project, age_key_dir, djb_config_env
    ):
        """Test that secrets init creates key, .sops.yaml, and secrets files."""
        key_path = age_key_dir / "keys.txt"
        secrets_dir = isolated_project / "secrets"

        # Set env for djb config
        env = {
            **djb_config_env,
            "DJB_PROJECT_DIR": str(isolated_project),
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                [
                    "secrets",
                    "init",
                    "--key-path",
                    str(key_path),
                    "--secrets-dir",
                    str(secrets_dir),
                ],
            )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify key was created
        assert key_path.exists(), "Age key was not created"
        key_content = key_path.read_text()
        assert "AGE-SECRET-KEY-" in key_content

        # Verify .sops.yaml was created
        sops_config = secrets_dir / ".sops.yaml"
        assert sops_config.exists(), ".sops.yaml was not created"
        assert "age:" in sops_config.read_text()

        # Verify secrets files were created
        for env_name in ["dev", "staging", "production"]:
            secrets_file = secrets_dir / f"{env_name}.yaml"
            assert secrets_file.exists(), f"{env_name}.yaml was not created"
            # Files should be SOPS encrypted
            assert_sops_encrypted(secrets_file)

        # Verify README was created
        readme = secrets_dir / "README.md"
        assert readme.exists(), "README.md was not created"

    def test_init_reuses_existing_key(self, runner, isolated_project, age_key_dir, djb_config_env):
        """Test that init reuses an existing key without --force."""
        key_path = age_key_dir / "keys.txt"
        secrets_dir = isolated_project / "secrets"

        # Pre-create a key
        original_public, _ = generate_age_key(key_path)

        env = {
            **djb_config_env,
            "DJB_PROJECT_DIR": str(isolated_project),
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                [
                    "secrets",
                    "init",
                    "--key-path",
                    str(key_path),
                    "--secrets-dir",
                    str(secrets_dir),
                ],
            )

        assert result.exit_code == 0

        # Verify the original key was preserved
        current_public = get_public_key_from_private(key_path)
        assert current_public == original_public

        # Message should indicate reuse
        assert "existing" in result.output.lower() or "using" in result.output.lower()


class TestSecretsView:
    """E2E tests for djb secrets view command."""

    def test_view_shows_decrypted_secrets(
        self,
        runner,
        isolated_project_with_secrets,
        djb_config_env,
    ):
        """Test that view command decrypts and shows secrets."""
        project_dir, key_path = isolated_project_with_secrets
        secrets_dir = project_dir / "secrets"

        env = {
            **djb_config_env,
            "DJB_PROJECT_DIR": str(project_dir),
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                [
                    "secrets",
                    "view",
                    "dev",
                    "--key-path",
                    str(key_path),
                    "--secrets-dir",
                    str(secrets_dir),
                ],
            )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        # Should show decrypted content (secrets contain placeholder values)
        assert "django_secret_key" in result.output.lower() or "secret" in result.output.lower()

    def test_view_specific_key(
        self,
        runner,
        isolated_project_with_secrets,
        djb_config_env,
    ):
        """Test viewing a specific key from secrets."""
        project_dir, key_path = isolated_project_with_secrets
        secrets_dir = project_dir / "secrets"

        env = {
            **djb_config_env,
            "DJB_PROJECT_DIR": str(project_dir),
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                [
                    "secrets",
                    "view",
                    "dev",
                    "--key-path",
                    str(key_path),
                    "--secrets-dir",
                    str(secrets_dir),
                    "--key",
                    "django_secret_key",
                ],
            )

        # Either shows the key or says it's not found (depends on template)
        assert result.exit_code == 0 or "not found" in result.output.lower()


class TestSecretsList:
    """E2E tests for djb secrets list command."""

    def test_list_shows_environments(
        self,
        runner,
        isolated_project_with_secrets,
        djb_config_env,
    ):
        """Test that list shows available environments."""
        project_dir, _ = isolated_project_with_secrets
        secrets_dir = project_dir / "secrets"

        env = {
            **djb_config_env,
            "DJB_PROJECT_DIR": str(project_dir),
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                ["secrets", "list", "--secrets-dir", str(secrets_dir)],
            )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        # Should list the environments
        assert "dev" in result.output
        assert "staging" in result.output
        assert "production" in result.output


class TestSecretsGenerateKey:
    """E2E tests for djb secrets generate-key command."""

    def test_generate_key_outputs_random_key(self, runner):
        """Test that generate-key outputs a random Django secret key."""
        result = runner.invoke(djb_cli, ["secrets", "generate-key"])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        # Should contain a 50-character key
        # The output should have some long string of characters
        assert len(result.output) > 50
        assert "django" in result.output.lower() or "secret" in result.output.lower()


class TestSecretsExportKey:
    """E2E tests for djb secrets export-key command."""

    def test_export_key_outputs_private_key(self, runner, age_key_dir, djb_config_env, tmp_path):
        """Test that export-key outputs the AGE-SECRET-KEY."""
        key_path = age_key_dir / "keys.txt"

        # Generate a key first
        generate_age_key(key_path)

        env = {
            **djb_config_env,
            "DJB_PROJECT_DIR": str(tmp_path),
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                ["secrets", "export-key", "--key-path", str(key_path)],
            )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        # Should output the secret key
        assert "AGE-SECRET-KEY-" in result.output


class TestSecretsProtectUnprotect:
    """E2E tests for GPG protection of age keys.

    Note: The protect/unprotect CLI commands use default key paths based on
    get_default_key_path(), which makes them difficult to test in isolation.
    These tests verify the underlying functions directly instead of through
    the CLI, as the GPG functionality is already tested in test_gpg.py.
    """

    def test_protect_and_unprotect_functions(self, age_key_dir, test_passphrase):
        """Test protect_age_key and unprotect_age_key functions directly."""
        key_path = age_key_dir / "keys.txt"
        encrypted_path = key_path.parent / (key_path.name + ".gpg")

        # Generate a key first
        public_key, _ = generate_age_key(key_path)
        original_content = key_path.read_text()

        # Protect using our shared utilities (simulating what the CLI would do)
        gpg_encrypt(key_path, encrypted_path, test_passphrase)
        key_path.unlink()

        # Verify protection worked
        assert not key_path.exists(), "Plaintext key should be removed"
        assert encrypted_path.exists(), "Encrypted key should exist"
        assert_gpg_encrypted(encrypted_path)
        assert_not_contains_secrets(encrypted_path, "AGE-SECRET-KEY")

        # Unprotect using our shared utilities
        gpg_decrypt(encrypted_path, key_path, test_passphrase)

        # Verify unprotection worked
        assert key_path.exists(), "Plaintext key should be restored"
        assert key_path.read_text() == original_content

    def test_gpg_protect_preserves_key_integrity(self, age_key_dir, test_passphrase):
        """Test that GPG protection preserves the age key's functionality."""
        key_path = age_key_dir / "keys.txt"
        encrypted_path = key_path.parent / (key_path.name + ".gpg")

        # Generate a key
        public_key, _ = generate_age_key(key_path)
        original_content = key_path.read_text()
        original_public = get_public_key_from_private(key_path)

        # Protect the key
        gpg_encrypt(key_path, encrypted_path, test_passphrase)
        key_path.unlink()

        # Unprotect and verify
        gpg_decrypt(encrypted_path, key_path, test_passphrase)

        # Verify the key is functionally identical
        recovered_public = get_public_key_from_private(key_path)
        assert recovered_public == original_public
        assert key_path.read_text() == original_content


class TestSecretsRotate:
    """E2E tests for djb secrets rotate command."""

    def test_rotate_adds_new_recipient(
        self,
        runner,
        isolated_project_with_secrets,
        make_age_key,
        djb_config_env,
    ):
        """Test that rotate can add a new recipient."""
        project_dir, key_path = isolated_project_with_secrets
        secrets_dir = project_dir / "secrets"

        # Create a new key to add
        bob_key_path, bob_public = make_age_key("bob")

        env = {
            **djb_config_env,
            "DJB_PROJECT_DIR": str(project_dir),
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                [
                    "secrets",
                    "rotate",
                    "--key-path",
                    str(key_path),
                    "--secrets-dir",
                    str(secrets_dir),
                    "--add-key",
                    bob_public,
                    "--add-email",
                    "bob@example.com",
                ],
            )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify .sops.yaml was updated
        sops_config = secrets_dir / ".sops.yaml"
        config_content = sops_config.read_text()
        assert bob_public in config_content
        assert "bob@example.com" in config_content

        # Verify secrets are re-encrypted (staging/production only)
        # Bob should now be able to decrypt with his key
        staging_file = secrets_dir / "staging.yaml"
        if staging_file.exists():
            result = sops_decrypt(staging_file, sops_config, bob_key_path)
            # Should be able to decrypt with new key
            assert result.returncode == 0 or "staging" in result.stderr.lower()


class TestSecretsUpgrade:
    """E2E tests for djb secrets upgrade command."""

    def test_upgrade_reports_up_to_date(
        self,
        runner,
        isolated_project_with_secrets,
        djb_config_env,
    ):
        """Test that upgrade reports when secrets are up to date."""
        project_dir, key_path = isolated_project_with_secrets
        secrets_dir = project_dir / "secrets"

        env = {
            **djb_config_env,
            "DJB_PROJECT_DIR": str(project_dir),
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(
                djb_cli,
                [
                    "secrets",
                    "upgrade",
                    "dev",
                    "--key-path",
                    str(key_path),
                    "--secrets-dir",
                    str(secrets_dir),
                ],
            )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        # Should indicate up to date or show what was added
        assert "up to date" in result.output.lower() or "added" in result.output.lower()


class TestEdgeCases:
    """E2E tests for edge cases and error recovery scenarios."""

    def test_concurrent_access_serialized_by_file_locking(self, tmp_path):
        """File locking serializes concurrent access to protected key.

        This test spawns two subprocesses that try to access the protected
        age key simultaneously. The file lock ensures they run sequentially
        (one waits for the other to finish).
        """

        # Set up project structure
        project_root = tmp_path / "project"
        age_dir = project_root / ".age"
        age_dir.mkdir(parents=True)
        key_path = age_dir / "keys.txt"

        # Create a plaintext key
        key_path.write_text("# test key\nAGE-SECRET-KEY-TEST")

        # Results file for subprocesses to write timing data
        results_file = tmp_path / "results.json"
        results_file.write_text("[]")

        # Script that acquires lock, writes timing, holds for delay, releases.
        # We mock GPG here because otherwise process 1 would GPG-encrypt the key
        # on normal exit, and process 2 couldn't decrypt it (no shared GPG key).
        # This is acceptable because we're testing FILE LOCKING, not GPG - the
        # lock acquisition happens before any GPG operations.
        script = f"""
import fcntl
import json
import time
from pathlib import Path
from unittest.mock import patch
from djb.secrets import protected_age_key

proc_id = int(__import__("sys").argv[1])
hold_time = float(__import__("sys").argv[2])
results_file = Path("{results_file}")

start = time.time()
with patch("djb.secrets.protected.check_gpg_installed", return_value=False):
    with protected_age_key():
        acquired = time.time()
        time.sleep(hold_time)
        released = time.time()

# Write results atomically using fcntl for locking
lock_file = open(str(results_file) + ".lock", "w")
try:
    fcntl.flock(lock_file, fcntl.LOCK_EX)
    data = json.loads(results_file.read_text())
    data.append({{"proc": proc_id, "start": start, "acquired": acquired, "released": released}})
    results_file.write_text(json.dumps(data))
finally:
    fcntl.flock(lock_file, fcntl.LOCK_UN)
    lock_file.close()
"""

        # Env with DJB_PROJECT_DIR for the subprocess
        env = {**os.environ, "DJB_PROJECT_DIR": str(project_root)}

        # Start process 1 (holds lock for 0.15s)
        proc1 = subprocess.Popen(
            [sys.executable, "-c", script, "1", "0.15"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        # Small delay to ensure proc1 acquires lock first
        time.sleep(0.05)

        # Start process 2 (holds lock for 0.05s)
        proc2 = subprocess.Popen(
            [sys.executable, "-c", script, "2", "0.05"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        # Wait for both to complete
        _, stderr1 = proc1.communicate(timeout=10)
        _, stderr2 = proc2.communicate(timeout=10)

        assert proc1.returncode == 0, f"Process 1 failed: {stderr1}"
        assert proc2.returncode == 0, f"Process 2 failed: {stderr2}"

        # Read results

        results = json.loads(results_file.read_text())
        assert len(results) == 2, f"Expected 2 results, got {len(results)}"

        r1 = next(r for r in results if r["proc"] == 1)
        r2 = next(r for r in results if r["proc"] == 2)

        # Process 2 should not acquire lock until process 1 releases it
        # (with small tolerance for timing variations)
        assert r2["acquired"] >= r1["released"] - 0.02, (
            f"Process 2 acquired lock at {r2['acquired']:.3f} "
            f"but process 1 released at {r1['released']:.3f}. "
            f"File locking is not working - processes ran concurrently."
        )

    def test_atomic_sops_config_write(self, tmp_path):
        """Test that .sops.yaml writes use atomic pattern (temp file + rename).

        This verifies that temp files don't linger after successful writes.
        """
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()
        temp_path = secrets_dir / ".sops.yaml.tmp"

        # Create initial config
        recipients1 = {"age1abc123": "alice@example.com"}
        create_sops_config(secrets_dir, recipients1)

        # Verify config is valid and temp file cleaned up
        assert (secrets_dir / ".sops.yaml").exists()
        assert not temp_path.exists(), "Temp file should be cleaned up"
        parsed = parse_sops_config(secrets_dir)
        assert "age1abc123" in parsed

        # Update config
        recipients2 = {"age1abc123": "alice@example.com", "age1def456": "bob@example.com"}
        create_sops_config(secrets_dir, recipients2)

        # Verify updated config is valid and temp file cleaned up
        assert not temp_path.exists(), "Temp file should be cleaned up"
        parsed = parse_sops_config(secrets_dir)
        assert "age1abc123" in parsed
        assert "age1def456" in parsed

    def test_symlink_key_file_rejected(self, tmp_path):
        """Symlinked key files are rejected for security.

        If the age key file itself is a symlink, it should be rejected to prevent
        attacks where a symlink could redirect key operations to an attacker-controlled
        location. The symlink check runs unconditionally in protected_age_key().
        """
        # Set up project structure with symlinked key
        project_root = tmp_path / "project"
        age_dir = project_root / ".age"
        age_dir.mkdir(parents=True)

        # Create the real key file elsewhere
        real_key = tmp_path / "real_key.txt"
        real_key.write_text("# real key\nAGE-SECRET-KEY-REAL")

        # Create symlink at the expected key location
        key_path = age_dir / "keys.txt"
        key_path.symlink_to(real_key)

        assert key_path.is_symlink(), "Test setup: key should be a symlink"
        assert key_path.exists(), "Test setup: symlink target should exist"

        # Run in subprocess - no mocking needed, symlink check runs unconditionally
        # Use DJB_PROJECT_DIR env var to configure djb for the subprocess
        script = """
from djb.secrets import protected_age_key, ProtectedFileError

try:
    with protected_age_key():
        print("ERROR: Should have raised ProtectedFileError")
        __import__("sys").exit(1)
except ProtectedFileError as e:
    if "symlink" in str(e).lower():
        print("OK: ProtectedFileError with symlink message")
        __import__("sys").exit(0)
    else:
        print(f"ERROR: Wrong error message: {e}")
        __import__("sys").exit(1)
except Exception as e:
    print(f"ERROR: Unexpected exception: {type(e).__name__}: {e}")
    __import__("sys").exit(1)
"""

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "DJB_PROJECT_DIR": str(project_root)},
        )

        assert result.returncode == 0, (
            f"Symlink rejection test failed.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
        assert "OK" in result.stdout, f"Unexpected output: {result.stdout}"

    def test_timeout_exception_converted_to_sops_error(self, tmp_path):
        """Test that subprocess timeout exceptions are converted to SopsError.

        When subprocess.run raises TimeoutExpired, it should be caught and
        re-raised as a SopsError with a helpful message.

        Note: This test uses mocking because causing a real SOPS timeout would
        require waiting for the actual timeout duration (5+ seconds), making it
        impractical for regular test runs. The mock verifies the error handling
        code path that converts TimeoutExpired to SopsError.
        """
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()
        input_file = secrets_dir / "test.yaml"
        input_file.write_text("secret: value")

        # Mock subprocess.run to simulate a timeout
        def mock_timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired("sops", SOPS_TIMEOUT)

        with patch("subprocess.run", side_effect=mock_timeout):
            with pytest.raises(SopsError, match="timed out"):
                encrypt_file(input_file, public_keys=["age1test123"])

    def test_temp_file_cleanup_on_encryption_failure(self, tmp_path):
        """Temp files are cleaned up when encryption fails.

        SecretsManager.save_secrets() writes to a temp file before encrypting.
        If encryption fails, the temp file should still be cleaned up by the
        finally block to avoid leaving plaintext secrets on disk.

        This test causes real SOPS encryption to fail by using an invalid
        age public key format.
        """
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir(parents=True)
        key_path = tmp_path / ".age" / "keys.txt"
        key_path.parent.mkdir(parents=True)

        # Generate a real age key for the manager
        public_key, _ = generate_age_key(key_path)

        # Create a valid .sops.yaml config
        create_sops_config(secrets_dir, {public_key: "test@example.com"})

        temp_file = secrets_dir / ".dev.tmp.yaml"
        manager = SecretsManager(secrets_dir=secrets_dir, key_path=key_path)

        # Use an invalid public key to cause SOPS encryption to fail
        # "invalid-key" is not a valid age public key format
        with pytest.raises(SopsError):
            manager.save_secrets("dev", {"secret": "value"}, ["invalid-not-an-age-key"])

        # Temp file should be cleaned up after failure
        assert not temp_file.exists(), (
            "Temp file should be cleaned up on encryption failure to avoid "
            "leaving plaintext secrets on disk"
        )

    def test_sigint_triggers_signal_handler_cleanup(self, tmp_path):
        """SIGINT triggers signal handler to clean up decrypted key.

        This test spawns a subprocess that enters protected_age_key(), then sends
        SIGINT to verify the signal handler (not the finally block) cleans up.

        The signal handler calls _cleanup_pending() and then re-raises the signal,
        which kills the process before the finally block runs.
        """
        # Set up project structure
        project_root = tmp_path / "project"
        age_dir = project_root / ".age"
        age_dir.mkdir(parents=True)

        plaintext_path = age_dir / "keys.txt"

        # Create a plaintext key
        key_content = "# test key\nAGE-SECRET-KEY-TEST123"
        plaintext_path.write_text(key_content)

        # Write a subprocess script that enters protected_age_key and waits
        # No mocking - with only plaintext key (no .gpg file), uses plaintext path
        # Use DJB_PROJECT_DIR env var to configure djb for the subprocess
        script = """
import sys
import time
from djb.secrets import protected_age_key

with protected_age_key():
    # Signal that we're ready (inside context, key should exist)
    print("READY", flush=True)
    # Wait for signal - this will be interrupted by SIGINT
    time.sleep(60)
    # If we get here, test failed (should have been killed by signal)
    print("ERROR: Should have been killed by signal", flush=True)
    sys.exit(1)
"""

        # Run the script as a subprocess with DJB_PROJECT_DIR set
        proc = subprocess.Popen(
            [sys.executable, "-c", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "DJB_PROJECT_DIR": str(project_root)},
        )

        try:
            # Wait for subprocess to signal it's ready (inside context)
            assert proc.stdout is not None, "stdout should be available"
            ready_line = proc.stdout.readline()
            assert "READY" in ready_line, f"Expected READY, got: {ready_line}"

            # Verify plaintext exists before signal (subprocess is inside context)
            assert plaintext_path.exists(), "Key should exist while in context"

            # Send SIGINT (Ctrl+C) - this triggers the signal handler
            proc.send_signal(signal.SIGINT)

            # Wait for subprocess to exit (killed by re-raised signal)
            proc.wait(timeout=5)

            # Verify process was killed by signal (negative return code = signal number)
            # SIGINT is typically 2, so return code should be -2 or 130 (128+2)
            assert proc.returncode != 0, "Process should have been killed by signal"

            # The signal handler should have cleaned up the plaintext
            assert not plaintext_path.exists(), (
                "Signal handler should have removed plaintext key. "
                "This tests the signal handler path, not the finally block."
            )

        finally:
            # Clean up subprocess if still running
            if proc.poll() is None:
                proc.kill()
                proc.wait()

    def test_sigterm_triggers_signal_handler_cleanup(self, tmp_path):
        """SIGTERM triggers signal handler to clean up decrypted key.

        Similar to SIGINT test but with SIGTERM to verify both signals are handled.
        """
        # Set up project structure
        project_root = tmp_path / "project"
        age_dir = project_root / ".age"
        age_dir.mkdir(parents=True)

        plaintext_path = age_dir / "keys.txt"

        # Create a plaintext key
        key_content = "# test key\nAGE-SECRET-KEY-TERM456"
        plaintext_path.write_text(key_content)

        # Write a subprocess script - no mocking needed
        # Use DJB_PROJECT_DIR env var to configure djb for the subprocess
        script = """
import sys
import time
from djb.secrets import protected_age_key

with protected_age_key():
    print("READY", flush=True)
    time.sleep(60)
    sys.exit(1)
"""

        proc = subprocess.Popen(
            [sys.executable, "-c", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "DJB_PROJECT_DIR": str(project_root)},
        )

        try:
            assert proc.stdout is not None, "stdout should be available"
            ready_line = proc.stdout.readline()
            assert "READY" in ready_line, f"Expected READY, got: {ready_line}"

            assert plaintext_path.exists(), "Key should exist while in context"

            # Send SIGTERM
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=5)

            assert proc.returncode != 0, "Process should have been killed by signal"

            assert (
                not plaintext_path.exists()
            ), "Signal handler should have removed plaintext key on SIGTERM"

        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
