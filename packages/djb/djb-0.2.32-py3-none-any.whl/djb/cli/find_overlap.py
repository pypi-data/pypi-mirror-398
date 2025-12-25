"""Find tests with overlapping coverage for potential consolidation."""

from __future__ import annotations

import json
import subprocess
import tempfile
from itertools import combinations
from pathlib import Path

import click

from djb.core.logging import get_logger

logger = get_logger(__name__)


def has_pytest_cov(project_root: Path) -> bool:
    """Check if pytest-cov is available in the project's environment."""
    try:
        result = subprocess.run(
            ["uv", "run", "python", "-c", "import pytest_cov"],
            cwd=project_root,
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def collect_per_test_coverage(
    project_root: Path, packages: list[str] | None = None
) -> dict[str, set[str]]:
    """Collect coverage data for each test individually.

    Args:
        project_root: Root directory of the project.
        packages: List of package paths to analyze (e.g., ["src/djb/cli"]).
                  Defaults to ["src"] if not specified.

    Returns a dict mapping test node IDs to sets of covered lines (file:line format).
    """
    if not has_pytest_cov(project_root):
        raise click.ClickException("pytest-cov is required. Install with: uv add pytest-cov")

    # Default to src if no packages specified
    if not packages:
        packages = ["src"]

    # First, collect all test IDs
    result = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise click.ClickException(f"Failed to collect tests: {result.stderr}")

    test_ids = [
        line.strip()
        for line in result.stdout.strip().split("\n")
        if "::" in line and not line.startswith(" ")
    ]

    logger.info(f"Collecting coverage for {len(test_ids)} tests...")
    if packages != ["src"]:
        logger.info(f"  Packages: {', '.join(packages)}")

    coverage_data: dict[str, set[str]] = {}

    # Build --cov arguments for each package
    cov_args = []
    for pkg in packages:
        cov_args.append(f"--cov={project_root / pkg}")

    with tempfile.TemporaryDirectory() as tmpdir:
        for i, test_id in enumerate(test_ids):
            if (i + 1) % 50 == 0:
                logger.info(f"  Progress: {i + 1}/{len(test_ids)}")

            cov_file = Path(tmpdir) / f"cov_{i}.json"
            cmd = [
                "uv",
                "run",
                "pytest",
                test_id,
                *cov_args,
                "--cov-report=json",
                f"--cov-report=json:{cov_file}",
                "-q",
                "--no-header",
            ]
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
            )

            if cov_file.exists():
                with open(cov_file) as f:
                    data = json.load(f)
                covered = set()
                for filename, file_data in data.get("files", {}).items():
                    # Skip test files
                    if "test_" in filename or "conftest" in filename:
                        continue
                    for line in file_data.get("executed_lines", []):
                        covered.add(f"{filename}:{line}")
                coverage_data[test_id] = covered

    return coverage_data


def compute_jaccard_similarity(set1: set[str], set2: set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union else 0.0


def find_overlap_candidates(
    coverage_data: dict[str, set[str]], min_similarity: float = 0.95
) -> list[tuple[str, str, float]]:
    """Find pairs of tests in the same class with high coverage overlap."""
    # Group tests by class
    class_tests: dict[str, list[str]] = {}
    for test_id in coverage_data:
        # Extract class name from test_id (e.g., "file.py::TestClass::test_method")
        parts = test_id.split("::")
        if len(parts) >= 2:
            class_name = parts[1] if len(parts) >= 2 else ""
            file_class = f"{parts[0]}::{class_name}"
            if file_class not in class_tests:
                class_tests[file_class] = []
            class_tests[file_class].append(test_id)

    # Find high-overlap pairs within each class
    high_overlap: list[tuple[str, str, float]] = []
    for class_name, tests in class_tests.items():
        if len(tests) < 2:
            continue
        for t1, t2 in combinations(tests, 2):
            cov1 = coverage_data.get(t1, set())
            cov2 = coverage_data.get(t2, set())
            similarity = compute_jaccard_similarity(cov1, cov2)
            if similarity >= min_similarity:
                high_overlap.append((t1, t2, similarity))

    return sorted(high_overlap, key=lambda x: (-x[2], x[0]))


def group_parametrization_candidates(
    overlapping_pairs: list[tuple[str, str, float]],
) -> dict[str, list[str]]:
    """Group tests that can be parametrized together.

    Uses union-find to group tests with identical coverage.
    """
    if not overlapping_pairs:
        return {}

    # Filter to only 100% overlap pairs
    perfect_pairs = [(t1, t2) for t1, t2, sim in overlapping_pairs if sim >= 0.999]

    # Union-find
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        if x not in parent:
            parent[x] = x
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x: str, y: str) -> None:
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for t1, t2 in perfect_pairs:
        union(t1, t2)

    # Group by root
    groups: dict[str, list[str]] = {}
    for test in parent:
        root = find(test)
        if root not in groups:
            groups[root] = []
        groups[root].append(test)

    # Only return groups with 2+ tests
    return {k: sorted(v) for k, v in groups.items() if len(v) >= 2}


def run_find_overlap(
    project_root: Path,
    min_similarity: float = 0.95,
    show_pairs: bool = False,
    packages: list[str] | None = None,
) -> None:
    """Find tests with overlapping coverage for potential consolidation.

    Args:
        project_root: Root directory of the project.
        min_similarity: Minimum Jaccard similarity to report (0-1).
        show_pairs: If True, show all overlapping pairs instead of groups.
        packages: List of package paths to analyze (e.g., ["src/djb/cli"]).

    Collects per-test coverage data and identifies tests in the same class
    that cover the same code paths. These are candidates for consolidation
    using @pytest.mark.parametrize.
    """
    logger.info(f"Analyzing test coverage overlap in {project_root}")

    coverage_data = collect_per_test_coverage(project_root, packages)
    logger.info(f"Collected coverage for {len(coverage_data)} tests")

    overlapping = find_overlap_candidates(coverage_data, min_similarity)
    logger.info(f"Found {len(overlapping)} test pairs with ≥{min_similarity:.0%} overlap")

    if show_pairs:
        click.echo("\n=== Test Pairs with High Coverage Overlap ===\n")
        for t1, t2, sim in overlapping[:50]:  # Limit output
            click.echo(f"  {sim:.1%}: {t1}")
            click.echo(f"         {t2}")
            click.echo()
        if len(overlapping) > 50:
            click.echo(f"  ... and {len(overlapping) - 50} more pairs")
    else:
        groups = group_parametrization_candidates(overlapping)

        if not groups:
            click.echo("\nNo parametrization candidates found (need 100% overlap).")
            return

        click.echo("\n=== Parametrization Candidates ===")
        click.echo("Tests with 100% identical coverage that could use @pytest.mark.parametrize:\n")

        total_tests = 0
        for i, (_, tests) in enumerate(sorted(groups.items(), key=lambda x: -len(x[1])), 1):
            # Get the test class name
            class_name = tests[0].split("::")[1] if "::" in tests[0] else "Unknown"
            click.echo(f"{i}. {class_name} ({len(tests)} tests → 1 parametrized):")
            for test in tests:
                method = test.split("::")[-1]
                click.echo(f"   - {method}")
            click.echo()
            total_tests += len(tests)

        savings = total_tests - len(groups)
        click.echo(f"Total: {total_tests} tests could become {len(groups)} parametrized tests")
        click.echo(f"Potential reduction: {savings} tests")
