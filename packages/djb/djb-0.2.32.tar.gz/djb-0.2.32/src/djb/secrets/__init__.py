"""
djb.secrets - Encrypted secrets management with SOPS.

Provides encrypted secrets storage using SOPS with age encryption.

Quick start:
    from djb.secrets import load_secrets, SopsError

    try:
        secrets = load_secrets(environment="dev", secrets_dir=Path("secrets"))
    except SopsError as e:
        print(f"Decryption failed: {e}")

Public API:
    Core:
        SecretsManager - High-level secrets management class
        load_secrets, load_secrets_for_mode - Load decrypted secrets
        encrypt_file, decrypt_file - SOPS file encryption/decryption
        generate_age_key - Create new age keypair
        SopsError - SOPS operation failures

    Config:
        create_sops_config, parse_sops_config - .sops.yaml management
        get_all_recipients - List all age recipients from config
        SECRETS_ENVIRONMENTS - Standard environment names

    GPG Protection:
        protected_age_key - Context manager for GPG-protected keys
        protect_age_key, unprotect_age_key - Manual protection
        GpgError, GpgTimeoutError, ProtectedFileError - GPG-related errors
        GPG_TIMEOUT, GPG_INTERACTIVE_TIMEOUT - Timeout constants

    Initialization:
        init_or_upgrade_secrets - Set up secrets infrastructure
        SecretsStatus - Initialization status enum
"""

from __future__ import annotations

from djb.secrets.core import (
    SOPS_TIMEOUT,
    SecretsManager,
    SopsError,
    check_age_installed,
    check_sops_installed,
    create_sops_config,
    decrypt_file,
    encrypt_file,
    find_placeholder_secrets,
    format_identity,
    generate_age_key,
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
from djb.secrets.django import load_secrets_for_django
from djb.secrets.paths import (
    get_default_key_path,
    get_default_secrets_dir,
    get_encrypted_key_path,
)
from djb.secrets.gpg import (
    GPG_INTERACTIVE_TIMEOUT,
    GPG_TIMEOUT,
    GpgError,
    GpgTimeoutError,
    check_gpg_installed,
    generate_gpg_key,
    gpg_decrypt_file,
    gpg_encrypt_file,
    has_gpg_secret_key,
    init_gpg_agent_config,
    is_gpg_encrypted,
)
from djb.secrets.init import (
    PROJECT_SECRETS_ENVIRONMENTS,
    SECRETS_ENVIRONMENTS,
    SecretsStatus,
    init_or_upgrade_secrets,
)
from djb.secrets.protected import (
    ProtectedFileError,
    is_age_key_protected,
    protect_age_key,
    protected_age_key,
    unprotect_age_key,
)

__all__ = [
    # Core SOPS functions
    "SOPS_TIMEOUT",
    "SecretsManager",
    "SopsError",
    "check_age_installed",
    "check_sops_installed",
    "create_sops_config",
    "decrypt_file",
    "encrypt_file",
    "find_placeholder_secrets",
    "format_identity",
    "generate_age_key",
    "get_all_recipients",
    "get_default_key_path",
    "get_default_secrets_dir",
    "get_encrypted_key_path",
    "get_public_key_from_private",
    "is_placeholder_value",
    "is_valid_age_public_key",
    "load_secrets",
    "load_secrets_for_django",
    "load_secrets_for_mode",
    "parse_identity",
    "parse_sops_config",
    "rotate_keys",
    # GPG encryption
    "GPG_INTERACTIVE_TIMEOUT",
    "GPG_TIMEOUT",
    "GpgError",
    "GpgTimeoutError",
    "check_gpg_installed",
    "generate_gpg_key",
    "gpg_decrypt_file",
    "gpg_encrypt_file",
    "has_gpg_secret_key",
    "init_gpg_agent_config",
    "is_gpg_encrypted",
    # Protected file access
    "ProtectedFileError",
    "is_age_key_protected",
    "protect_age_key",
    "protected_age_key",
    "unprotect_age_key",
    # Initialization
    "PROJECT_SECRETS_ENVIRONMENTS",
    "SECRETS_ENVIRONMENTS",
    "SecretsStatus",
    "init_or_upgrade_secrets",
]
