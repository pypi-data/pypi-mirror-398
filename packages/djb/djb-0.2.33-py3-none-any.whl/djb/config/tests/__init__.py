"""
Config test utilities and base classes.

Provides:
    TestDjbConfigBase - Base class for test config objects (inherits from DjbConfigBase)
    make_test_config - Factory for creating test config instances
"""

from __future__ import annotations

from typing import Any

import attrs

from djb.config.config import DjbConfigBase, LoadState
from djb.config.resolution import ConfigSource


@attrs.frozen
class TestDjbConfigBase(DjbConfigBase):
    """Base class for test configurations that inherits from DjbConfigBase.

    Like production DjbConfigBase, this class is frozen (immutable).
    Unlike production, it:
    - Starts in LOADED state (no lazy loading machinery)
    - Uses _provenance parameter for test-controlled sources

    Because it inherits from DjbConfigBase, it can be used anywhere
    DjbConfigBase is expected (e.g., acquire_all_fields).

    Usage:
        @attrs.define
        class MyTestConfig(TestDjbConfigBase):
            name: str = attrs.field(
                default="default",
                metadata={ATTRSLIB_METADATA_KEY: mock_field},
            )

        config = MyTestConfig(_provenance={"name": ConfigSource.LOCAL_CONFIG})
        assert config.get_source("name") == ConfigSource.LOCAL_CONFIG
    """

    def __attrs_post_init__(self) -> None:
        """Mark as loaded immediately (skip lazy loading)."""
        object.__setattr__(self, "_loaded", LoadState.LOADED)


def make_test_config(
    fields: dict[str, Any],
    sources: dict[str, ConfigSource] | None = None,
) -> TestDjbConfigBase:
    """Factory for creating test config instances with custom fields.

    This is a convenience function for tests that need a quick config with
    specific fields, without defining a full subclass.

    Args:
        fields: Dict mapping field names to their values
        sources: Dict mapping field names to their ConfigSource (for get_source)

    Returns:
        A TestDjbConfigBase instance with the given fields set as attributes

    Usage:
        config = make_test_config(
            fields={"name": "John", "email": "john@example.com"},
            sources={"name": ConfigSource.LOCAL_CONFIG},
        )
        assert config.name == "John"
        assert config.get_source("name") == ConfigSource.LOCAL_CONFIG
    """
    config = TestDjbConfigBase(_provenance=sources or {})
    for name, value in fields.items():
        object.__setattr__(config, name, value)
    return config


__all__ = [
    "TestDjbConfigBase",
    "make_test_config",
]
