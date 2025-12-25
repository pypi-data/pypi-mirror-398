"""
Shared constants for the config system.

This module is a leaf module with no config package imports,
used for constants that are shared across multiple modules
where placing them in a single owner would create circular imports.
"""

# Metadata key for storing ConfigField in attrs field metadata
ATTRSLIB_METADATA_KEY = "djb_config_field"
