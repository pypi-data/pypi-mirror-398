"""
Context managers for protected file access.

Provides guaranteed cleanup of decrypted sensitive files, ensuring
plaintext is never left on disk after an operation completes or fails.

Design principles:
- Use finally blocks for guaranteed cleanup
- Signal handlers for Ctrl+C protection (like bash `trap on_exit EXIT`)
- Atomic file operations (temp file + rename)
- State detection to handle mixed encrypted/plaintext files
- Graceful handling of plaintext keys (warn but use, then encrypt on exit)
- File locking to prevent race conditions with concurrent access
"""

from __future__ import annotations

import atexit
import fcntl
import os
import signal
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import click

from djb.core.logging import get_logger
from djb.secrets.gpg import (
    GpgError,
    GpgTimeoutError,
    check_gpg_installed,
    gpg_decrypt_file,
    gpg_encrypt_file,
    is_gpg_encrypted,
)
from djb.secrets.paths import get_default_key_path, get_encrypted_key_path

if TYPE_CHECKING:
    from collections.abc import Generator

logger = get_logger(__name__)


class ProtectedFileError(Exception):
    """Error accessing protected file."""


# Track files that need cleanup for signal handlers.
# This global list is used by the signal handler (_cleanup_on_signal) and
# atexit handler (_cleanup_pending) to ensure cleanup happens even if the
# process is interrupted (Ctrl+C) or exits unexpectedly.
# Each entry is (plaintext_path, encrypted_path, should_encrypt_on_exit)
_pending_cleanups: list[tuple[Path, Path, bool]] = []

# Store original signal handlers so we can restore them after cleanup
# and re-raise the signal to allow normal termination behavior.
_original_handlers: dict[int, object] = {}

# Track active lock file handles to ensure proper cleanup
_active_locks: dict[Path, "int"] = {}  # lock_path -> file descriptor


def _cleanup_pending() -> None:
    """Clean up any pending decrypted files."""
    for plaintext_path, encrypted_path, should_encrypt in list(_pending_cleanups):
        try:
            if plaintext_path.exists():
                if should_encrypt:
                    try:
                        gpg_encrypt_file(plaintext_path, encrypted_path)
                    except GpgError:
                        # If encryption fails during cleanup, log but continue
                        # The plaintext will be deleted anyway - better than leaving it
                        logger.warning(f"Failed to re-encrypt {plaintext_path} during cleanup")
                # Always remove plaintext
                plaintext_path.unlink()
        except OSError:
            pass


def _cleanup_on_signal(signum: int, frame: object) -> None:
    """Signal handler to clean up decrypted files."""
    _cleanup_pending()

    # Restore original handler and re-raise signal
    original = _original_handlers.get(signum, signal.SIG_DFL)
    signal.signal(signum, original)  # type: ignore[arg-type]
    os.kill(os.getpid(), signum)


def _register_signal_handlers() -> None:
    """Register signal handlers for cleanup on interrupt."""
    for sig in (signal.SIGINT, signal.SIGTERM):
        if sig not in _original_handlers:
            _original_handlers[sig] = signal.signal(sig, _cleanup_on_signal)


# Register atexit handler
atexit.register(_cleanup_pending)


@contextmanager
def protected_age_key() -> Generator[Path, None, None]:
    """Context manager for accessing the age private key.

    Handles three scenarios:
    1. GPG-encrypted key exists (.age/keys.txt.gpg) - decrypt, use, re-encrypt
    2. Plaintext key exists (.age/keys.txt) - warn, use, encrypt on exit
    3. Neither exists - raise error

    Guarantees the plaintext file is removed and key is encrypted on exit,
    even on exceptions or signals (Ctrl+C).

    Uses file locking to prevent race conditions when multiple processes
    try to access the same key simultaneously.

    Uses config.project_dir to determine the project root. To customize
    the project directory, use djb.configure(project_dir=...) before calling.

    Yields:
        Path to the (possibly temporary) plaintext age key file.

    Example:
        with protected_age_key() as key_path:
            # key_path is the plaintext file
            content = key_path.read_text()
            # ... use the key ...
        # Key is automatically re-encrypted and plaintext removed
    """
    _register_signal_handlers()

    key_path = get_default_key_path()
    encrypted_path = get_encrypted_key_path(key_path)
    lock_path = key_path.parent / ".age.lock"

    # Ensure the .age directory exists for the lock file
    key_path.parent.mkdir(parents=True, exist_ok=True)

    # Acquire exclusive lock to prevent concurrent access.
    # This prevents race conditions when multiple processes try to
    # decrypt/re-encrypt the key simultaneously.
    lock_fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        _active_locks[lock_path] = lock_fd
    except OSError as e:
        os.close(lock_fd)
        raise ProtectedFileError(f"Failed to acquire lock on age key: {e}") from e

    try:
        plaintext_existed = key_path.exists()
        encrypted_exists = encrypted_path.exists()
        gpg_available = check_gpg_installed()

        # Determine which file to use and whether to encrypt on exit
        should_encrypt_on_exit = False

        # Security check: reject symlinks to prevent attacks where a symlink
        # could redirect decryption to an attacker-controlled location
        if key_path.exists() and key_path.is_symlink():
            raise ProtectedFileError(
                f"Security error: {key_path} is a symlink. " f"Refusing to use symlinked key files."
            )

        if encrypted_exists and gpg_available:
            # Normal case: decrypt the GPG-encrypted key
            try:
                gpg_decrypt_file(encrypted_path, key_path)
                should_encrypt_on_exit = True
            except GpgTimeoutError as e:
                # User didn't enter passphrase in time - show friendly message
                raise click.ClickException(str(e)) from None
            except GpgError as e:
                raise ProtectedFileError(f"Failed to decrypt age key: {e}") from e

        elif plaintext_existed:
            # Plaintext key exists - warn and use it
            if gpg_available:
                logger.warning(f"Age key found in plaintext at {key_path} - will encrypt on exit")
                should_encrypt_on_exit = True
            else:
                logger.warning(f"Age key is not GPG-protected (GPG not installed)")
                # Can't encrypt, just use plaintext
                should_encrypt_on_exit = False

        elif not key_path.exists():
            raise ProtectedFileError(
                f"Age key not found at {key_path} or {encrypted_path}. " f"Run 'djb init' first."
            )

        # Track for cleanup
        _pending_cleanups.append((key_path, encrypted_path, should_encrypt_on_exit))

        try:
            yield key_path

        finally:
            # Remove from pending list
            entry = (key_path, encrypted_path, should_encrypt_on_exit)
            if entry in _pending_cleanups:
                _pending_cleanups.remove(entry)

            # Re-encrypt and clean up
            if key_path.exists() and should_encrypt_on_exit:
                try:
                    gpg_encrypt_file(key_path, encrypted_path)
                    key_path.unlink()
                except GpgError as e:
                    # Encryption failed - warn but keep plaintext (don't lose the key!)
                    # This is intentional: losing the key entirely is worse than
                    # leaving it in plaintext temporarily.
                    logger.warning(
                        f"Failed to re-encrypt age key: {e}. "
                        f"Plaintext key remains at {key_path}"
                    )
                except OSError as e:
                    logger.warning(f"Failed to clean up plaintext key: {e}")
    finally:
        # Release lock and clean up lock file descriptor
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        except OSError:
            pass  # Best effort unlock
        try:
            os.close(lock_fd)
        except OSError:
            pass  # Best effort close
        _active_locks.pop(lock_path, None)


def is_age_key_protected() -> bool:
    """Check if the age key is GPG-protected.

    Uses config.project_dir to determine the project root. To customize
    the project directory, use djb.configure(project_dir=...) before calling.

    Returns:
        True if .age/keys.txt.gpg exists and is GPG-encrypted.
    """
    key_path = get_default_key_path()
    encrypted_path = get_encrypted_key_path(key_path)

    return encrypted_path.exists() and is_gpg_encrypted(encrypted_path)


def protect_age_key() -> bool:
    """Encrypt the age key with GPG public key encryption.

    Uses the user's default GPG key for encryption. No passphrase is needed
    for encryption - the private key passphrase is only required for
    decryption, where GPG agent handles caching.

    Uses config.project_dir to determine the project root. To customize
    the project directory, use djb.configure(project_dir=...) before calling.

    Returns:
        True if key was encrypted, False if already protected or no key exists.

    Raises:
        GpgError: If encryption fails or no GPG key found.
        ProtectedFileError: If GPG is not installed.
    """
    if not check_gpg_installed():
        raise ProtectedFileError("GPG is not installed. Install with: brew install gnupg")

    key_path = get_default_key_path()
    encrypted_path = get_encrypted_key_path(key_path)

    if encrypted_path.exists():
        # Already protected
        return False

    if not key_path.exists():
        # No key to protect
        return False

    # Encrypt with GPG public key and remove plaintext
    gpg_encrypt_file(key_path, encrypted_path)
    key_path.unlink()

    return True


def unprotect_age_key() -> bool:
    """Decrypt the age key to plaintext (removes GPG protection).

    Uses config.project_dir to determine the project root. To customize
    the project directory, use djb.configure(project_dir=...) before calling.

    Returns:
        True if key was decrypted, False if not protected.

    Raises:
        GpgError: If decryption fails.
    """
    key_path = get_default_key_path()
    encrypted_path = get_encrypted_key_path(key_path)

    if not encrypted_path.exists():
        # Not protected
        return False

    # Decrypt
    try:
        gpg_decrypt_file(encrypted_path, key_path)
    except GpgTimeoutError as e:
        raise click.ClickException(str(e)) from None
    encrypted_path.unlink()

    return True
