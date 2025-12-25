"""Shared test utilities for djb CLI E2E tests.

This module provides reusable helper functions for:
- GPG encryption/decryption with environment isolation
- Age/SOPS operations
- Project structure creation
- Assertion helpers
- Context managers for safe decrypt-use-cleanup cycles

All utilities are designed to avoid polluting the user's real environment
by accepting optional parameters for isolated directories and configs.
"""

from __future__ import annotations

import os
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from djb.cli.djb import djb_cli

if TYPE_CHECKING:
    from collections.abc import Generator


# =============================================================================
# GPG Utilities
# =============================================================================


def gpg_encrypt(
    input_path: Path,
    output_path: Path,
    passphrase: str,
    *,
    gpg_home: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Encrypt a file using GPG symmetric encryption.

    Args:
        input_path: Path to the plaintext file to encrypt
        output_path: Path where encrypted file will be written
        passphrase: Passphrase for encryption
        gpg_home: Optional GPG home directory for isolation (avoids ~/.gnupg)

    Returns:
        CompletedProcess with returncode, stdout, stderr
    """
    cmd = [
        "gpg",
        "--symmetric",
        "--batch",
        "--yes",
        "--armor",
        "--passphrase-fd",
        "0",
        "--output",
        str(output_path),
        str(input_path),
    ]

    if gpg_home:
        cmd.insert(1, "--homedir")
        cmd.insert(2, str(gpg_home))

    return subprocess.run(
        cmd,
        input=passphrase,
        capture_output=True,
        text=True,
    )


def gpg_decrypt(
    input_path: Path,
    output_path: Path,
    passphrase: str,
    *,
    gpg_home: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Decrypt a GPG-encrypted file.

    Args:
        input_path: Path to the encrypted file
        output_path: Path where decrypted file will be written
        passphrase: Passphrase for decryption
        gpg_home: Optional GPG home directory for isolation

    Returns:
        CompletedProcess with returncode, stdout, stderr
    """
    cmd = [
        "gpg",
        "--decrypt",
        "--batch",
        "--yes",
        "--passphrase-fd",
        "0",
        "--output",
        str(output_path),
        str(input_path),
    ]

    if gpg_home:
        cmd.insert(1, "--homedir")
        cmd.insert(2, str(gpg_home))

    return subprocess.run(
        cmd,
        input=passphrase,
        capture_output=True,
        text=True,
    )


# =============================================================================
# Age/SOPS Utilities
# =============================================================================


def create_sops_config(secrets_dir: Path, public_key: str) -> Path:
    """Create a .sops.yaml config for testing.

    Args:
        secrets_dir: Directory where .sops.yaml will be created
        public_key: Age public key to use for encryption

    Returns:
        Path to the created .sops.yaml file
    """
    config_path = secrets_dir / ".sops.yaml"
    config_path.write_text(
        f"""creation_rules:
  - path_regex: '.*\\.yaml$'
    key_groups:
      - age:
          - {public_key}
"""
    )
    return config_path


def sops_encrypt(
    file_path: Path,
    config_path: Path,
    key_path: Path,
) -> subprocess.CompletedProcess[str]:
    """Encrypt a file with SOPS.

    Args:
        file_path: Path to the file to encrypt (will be encrypted in-place)
        config_path: Path to .sops.yaml config
        key_path: Path to age key file

    Returns:
        CompletedProcess with returncode, stdout, stderr
    """
    env = os.environ.copy()
    env["SOPS_AGE_KEY_FILE"] = str(key_path)

    return subprocess.run(
        [
            "sops",
            "--encrypt",
            "--config",
            str(config_path),
            "--in-place",
            str(file_path),
        ],
        capture_output=True,
        text=True,
        env=env,
    )


def sops_decrypt(
    file_path: Path,
    config_path: Path,
    key_path: Path,
) -> subprocess.CompletedProcess[str]:
    """Decrypt a SOPS-encrypted file (returns content in stdout).

    Args:
        file_path: Path to the encrypted file
        config_path: Path to .sops.yaml config
        key_path: Path to age key file

    Returns:
        CompletedProcess with decrypted content in stdout
    """
    env = os.environ.copy()
    env["SOPS_AGE_KEY_FILE"] = str(key_path)

    return subprocess.run(
        [
            "sops",
            "--decrypt",
            "--config",
            str(config_path),
            str(file_path),
        ],
        capture_output=True,
        text=True,
        env=env,
    )


def sops_decrypt_in_place(
    file_path: Path,
    config_path: Path,
    key_path: Path,
) -> subprocess.CompletedProcess[str]:
    """Decrypt a SOPS-encrypted file in place.

    Args:
        file_path: Path to the encrypted file (will be decrypted in-place)
        config_path: Path to .sops.yaml config
        key_path: Path to age key file

    Returns:
        CompletedProcess with returncode, stdout, stderr
    """
    env = os.environ.copy()
    env["SOPS_AGE_KEY_FILE"] = str(key_path)

    return subprocess.run(
        [
            "sops",
            "--decrypt",
            "--config",
            str(config_path),
            "--in-place",
            str(file_path),
        ],
        capture_output=True,
        text=True,
        env=env,
    )


def age_encrypt(
    input_path: Path,
    output_path: Path,
    public_key: str,
) -> subprocess.CompletedProcess[str]:
    """Encrypt a file with age.

    Args:
        input_path: Path to the plaintext file
        output_path: Path where encrypted file will be written
        public_key: Age public key for encryption

    Returns:
        CompletedProcess with returncode, stdout, stderr
    """
    return subprocess.run(
        ["age", "-r", public_key, "-o", str(output_path), str(input_path)],
        capture_output=True,
        text=True,
    )


def age_decrypt(
    input_path: Path,
    output_path: Path,
    key_path: Path,
) -> subprocess.CompletedProcess[str]:
    """Decrypt an age-encrypted file.

    Args:
        input_path: Path to the encrypted file
        output_path: Path where decrypted file will be written
        key_path: Path to age private key file

    Returns:
        CompletedProcess with returncode, stdout, stderr
    """
    return subprocess.run(
        ["age", "-d", "-i", str(key_path), "-o", str(output_path), str(input_path)],
        capture_output=True,
        text=True,
    )


# =============================================================================
# Project Setup Utilities
# =============================================================================


def init_git_repo(
    project_dir: Path,
    *,
    user_email: str = "e2e-test@example.com",
    user_name: str = "E2E Test",
) -> None:
    """Initialize a git repository with user config.

    Args:
        project_dir: Directory to initialize git in
        user_email: Git user.email config
        user_name: Git user.name config
    """
    subprocess.run(["git", "init", str(project_dir)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(project_dir), "config", "user.email", user_email],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(project_dir), "config", "user.name", user_name],
        capture_output=True,
        check=True,
    )


def add_initial_commit(project_dir: Path, message: str = "Initial commit") -> None:
    """Stage all files and create an initial commit.

    Args:
        project_dir: Git repository directory
        message: Commit message
    """
    subprocess.run(["git", "-C", str(project_dir), "add", "."], capture_output=True)
    subprocess.run(
        ["git", "-C", str(project_dir), "commit", "-m", message],
        capture_output=True,
    )


def create_pyproject_toml(
    project_dir: Path,
    name: str = "test-project",
    version: str = "0.1.0",
    *,
    extra_content: str = "",
) -> None:
    """Create a pyproject.toml with djb config.

    Args:
        project_dir: Project directory
        name: Project name
        version: Project version
        extra_content: Additional TOML content to append
    """
    content = f"""[project]
name = "{name}"
version = "{version}"

[tool.djb]
project_name = "{name}"
"""
    if extra_content:
        content += f"\n{extra_content}"
    (project_dir / "pyproject.toml").write_text(content)


def add_django_settings(
    project_dir: Path,
    package_name: str = "myproject",
    *,
    installed_apps: list[str] | None = None,
) -> None:
    """Create a Django settings structure.

    Args:
        project_dir: Project directory
        package_name: Name of the Django package/settings directory
        installed_apps: List of installed apps (defaults to Django built-ins)
    """
    if installed_apps is None:
        installed_apps = [
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
        ]

    django_dir = project_dir / package_name
    django_dir.mkdir(exist_ok=True)
    (django_dir / "__init__.py").write_text("")

    apps_str = ",\n    ".join(f'"{app}"' for app in installed_apps)
    settings_content = f'''"""Django settings."""

INSTALLED_APPS = [
    {apps_str},
]
'''
    (django_dir / "settings.py").write_text(settings_content)


def add_django_settings_from_startproject(
    project_dir: Path,
    package_name: str = "myproject",
) -> None:
    """Create a realistic Django settings structure using django-admin startproject.

    Unlike add_django_settings() which creates minimal fake settings, this function
    uses Django's startproject command to generate a complete, realistic settings
    module. This makes tests more accurate by testing against real Django structure.

    The generated project includes:
    - settings.py with SECRET_KEY, DEBUG, INSTALLED_APPS, MIDDLEWARE, etc.
    - urls.py with admin patterns
    - wsgi.py and asgi.py
    - __init__.py

    Args:
        project_dir: Project directory where Django package will be created
        package_name: Name of the Django package/settings directory
    """
    # Use Django's startproject to create a realistic project structure
    result = subprocess.run(
        [
            "django-admin",
            "startproject",
            package_name,
            str(project_dir),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"django-admin startproject failed: {result.stderr or result.stdout}")


def add_frontend_package(
    project_dir: Path,
    name: str = "frontend",
    version: str = "0.1.0",
) -> None:
    """Create a frontend directory with package.json.

    Args:
        project_dir: Project directory
        name: Package name for package.json
        version: Package version
    """
    frontend_dir = project_dir / "frontend"
    frontend_dir.mkdir(exist_ok=True)
    (frontend_dir / "package.json").write_text(f'{{"name": "{name}", "version": "{version}"}}')


def add_python_package(project_dir: Path, package_name: str = "myproject") -> None:
    """Create a Python package directory with __init__.py.

    Args:
        project_dir: Project directory
        package_name: Name of the Python package
    """
    pkg_dir = project_dir / package_name
    pkg_dir.mkdir(exist_ok=True)
    (pkg_dir / "__init__.py").write_text("")


def create_isolated_project(
    tmp_path: Path,
    *,
    with_git: bool = True,
    with_secrets: bool = False,
    with_frontend: bool = False,
    project_name: str = "test-project",
) -> Path:
    """Create a minimal isolated project structure for testing.

    Args:
        tmp_path: Base temporary directory
        with_git: Initialize a git repository
        with_secrets: Create a secrets/ directory
        with_frontend: Create a frontend/ directory with package.json
        project_name: Name for the project

    Returns:
        Path to the created project directory
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    create_pyproject_toml(project_dir, name=project_name)

    if with_git:
        init_git_repo(project_dir)

    if with_secrets:
        (project_dir / "secrets").mkdir()

    if with_frontend:
        add_frontend_package(project_dir, name=f"{project_name}-frontend")

    return project_dir


# =============================================================================
# Assertion Helpers
# =============================================================================


def assert_gpg_encrypted(file_path: Path) -> None:
    """Assert that a file is GPG encrypted (ASCII-armored).

    Args:
        file_path: Path to the file to check

    Raises:
        AssertionError: If file is not GPG encrypted
    """
    content = file_path.read_text()
    assert "BEGIN PGP MESSAGE" in content, f"{file_path} is not GPG encrypted"


def assert_sops_encrypted(file_path: Path) -> None:
    """Assert that a file is SOPS encrypted.

    Args:
        file_path: Path to the file to check

    Raises:
        AssertionError: If file is not SOPS encrypted
    """
    content = file_path.read_text()
    assert "sops:" in content, f"{file_path} is not SOPS encrypted"


def assert_not_contains_secrets(file_path: Path, *secrets: str) -> None:
    """Assert that a file doesn't contain any of the given secrets in plaintext.

    Args:
        file_path: Path to the file to check
        *secrets: Secret strings that should not appear in the file

    Raises:
        AssertionError: If any secret is found in plaintext
    """
    content = file_path.read_text()
    for secret in secrets:
        assert secret not in content, f"Found plaintext secret '{secret}' in {file_path}"


def assert_contains(file_path: Path, *expected: str) -> None:
    """Assert that a file contains all the expected strings.

    Args:
        file_path: Path to the file to check
        *expected: Strings that should appear in the file

    Raises:
        AssertionError: If any expected string is not found
    """
    content = file_path.read_text()
    for text in expected:
        assert text in content, f"Expected '{text}' not found in {file_path}"


# =============================================================================
# Context Managers for Safe Encryption Handling
# =============================================================================


@contextmanager
def temporarily_decrypted_gpg(
    encrypted_path: Path,
    decrypted_path: Path,
    passphrase: str,
    *,
    gpg_home: Path | None = None,
    cleanup_only: bool = False,
) -> Generator[Path, None, None]:
    """Context manager for safe GPG decrypt-use-cleanup cycle.

    Decrypts a file, yields the decrypted path for operations, then
    ensures the plaintext is deleted even if an exception occurs.

    Args:
        encrypted_path: Path to the GPG-encrypted file
        decrypted_path: Path where decrypted file will be written
        passphrase: GPG passphrase
        gpg_home: Optional GPG home directory for isolation
        cleanup_only: If True, only delete plaintext (don't re-encrypt)

    Yields:
        Path to the decrypted file

    Example:
        with temporarily_decrypted_gpg(encrypted, plaintext, "pass") as decrypted:
            content = decrypted.read_text()
            # Use the decrypted content...
        # Plaintext is automatically deleted
    """
    try:
        result = gpg_decrypt(encrypted_path, decrypted_path, passphrase, gpg_home=gpg_home)
        if result.returncode != 0:
            raise RuntimeError(f"GPG decryption failed: {result.stderr}")
        yield decrypted_path
    finally:
        # Always clean up plaintext, even on test failure
        if decrypted_path.exists():
            if not cleanup_only:
                # Re-encrypt if changes were made
                gpg_encrypt(decrypted_path, encrypted_path, passphrase, gpg_home=gpg_home)
            # Delete plaintext
            decrypted_path.unlink()


@contextmanager
def temporarily_decrypted_sops(
    encrypted_path: Path,
    config_path: Path,
    key_path: Path,
    *,
    cleanup_only: bool = False,
) -> Generator[Path, None, None]:
    """Context manager for safe SOPS decrypt-use-cleanup cycle.

    Decrypts a SOPS file in place, yields for operations, then
    re-encrypts even if an exception occurs.

    Args:
        encrypted_path: Path to the SOPS-encrypted file
        config_path: Path to .sops.yaml config
        key_path: Path to age key file
        cleanup_only: If True, only re-encrypt (don't preserve changes)

    Yields:
        Path to the decrypted file (same as encrypted_path, modified in place)

    Example:
        with temporarily_decrypted_sops(secrets_file, config, key) as decrypted:
            content = decrypted.read_text()
            # Modify content if needed...
        # File is automatically re-encrypted
    """
    original_content = encrypted_path.read_text()
    try:
        result = sops_decrypt_in_place(encrypted_path, config_path, key_path)
        if result.returncode != 0:
            raise RuntimeError(f"SOPS decryption failed: {result.stderr}")
        yield encrypted_path
    finally:
        # Always re-encrypt
        if cleanup_only:
            # Restore original encrypted content
            encrypted_path.write_text(original_content)
        else:
            # Re-encrypt current content
            result = sops_encrypt(encrypted_path, config_path, key_path)
            if result.returncode != 0:
                # If re-encryption fails, restore original to avoid data loss
                encrypted_path.write_text(original_content)
                raise RuntimeError(f"SOPS re-encryption failed: {result.stderr}")


# =============================================================================
# CLI Invocation Helpers
# =============================================================================


def invoke_djb(
    runner,
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    catch_exceptions: bool = True,
) -> object:
    """Invoke djb CLI command with proper setup.

    Args:
        runner: Click CliRunner instance
        args: Command arguments (e.g., ["secrets", "init"])
        env: Optional environment variables
        catch_exceptions: Whether to catch exceptions (default True)

    Returns:
        Click Result object
    """
    return runner.invoke(
        djb_cli,
        args,
        env=env,
        catch_exceptions=catch_exceptions,
    )
