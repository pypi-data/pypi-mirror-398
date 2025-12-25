"""
djb secrets initialization - Initialize secrets for environments.

Provides functions for creating and upgrading encrypted secrets files
for different deployment environments using SOPS.

There are two types of secrets:
- User secrets (dev.yaml): Encrypted with user's own age key, gitignored
- Project secrets (staging.yaml, production.yaml): Multi-recipient encryption, committed

This separation allows new users to get started immediately without waiting
for a teammate to rotate project secrets.
"""

from __future__ import annotations

import secrets as py_secrets
import string
from pathlib import Path
from typing import NamedTuple

import yaml

from djb.core.logging import get_logger
from djb.secrets.core import (
    SecretsManager,
    SopsError,
    check_age_installed,
    check_sops_installed,
    create_sops_config,
    format_identity,
    generate_age_key,
    get_default_key_path,
    get_encrypted_key_path,
    get_public_key_from_private,
    parse_sops_config,
    rotate_keys,
)
from djb.secrets.gpg import GpgError, check_gpg_installed
from djb.secrets.protected import is_age_key_protected, protect_age_key, protected_age_key

logger = get_logger(__name__)

# Environments to manage secrets for
SECRETS_ENVIRONMENTS = ["dev", "staging", "production"]

# User secrets are encrypted with user's own key only (not shared via git)
USER_SECRETS_ENVIRONMENTS = ["dev"]

# Project secrets are encrypted for all team members (committed to git)
PROJECT_SECRETS_ENVIRONMENTS = ["staging", "production"]


def _get_encrypted_recipients(secrets_file: Path) -> set[str]:
    """Get the list of recipients from a SOPS-encrypted file's metadata.

    SOPS stores recipient info in the 'sops.age' section of encrypted files.

    Returns:
        Set of public key strings the file is encrypted for, or empty set if
        the file doesn't exist or can't be parsed.
    """
    if not secrets_file.exists():
        return set()

    try:
        with open(secrets_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "sops" not in data or "age" not in data["sops"]:
            return set()

        return {entry["recipient"] for entry in data["sops"]["age"]}
    except (OSError, yaml.YAMLError, KeyError, TypeError):
        # File read error, invalid YAML, or unexpected structure
        return set()


class SecretsStatus(NamedTuple):
    """Status of secrets initialization for an environment."""

    initialized: list[str]  # Newly created
    upgraded: list[str]  # Existing but upgraded with new keys
    up_to_date: list[str]  # Already up to date


def _generate_secret_key(length: int = 50) -> str:
    """Generate a random secret key suitable for Django's SECRET_KEY."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return "".join(py_secrets.choice(chars) for _ in range(length))


def _get_template(env: str, *, project_name: str | None = None) -> dict:
    """Get the secrets template for an environment.

    Template structure varies by environment:
    - Production: django_secret_key, superuser (no db_credentials since
      Heroku provides DATABASE_URL)
    - Dev/Staging: django_secret_key, db_credentials, superuser (for local
      database setup)

    For user secrets (dev), values are auto-generated with sensible defaults.
    For project secrets (staging/production), placeholders indicate values
    that need to be configured by the team.
    """
    # Dev gets sensible auto-generated defaults (user secret - gitignored)
    if env == "dev":
        db_name = project_name or "app"
        return {
            "django_secret_key": _generate_secret_key(),
            "db_credentials": {
                "username": db_name,
                "password": _generate_secret_key(20),
                "database": db_name,
                "host": "localhost",
                "port": 5432,
            },
            "superuser": {
                "username": "admin",
                "email": "admin@example.com",
                "password": _generate_secret_key(16),
            },
        }

    # Production doesn't need db_credentials (Heroku provides DATABASE_URL)
    if env == "production":
        return {
            "django_secret_key": f"CHANGE-ME-{env.upper()}-KEY",
            "superuser": {
                "username": "admin",
                "email": "admin@example.com",
                "password": f"CHANGE-ME-{env.upper()}-PASSWORD",
            },
        }

    # Staging needs db_credentials for non-Heroku deployments
    return {
        "django_secret_key": f"CHANGE-ME-{env.upper()}-KEY",
        "db_credentials": {
            "username": "app",
            "password": f"CHANGE-ME-{env.upper()}-PASSWORD",
            "database": "app",
            "host": "localhost",
            "port": 5432,
        },
        "superuser": {
            "username": "admin",
            "email": "admin@example.com",
            "password": f"CHANGE-ME-{env.upper()}-PASSWORD",
        },
    }


def _deep_merge_missing(existing: dict, template: dict) -> tuple[dict, list[str]]:
    """Merge template keys into existing dict, only adding missing keys.

    Returns the merged dict and a list of keys that were added.
    """
    result = dict(existing)
    added = []

    for key, value in template.items():
        if key not in result:
            result[key] = value
            added.append(key)
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            # Recursively merge nested dicts
            nested_result, nested_added = _deep_merge_missing(result[key], value)
            result[key] = nested_result
            added.extend(f"{key}.{k}" for k in nested_added)

    return result, added


def _do_secrets_upgrade(
    secrets_dir: Path,
    key_path: Path,
    public_key: str,
    all_public_keys: list[str],
    needs_reencrypt: bool,
    project_name: str | None,
) -> SecretsStatus:
    """Perform the actual secrets upgrade with a valid key path.

    This function requires the age key file to exist at key_path. When the key
    is GPG-protected, callers should invoke this inside a protected_age_key()
    context to ensure the key is temporarily decrypted.

    Args:
        secrets_dir: Directory containing secrets files
        key_path: Path to the (unencrypted) age private key file
        public_key: The user's public key
        all_public_keys: List of all team member public keys
        needs_reencrypt: Whether project secrets need re-encryption
        project_name: Project name for template defaults

    Returns:
        SecretsStatus indicating what was done
    """
    # Re-encrypt project secrets if team membership changed
    if needs_reencrypt:
        logger.next("Re-encrypting project secrets for updated team")
        for env in PROJECT_SECRETS_ENVIRONMENTS:
            secrets_file = secrets_dir / f"{env}.yaml"
            if secrets_file.exists():
                try:
                    rotate_keys(secrets_file, all_public_keys, key_path)
                    logger.done(f"Re-encrypted {env}")
                except SopsError as e:
                    logger.warning(f"Failed to re-encrypt {env}: {e}")
                    logger.info("Ask a team member who can decrypt to run: djb secrets rotate")

    manager = SecretsManager(secrets_dir=secrets_dir, key_path=key_path)

    initialized: list[str] = []
    upgraded: list[str] = []
    up_to_date: list[str] = []

    # Handle user secrets (dev) - encrypted with user's own key only
    for env in USER_SECRETS_ENVIRONMENTS:
        secrets_file = secrets_dir / f"{env}.yaml"
        template = _get_template(env, project_name=project_name)

        if not secrets_file.exists():
            # Create new user secrets file with user's own key only
            manager.save_secrets(env, template, [public_key])
            initialized.append(env)
        else:
            # Upgrade existing user secrets with any new template keys
            existing = manager.load_secrets(env)
            merged, added = _deep_merge_missing(existing, template)

            if added:
                manager.save_secrets(env, merged, [public_key])
                upgraded.append(env)
            else:
                up_to_date.append(env)

    # Handle project secrets (staging/production) - encrypted for all team members
    for env in PROJECT_SECRETS_ENVIRONMENTS:
        secrets_file = secrets_dir / f"{env}.yaml"
        template = _get_template(env, project_name=project_name)

        if not secrets_file.exists():
            # Create new project secrets file for all recipients
            manager.save_secrets(env, template, all_public_keys)
            initialized.append(env)
        else:
            # Upgrade existing project secrets with any new template keys
            try:
                existing = manager.load_secrets(env)
                merged, added = _deep_merge_missing(existing, template)

                if added:
                    manager.save_secrets(env, merged, all_public_keys)
                    upgraded.append(env)
                else:
                    up_to_date.append(env)
            except (FileNotFoundError, SopsError) as e:
                # Can't decrypt (missing key, new team member, etc.)
                logger.warning(f"Failed to upgrade {env} secrets: {e}")
                up_to_date.append(env)

    return SecretsStatus(initialized=initialized, upgraded=upgraded, up_to_date=up_to_date)


def init_or_upgrade_secrets(
    project_root: Path,
    email: str | None = None,
    name: str | None = None,
    project_name: str | None = None,
) -> SecretsStatus:
    """Initialize or upgrade secrets for all environments.

    Secrets are divided into two categories:
    - User secrets (dev.yaml): Encrypted with user's own key only, gitignored
    - Project secrets (staging.yaml, production.yaml): Multi-recipient, committed

    For each environment:
    - If secrets file doesn't exist: create it from template
    - If secrets file exists: upgrade it with any new template keys

    Args:
        project_root: Root directory of the project
        email: Email to associate with the public key
        name: Name to associate with the public key (for git-style identity)
        project_name: Project name (used for db_credentials defaults in dev)

    Returns a SecretsStatus indicating what was done.

    Raises:
        RuntimeError: If SOPS or age is not installed
    """
    # Check prerequisites (CLI should auto-install, but check here for programmatic use)
    if not check_sops_installed():
        raise RuntimeError("SOPS is not installed")
    if not check_age_installed():
        raise RuntimeError("age is not installed")

    key_path = get_default_key_path()
    secrets_dir = project_root / "secrets"

    # Ensure age key exists
    key_was_generated = False
    if not key_path.exists():
        # Check if key is GPG-protected
        encrypted_path = get_encrypted_key_path(key_path)
        if encrypted_path.exists():
            # Key exists but is GPG-protected - need to decrypt to get public key
            with protected_age_key() as decrypted_key_path:
                public_key = get_public_key_from_private(decrypted_key_path)
        else:
            public_key, _ = generate_age_key(key_path)
            key_was_generated = True
            logger.done(f"Generated age key at {key_path}")
    else:
        public_key = get_public_key_from_private(key_path)

    # Enable GPG protection for new or unprotected keys
    if check_gpg_installed():
        if key_was_generated or (key_path.exists() and not is_age_key_protected()):
            try:
                if protect_age_key():
                    logger.done("Protected age key with GPG encryption")
            except GpgError as e:
                logger.warning(f"Could not enable GPG protection: {e}")
                logger.info("Age key remains unencrypted. Run 'djb secrets protect' to retry.")
    elif key_was_generated:
        logger.warning("GPG not installed - age key stored without encryption")
        logger.info("Install GPG and run 'djb secrets protect' to secure your key")

    # Ensure secrets directory exists
    secrets_dir.mkdir(parents=True, exist_ok=True)

    # Create .gitignore for secrets directory if needed
    gitignore_path = secrets_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(
            "# Decrypted secrets (never commit these)\n"
            "*.decrypted.yaml\n"
            "*.plaintext.yaml\n"
            "*.secret\n"
            "*.tmp.yaml\n"
            "\n"
            "# User secrets (encrypted with user's own key, not shared)\n"
            "dev.yaml\n"
        )

    # Get existing recipients from .sops.yaml (if any)
    recipients = parse_sops_config(secrets_dir)
    original_recipients = dict(recipients)

    # Format identity (Name <email> or just email)
    identity = format_identity(name, email) if email else "unknown@example.com"

    # Add user's key if not already present
    if public_key not in recipients:
        recipients[public_key] = identity
        logger.done(f"Added public key for {identity}")
    elif email and not recipients[public_key]:
        # Update identity if we have it and it was missing
        recipients[public_key] = identity

    # Only write .sops.yaml if recipients changed
    if recipients != original_recipients:
        create_sops_config(secrets_dir, recipients)
        logger.done("Updated .sops.yaml configuration")

    # Get all public keys for project secrets (multi-recipient)
    all_public_keys = list(recipients.keys())
    expected_keys = set(all_public_keys)

    # Check project secrets files to detect team membership changes
    # (e.g., when someone pulls .sops.yaml with new/removed keys)
    all_added: set[str] = set()
    all_removed: set[str] = set()

    for env in PROJECT_SECRETS_ENVIRONMENTS:
        secrets_file = secrets_dir / f"{env}.yaml"
        if secrets_file.exists():
            actual_keys = _get_encrypted_recipients(secrets_file)
            if actual_keys:  # Only compare if we could read the keys
                added = expected_keys - actual_keys
                removed = actual_keys - expected_keys
                all_added.update(added)
                all_removed.update(removed)

    # Report team membership changes (exclude current user's key - they know they just joined)
    other_added = all_added - {public_key}
    if other_added:
        for key in other_added:
            added_identity = recipients.get(key, "unknown")
            logger.warning(f"New team member added: {added_identity}")

    if all_removed:
        for key in all_removed:
            # We don't have emails for removed keys, show truncated key
            logger.warning(f"Team member removed: {key[:20]}...")

    # Determine if we need re-encryption due to team membership changes
    # Note: if current user was just added, they can't re-encrypt - someone else must do it
    needs_reencrypt = bool(other_added or all_removed)

    # Perform secrets upgrade - use protected context if key is GPG-protected
    if is_age_key_protected():
        with protected_age_key() as decrypted_key_path:
            return _do_secrets_upgrade(
                secrets_dir=secrets_dir,
                key_path=decrypted_key_path,
                public_key=public_key,
                all_public_keys=all_public_keys,
                needs_reencrypt=needs_reencrypt,
                project_name=project_name,
            )
    else:
        return _do_secrets_upgrade(
            secrets_dir=secrets_dir,
            key_path=key_path,
            public_key=public_key,
            all_public_keys=all_public_keys,
            needs_reencrypt=needs_reencrypt,
            project_name=project_name,
        )
