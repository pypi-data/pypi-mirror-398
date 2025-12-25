"""
djb.tests.e2e - E2E tests and utilities for djb CLI.

Tests exercise the djb CLI against real external tools (GPG, age, SOPS,
PostgreSQL) while mocking cloud services (Heroku, PyPI).

Run with: pytest --run-e2e

Fixtures (auto-discovered by pytest from conftest.py):
    Prerequisite checks:
        require_gpg, require_age, require_sops, require_postgres

    CLI runners:
        runner, e2e_runner

    Environment isolation:
        isolated_env, gpg_home, age_key_dir

    Project setup:
        isolated_project, isolated_project_with_secrets, secrets_dir

    Age keys:
        make_age_key (factory), alice_key, bob_key

    SOPS config:
        setup_sops_config

    PostgreSQL:
        pg_test_database

    Git repos:
        git_repo, git_repo_with_commits

    Cloud mocks:
        mock_heroku_cli, mock_pypi_publish

    DJB config:
        djb_config_env

    Test data:
        test_passphrase, test_secret_value

Utilities:
    GPG:
        gpg_encrypt, gpg_decrypt

    Age/SOPS:
        create_sops_config, sops_encrypt, sops_decrypt, sops_decrypt_in_place
        age_encrypt, age_decrypt

    Project setup (composable helpers):
        init_git_repo - Initialize git repo with user config
        add_initial_commit - Stage files and create commit
        create_pyproject_toml - Create pyproject.toml with djb config
        add_django_settings - Create minimal Django settings structure
        add_django_settings_from_startproject - Create realistic Django settings via startproject
        add_frontend_package - Create frontend dir with package.json
        add_python_package - Create Python package with __init__.py
        create_isolated_project - Higher-level project setup

    Assertions:
        assert_gpg_encrypted, assert_sops_encrypted
        assert_not_contains_secrets, assert_contains

    Context managers:
        temporarily_decrypted_gpg, temporarily_decrypted_sops

    CLI helpers:
        invoke_djb
"""

from __future__ import annotations

from .utils import (
    add_django_settings,
    add_django_settings_from_startproject,
    add_frontend_package,
    add_initial_commit,
    add_python_package,
    age_decrypt,
    age_encrypt,
    assert_contains,
    assert_gpg_encrypted,
    assert_not_contains_secrets,
    assert_sops_encrypted,
    create_isolated_project,
    create_pyproject_toml,
    create_sops_config,
    gpg_decrypt,
    gpg_encrypt,
    init_git_repo,
    invoke_djb,
    sops_decrypt,
    sops_decrypt_in_place,
    sops_encrypt,
    temporarily_decrypted_gpg,
    temporarily_decrypted_sops,
)

__all__ = [
    "add_django_settings",
    "add_django_settings_from_startproject",
    "add_frontend_package",
    "add_initial_commit",
    "add_python_package",
    "age_decrypt",
    "age_encrypt",
    "assert_contains",
    "assert_gpg_encrypted",
    "assert_not_contains_secrets",
    "assert_sops_encrypted",
    "create_isolated_project",
    "create_pyproject_toml",
    "create_sops_config",
    "gpg_decrypt",
    "gpg_encrypt",
    "init_git_repo",
    "invoke_djb",
    "sops_decrypt",
    "sops_decrypt_in_place",
    "sops_encrypt",
    "temporarily_decrypted_gpg",
    "temporarily_decrypted_sops",
]
