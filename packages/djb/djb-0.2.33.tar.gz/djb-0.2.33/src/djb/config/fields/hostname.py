"""
HostnameField - Field for production hostname with dynamic default.

The default value is computed from the project_name field: `{project_name}.com`
"""

from __future__ import annotations

from djb.config.acquisition import AcquisitionContext, AcquisitionResult
from djb.config.field import ConfigFieldABC
from djb.config.fields.project_name import DEFAULT_PROJECT_NAME
from djb.config.prompting import prompt


class HostnameField(ConfigFieldABC):
    """Field for production hostname with dynamic default.

    The default is `{project_name}.com`, computed during acquisition.
    """

    def __init__(self, **kwargs):
        """Initialize hostname field."""
        super().__init__(
            prompt_text="Enter production hostname",
            **kwargs,
        )

    def acquire(self, ctx: AcquisitionContext) -> AcquisitionResult | None:
        """Acquire hostname with dynamic default from project_name."""
        # Compute dynamic default from project_name
        project_name = ctx.other_values.get("project_name", DEFAULT_PROJECT_NAME)
        default = f"{project_name}.com"

        # Use current value if available, otherwise use computed default
        current_default = str(ctx.current_value) if ctx.current_value else default

        # Prompt user
        result = prompt(
            self.prompt_text or "Enter production hostname",
            default=current_default,
        )

        if result.source == "cancelled":
            return None

        return self._prompted_result(result.value)
