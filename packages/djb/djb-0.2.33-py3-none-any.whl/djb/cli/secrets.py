"""
djb secrets CLI - Manage encrypted secrets with SOPS.

Provides commands for initializing, editing, and managing encrypted secrets
using SOPS with age encryption (X25519 + ChaCha20-Poly1305).

Why SOPS?
---------
- Native support for age encryption and multi-recipient
- Built-in editor integration
- Preserves YAML structure while encrypting values

Why Age Encryption Over PGP/GPG?
--------------------------------
- Age has a single key format vs PGP's complex keyring
- A single line for private key, easy to backup

Key Management
--------------
- Private key stored at .age/keys.txt in project root (NEVER committed)
- Each project has its own key for better isolation
- Public key shared with team members for multi-recipient encryption
- The `djb init` command generates keys and template files
- Backup your private key: `djb secrets export-key | pbcopy` (saves to clipboard)

Editing Workflow
----------------
The `djb secrets edit <env>` command uses SOPS to:
1. Decrypt the secrets file in-memory
2. Open your $EDITOR (or vim)
3. Re-encrypt on save

This ensures plaintext secrets never persist on disk.
"""

from __future__ import annotations

import os
import platform
import readline  # noqa: F401 - enables line editing for input()
import secrets as py_secrets
import shutil
import string
import subprocess
import sys
from pathlib import Path

import click
import yaml

from djb.cli.context import CliContext
from djb.core.logging import get_logger
from djb.secrets import (
    GpgError,
    ProtectedFileError,
    SECRETS_ENVIRONMENTS,
    SecretsManager,
    SopsError,
    check_age_installed,
    check_gpg_installed,
    check_sops_installed,
    create_sops_config,
    format_identity,
    generate_age_key,
    generate_gpg_key,
    get_all_recipients,
    get_default_key_path,
    get_default_secrets_dir,
    get_public_key_from_private,
    has_gpg_secret_key,
    init_gpg_agent_config,
    is_age_key_protected,
    is_valid_age_public_key,
    parse_identity,
    parse_sops_config,
    protect_age_key,
    protected_age_key,
    rotate_keys,
    unprotect_age_key,
)

# Internal imports for CLI-specific needs (not part of public API)
from djb.secrets.init import (
    PROJECT_SECRETS_ENVIRONMENTS,
    USER_SECRETS_ENVIRONMENTS,
    _deep_merge_missing,
    _get_template,
)

logger = get_logger(__name__)


def _get_config():
    """Get the DjbConfig from the current Click context.

    Returns the config object from the CliContext, which is set up by the djb CLI.
    """
    ctx = click.get_current_context(silent=True)
    if ctx is None:
        raise click.ClickException("No Click context available")
    ctx_obj = ctx.find_object(CliContext)
    if ctx_obj is None:
        raise click.ClickException("No CliContext found")
    return ctx_obj.config


# Template for secrets directory README, accepts {key_path} and {public_key} format args
_README_TEMPLATE = """# Secrets Directory

This directory contains SOPS-encrypted secrets for different environments.

## Your Age Key

- **Private key**: `{key_path}`
- **Public key**: `{public_key}`

**IMPORTANT:** Never commit your private key to git! It should stay at `~/.age/keys.txt`.

## Files

| File | Purpose |
|------|---------|
| `dev.yaml` | Development secrets (local machine) |
| `staging.yaml` | Staging environment secrets |
| `production.yaml` | Production secrets |
| `.sops.yaml` | SOPS configuration with team member keys (commit this) |

## Managing Secrets

### Edit secrets
```bash
djb secrets edit dev           # Edit development secrets
djb secrets edit production    # Edit production secrets
```

### View secrets (careful in shared environments)
```bash
djb secrets view dev
djb secrets view production --key django_secret_key
```

### List available environments
```bash
djb secrets list
```

### Generate a random string (50 chars)
```bash
djb secrets generate-key
```

## Adding Team Members

To add a new team member:

1. Have them run `djb init` (sets up email, generates age key, initializes secrets)
2. They share their public key (starts with `age...`) with you
3. Add their key and re-encrypt: `djb secrets rotate --add-key age1... --add-email their@email.com`
4. Commit the updated `.sops.yaml` and secrets files

To remove a team member:

```bash
djb secrets rotate --remove-key their@email.com
```

## How It Works

Secrets are encrypted using SOPS with age encryption:
- Keys are visible in git diffs (e.g., `django_secret_key:`)
- Values are encrypted inline in the YAML
- Safe to commit encrypted files to git
- Decryption requires the private key at `~/.age/keys.txt`

## Security Best Practices

1. **Never commit `~/.age/keys.txt`** - it's your private key
2. **Backup your key** - store it in a password manager
3. **Use strong secrets** - run `djb secrets generate-key` for Django keys
4. **Rotate secrets** after team changes or suspected compromise
5. **Different secrets per environment** - never reuse prod secrets in dev
"""


def _check_homebrew_installed() -> bool:
    """Check if Homebrew is installed."""
    return shutil.which("brew") is not None


def _install_with_homebrew(package: str) -> bool:
    """Install a package using Homebrew.

    Returns True if installation succeeded.
    """
    logger.next(f"Installing {package} with Homebrew")
    try:
        result = subprocess.run(
            ["brew", "install", package],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.done(f"Installed {package}")
            return True
        else:
            logger.fail(f"Failed to install {package}: {result.stderr}")
            return False
    except (FileNotFoundError, OSError) as e:
        logger.fail(f"Failed to install {package}: {e}")
        return False


def _ensure_prerequisites(quiet: bool = False, include_gpg: bool = True) -> bool:
    """Ensure SOPS, age, and GPG are installed, auto-installing if possible.

    This function handles the complete prerequisite workflow:
    1. Check which tools (sops, age, gnupg) are already installed
    2. Report status of installed tools (unless quiet=True)
    3. On macOS with Homebrew: auto-install missing tools
    4. On other platforms: show manual installation instructions

    Args:
        quiet: If True, don't log "already installed" messages
        include_gpg: If True, also check for GPG (default True)

    Returns:
        True if all prerequisites are met, False otherwise
    """
    missing = []
    installed = []

    if not check_sops_installed():
        missing.append("sops")
    else:
        installed.append("sops")

    if not check_age_installed():
        missing.append("age")
    else:
        installed.append("age")

    if include_gpg:
        if not check_gpg_installed():
            missing.append("gnupg")
        else:
            installed.append("gnupg")

    # Report already installed tools
    if not quiet:
        for tool in installed:
            logger.done(f"{tool} already installed")

    if not missing:
        return True

    # Check if we can install
    is_macos = platform.system() == "Darwin"
    has_brew = _check_homebrew_installed()

    if is_macos and has_brew:
        # Auto-install missing tools
        for package in missing:
            if not _install_with_homebrew(package):
                return False
        return True
    else:
        logger.fail(f"Missing required tools: {', '.join(missing)}")
        logger.info("Please install:")
        if is_macos:
            logger.info("  First install Homebrew: https://brew.sh")
        for package in missing:
            if is_macos:
                logger.info(f"  brew install {package}")
            else:
                install_urls = {
                    "sops": "https://github.com/getsops/sops#install",
                    "age": "https://github.com/FiloSottile/age#installation",
                    "gnupg": "https://gnupg.org/download/",
                }
                logger.info(f"  See: {install_urls.get(package, package)}")
        return False


def _check_prerequisites():
    """Check that SOPS and age are installed, exit if not."""
    if not _ensure_prerequisites():
        sys.exit(1)


@click.group()
def secrets():
    """Manage encrypted secrets for different environments."""
    pass


def _ensure_gpg_setup() -> bool:
    """Ensure GPG is properly configured with a secret key.

    Sets up GPG agent configuration and generates a GPG keypair if needed.
    Uses the user's configured email and name from djb config.

    Returns:
        True if GPG is ready to use, False if setup failed.
    """
    # Initialize GPG agent config if not exists
    if init_gpg_agent_config():
        logger.done("Created GPG agent config with passphrase caching")

    # Check if user has a GPG key
    if has_gpg_secret_key():
        return True

    # Need to generate a GPG key
    logger.warning("No GPG key found - one is needed for age key protection")

    cfg = _get_config()
    user_email = cfg.email
    user_name = cfg.name

    if not user_email:
        logger.fail("Email not configured. Run 'djb init' first.")
        return False

    if not user_name:
        user_name = user_email.split("@")[0]

    logger.next(f"Generating GPG key for {user_name} <{user_email}>")

    try:
        generate_gpg_key(user_name, user_email)
        logger.done("Generated GPG keypair")
        return True
    except GpgError as e:
        logger.fail(f"Failed to generate GPG key: {e}")
        logger.info("You can generate one manually with: gpg --gen-key")
        return False


@secrets.command("init")
@click.option(
    "--key-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to store age key (default: ~/.age/keys.txt)",
)
@click.option(
    "--secrets-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory for secrets files (default: ./secrets)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing key file if it exists",
)
def init(key_path: Path | None, secrets_dir: Path | None, force: bool):
    """Initialize secrets management for this project.

    NOTE: `djb init` automatically runs this command. You typically don't need
    to run `djb secrets init` directly unless you need advanced options.

    Sets up SOPS with age encryption:

    \b
    - Generates an age encryption key (.age/keys.txt in project root)
    - Creates encrypted secrets files for dev/staging/production
    - Sets up .sops.yaml configuration for multi-recipient encryption
    - Displays your public key for sharing with team members
    - Configures GPG agent for passphrase caching
    - Generates a GPG key if needed (for age key protection)

    Safe to run if key already exists - you'll be prompted to reuse it.

    \b
    Examples:
      djb secrets init --force          # Regenerate key
      djb secrets init --key-path ./my.key  # Custom key location

    \b
    Backup your private key:
      djb secrets export-key | pbcopy   # Copy to clipboard for password manager
    """
    # Ensure SOPS, age, and GPG are installed (auto-installs on macOS with Homebrew)
    if not _ensure_prerequisites():
        sys.exit(1)

    # Ensure GPG is configured with a key for age key protection
    if not _ensure_gpg_setup():
        sys.exit(1)

    if key_path is None:
        key_path = get_default_key_path()

    if secrets_dir is None:
        secrets_dir = get_default_secrets_dir()

    # Check if key already exists
    if key_path.exists() and not force:
        public_key = get_public_key_from_private(key_path)
        logger.info(f"Using existing age key at {key_path}")
    else:
        # Generate new age key
        public_key, _ = generate_age_key(key_path)
        logger.done(f"Generated age key at {key_path}")

    # Display public key
    logger.info("\nYour public key (share with team members):")
    logger.highlight(f"  {public_key}")

    # Create secrets directory
    secrets_dir.mkdir(parents=True, exist_ok=True)

    # Get existing recipients from .sops.yaml (if any)
    cfg = _get_config()
    user_email = cfg.email or "unknown@example.com"
    user_name = cfg.name
    user_identity = format_identity(user_name, user_email)
    recipients = parse_sops_config(secrets_dir)

    # Add user's key if not already present
    if public_key not in recipients:
        recipients[public_key] = user_identity
        logger.done(f"Added your public key to .sops.yaml")
    else:
        existing_identity = recipients[public_key]
        if existing_identity:
            logger.info(f"Public key already in .sops.yaml ({existing_identity})")
        else:
            # Update identity for existing key
            recipients[public_key] = user_identity

    # Create/update .sops.yaml configuration with identity comments
    create_sops_config(secrets_dir, recipients)
    logger.done("Updated .sops.yaml configuration")

    # Get all public keys for encryption
    all_public_keys = list(recipients.keys())

    # Create .gitignore for secrets directory
    gitignore_path = secrets_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(
            "# Decrypted secrets (never commit these)\n"
            "*.decrypted.yaml\n"
            "*.plaintext.yaml\n"
            "*.secret\n"
            "*.tmp.yaml\n"
        )

    # Create template secrets files for each environment
    manager = SecretsManager(secrets_dir=secrets_dir, key_path=key_path)

    for env in SECRETS_ENVIRONMENTS:
        secrets_file = secrets_dir / f"{env}.yaml"
        if not secrets_file.exists():
            template = _get_template(env)
            manager.save_secrets(env, template, all_public_keys)
            logger.done(f"Created {env}.yaml")

    # Create README for secrets directory
    readme_path = secrets_dir / "README.md"
    if not readme_path.exists():
        readme_content = _README_TEMPLATE.format(key_path=key_path, public_key=public_key)
        readme_path.write_text(readme_content)
        logger.done("Created README.md")

    logger.done(f"Secrets management initialized in {secrets_dir}")
    logger.info("\nNext steps:")
    logger.info("  1. Edit your secrets: djb secrets edit dev")
    logger.info(f"  2. Add secrets to git: git add {secrets_dir}/*.yaml {secrets_dir}/.sops.yaml")
    logger.info(f"  3. Keep your key safe: backup {key_path}")


@secrets.command("edit")
@click.argument("environment", type=click.Choice(SECRETS_ENVIRONMENTS))
@click.option(
    "--key-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to age key file",
)
@click.option(
    "--secrets-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory containing secrets files",
)
def edit(
    environment: str,
    key_path: Path | None,
    secrets_dir: Path | None,
):
    """Edit secrets for an environment.

    Uses SOPS to decrypt the secrets file, open it in your editor ($EDITOR or vim),
    then automatically re-encrypts when you save and close.

    Creates a new secrets file if the environment doesn't exist yet.

    \b
    Examples:
      djb secrets edit dev              # Edit dev secrets
      djb secrets edit production       # Edit production secrets
    """
    _check_prerequisites()

    if secrets_dir is None:
        secrets_dir = get_default_secrets_dir()

    # Use protected_age_key context manager for GPG-protected keys
    # If user provides explicit key_path, use that directly
    if key_path is not None:
        _edit_with_key(environment, key_path, secrets_dir)
    else:
        try:
            with protected_age_key() as actual_key_path:
                _edit_with_key(environment, actual_key_path, secrets_dir)
        except ProtectedFileError as e:
            logger.fail(str(e))
            sys.exit(1)


def _edit_with_key(environment: str, key_path: Path, secrets_dir: Path) -> None:
    """Internal helper to edit secrets with a given key path."""
    secrets_file = secrets_dir / f"{environment}.yaml"

    # Check if file exists, create if not
    if not secrets_file.exists():
        logger.warning(f"Secrets file for '{environment}' not found.")
        if click.confirm("Create new secrets file?"):
            public_key = get_public_key_from_private(key_path)

            # User secrets (dev) are encrypted with user's key only
            # Project secrets are encrypted for all team members
            if environment in USER_SECRETS_ENVIRONMENTS:
                encrypt_keys = [public_key]
            else:
                encrypt_keys = get_all_recipients(secrets_dir)
                if not encrypt_keys:
                    encrypt_keys = [public_key]

            manager = SecretsManager(secrets_dir=secrets_dir, key_path=key_path)
            template = _get_template(environment, project_name=_get_config().project_name)
            manager.save_secrets(environment, template, encrypt_keys)
            logger.done(f"Created {environment}.yaml")
        else:
            sys.exit(1)

    # Use SOPS to edit the file directly (SOPS uses $EDITOR automatically)
    env = os.environ.copy()
    env["SOPS_AGE_KEY_FILE"] = str(key_path)

    try:
        result = subprocess.run(
            ["sops", "--config", str(secrets_dir / ".sops.yaml"), str(secrets_file)],
            env=env,
        )
        if result.returncode == 0:
            logger.done(f"Saved secrets for {environment}")
        else:
            logger.fail(f"SOPS edit failed with exit code {result.returncode}")
            sys.exit(1)
    except FileNotFoundError:
        logger.fail("SOPS not found. Install with: brew install sops")
        sys.exit(1)


@secrets.command("view")
@click.argument("environment", type=click.Choice(SECRETS_ENVIRONMENTS))
@click.option(
    "--key-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to age key file",
)
@click.option(
    "--secrets-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory containing secrets files",
)
@click.option(
    "--key",
    "secret_key",
    default=None,
    help="Show only this specific key",
)
def view(
    environment: str,
    key_path: Path | None,
    secrets_dir: Path | None,
    secret_key: str | None,
):
    """View decrypted secrets without editing.

    Displays secrets in plaintext - use carefully in secure environments only.

    \b
    Examples:
      djb secrets view dev              # View all dev secrets
      djb secrets view prod --key django_secret_key  # View one key
    """
    _check_prerequisites()

    if secrets_dir is None:
        secrets_dir = get_default_secrets_dir()

    # Use protected_age_key context manager for GPG-protected keys
    if key_path is not None:
        _view_with_key(environment, key_path, secrets_dir, secret_key)
    else:
        try:
            with protected_age_key() as actual_key_path:
                _view_with_key(environment, actual_key_path, secrets_dir, secret_key)
        except ProtectedFileError as e:
            logger.fail(str(e))
            sys.exit(1)


def _view_with_key(
    environment: str, key_path: Path, secrets_dir: Path, secret_key: str | None
) -> None:
    """Internal helper to view secrets with a given key path."""
    # Load and decrypt
    manager = SecretsManager(secrets_dir=secrets_dir, key_path=key_path)
    try:
        secrets_data = manager.load_secrets(environment)
    except SopsError as e:
        logger.fail(f"Failed to decrypt: {e}")
        sys.exit(1)

    if secret_key:
        # Show specific key
        if secret_key in secrets_data:
            logger.info(f"{secret_key}: {secrets_data[secret_key]}")
        else:
            logger.fail(f"Key '{secret_key}' not found")
            sys.exit(1)
    else:
        # Show all secrets
        logger.info(f"Secrets for {environment}:")
        logger.info(yaml.dump(secrets_data, default_flow_style=False, sort_keys=False))


@secrets.command("list")
@click.option(
    "--secrets-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory containing secrets files",
)
def list_environments(secrets_dir: Path | None):
    """List available secret environments.

    Shows all encrypted secrets files in the secrets directory.

    \b
    Example:
      djb secrets list
    """
    if secrets_dir is None:
        secrets_dir = get_default_secrets_dir()

    if not secrets_dir.exists():
        logger.warning("No secrets directory found.")
        logger.info("Run 'djb init' to get started.")
        return

    # Find all .yaml files (excluding .sops.yaml)
    secret_files = sorted(f for f in secrets_dir.glob("*.yaml") if f.name != ".sops.yaml")

    if not secret_files:
        logger.warning("No secret files found.")
        return

    logger.info("Available environments:")
    for file in secret_files:
        env_name = file.stem
        logger.info(f"  - {env_name}")


@secrets.command("generate-key")
def generate_key():
    """Generate a new random Django secret key.

    Creates a cryptographically secure 50-character secret key
    suitable for Django's SECRET_KEY setting.

    \b
    Example:
      djb secrets generate-key
    """
    chars = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    secret_key = "".join(py_secrets.choice(chars) for _ in range(50))

    logger.info("Generated Django secret key:")
    logger.highlight(secret_key)
    logger.info("\nAdd this to your secrets file with:")
    logger.info("  djb secrets edit <environment>")


@secrets.command("export-key")
@click.option(
    "--key-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to age key file (default: .age/keys.txt in project root)",
)
def export_key(key_path: Path | None):
    """Export the private key for backup.

    Outputs only the secret key line (AGE-SECRET-KEY-...) which can be
    copied to a password manager for safekeeping.

    \b
    Examples:
      djb secrets export-key              # Print to stdout
      djb secrets export-key | pbcopy     # Copy to clipboard (macOS)
      djb secrets export-key | xclip      # Copy to clipboard (Linux)

    \b
    Important:
      - Store this key securely in a password manager
      - Never commit the key to version control
      - If lost, you won't be able to decrypt existing secrets
    """
    # Use protected_age_key context manager for GPG-protected keys
    if key_path is not None:
        _export_key_from_path(key_path)
    else:
        try:
            with protected_age_key() as actual_key_path:
                _export_key_from_path(actual_key_path)
        except ProtectedFileError as e:
            logger.fail(str(e))
            sys.exit(1)


def _export_key_from_path(key_path: Path) -> None:
    """Internal helper to export key from a given path."""
    if not key_path.exists():
        logger.fail(f"Key file not found: {key_path}")
        logger.info("\nTo create a key, run:")
        logger.info("  djb init")
        sys.exit(1)

    # Read the key file and extract just the secret key line
    content = key_path.read_text()
    for line in content.splitlines():
        if line.startswith("AGE-SECRET-KEY-"):
            # Output just the key, no newline for clean piping
            sys.stdout.write(line)
            return

    logger.fail("No AGE-SECRET-KEY found in key file")
    sys.exit(1)


@secrets.command("upgrade")
@click.argument(
    "environment",
    type=click.Choice(SECRETS_ENVIRONMENTS),
    required=False,
)
@click.option(
    "--key-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to age key file",
)
@click.option(
    "--secrets-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory containing secrets files",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be added without making changes",
)
@click.option(
    "--all",
    "all_envs",
    is_flag=True,
    help="Upgrade all environments",
)
def upgrade(
    environment: str | None,
    key_path: Path | None,
    secrets_dir: Path | None,
    dry_run: bool,
    all_envs: bool,
):
    """Add missing secrets from template to existing secrets files.

    Upgrades secrets files by adding any new keys from the template while
    preserving existing values. Useful when djb adds new secret fields.

    \b
    Examples:
      djb secrets upgrade dev             # Upgrade dev secrets
      djb secrets upgrade --all           # Upgrade all environments
      djb secrets upgrade dev --dry-run   # Preview changes
    """
    _check_prerequisites()

    if secrets_dir is None:
        secrets_dir = get_default_secrets_dir()

    if not environment and not all_envs:
        logger.fail("Specify an environment or use --all")
        sys.exit(1)

    # Use protected_age_key context manager for GPG-protected keys
    if key_path is not None:
        _upgrade_with_key(environment, key_path, secrets_dir, dry_run, all_envs)
    else:
        try:
            with protected_age_key() as actual_key_path:
                _upgrade_with_key(environment, actual_key_path, secrets_dir, dry_run, all_envs)
        except ProtectedFileError as e:
            logger.fail(str(e))
            sys.exit(1)


def _upgrade_with_key(
    environment: str | None,
    key_path: Path,
    secrets_dir: Path,
    dry_run: bool,
    all_envs: bool,
) -> None:
    """Internal helper to upgrade secrets with a given key path."""
    # Load manager
    manager = SecretsManager(secrets_dir=secrets_dir, key_path=key_path)
    all_public_keys = get_all_recipients(secrets_dir)

    if not all_public_keys:
        public_key = get_public_key_from_private(key_path)
        all_public_keys = [public_key]

    # Determine which environments to upgrade
    if all_envs:
        environments = SECRETS_ENVIRONMENTS
    else:
        assert environment is not None  # Checked above
        environments = [environment]

    for env in environments:
        secrets_file = secrets_dir / f"{env}.yaml"
        if not secrets_file.exists():
            logger.warning(f"Skipping {env}: secrets file not found")
            continue

        # Load existing secrets
        try:
            existing = manager.load_secrets(env)
        except (FileNotFoundError, SopsError) as e:
            logger.fail(f"Skipping {env}: failed to load ({e})")
            continue

        # Get template and merge
        template = _get_template(env)
        merged, added = _deep_merge_missing(existing, template)

        if not added:
            logger.info(f"{env}: already up to date")
            continue

        if dry_run:
            logger.warning(f"{env}: would add {len(added)} key(s):")
            for key in added:
                logger.info(f"  + {key}")
        else:
            manager.save_secrets(env, merged, all_public_keys)
            logger.done(f"{env}: added {len(added)} key(s):")
            for key in added:
                logger.info(f"  + {key}")


@secrets.command("rotate")
@click.argument(
    "environment",
    type=click.Choice([*PROJECT_SECRETS_ENVIRONMENTS, "all"]),
    required=False,
    default="all",
)
@click.option(
    "--key-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to age key file",
)
@click.option(
    "--secrets-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory containing secrets files",
)
@click.option(
    "--new-key",
    is_flag=True,
    help="Generate a new key (rotates your personal key)",
)
@click.option(
    "--add-key",
    type=str,
    default=None,
    help="Add a new public key (age...) to encrypt for",
)
@click.option(
    "--add-email",
    type=str,
    default=None,
    help="Email for the new key being added (used with --add-key)",
)
@click.option(
    "--add-name",
    type=str,
    default=None,
    help="Name for the new key being added (used with --add-key, optional)",
)
@click.option(
    "--remove-key",
    type=str,
    default=None,
    help="Remove a public key (age... or identity) from recipients",
)
def rotate(
    environment: str,
    key_path: Path | None,
    secrets_dir: Path | None,
    new_key: bool,
    add_key: str | None,
    add_email: str | None,
    add_name: str | None,
    remove_key: str | None,
):
    """Re-encrypt project secrets with updated recipient keys.

    This command manages project secrets (staging, production) which are
    shared among team members. User secrets (dev) are encrypted with each
    user's own key and don't need rotation.

    Use this command for:
    - Adding a new team member (--add-key)
    - Removing a team member (--remove-key)
    - Rotating your own key (--new-key)
    - Re-encrypting after updating .sops.yaml (no flags)

    By default, re-encrypts all project secrets. Specify an environment
    to only re-encrypt that one.

    \b
    Examples:
      djb secrets rotate                           # Re-encrypt all project secrets
      djb secrets rotate --add-key age1abc... --add-email bob@example.com --add-name "Bob Smith"
      djb secrets rotate --remove-key bob@example.com
      djb secrets rotate --new-key                 # Rotate your personal key
      djb secrets rotate staging                   # Only re-encrypt staging
    """
    _check_prerequisites()

    if secrets_dir is None:
        secrets_dir = get_default_secrets_dir()

    # Use protected_age_key context manager for GPG-protected keys
    if key_path is not None:
        _rotate_with_key(
            environment,
            key_path,
            secrets_dir,
            new_key,
            add_key,
            add_email,
            add_name,
            remove_key,
        )
    else:
        try:
            with protected_age_key() as actual_key_path:
                _rotate_with_key(
                    environment,
                    actual_key_path,
                    secrets_dir,
                    new_key,
                    add_key,
                    add_email,
                    add_name,
                    remove_key,
                )
        except ProtectedFileError as e:
            logger.fail(str(e))
            sys.exit(1)


def _rotate_with_key(
    environment: str,
    key_path: Path,
    secrets_dir: Path,
    new_key: bool,
    add_key: str | None,
    add_email: str | None,
    add_name: str | None,
    remove_key: str | None,
) -> None:
    """Internal helper to rotate secrets with a given key path."""
    # Load existing recipients from .sops.yaml
    recipients = parse_sops_config(secrets_dir)
    old_public_key = get_public_key_from_private(key_path)

    # Handle --new-key: generate new key and update .sops.yaml
    if new_key:
        logger.warning("This will generate a new encryption key!")
        logger.info("Your old key will be backed up.")

        if not click.confirm("Continue?"):
            logger.info("Aborted.")
            return

        # Backup old key
        backup_path = key_path.with_suffix(".txt.backup")
        old_key_content = key_path.read_text()
        backup_path.write_text(old_key_content)
        backup_path.chmod(0o600)
        logger.info(f"Old key backed up to {backup_path}")

        # Generate new key
        new_public_key, _ = generate_age_key(key_path)

        logger.done(f"Generated new key at {key_path}")
        logger.info("\nNew public key:")
        logger.highlight(f"  {new_public_key}")

        # Update recipients: remove old key, add new key with same identity
        old_identity = recipients.pop(old_public_key, None)
        if old_identity:
            recipients[new_public_key] = old_identity
            logger.done("Updated .sops.yaml with new key")
        else:
            cfg = _get_config()
            user_email = cfg.email or "unknown@example.com"
            user_name = cfg.name
            user_identity = format_identity(user_name, user_email)
            recipients[new_public_key] = user_identity
            logger.done("Added new key to .sops.yaml")

    # Handle --add-key: add a new public key
    if add_key:
        if not is_valid_age_public_key(add_key):
            logger.fail(f"Invalid age public key: {add_key}")
            logger.info("Age public keys start with 'age1' and are 62 characters long.")
            logger.info("Example: age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p")
            sys.exit(1)

        if add_key in recipients:
            logger.warning("Key already exists in .sops.yaml")
        else:
            email = add_email or input("Email for the new key: ").strip()
            identity = format_identity(add_name, email)
            recipients[add_key] = identity
            logger.done(f"Added key for {identity}")

    # Handle --remove-key: remove a public key (by key, email, or identity)
    if remove_key:
        # Find the key to remove
        key_to_remove = None
        if remove_key.startswith("age"):
            # Remove by key
            if remove_key in recipients:
                key_to_remove = remove_key
        else:
            # Remove by email or identity match
            for key, identity in recipients.items():
                # Match exact identity or just the email part
                _, stored_email = parse_identity(identity)
                if identity == remove_key or stored_email == remove_key:
                    key_to_remove = key
                    break

        if key_to_remove:
            # Prevent removing the last decryptor
            if len(recipients) == 1:
                logger.fail("Cannot remove the last recipient!")
                logger.info("This would make all secrets permanently unrecoverable.")
                logger.info("Add another recipient first, then remove this one.")
                sys.exit(1)

            del recipients[key_to_remove]
            logger.done(f"Removed key: {remove_key}")
        else:
            logger.warning(f"Key not found: {remove_key}")

    # Validate we have recipients
    if not recipients:
        logger.fail("No public keys found in .sops.yaml")
        sys.exit(1)

    # Update .sops.yaml with new keys
    create_sops_config(secrets_dir, recipients)
    logger.done("Updated .sops.yaml configuration")

    # Get keys list for re-encryption
    all_public_keys = list(recipients.keys())

    logger.info(f"Re-encrypting for {len(all_public_keys)} recipient(s)")

    # Determine which environments to re-encrypt (only project secrets)
    if environment == "all":
        environments = PROJECT_SECRETS_ENVIRONMENTS
    else:
        environments = [environment]

    # Re-encrypt each project secret using SOPS updatekeys
    for env in environments:
        secrets_file = secrets_dir / f"{env}.yaml"
        if not secrets_file.exists():
            logger.warning(f"Skipping {env}: secrets file not found")
            continue

        try:
            rotate_keys(secrets_file, all_public_keys, key_path)
            logger.done(f"Re-encrypted {env}")
        except SopsError as e:
            logger.fail(f"Failed to re-encrypt {env}: {e}")

    logger.info("\nDon't forget to commit the updated secrets files!")


@secrets.command("protect")
@click.option(
    "--key-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to age key file to protect",
)
def protect(key_path: Path | None):
    """Enable GPG protection for the age private key.

    Encrypts the age private key using your GPG public key.
    GPG agent caches the private key passphrase for decryption.

    After protection:
    - The plaintext .age/keys.txt is replaced with .age/keys.txt.gpg
    - All secrets operations automatically decrypt/re-encrypt the key
    - GPG agent caches the passphrase for the session

    \b
    Example:
        djb secrets protect
    """
    if not _ensure_prerequisites():
        sys.exit(1)

    # Ensure GPG is configured with a key
    if not _ensure_gpg_setup():
        sys.exit(1)

    if key_path is None:
        key_path = get_default_key_path()

    if not key_path.exists():
        # Check if already protected
        encrypted_path = key_path.parent / (key_path.name + ".gpg")
        if encrypted_path.exists():
            logger.info("Age key is already GPG protected")
            return
        logger.fail(f"Age key not found at {key_path}")
        logger.info("Run 'djb init' first.")
        sys.exit(1)

    if is_age_key_protected():
        logger.info("Age key is already GPG protected")
        return

    if not check_gpg_installed():
        logger.fail("GPG is not installed")
        logger.info("Install with: brew install gnupg")
        sys.exit(1)

    try:
        protect_age_key()
        logger.done("Protected age key with GPG encryption")
        logger.info(f"Encrypted key at: {key_path.parent / (key_path.name + '.gpg')}")
    except GpgError as e:
        logger.fail(f"Failed to protect key: {e}")
        sys.exit(1)


@secrets.command("unprotect")
@click.option(
    "--key-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to GPG-encrypted age key file",
)
def unprotect(key_path: Path | None):
    """Remove GPG protection from the age private key.

    Decrypts the GPG-protected key back to plaintext.
    Use this for troubleshooting or if you want to disable GPG protection.

    \b
    Example:
        djb secrets unprotect
    """
    if key_path is None:
        key_path = get_default_key_path()

    if not is_age_key_protected():
        logger.info("Age key is not GPG protected")
        return

    try:
        unprotect_age_key()
        logger.done("Removed GPG protection from age key")
        logger.info(f"Plaintext key at: {key_path}")
    except GpgError as e:
        logger.fail(f"Failed to unprotect key: {e}")
        sys.exit(1)
