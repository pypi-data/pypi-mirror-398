"""Tests for djb.cli.find_overlap module."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from djb.cli.find_overlap import (
    compute_jaccard_similarity,
    find_overlap_candidates,
    group_parametrization_candidates,
    has_pytest_cov,
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
