"""
djb.cli - Command-line interface for the djb platform.

Provides subcommands for project initialization, secrets management,
health checks, deployment, and development utilities.

Usage:
    uv run djb --help           # Show all commands
    uv run djb health           # Run lint, typecheck, and tests
    uv run djb secrets init     # Initialize encrypted secrets

Commands:
    Core:
        init - Initialize a new djb project
        health - Run lint, typecheck, and tests (with --backend/--frontend scoping)
        config - Show or modify configuration
        db - Database operations (createdb, migrate, shell)

    Secrets:
        secrets init - Set up encrypted secrets with age/SOPS
        secrets edit - Edit secrets in $EDITOR
        secrets add-recipient - Add a new team member's key
        secrets rotate - Re-encrypt with new keys

    Deployment:
        deploy - Deploy to Heroku
        publish - Publish djb to PyPI

    Development:
        seed - Populate database with sample data
        sync-superuser - Create/update Django superuser from secrets
        dependencies - Check and update dependencies
        editable-djb - Toggle djb editable installation

See Also:
    djb/src/djb/cli/README.md - Detailed CLI architecture
    docs/SECRETS_GUIDE.md - Secrets management guide
"""
