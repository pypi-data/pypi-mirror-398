"""Tests for ShardMerger component."""

from __future__ import annotations

import pytest

from daimyo.application.rule_service import RuleMergingService
from daimyo.application.scope_resolution.shard_merger import ShardMerger
from daimyo.domain import (
    Category,
    CategoryKey,
    MergedScope,
    Rule,
    RuleSet,
    RuleType,
    Scope,
    ScopeMetadata,
)


class TestShardMerger:
    """Test suite for ShardMerger."""

    @pytest.fixture
    def rule_merger(self):
        """Create RuleMergingService instance."""
        return RuleMergingService()

    @pytest.fixture
    def shard_merger(self, rule_merger):
        """Create ShardMerger instance."""
        return ShardMerger(rule_merger)

    @pytest.fixture
    def local_parent_scope(self):
        """Create local parent scope with rules."""
        metadata = ScopeMetadata(
            name="parent-scope", description="Local parent", parent=None
        )

        commandments = RuleSet()
        cat = Category(key=CategoryKey.from_string("python"), when="When writing Python")
        cat.add_rule(Rule("Use type hints", RuleType.COMMANDMENT))
        cat.add_rule(Rule("Follow PEP 8", RuleType.COMMANDMENT))
        commandments.add_category(cat)

        suggestions = RuleSet()
        sug_cat = Category(key=CategoryKey.from_string("python"), when="When writing Python")
        sug_cat.add_rule(Rule("Consider dataclasses", RuleType.SUGGESTION))
        suggestions.add_category(sug_cat)

        return Scope(
            metadata=metadata,
            commandments=commandments,
            suggestions=suggestions,
            source="local",
        )

    @pytest.fixture
    def remote_parent_scope(self):
        """Create remote parent scope with rules."""
        metadata = ScopeMetadata(
            name="parent-scope", description="Remote parent", parent=None
        )

        commandments = RuleSet()
        cat = Category(key=CategoryKey.from_string("python"), when="When writing Python")
        cat.add_rule(Rule("Use async/await", RuleType.COMMANDMENT))
        commandments.add_category(cat)

        suggestions = RuleSet()
        sug_cat = Category(key=CategoryKey.from_string("python"), when="When writing Python")
        sug_cat.add_rule(Rule("Use f-strings", RuleType.SUGGESTION))
        suggestions.add_category(sug_cat)

        return Scope(
            metadata=metadata,
            commandments=commandments,
            suggestions=suggestions,
            source="remote",
        )

    @pytest.fixture
    def child_merged_scope(self):
        """Create child merged scope."""
        metadata = ScopeMetadata(
            name="child-scope", description="Child scope", parent="parent-scope"
        )

        commandments = RuleSet()
        cat = Category(key=CategoryKey.from_string("python.web"), when="When writing web code")
        cat.add_rule(Rule("Use FastAPI", RuleType.COMMANDMENT))
        commandments.add_category(cat)

        suggestions = RuleSet()

        return MergedScope(
            metadata=metadata,
            commandments=commandments,
            suggestions=suggestions,
            sources=["local"],
        )

    @pytest.fixture
    def parent_merged_scope(self):
        """Create parent merged scope."""
        metadata = ScopeMetadata(
            name="parent-scope", description="Parent scope", parent=None
        )

        commandments = RuleSet()
        cat = Category(key=CategoryKey.from_string("python"), when="When writing Python")
        cat.add_rule(Rule("Use type hints", RuleType.COMMANDMENT))
        commandments.add_category(cat)

        suggestions = RuleSet()
        sug_cat = Category(key=CategoryKey.from_string("python"), when="When writing Python")
        sug_cat.add_rule(Rule("Consider dataclasses", RuleType.SUGGESTION))
        suggestions.add_category(sug_cat)

        return MergedScope(
            metadata=metadata,
            commandments=commandments,
            suggestions=suggestions,
            sources=["remote", "local"],
        )

    def test_merger_initialization(self, rule_merger):
        """Test ShardMerger can be initialized with RuleMergingService."""
        merger = ShardMerger(rule_merger)
        assert merger.rule_merger is rule_merger

    def test_merge_parent_shards_combines_commandments(
        self, shard_merger, local_parent_scope, remote_parent_scope
    ):
        """Test merging parent shards combines commandments from both."""
        result = shard_merger.merge_parent_shards(local_parent_scope, remote_parent_scope)

        assert result.metadata.name == "parent-scope"
        python_cat = result.commandments.get_category(CategoryKey.from_string("python"))
        assert python_cat is not None
        rules = [rule.text for rule in python_cat.rules]
        assert "Use async/await" in rules
        assert "Use type hints" in rules
        assert "Follow PEP 8" in rules

    def test_merge_parent_shards_combines_suggestions(
        self, shard_merger, local_parent_scope, remote_parent_scope
    ):
        """Test merging parent shards combines suggestions from both."""
        result = shard_merger.merge_parent_shards(local_parent_scope, remote_parent_scope)

        python_cat = result.suggestions.get_category(CategoryKey.from_string("python"))
        assert python_cat is not None
        rules = [rule.text for rule in python_cat.rules]
        assert "Use f-strings" in rules
        assert "Consider dataclasses" in rules

    def test_merge_parent_shards_uses_local_metadata(
        self, shard_merger, local_parent_scope, remote_parent_scope
    ):
        """Test merging parent shards uses local scope's metadata."""
        result = shard_merger.merge_parent_shards(local_parent_scope, remote_parent_scope)

        assert result.metadata is local_parent_scope.metadata
        assert result.metadata.description == "Local parent"

    def test_merge_parent_shards_combines_sources(
        self, shard_merger, local_parent_scope, remote_parent_scope
    ):
        """Test merging parent shards combines source strings."""
        result = shard_merger.merge_parent_shards(local_parent_scope, remote_parent_scope)

        assert result.source == "remote+local"
        assert "remote" in result.source
        assert "local" in result.source

    def test_merge_parent_shards_empty_remote(self, shard_merger, local_parent_scope):
        """Test merging when remote parent has no rules."""
        empty_remote = Scope(
            metadata=ScopeMetadata(name="parent-scope", description="Empty"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="remote",
        )

        result = shard_merger.merge_parent_shards(local_parent_scope, empty_remote)

        python_cat = result.commandments.get_category(CategoryKey.from_string("python"))
        assert python_cat is not None
        assert len(python_cat.rules) == 2

    def test_merge_parent_shards_empty_local(self, shard_merger, remote_parent_scope):
        """Test merging when local parent has no rules."""
        empty_local = Scope(
            metadata=ScopeMetadata(name="parent-scope", description="Empty"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        result = shard_merger.merge_parent_shards(empty_local, remote_parent_scope)

        python_cat = result.commandments.get_category(CategoryKey.from_string("python"))
        assert python_cat is not None
        assert len(python_cat.rules) == 1

    def test_merge_child_with_parent_combines_commandments(
        self, shard_merger, child_merged_scope, parent_merged_scope
    ):
        """Test merging child with parent combines commandments."""
        result = shard_merger.merge_child_with_parent(child_merged_scope, parent_merged_scope)

        python_cat = result.commandments.get_category(CategoryKey.from_string("python"))
        assert python_cat is not None
        rules = [rule.text for rule in python_cat.rules]
        assert "Use type hints" in rules

        web_cat = result.commandments.get_category(CategoryKey.from_string("python.web"))
        assert web_cat is not None
        rules = [rule.text for rule in web_cat.rules]
        assert "Use FastAPI" in rules

    def test_merge_child_with_parent_combines_suggestions(
        self, shard_merger, child_merged_scope, parent_merged_scope
    ):
        """Test merging child with parent combines suggestions."""
        result = shard_merger.merge_child_with_parent(child_merged_scope, parent_merged_scope)

        python_cat = result.suggestions.get_category(CategoryKey.from_string("python"))
        assert python_cat is not None
        rules = [rule.text for rule in python_cat.rules]
        assert "Consider dataclasses" in rules

    def test_merge_child_with_parent_uses_child_metadata(
        self, shard_merger, child_merged_scope, parent_merged_scope
    ):
        """Test merging child with parent uses child's metadata."""
        result = shard_merger.merge_child_with_parent(child_merged_scope, parent_merged_scope)

        assert result.metadata is child_merged_scope.metadata
        assert result.metadata.name == "child-scope"
        assert result.metadata.description == "Child scope"

    def test_merge_child_with_parent_combines_sources(
        self, shard_merger, child_merged_scope, parent_merged_scope
    ):
        """Test merging child with parent combines sources list."""
        result = shard_merger.merge_child_with_parent(child_merged_scope, parent_merged_scope)

        assert result.sources == ["remote", "local", "local"]
        assert len(result.sources) == 3

    def test_merge_child_with_parent_parent_before_child_sources(
        self, shard_merger, child_merged_scope, parent_merged_scope
    ):
        """Test parent sources come before child sources."""
        result = shard_merger.merge_child_with_parent(child_merged_scope, parent_merged_scope)

        assert result.sources[0] == "remote"
        assert result.sources[1] == "local"
        assert result.sources[2] == "local"

    def test_merge_child_with_parent_empty_parent(self, shard_merger, child_merged_scope):
        """Test merging child with empty parent."""
        empty_parent = MergedScope(
            metadata=ScopeMetadata(name="parent-scope", description="Empty"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            sources=["remote"],
        )

        result = shard_merger.merge_child_with_parent(child_merged_scope, empty_parent)

        web_cat = result.commandments.get_category(CategoryKey.from_string("python.web"))
        assert web_cat is not None
        assert len(web_cat.rules) == 1

    def test_merge_child_with_parent_empty_child(self, shard_merger, parent_merged_scope):
        """Test merging empty child with parent."""
        empty_child = MergedScope(
            metadata=ScopeMetadata(name="child-scope", description="Empty", parent="parent"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            sources=["local"],
        )

        result = shard_merger.merge_child_with_parent(empty_child, parent_merged_scope)

        python_cat = result.commandments.get_category(CategoryKey.from_string("python"))
        assert python_cat is not None
        assert len(python_cat.rules) == 1

    def test_merge_overlapping_categories(self, shard_merger):
        """Test merging when both parent and child have same category."""
        parent_metadata = ScopeMetadata(name="parent", description="Parent")
        parent_commandments = RuleSet()
        parent_cat = Category(key=CategoryKey.from_string("python"), when="Parent context")
        parent_cat.add_rule(Rule("Parent rule", RuleType.COMMANDMENT))
        parent_commandments.add_category(parent_cat)

        parent = MergedScope(
            metadata=parent_metadata,
            commandments=parent_commandments,
            suggestions=RuleSet(),
            sources=["remote"],
        )

        child_metadata = ScopeMetadata(name="child", description="Child", parent="parent")
        child_commandments = RuleSet()
        child_cat = Category(key=CategoryKey.from_string("python"), when="Child context")
        child_cat.add_rule(Rule("Child rule", RuleType.COMMANDMENT))
        child_commandments.add_category(child_cat)

        child = MergedScope(
            metadata=child_metadata,
            commandments=child_commandments,
            suggestions=RuleSet(),
            sources=["local"],
        )

        result = shard_merger.merge_child_with_parent(child, parent)

        python_cat = result.commandments.get_category(CategoryKey.from_string("python"))
        assert python_cat is not None
        rules = [rule.text for rule in python_cat.rules]
        assert "Parent rule" in rules
        assert "Child rule" in rules
        assert len(python_cat.rules) == 2

    def test_returns_scope_instance_for_parent_shards(
        self, shard_merger, local_parent_scope, remote_parent_scope
    ):
        """Test merge_parent_shards returns Scope instance."""
        result = shard_merger.merge_parent_shards(local_parent_scope, remote_parent_scope)

        assert isinstance(result, Scope)
        assert not isinstance(result, MergedScope)

    def test_returns_merged_scope_instance_for_child_parent(
        self, shard_merger, child_merged_scope, parent_merged_scope
    ):
        """Test merge_child_with_parent returns MergedScope instance."""
        result = shard_merger.merge_child_with_parent(child_merged_scope, parent_merged_scope)

        assert isinstance(result, MergedScope)
