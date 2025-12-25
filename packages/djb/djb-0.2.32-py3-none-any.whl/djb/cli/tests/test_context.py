"""Tests for djb.cli.context module."""

from __future__ import annotations

from unittest.mock import MagicMock

import click
import pytest
from click.testing import CliRunner

from djb.cli.context import (
    CliContext,
    CliHealthContext,
    CliHerokuContext,
    pass_context,
)


class TestCliContext:
    """Tests for the CliContext dataclass."""

    def test_default_values(self):
        """Test CliContext has correct default values."""
        ctx = CliContext()
        assert ctx.verbose is False
        assert ctx.quiet is False
        assert ctx.config is None
        assert ctx.scope_frontend is False
        assert ctx.scope_backend is False

    def test_custom_values(self):
        """Test CliContext can be initialized with custom values."""
        config = MagicMock()
        ctx = CliContext(
            verbose=True,
            quiet=True,
            config=config,
            scope_frontend=True,
            scope_backend=True,
        )
        assert ctx.verbose is True
        assert ctx.quiet is True
        assert ctx.config is config
        assert ctx.scope_frontend is True
        assert ctx.scope_backend is True


class TestCliHealthContext:
    """Tests for the CliHealthContext dataclass."""

    def test_inherits_from_cli_context(self):
        """Test CliHealthContext is a subclass of CliContext."""
        assert issubclass(CliHealthContext, CliContext)

    def test_default_values(self):
        """Test CliHealthContext has correct default values."""
        ctx = CliHealthContext()
        # Inherited fields
        assert ctx.verbose is False
        assert ctx.quiet is False
        assert ctx.config is None
        # Specialized fields
        assert ctx.fix is False
        assert ctx.cov is False

    def test_specialized_values(self):
        """Test CliHealthContext specialized fields."""
        ctx = CliHealthContext(fix=True, cov=True)
        assert ctx.fix is True
        assert ctx.cov is True

    def test_combined_inheritance_and_specialized(self):
        """Test CliHealthContext with both inherited and specialized values."""
        config = MagicMock()
        ctx = CliHealthContext(
            verbose=True,
            config=config,
            fix=True,
            cov=True,
        )
        assert ctx.verbose is True
        assert ctx.config is config
        assert ctx.fix is True
        assert ctx.cov is True


class TestCliHerokuContext:
    """Tests for the CliHerokuContext dataclass."""

    def test_inherits_from_cli_context(self):
        """Test CliHerokuContext is a subclass of CliContext."""
        assert issubclass(CliHerokuContext, CliContext)

    def test_default_values(self):
        """Test CliHerokuContext has correct default values."""
        ctx = CliHerokuContext()
        # Inherited fields
        assert ctx.verbose is False
        assert ctx.quiet is False
        assert ctx.config is None
        # Specialized fields
        assert ctx.app is None

    def test_specialized_values(self):
        """Test CliHerokuContext specialized fields."""
        ctx = CliHerokuContext(app="my-app")
        assert ctx.app == "my-app"

    def test_combined_inheritance_and_specialized(self):
        """Test CliHerokuContext with both inherited and specialized values."""
        config = MagicMock()
        ctx = CliHerokuContext(
            verbose=True,
            config=config,
            app="production-app",
        )
        assert ctx.verbose is True
        assert ctx.config is config
        assert ctx.app == "production-app"


class TestPassContext:
    """Tests for the pass_context decorator."""

    def test_pass_context_without_parentheses(self):
        """Test @pass_context without parentheses works."""
        cli_ctx = CliContext(verbose=True)

        @pass_context
        def my_command(ctx: CliContext):
            return ctx.verbose

        @click.command()
        @click.pass_context
        def wrapper(ctx):
            ctx.obj = cli_ctx
            return my_command()

        runner = CliRunner()
        result = runner.invoke(wrapper)
        assert result.exit_code == 0

    def test_pass_context_with_parentheses(self):
        """Test @pass_context() with parentheses works."""
        cli_ctx = CliContext(verbose=True)

        @pass_context()
        def my_command(ctx: CliContext):
            return ctx.verbose

        @click.command()
        @click.pass_context
        def wrapper(ctx):
            ctx.obj = cli_ctx
            return my_command()

        runner = CliRunner()
        result = runner.invoke(wrapper)
        assert result.exit_code == 0

    def test_pass_context_with_health_context(self):
        """Test @pass_context(CliHealthContext) works."""
        health_ctx = CliHealthContext(fix=True)

        @pass_context(CliHealthContext)
        def lint_command(ctx: CliHealthContext):
            return ctx.fix

        @click.command()
        @click.pass_context
        def wrapper(ctx):
            ctx.obj = health_ctx
            return lint_command()

        runner = CliRunner()
        result = runner.invoke(wrapper)
        assert result.exit_code == 0

    def test_pass_context_with_heroku_context(self):
        """Test @pass_context(CliHerokuContext) works."""
        heroku_ctx = CliHerokuContext(app="test-app")

        @pass_context(CliHerokuContext)
        def deploy_command(ctx: CliHerokuContext):
            return ctx.app

        @click.command()
        @click.pass_context
        def wrapper(ctx):
            ctx.obj = heroku_ctx
            return deploy_command()

        runner = CliRunner()
        result = runner.invoke(wrapper)
        assert result.exit_code == 0

    def test_pass_context_wrong_type_raises(self):
        """Test @pass_context raises when context type mismatches."""
        cli_ctx = CliContext()  # Not CliHealthContext

        @pass_context(CliHealthContext)
        def lint_command(ctx: CliHealthContext):
            return ctx.fix

        @click.command()
        @click.pass_context
        def wrapper(ctx):
            ctx.obj = cli_ctx
            return lint_command()

        runner = CliRunner()
        result = runner.invoke(wrapper)
        # Should fail due to assertion error
        assert result.exit_code != 0

    def test_pass_context_preserves_function_name(self):
        """Test @pass_context preserves the wrapped function's name."""

        @pass_context
        def my_special_command(ctx: CliContext):
            pass

        assert my_special_command.__name__ == "my_special_command"

    def test_pass_context_passes_additional_args(self):
        """Test @pass_context passes additional arguments to the function."""
        cli_ctx = CliContext()
        received_args = []

        @pass_context
        def my_command(ctx: CliContext, name: str, count: int):
            received_args.append((name, count))
            return f"{name}: {count}"

        @click.command()
        @click.pass_context
        def wrapper(ctx):
            ctx.obj = cli_ctx
            return my_command("test", count=42)

        runner = CliRunner()
        result = runner.invoke(wrapper)
        assert result.exit_code == 0
        assert received_args == [("test", 42)]
