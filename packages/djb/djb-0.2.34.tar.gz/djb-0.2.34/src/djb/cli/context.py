"""CLI context for passing global options to subcommands."""

from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, ParamSpec, TypeVar, overload

import click

if TYPE_CHECKING:
    from djb.config import DjbConfig

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T", bound="CliContext")


@dataclass
class CliContext:
    """Context object passed through click's ctx.obj.

    This dataclass holds global CLI options that any subcommand can access.
    Use ctx.ensure_object(CliContext) in the main CLI group and access
    values via ctx.obj.<field_name> in subcommands.

    Subcommand groups can specialize the context by:
    1. Saving the parent context: `parent_ctx = ctx.obj`
    2. Creating their specialized context: `ctx.obj = CliHealthContext()`
    3. Copying parent fields: `ctx.obj.__dict__.update(parent_ctx.__dict__)`
    4. Setting specialized fields: `ctx.obj.fix = fix`

    Example:
        @pass_context
        def my_command(cli_ctx: CliContext):
            project_dir = cli_ctx.config.project_dir
    """

    # Global options (set by djb_cli)
    verbose: bool = False
    quiet: bool = False

    # Config is set by djb_cli before any subcommand runs.
    # Typed as DjbConfig for IDE support; default None for dataclass machinery.
    config: "DjbConfig" = field(default=None)  # type: ignore[assignment]

    # Scope options (useful for multiple commands)
    scope_frontend: bool = False
    scope_backend: bool = False


@dataclass
class CliHealthContext(CliContext):
    """Specialized context for `djb health` command group.

    Inherits all global options from CliContext and adds health-specific options.
    """

    fix: bool = False
    cov: bool = False


@dataclass
class CliHerokuContext(CliContext):
    """Specialized context for `djb deploy heroku` command group.

    Inherits all global options from CliContext and adds heroku-specific options.
    """

    app: str | None = None


@overload
def pass_context() -> Callable[[Callable[..., R]], Callable[..., R]]: ...


@overload
def pass_context(ctx_type: type[T]) -> Callable[[Callable[..., R]], Callable[..., R]]: ...


@overload
def pass_context(ctx_type: Callable[..., R]) -> Callable[..., R]: ...


def pass_context(
    ctx_type: type[T] | Callable[..., R] | None = None,
) -> Callable[[Callable[..., R]], Callable[..., R]] | Callable[..., R]:
    """Decorator that passes a context object as the first argument to a command.

    Can be used with or without parentheses:

        @click.command()
        @pass_context  # Uses CliContext (default)
        def my_command(cli_ctx: CliContext):
            project_dir = cli_ctx.config.project_dir

        @health.command()
        @pass_context(CliHealthContext)  # Uses CliHealthContext
        def lint(health_ctx: CliHealthContext):
            fix = health_ctx.fix

    Args:
        ctx_type: The context class to expect (default: CliContext).
            When used without parentheses, this is the decorated function.
    """
    # Handle @pass_context without parentheses (ctx_type is the function)
    if ctx_type is not None and callable(ctx_type) and not isinstance(ctx_type, type):
        f = ctx_type
        return _make_context_wrapper(f, CliContext)

    # Handle @pass_context() or @pass_context(SomeContextClass)
    actual_type: type[CliContext] = ctx_type if isinstance(ctx_type, type) else CliContext

    def decorator(f: Callable[..., R]) -> Callable[..., R]:
        return _make_context_wrapper(f, actual_type)

    return decorator


def _make_context_wrapper(f: Callable[..., R], ctx_type: type[T]) -> Callable[..., R]:
    """Create a wrapper that passes the context to the function."""

    @functools.wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        ctx = click.get_current_context()
        cli_ctx = ctx.obj
        assert isinstance(cli_ctx, ctx_type), f"Expected {ctx_type.__name__} at ctx.obj"
        return f(cli_ctx, *args, **kwargs)

    return wrapper
