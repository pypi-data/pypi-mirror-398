"""Tests for CircularDependencyDetector component."""

from __future__ import annotations

import pytest

from daimyo.application.scope_resolution.circular_dependency_detector import (
    CircularDependencyDetector,
)
from daimyo.domain import CircularDependencyError, InheritanceDepthExceededError


class TestCircularDependencyDetector:
    """Test suite for CircularDependencyDetector."""

    def test_detector_initialization(self):
        """Test detector can be initialized with max depth."""
        detector = CircularDependencyDetector(max_depth=5)
        assert detector.max_depth == 5

    def test_check_and_mark_first_scope(self):
        """Test checking and marking first scope in chain."""
        detector = CircularDependencyDetector(max_depth=10)
        visited = set()

        new_visited = detector.check_and_mark("scope-a", visited, depth=0)

        assert "scope-a" in new_visited
        assert len(new_visited) == 1
        assert visited == set()

    def test_check_and_mark_multiple_scopes(self):
        """Test checking and marking multiple scopes sequentially."""
        detector = CircularDependencyDetector(max_depth=10)
        visited = set()

        visited = detector.check_and_mark("scope-a", visited, depth=0)
        assert "scope-a" in visited

        visited = detector.check_and_mark("scope-b", visited, depth=1)
        assert "scope-a" in visited
        assert "scope-b" in visited
        assert len(visited) == 2

        visited = detector.check_and_mark("scope-c", visited, depth=2)
        assert len(visited) == 3

    def test_check_and_mark_preserves_original_visited_set(self):
        """Test that check_and_mark returns new set without modifying original."""
        detector = CircularDependencyDetector(max_depth=10)
        original_visited = {"scope-a", "scope-b"}
        original_copy = original_visited.copy()

        new_visited = detector.check_and_mark("scope-c", original_visited, depth=2)

        assert original_visited == original_copy
        assert "scope-c" in new_visited
        assert "scope-a" in new_visited
        assert "scope-b" in new_visited
        assert len(new_visited) == 3

    def test_detect_circular_dependency_direct(self):
        """Test detecting direct circular dependency (scope references itself)."""
        detector = CircularDependencyDetector(max_depth=10)
        visited = {"scope-a"}

        with pytest.raises(CircularDependencyError) as exc_info:
            detector.check_and_mark("scope-a", visited, depth=1)

        assert "scope-a" in str(exc_info.value)
        assert "Circular dependency detected" in str(exc_info.value)

    def test_detect_circular_dependency_in_chain(self):
        """Test detecting circular dependency in inheritance chain."""
        detector = CircularDependencyDetector(max_depth=10)
        visited = {"scope-a", "scope-b", "scope-c"}

        with pytest.raises(CircularDependencyError) as exc_info:
            detector.check_and_mark("scope-b", visited, depth=3)

        assert "scope-b" in str(exc_info.value)
        assert "already in chain" in str(exc_info.value)

    def test_depth_limit_not_exceeded(self):
        """Test normal operation when depth is within limits."""
        detector = CircularDependencyDetector(max_depth=5)
        visited = set()

        visited = detector.check_and_mark("scope-a", visited, depth=0)
        visited = detector.check_and_mark("scope-b", visited, depth=1)
        visited = detector.check_and_mark("scope-c", visited, depth=2)
        visited = detector.check_and_mark("scope-d", visited, depth=3)
        visited = detector.check_and_mark("scope-e", visited, depth=4)
        visited = detector.check_and_mark("scope-f", visited, depth=5)

        assert len(visited) == 6

    def test_depth_limit_exceeded(self):
        """Test that exceeding max depth raises InheritanceDepthExceededError."""
        detector = CircularDependencyDetector(max_depth=3)
        visited = set()

        visited = detector.check_and_mark("scope-a", visited, depth=0)
        visited = detector.check_and_mark("scope-b", visited, depth=1)
        visited = detector.check_and_mark("scope-c", visited, depth=2)
        visited = detector.check_and_mark("scope-d", visited, depth=3)

        with pytest.raises(InheritanceDepthExceededError) as exc_info:
            detector.check_and_mark("scope-e", visited, depth=4)

        assert "Maximum inheritance depth" in str(exc_info.value)
        assert "3" in str(exc_info.value)
        assert "exceeded" in str(exc_info.value)

    def test_depth_limit_at_boundary(self):
        """Test that depth equal to max_depth is allowed."""
        detector = CircularDependencyDetector(max_depth=2)
        visited = set()

        visited = detector.check_and_mark("scope-a", visited, depth=0)
        visited = detector.check_and_mark("scope-b", visited, depth=1)
        visited = detector.check_and_mark("scope-c", visited, depth=2)

        assert len(visited) == 3

    def test_depth_limit_just_over_boundary(self):
        """Test that depth exceeding max_depth by 1 raises error."""
        detector = CircularDependencyDetector(max_depth=2)
        visited = set()

        visited = detector.check_and_mark("scope-a", visited, depth=0)
        visited = detector.check_and_mark("scope-b", visited, depth=1)
        visited = detector.check_and_mark("scope-c", visited, depth=2)

        with pytest.raises(InheritanceDepthExceededError):
            detector.check_and_mark("scope-d", visited, depth=3)

    def test_circular_check_before_depth_check(self):
        """Test that circular dependency is checked before depth limit."""
        detector = CircularDependencyDetector(max_depth=2)
        visited = {"scope-a", "scope-b"}

        with pytest.raises(CircularDependencyError):
            detector.check_and_mark("scope-a", visited, depth=10)

    def test_empty_visited_set(self):
        """Test with empty visited set."""
        detector = CircularDependencyDetector(max_depth=5)
        visited = set()

        new_visited = detector.check_and_mark("first-scope", visited, depth=0)

        assert len(new_visited) == 1
        assert "first-scope" in new_visited

    def test_depth_zero(self):
        """Test that depth 0 always works."""
        detector = CircularDependencyDetector(max_depth=0)
        visited = set()

        new_visited = detector.check_and_mark("scope-a", visited, depth=0)

        assert "scope-a" in new_visited

    def test_depth_zero_exceeded(self):
        """Test that depth 1 with max_depth=0 raises error."""
        detector = CircularDependencyDetector(max_depth=0)
        visited = set()

        with pytest.raises(InheritanceDepthExceededError):
            detector.check_and_mark("scope-a", visited, depth=1)
