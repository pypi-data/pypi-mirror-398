"""
djb db CLI - Database management commands.

Provides commands for setting up and managing PostgreSQL databases for development.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import IntEnum, auto
from time import sleep, time

import click

from djb import config
from djb.cli.context import CliContext, pass_context
from djb.core.logging import get_logger
from djb.cli.utils import check_cmd
from djb.secrets import SopsError, load_secrets

logger = get_logger(__name__)


class DbStatus(IntEnum):
    """Database connection status levels."""

    UNINSTALLED = auto()  # PostgreSQL not installed
    UNREACHABLE = auto()  # PostgreSQL not running
    NO_DATABASE = auto()  # Database doesn't exist
    NO_USER = auto()  # User doesn't exist or wrong password
    OK = auto()  # Everything is working


@dataclass
class DbSettings:
    """Database connection settings."""

    name: str
    user: str
    password: str
    host: str
    port: int


def _get_db_settings_from_secrets() -> DbSettings | None:
    """Get database settings from dev secrets.

    Loads the db_credentials from the dev secrets file (secrets/dev.yaml).

    Returns:
        DbSettings if successful, None if secrets can't be loaded or db_credentials not found.
    """
    secrets_dir = config.project_dir / "secrets"
    if not secrets_dir.exists():
        return None

    try:
        secrets = load_secrets(environment="dev", secrets_dir=secrets_dir)
    except SopsError as e:
        # SOPS decryption failed - likely user's key not in .sops.yaml
        error_msg = str(e).lower()
        if "decrypt" in error_msg or "key" in error_msg or "recipient" in error_msg:
            logger.info("Could not decrypt dev secrets (your key may not be in .sops.yaml yet)")
        else:
            logger.info(f"Could not load dev secrets: {e}")
        return None
    except Exception as e:
        # Catch other exceptions - FileNotFoundError, KeyError, ValueError, etc.
        logger.debug(f"Could not load db settings from secrets: {e}")
        return None

    db_creds = secrets.get("db_credentials")

    if not isinstance(db_creds, dict):
        return None

    # Extract settings with defaults
    return DbSettings(
        name=db_creds.get("database", ""),
        user=db_creds.get("username", ""),
        password=db_creds.get("password", ""),
        host=db_creds.get("host", "localhost"),
        port=int(db_creds.get("port", 5432)),
    )


def _get_default_db_settings() -> DbSettings:
    """Get default database settings based on project name.

    Falls back to reasonable defaults if project name can't be determined.
    """
    project_name = config.project_name or config.project_dir.name

    # Sanitize project name for database use (replace hyphens with underscores)
    db_name = project_name.replace("-", "_")

    return DbSettings(
        name=db_name,
        user=db_name,
        password="foobarqux",  # Default dev password
        host="localhost",
        port=5432,
    )


def get_db_settings() -> DbSettings:
    """Get database settings from dev secrets, falling back to project-name defaults.

    Priority:
    1. db_credentials from secrets/dev.yaml
    2. Defaults based on project name (database=project_name, user=project_name, password=foobarqux)

    For new users who haven't been added to .sops.yaml yet, the fallback
    provides sensible defaults so they can still set up their local database.
    """
    settings = _get_db_settings_from_secrets()
    if settings and settings.name and settings.user:
        return settings

    # Fall back to project-name defaults
    defaults = _get_default_db_settings()
    logger.info(f"Using default database settings (db={defaults.name}, user={defaults.user})")
    return defaults


def check_postgres_installed() -> bool:
    """Check if PostgreSQL client tools are installed."""
    return shutil.which("psql") is not None


def check_postgres_running(host: str = "localhost", port: int = 5432) -> bool:
    """Check if PostgreSQL server is reachable."""
    if not shutil.which("pg_isready"):
        return False
    result = subprocess.run(
        ["pg_isready", "-h", host, "-p", str(port)],
        capture_output=True,
    )
    return result.returncode == 0


def _run_psql(
    query: str,
    database: str = "postgres",
    host: str = "localhost",
    port: int = 5432,
) -> subprocess.CompletedProcess[str]:
    """Run a psql query against the specified database."""
    return subprocess.run(
        ["psql", "-h", host, "-p", str(port), database, "-tAc", query],
        capture_output=True,
        text=True,
    )


def database_exists(name: str, host: str = "localhost", port: int = 5432) -> bool:
    """Check if a database exists."""
    result = _run_psql(
        f"SELECT 1 FROM pg_database WHERE datname='{name}';",
        host=host,
        port=port,
    )
    return result.stdout.strip() == "1"


def user_exists(username: str, host: str = "localhost", port: int = 5432) -> bool:
    """Check if a database user exists."""
    result = _run_psql(
        f"SELECT 1 FROM pg_user WHERE usename='{username}';",
        host=host,
        port=port,
    )
    return result.stdout.strip() == "1"


def can_connect_as_user(settings: DbSettings) -> bool:
    """Check if we can connect to the database as the specified user."""
    try:
        result = subprocess.run(
            [
                "psql",
                "-h",
                settings.host,
                "-p",
                str(settings.port),
                "-U",
                settings.user,
                "-d",
                settings.name,
                "-c",
                "SELECT 1;",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PGPASSWORD": settings.password},
        )
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False


def get_db_status(settings: DbSettings) -> DbStatus:
    """Get the current database status."""
    if not check_postgres_installed():
        return DbStatus.UNINSTALLED

    if not check_postgres_running(settings.host, settings.port):
        return DbStatus.UNREACHABLE

    if not database_exists(settings.name, settings.host, settings.port):
        return DbStatus.NO_DATABASE

    if not user_exists(settings.user, settings.host, settings.port):
        return DbStatus.NO_USER

    if can_connect_as_user(settings):
        return DbStatus.OK

    return DbStatus.NO_USER


def create_database(settings: DbSettings) -> bool:
    """Create the database if it doesn't exist.

    Returns:
        True if database was created or already exists, False on error.
    """
    if database_exists(settings.name, settings.host, settings.port):
        logger.done(f"Database '{settings.name}' already exists")
        return True

    logger.next(f"Creating database '{settings.name}'")
    result = _run_psql(
        f"CREATE DATABASE {settings.name};",
        host=settings.host,
        port=settings.port,
    )
    if result.returncode == 0:
        logger.done(f"Database '{settings.name}' created")
        return True
    else:
        logger.fail(f"Failed to create database: {result.stderr.strip()}")
        return False


def create_user_and_grant(settings: DbSettings) -> bool:
    """Create user and grant privileges if needed.

    This is idempotent - if user exists, it updates the password.
    Grants all privileges on the database to the user.

    Returns:
        True on success, False on error.
    """
    user_already_exists = user_exists(settings.user, settings.host, settings.port)

    if user_already_exists:
        logger.info(f"User '{settings.user}' already exists, updating password")
    else:
        logger.next(f"Creating user '{settings.user}'")

    # Use DO block to handle user creation/update idempotently
    query = f"""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT FROM pg_user WHERE usename = '{settings.user}'
        ) THEN
            CREATE USER {settings.user} WITH PASSWORD '{settings.password}';
        ELSE
            ALTER USER {settings.user} WITH PASSWORD '{settings.password}';
        END IF;

        GRANT ALL PRIVILEGES ON DATABASE {settings.name} TO {settings.user};
    END
    $$;
    """

    result = _run_psql(query, host=settings.host, port=settings.port)

    if result.returncode == 0:
        if user_already_exists:
            logger.done(f"User '{settings.user}' password updated and privileges granted")
        else:
            logger.done(f"User '{settings.user}' created and granted privileges")
        return True
    else:
        logger.fail(f"Failed to create/update user: {result.stderr.strip()}")
        return False


def grant_schema_permissions(settings: DbSettings) -> bool:
    """Grant schema permissions to the user.

    PostgreSQL 15+ requires explicit schema permissions for creating tables.

    Returns:
        True on success, False on error.
    """
    logger.next(f"Granting schema permissions to '{settings.user}'")

    # Connect to the target database to grant schema permissions
    result = subprocess.run(
        [
            "psql",
            "-h",
            settings.host,
            "-p",
            str(settings.port),
            settings.name,
            "-c",
            f"GRANT ALL ON SCHEMA public TO {settings.user};",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        logger.done("Schema permissions granted")
        return True
    else:
        # This might fail if the user doesn't have permission, but that's often OK
        logger.warning(f"Could not grant schema permissions: {result.stderr.strip()}")
        return True  # Non-fatal


def wait_for_postgres(
    host: str = "localhost",
    port: int = 5432,
    timeout: float = 10.0,
) -> bool:
    """Wait for PostgreSQL to become available.

    Args:
        host: PostgreSQL host
        port: PostgreSQL port
        timeout: Maximum seconds to wait

    Returns:
        True if PostgreSQL is available, False if timeout
    """
    logger.next(f"Waiting for PostgreSQL at {host}:{port}")
    start_time = time()

    while time() - start_time < timeout:
        if check_postgres_running(host, port):
            logger.done("PostgreSQL is ready")
            return True
        sleep(0.5)

    logger.fail(f"PostgreSQL not available after {timeout}s")
    return False


def start_postgres_service() -> bool:
    """Attempt to start PostgreSQL service via Homebrew.

    Returns:
        True if service started or already running, False on error.
    """
    if check_cmd(["brew", "services", "list"]):
        logger.next("Starting PostgreSQL service")
        result = subprocess.run(
            ["brew", "services", "start", "postgresql@17"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True
        # Try without version suffix
        result = subprocess.run(
            ["brew", "services", "start", "postgresql"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    return False


def init_database(
    *,
    start_service: bool = True,
    quiet: bool = False,
) -> bool:
    """Initialize database with user and permissions.

    This is the main entry point for database initialization.
    It's idempotent - safe to run multiple times.

    Args:
        start_service: Whether to attempt starting PostgreSQL if not running
        quiet: Suppress non-error output

    Returns:
        True on success, False on error
    """
    settings = get_db_settings()

    if not quiet:
        logger.info(f"Database: {settings.name}")
        logger.info(f"User: {settings.user}")
        logger.info(f"Host: {settings.host}:{settings.port}")

    # Check PostgreSQL installation
    if not check_postgres_installed():
        logger.fail("PostgreSQL is not installed")
        logger.tip("Install with: brew install postgresql@17")
        return False

    # Check if PostgreSQL is running
    if not check_postgres_running(settings.host, settings.port):
        if start_service:
            if not start_postgres_service():
                logger.fail("Could not start PostgreSQL service")
                return False
            if not wait_for_postgres(settings.host, settings.port):
                return False
        else:
            logger.fail("PostgreSQL is not running")
            logger.tip("Start with: brew services start postgresql@17")
            return False

    # Check current status
    status = get_db_status(settings)

    if status == DbStatus.OK:
        if not quiet:
            logger.done("Database already configured correctly")
        return True

    # Create database if needed
    if status <= DbStatus.NO_DATABASE:
        if not create_database(settings):
            return False

    # Create user and grant privileges
    if not create_user_and_grant(settings):
        return False

    # Grant schema permissions (PostgreSQL 15+)
    grant_schema_permissions(settings)

    # Verify final connection
    if can_connect_as_user(settings):
        if not quiet:
            logger.done("Database initialization complete")
        return True
    else:
        logger.fail("Could not verify database connection")
        return False


@click.group("db")
def db():
    """Database management commands.

    Commands for setting up and managing PostgreSQL databases
    for local development.
    """
    pass


@db.command("init")
@click.option(
    "--no-start",
    is_flag=True,
    help="Don't attempt to start PostgreSQL service if not running",
)
@pass_context
def db_init(cli_ctx: CliContext, no_start: bool):
    """Initialize development database.

    Creates the PostgreSQL database and user specified in Django settings.
    Uses defaults based on project name if Django settings aren't available.

    This command is idempotent - safe to run multiple times.
    If the database and user already exist with correct credentials,
    this is a no-op.

    \b
    What this does:
    * Checks if PostgreSQL is installed and running
    * Creates the database if it doesn't exist
    * Creates the user if it doesn't exist
    * Grants necessary permissions

    \b
    Examples:
      djb db init           # Initialize database
      djb db init --no-start  # Don't auto-start PostgreSQL
    """
    # cli_ctx.config ensures config is loaded; init_database uses global config
    _ = cli_ctx.config

    logger.next("Initializing development database")

    if not init_database(start_service=not no_start):
        raise click.ClickException("Database initialization failed")


@db.command("status")
@pass_context
def db_status(cli_ctx: CliContext):
    """Show database connection status.

    Checks PostgreSQL installation, service status, and whether
    the database and user exist and are accessible.
    """
    # cli_ctx.config ensures config is loaded; get_db_settings uses global config
    _ = cli_ctx.config
    settings = get_db_settings()

    logger.info("Database configuration:")
    logger.info(f"  Name: {settings.name}")
    logger.info(f"  User: {settings.user}")
    logger.info(f"  Host: {settings.host}:{settings.port}")
    logger.note()

    status = get_db_status(settings)

    status_messages = {
        DbStatus.UNINSTALLED: (
            "PostgreSQL is not installed",
            "Install with: brew install postgresql@17",
        ),
        DbStatus.UNREACHABLE: (
            "PostgreSQL is not running",
            "Start with: brew services start postgresql@17",
        ),
        DbStatus.NO_DATABASE: (f"Database '{settings.name}' does not exist", "Run: djb db init"),
        DbStatus.NO_USER: (
            f"User '{settings.user}' doesn't exist or password is incorrect",
            "Run: djb db init",
        ),
        DbStatus.OK: ("Database is configured and accessible", None),
    }

    message, tip = status_messages[status]

    if status == DbStatus.OK:
        logger.done(message)
    else:
        logger.fail(message)
        if tip:
            logger.tip(tip)
