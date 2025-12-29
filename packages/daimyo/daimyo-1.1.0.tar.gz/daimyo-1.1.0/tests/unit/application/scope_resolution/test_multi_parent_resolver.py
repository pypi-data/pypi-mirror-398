"""Tests for MultiParentResolver."""

import pytest
from unittest.mock import Mock

from daimyo.application.scope_resolution.multi_parent_resolver import MultiParentResolver
from daimyo.domain import Category, CategoryKey, MergedScope, Rule, RuleSet, RuleType, ScopeMetadata


class TestMultiParentResolver:
    """Tests for MultiParentResolver class."""

    def setup_method(self):
        """Setup for each test."""
        self.parent_resolver = Mock()
        self.shard_merger = Mock()
        self.resolver = MultiParentResolver(self.parent_resolver, self.shard_merger)

    def test_resolve_empty_parent_list(self):
        """Test resolving with empty parent list returns None."""
        result = self.resolver.resolve_multiple_parents([], set(), depth=1)

        assert result is None
        self.parent_resolver.resolve_parent.assert_not_called()

    def test_resolve_single_parent_in_list(self):
        """Test single parent in list works correctly."""
        parent_scope = self._create_merged_scope("parent1")
        self.parent_resolver.resolve_parent.return_value = parent_scope

        result = self.resolver.resolve_multiple_parents(["parent1"], {"child"}, depth=1)

        assert result == parent_scope
        self.parent_resolver.resolve_parent.assert_called_once_with("parent1", {"child"}, 1)
        self.shard_merger.merge_child_with_parent.assert_not_called()

    def test_resolve_two_parents_merge_order(self):
        """Test that first parent in list has higher priority than second."""
        parent1 = self._create_merged_scope("parent1", ["p1-source"])
        parent2 = self._create_merged_scope("parent2", ["p2-source"])
        merged = self._create_merged_scope("merged", ["p2-source", "p1-source"])

        self.parent_resolver.resolve_parent.side_effect = [parent1, parent2]
        self.shard_merger.merge_child_with_parent.return_value = merged

        result = self.resolver.resolve_multiple_parents(["parent1", "parent2"], {"child"}, 1)

        assert result == merged
        assert self.parent_resolver.resolve_parent.call_count == 2
        self.shard_merger.merge_child_with_parent.assert_called_once_with(parent1, parent2)

    def test_resolve_three_parents_merge_order(self):
        """Test merge order with three parents."""
        p1 = self._create_merged_scope("p1", ["p1"])
        p2 = self._create_merged_scope("p2", ["p2"])
        p3 = self._create_merged_scope("p3", ["p3"])

        self.parent_resolver.resolve_parent.side_effect = [p1, p2, p3]

        merged_p2_p3 = self._create_merged_scope("merged", ["p3", "p2"])
        final = self._create_merged_scope("final", ["p3", "p2", "p1"])

        self.shard_merger.merge_child_with_parent.side_effect = [merged_p2_p3, final]

        result = self.resolver.resolve_multiple_parents(["p1", "p2", "p3"], {"child"}, 1)

        assert result == final
        assert self.parent_resolver.resolve_parent.call_count == 3
        assert self.shard_merger.merge_child_with_parent.call_count == 2
        calls = self.shard_merger.merge_child_with_parent.call_args_list
        assert calls[0][0] == (p2, p3)
        assert calls[1][0] == (p1, merged_p2_p3)

    def test_resolve_parent_not_found_skips(self):
        """Test that missing parents are skipped gracefully."""
        p1 = self._create_merged_scope("p1")
        self.parent_resolver.resolve_parent.side_effect = [p1, None, None]

        result = self.resolver.resolve_multiple_parents(["p1", "p2", "p3"], {"child"}, 1)

        assert result == p1
        assert self.parent_resolver.resolve_parent.call_count == 3

    def test_resolve_all_parents_not_found(self):
        """Test when no parents are found."""
        self.parent_resolver.resolve_parent.return_value = None

        result = self.resolver.resolve_multiple_parents(["p1", "p2"], {"child"}, 1)

        assert result is None
        assert self.parent_resolver.resolve_parent.call_count == 2

    def test_resolve_with_visited_set(self):
        """Test that visited set is passed correctly."""
        p1 = self._create_merged_scope("p1")
        self.parent_resolver.resolve_parent.return_value = p1

        visited = {"child", "ancestor"}
        self.resolver.resolve_multiple_parents(["p1"], visited, depth=2)

        self.parent_resolver.resolve_parent.assert_called_once_with("p1", visited, 2)

    def _create_merged_scope(
        self, name: str, sources: list[str] | None = None
    ) -> MergedScope:
        """Helper to create a MergedScope for testing."""
        metadata = ScopeMetadata(name=name, description=f"{name} scope")
        return MergedScope(
            metadata=metadata,
            commandments=RuleSet(),
            suggestions=RuleSet(),
            sources=sources or [name],
        )


__all__ = ["TestMultiParentResolver"]
