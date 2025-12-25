"""
djb.tests - Test utilities for djb core tests.

Auto-enabled fixtures (applied to all tests automatically):
    clean_djb_env - Ensures a clean environment by removing DJB_* env vars
                    and resets the lazy config singleton before/after each test.

Factory fixtures:
    make_config_file - Factory for creating config files in .djb directory.
                       Usage: make_config_file("name: John") -> creates .djb/local.yaml
                              make_config_file({"key": "val"}, config_type="project")

Test modules:
    test_config - Tests for DjbConfig, configure, load/save_config, provenance tracking
    test_field - Tests for ConfigFieldABC, StringField base class
    test_acquisition - Tests for field acquisition, AcquisitionContext, GitConfigSource
    test_prompting - Tests for prompt(), confirm(), PromptResult
    test_resolution - Tests for ProvenanceChainMap, ResolutionContext, ConfigSource
    test_project - Tests for project detection (find_project_root, find_pyproject_root)
    test_types - Tests for Mode, Target enums
"""

from __future__ import annotations

__all__: list[str] = []
