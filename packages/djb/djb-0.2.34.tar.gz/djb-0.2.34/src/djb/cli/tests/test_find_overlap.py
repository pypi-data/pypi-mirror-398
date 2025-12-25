"""Tests for djb.cli.find_overlap module."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import click
import pytest

from djb.cli.find_overlap import (
    collect_per_test_coverage,
    compute_jaccard_similarity,
    find_overlap_candidates,
    group_parametrization_candidates,
    has_pytest_cov,
    run_find_overlap,
)


class TestComputeJaccardSimilarity:
    """Tests for the compute_jaccard_similarity function."""

    def test_identical_sets(self):
        """Test similarity of identical sets is 1.0."""
        set1 = {"a", "b", "c"}
        set2 = {"a", "b", "c"}
        assert compute_jaccard_similarity(set1, set2) == 1.0

    def test_disjoint_sets(self):
        """Test similarity of disjoint sets is 0.0."""
        set1 = {"a", "b", "c"}
        set2 = {"d", "e", "f"}
        assert compute_jaccard_similarity(set1, set2) == 0.0

    def test_partial_overlap(self):
        """Test similarity with partial overlap."""
        set1 = {"a", "b", "c"}
        set2 = {"b", "c", "d"}
        # Intersection: {b, c} = 2
        # Union: {a, b, c, d} = 4
        assert compute_jaccard_similarity(set1, set2) == 0.5

    def test_empty_first_set(self):
        """Test similarity when first set is empty."""
        set1: set[str] = set()
        set2 = {"a", "b", "c"}
        assert compute_jaccard_similarity(set1, set2) == 0.0

    def test_empty_second_set(self):
        """Test similarity when second set is empty."""
        set1 = {"a", "b", "c"}
        set2: set[str] = set()
        assert compute_jaccard_similarity(set1, set2) == 0.0

    def test_both_empty(self):
        """Test similarity when both sets are empty."""
        set1: set[str] = set()
        set2: set[str] = set()
        assert compute_jaccard_similarity(set1, set2) == 0.0

    def test_subset_relationship(self):
        """Test similarity when one set is a subset of the other."""
        set1 = {"a", "b"}
        set2 = {"a", "b", "c", "d"}
        # Intersection: 2, Union: 4
        assert compute_jaccard_similarity(set1, set2) == 0.5

    def test_single_element_sets(self):
        """Test similarity with single element sets."""
        set1 = {"a"}
        set2 = {"a"}
        assert compute_jaccard_similarity(set1, set2) == 1.0

        set1 = {"a"}
        set2 = {"b"}
        assert compute_jaccard_similarity(set1, set2) == 0.0


class TestFindOverlapCandidates:
    """Tests for the find_overlap_candidates function."""

    def test_empty_coverage_data(self):
        """Test with empty coverage data returns empty list."""
        result = find_overlap_candidates({})
        assert result == []

    def test_single_test(self):
        """Test with single test returns empty list."""
        coverage = {"test.py::TestClass::test_one": {"file.py:1", "file.py:2"}}
        result = find_overlap_candidates(coverage)
        assert result == []

    def test_tests_in_different_classes(self):
        """Test that tests in different classes are not compared."""
        coverage = {
            "test.py::TestClassA::test_one": {"file.py:1", "file.py:2"},
            "test.py::TestClassB::test_one": {"file.py:1", "file.py:2"},
        }
        result = find_overlap_candidates(coverage, min_similarity=0.95)
        # Different classes, no overlap reported
        assert result == []

    def test_high_overlap_same_class(self):
        """Test that high overlap in same class is found."""
        coverage = {
            "test.py::TestClass::test_one": {"file.py:1", "file.py:2", "file.py:3"},
            "test.py::TestClass::test_two": {"file.py:1", "file.py:2", "file.py:3"},
        }
        result = find_overlap_candidates(coverage, min_similarity=0.95)
        assert len(result) == 1
        t1, t2, sim = result[0]
        assert sim == 1.0
        assert "test_one" in t1 or "test_one" in t2
        assert "test_two" in t1 or "test_two" in t2

    def test_low_overlap_filtered_out(self):
        """Test that low overlap pairs are filtered out."""
        coverage = {
            "test.py::TestClass::test_one": {"file.py:1", "file.py:2"},
            "test.py::TestClass::test_two": {"file.py:3", "file.py:4"},
        }
        result = find_overlap_candidates(coverage, min_similarity=0.5)
        # 0% overlap, filtered out
        assert result == []

    def test_similarity_threshold(self):
        """Test similarity threshold filtering."""
        coverage = {
            "test.py::TestClass::test_one": {"a", "b", "c", "d"},
            "test.py::TestClass::test_two": {"a", "b", "c", "e"},
        }
        # Similarity = 3/5 = 0.6
        result_high = find_overlap_candidates(coverage, min_similarity=0.8)
        assert len(result_high) == 0

        result_low = find_overlap_candidates(coverage, min_similarity=0.5)
        assert len(result_low) == 1

    def test_multiple_pairs_sorted(self):
        """Test that results are sorted by similarity descending."""
        coverage = {
            "test.py::TestClass::test_a": {"1", "2", "3", "4"},
            "test.py::TestClass::test_b": {"1", "2", "3", "4"},  # 100% with test_a
            "test.py::TestClass::test_c": {"1", "2", "3", "5"},  # 75% with test_a
        }
        result = find_overlap_candidates(coverage, min_similarity=0.5)
        assert len(result) >= 1
        # First pair should have highest similarity
        if len(result) >= 2:
            assert result[0][2] >= result[1][2]

    def test_handles_missing_coverage(self):
        """Test that tests with no coverage data are handled gracefully."""
        coverage = {
            "test.py::TestClass::test_one": set(),
            "test.py::TestClass::test_two": {"file.py:1"},
        }
        # Empty set has 0 similarity, so with min_similarity=0.0 it's included
        result = find_overlap_candidates(coverage, min_similarity=0.0)
        assert len(result) == 1
        assert result[0][2] == 0.0

        # With any positive threshold, it's filtered out
        result = find_overlap_candidates(coverage, min_similarity=0.1)
        assert result == []


class TestGroupParametrizationCandidates:
    """Tests for the group_parametrization_candidates function."""

    def test_empty_input(self):
        """Test with empty list returns empty dict."""
        result = group_parametrization_candidates([])
        assert result == {}

    def test_no_perfect_overlap(self):
        """Test that pairs with <100% overlap are not grouped."""
        pairs = [
            ("test::A::one", "test::A::two", 0.95),
            ("test::B::one", "test::B::two", 0.90),
        ]
        result = group_parametrization_candidates(pairs)
        assert result == {}

    def test_perfect_overlap_pair(self):
        """Test that 100% overlap pairs are grouped."""
        pairs = [
            ("test::A::one", "test::A::two", 1.0),
        ]
        result = group_parametrization_candidates(pairs)
        assert len(result) == 1
        group = list(result.values())[0]
        assert "test::A::one" in group
        assert "test::A::two" in group

    def test_transitive_grouping(self):
        """Test that transitive relationships are grouped together."""
        pairs = [
            ("test::A::one", "test::A::two", 1.0),
            ("test::A::two", "test::A::three", 1.0),
        ]
        result = group_parametrization_candidates(pairs)
        assert len(result) == 1
        group = list(result.values())[0]
        assert len(group) == 3
        assert "test::A::one" in group
        assert "test::A::two" in group
        assert "test::A::three" in group

    def test_separate_groups(self):
        """Test that unrelated pairs form separate groups."""
        pairs = [
            ("test::A::one", "test::A::two", 1.0),
            ("test::B::one", "test::B::two", 1.0),
        ]
        result = group_parametrization_candidates(pairs)
        assert len(result) == 2

    def test_threshold_for_perfect_overlap(self):
        """Test that only 99.9%+ overlap is considered perfect."""
        pairs = [
            ("test::A::one", "test::A::two", 0.999),
            ("test::B::one", "test::B::two", 0.998),  # Below threshold
        ]
        result = group_parametrization_candidates(pairs)
        assert len(result) == 1
        group = list(result.values())[0]
        assert "test::A::one" in group


class TestHasPytestCov:
    """Tests for the has_pytest_cov function."""

    def test_pytest_cov_available(self, tmp_path: Path):
        """Test returns True when pytest-cov is available."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = has_pytest_cov(tmp_path)

        assert result is True
        mock_run.assert_called_once()

    def test_pytest_cov_not_available(self, tmp_path: Path):
        """Test returns False when pytest-cov is not available."""
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("subprocess.run", return_value=mock_result):
            result = has_pytest_cov(tmp_path)

        assert result is False

    def test_timeout_returns_false(self, tmp_path: Path):
        """Test returns False on timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="test", timeout=10)):
            result = has_pytest_cov(tmp_path)

        assert result is False

    def test_file_not_found_returns_false(self, tmp_path: Path):
        """Test returns False when uv is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = has_pytest_cov(tmp_path)

        assert result is False


class TestCollectPerTestCoverage:
    """Tests for the collect_per_test_coverage function."""

    def test_raises_when_pytest_cov_not_available(self, tmp_path: Path):
        """Test raises ClickException when pytest-cov is not available."""
        with patch("djb.cli.find_overlap.has_pytest_cov", return_value=False):
            with pytest.raises(click.ClickException) as exc_info:
                collect_per_test_coverage(tmp_path)

        assert "pytest-cov is required" in str(exc_info.value)

    def test_raises_when_test_collection_fails(self, tmp_path: Path):
        """Test raises ClickException when pytest --collect-only fails."""
        with (
            patch("djb.cli.find_overlap.has_pytest_cov", return_value=True),
            patch("djb.cli.find_overlap.subprocess.run") as mock_run,
        ):
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="Collection error",
            )

            with pytest.raises(click.ClickException) as exc_info:
                collect_per_test_coverage(tmp_path)

        assert "Failed to collect tests" in str(exc_info.value)

    def test_collects_coverage_for_each_test(self, tmp_path: Path):
        """Test collects coverage data for each test."""
        test_ids = [
            "test_module.py::TestClass::test_one",
            "test_module.py::TestClass::test_two",
        ]
        collect_output = "\n".join(test_ids) + "\n"

        # Create mock coverage JSON files
        coverage_json_one = {
            "files": {
                "src/module.py": {"executed_lines": [1, 2, 3]},
                "test_module.py": {"executed_lines": [10, 20]},  # Should be skipped
            }
        }
        coverage_json_two = {
            "files": {
                "src/module.py": {"executed_lines": [1, 2, 5]},
            }
        }

        def subprocess_side_effect(cmd, *args, **kwargs):
            # First call: collect test IDs
            if "--collect-only" in cmd:
                return Mock(returncode=0, stdout=collect_output, stderr="")
            # Subsequent calls: run individual tests with coverage
            result = Mock(returncode=0, stdout="", stderr="")
            return result

        with (
            patch("djb.cli.find_overlap.has_pytest_cov", return_value=True),
            patch("djb.cli.find_overlap.subprocess.run", side_effect=subprocess_side_effect),
            patch("tempfile.TemporaryDirectory") as mock_tmpdir,
        ):
            # Mock the temporary directory
            mock_tmpdir.return_value.__enter__.return_value = str(tmp_path)

            # Create the mock coverage files
            cov_file_0 = tmp_path / "cov_0.json"
            cov_file_1 = tmp_path / "cov_1.json"
            cov_file_0.write_text(json.dumps(coverage_json_one))
            cov_file_1.write_text(json.dumps(coverage_json_two))

            result = collect_per_test_coverage(tmp_path)

        # Verify coverage was collected
        assert len(result) == 2
        assert test_ids[0] in result
        assert test_ids[1] in result

        # Verify test files are excluded from coverage
        for test_id, covered in result.items():
            for line in covered:
                assert "test_" not in line
                assert "conftest" not in line

    def test_uses_default_packages_when_not_specified(self, tmp_path: Path):
        """Test uses ['src'] as default packages."""
        with (
            patch("djb.cli.find_overlap.has_pytest_cov", return_value=True),
            patch("djb.cli.find_overlap.subprocess.run") as mock_run,
            patch("tempfile.TemporaryDirectory") as mock_tmpdir,
        ):
            mock_run.return_value = Mock(
                returncode=0,
                stdout="test.py::test_one\n",
                stderr="",
            )
            mock_tmpdir.return_value.__enter__.return_value = str(tmp_path)

            collect_per_test_coverage(tmp_path)

        # Check that the coverage command includes --cov=<project>/src
        calls = mock_run.call_args_list
        # Find the coverage run call (not the collect-only call)
        for call in calls:
            cmd = call[0][0]
            if "--cov-report=json" in cmd:
                cov_args = [arg for arg in cmd if arg.startswith("--cov=")]
                assert len(cov_args) == 1
                assert cov_args[0].endswith("src")

    def test_uses_custom_packages_when_specified(self, tmp_path: Path):
        """Test uses specified packages for coverage."""
        custom_packages = ["src/djb/cli", "src/djb/core"]

        with (
            patch("djb.cli.find_overlap.has_pytest_cov", return_value=True),
            patch("djb.cli.find_overlap.subprocess.run") as mock_run,
            patch("tempfile.TemporaryDirectory") as mock_tmpdir,
        ):
            mock_run.return_value = Mock(
                returncode=0,
                stdout="test.py::test_one\n",
                stderr="",
            )
            mock_tmpdir.return_value.__enter__.return_value = str(tmp_path)

            collect_per_test_coverage(tmp_path, packages=custom_packages)

        # Check that the coverage command includes --cov for each package
        calls = mock_run.call_args_list
        for call in calls:
            cmd = call[0][0]
            if "--cov-report=json" in cmd:
                cov_args = [arg for arg in cmd if arg.startswith("--cov=")]
                assert len(cov_args) == 2

    def test_handles_empty_test_collection(self, tmp_path: Path):
        """Test handles case when no tests are collected."""
        with (
            patch("djb.cli.find_overlap.has_pytest_cov", return_value=True),
            patch("djb.cli.find_overlap.subprocess.run") as mock_run,
            patch("tempfile.TemporaryDirectory") as mock_tmpdir,
        ):
            # Return empty output (no tests)
            mock_run.return_value = Mock(
                returncode=0,
                stdout="\n",
                stderr="",
            )
            mock_tmpdir.return_value.__enter__.return_value = str(tmp_path)

            result = collect_per_test_coverage(tmp_path)

        assert result == {}

    def test_handles_missing_coverage_file(self, tmp_path: Path):
        """Test handles case when coverage file is not created for a test."""
        with (
            patch("djb.cli.find_overlap.has_pytest_cov", return_value=True),
            patch("djb.cli.find_overlap.subprocess.run") as mock_run,
            patch("tempfile.TemporaryDirectory") as mock_tmpdir,
        ):
            mock_run.return_value = Mock(
                returncode=0,
                stdout="test.py::test_one\n",
                stderr="",
            )
            mock_tmpdir.return_value.__enter__.return_value = str(tmp_path)
            # Don't create the coverage file - simulating test failure

            result = collect_per_test_coverage(tmp_path)

        # Test should not be in results since no coverage file was created
        assert "test.py::test_one" not in result

    def test_filters_tests_with_leading_spaces(self, tmp_path: Path):
        """Test filters out indented lines from test collection output."""
        # pytest --collect-only can output indented lines for parametrized test details
        collect_output = (
            "test.py::test_one\n"
            "  <Module test.py>\n"  # Indented lines should be filtered
            "test.py::test_two\n"
        )

        with (
            patch("djb.cli.find_overlap.has_pytest_cov", return_value=True),
            patch("djb.cli.find_overlap.subprocess.run") as mock_run,
            patch("tempfile.TemporaryDirectory") as mock_tmpdir,
        ):
            mock_run.return_value = Mock(
                returncode=0,
                stdout=collect_output,
                stderr="",
            )
            mock_tmpdir.return_value.__enter__.return_value = str(tmp_path)
            # Create coverage files for the valid test IDs
            (tmp_path / "cov_0.json").write_text(json.dumps({"files": {}}))
            (tmp_path / "cov_1.json").write_text(json.dumps({"files": {}}))

            result = collect_per_test_coverage(tmp_path)

        # Should have 2 tests (no indented lines)
        assert len(result) == 2


class TestRunFindOverlap:
    """Tests for the run_find_overlap function."""

    def test_calls_collect_per_test_coverage(self, tmp_path: Path):
        """Test calls collect_per_test_coverage with correct args."""
        with (
            patch("djb.cli.find_overlap.collect_per_test_coverage") as mock_collect,
            patch("djb.cli.find_overlap.find_overlap_candidates") as mock_find,
            patch("djb.cli.find_overlap.group_parametrization_candidates"),
        ):
            mock_collect.return_value = {}
            mock_find.return_value = []

            run_find_overlap(tmp_path, packages=["src/djb/cli"])

        mock_collect.assert_called_once_with(tmp_path, ["src/djb/cli"])

    def test_passes_min_similarity_to_find_overlap_candidates(self, tmp_path: Path):
        """Test passes min_similarity to find_overlap_candidates."""
        with (
            patch("djb.cli.find_overlap.collect_per_test_coverage") as mock_collect,
            patch("djb.cli.find_overlap.find_overlap_candidates") as mock_find,
            patch("djb.cli.find_overlap.group_parametrization_candidates"),
        ):
            mock_collect.return_value = {"test::one": {"a"}}
            mock_find.return_value = []

            run_find_overlap(tmp_path, min_similarity=0.8)

        mock_find.assert_called_once()
        args, kwargs = mock_find.call_args
        assert args[1] == 0.8  # min_similarity

    def test_show_pairs_outputs_overlapping_pairs(self, tmp_path: Path):
        """Test show_pairs=True outputs pairs instead of groups."""
        overlapping = [
            ("test.py::TestClass::test_one", "test.py::TestClass::test_two", 0.98),
        ]

        with (
            patch("djb.cli.find_overlap.collect_per_test_coverage") as mock_collect,
            patch("djb.cli.find_overlap.find_overlap_candidates") as mock_find,
            patch("djb.cli.find_overlap.group_parametrization_candidates") as mock_group,
            patch("click.echo") as mock_echo,
        ):
            mock_collect.return_value = {"test::one": {"a"}}
            mock_find.return_value = overlapping

            run_find_overlap(tmp_path, show_pairs=True)

        # group_parametrization_candidates should not be called when show_pairs=True
        mock_group.assert_not_called()
        # Should output the pairs
        assert mock_echo.called

    def test_groups_mode_outputs_parametrization_candidates(self, tmp_path: Path):
        """Test default mode outputs grouped parametrization candidates."""
        overlapping = [
            ("test.py::TestClass::test_one", "test.py::TestClass::test_two", 1.0),
        ]
        groups = {
            "test.py::TestClass::test_one": [
                "test.py::TestClass::test_one",
                "test.py::TestClass::test_two",
            ]
        }

        with (
            patch("djb.cli.find_overlap.collect_per_test_coverage") as mock_collect,
            patch("djb.cli.find_overlap.find_overlap_candidates") as mock_find,
            patch("djb.cli.find_overlap.group_parametrization_candidates") as mock_group,
            patch("click.echo") as mock_echo,
        ):
            mock_collect.return_value = {"test::one": {"a"}}
            mock_find.return_value = overlapping
            mock_group.return_value = groups

            run_find_overlap(tmp_path, show_pairs=False)

        mock_group.assert_called_once_with(overlapping)
        # Should output something about parametrization
        echo_calls = [str(call) for call in mock_echo.call_args_list]
        combined_output = " ".join(echo_calls)
        assert "Parametrization" in combined_output or "parametrize" in combined_output.lower()

    def test_outputs_no_candidates_message_when_groups_empty(self, tmp_path: Path):
        """Test outputs message when no parametrization candidates found."""
        with (
            patch("djb.cli.find_overlap.collect_per_test_coverage") as mock_collect,
            patch("djb.cli.find_overlap.find_overlap_candidates") as mock_find,
            patch("djb.cli.find_overlap.group_parametrization_candidates") as mock_group,
            patch("click.echo") as mock_echo,
        ):
            mock_collect.return_value = {}
            mock_find.return_value = []
            mock_group.return_value = {}

            run_find_overlap(tmp_path)

        echo_calls = [str(call) for call in mock_echo.call_args_list]
        combined_output = " ".join(echo_calls)
        assert "No parametrization candidates" in combined_output

    def test_limits_output_to_50_pairs(self, tmp_path: Path):
        """Test limits pairs output to 50 entries."""
        # Create 60 overlapping pairs
        overlapping = [
            (f"test.py::TestClass::test_{i}", f"test.py::TestClass::test_{i+1}", 0.98)
            for i in range(60)
        ]

        with (
            patch("djb.cli.find_overlap.collect_per_test_coverage") as mock_collect,
            patch("djb.cli.find_overlap.find_overlap_candidates") as mock_find,
            patch("click.echo") as mock_echo,
        ):
            mock_collect.return_value = {}
            mock_find.return_value = overlapping

            run_find_overlap(tmp_path, show_pairs=True)

        # Should mention "and X more pairs"
        echo_calls = [str(call) for call in mock_echo.call_args_list]
        combined_output = " ".join(echo_calls)
        assert "10 more pairs" in combined_output
