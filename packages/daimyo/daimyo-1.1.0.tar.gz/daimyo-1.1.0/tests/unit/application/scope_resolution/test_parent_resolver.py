"""Tests for ParentResolver component."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from daimyo.application.rule_service import RuleMergingService
from daimyo.application.scope_resolution.circular_dependency_detector import (
    CircularDependencyDetector,
)
from daimyo.application.scope_resolution.parent_resolver import ParentResolver
from daimyo.application.scope_resolution.remote_scope_fetcher import RemoteScopeFetcher
from daimyo.application.scope_resolution.shard_merger import ShardMerger
from daimyo.domain import (
    Category,
    CategoryKey,
    CircularDependencyError,
    InheritanceDepthExceededError,
    MergedScope,
    RemoteScopeClient,
    Rule,
    RuleSet,
    RuleType,
    Scope,
    ScopeMetadata,
    ScopeRepository,
)


class TestParentResolver:
    """Test suite for ParentResolver."""

    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        return Mock(spec=ScopeRepository)

    @pytest.fixture
    def mock_remote_client(self):
        """Create mock remote client."""
        return Mock(spec=RemoteScopeClient)

    @pytest.fixture
    def circular_detector(self):
        """Create circular dependency detector."""
        return CircularDependencyDetector(max_depth=10)

    @pytest.fixture
    def remote_fetcher(self, mock_remote_client):
        """Create remote scope fetcher."""
        return RemoteScopeFetcher(
            remote_client=mock_remote_client, master_url="https://example.com"
        )

    @pytest.fixture
    def shard_merger(self):
        """Create shard merger."""
        return ShardMerger(RuleMergingService())

    @pytest.fixture
    def parent_resolver(
        self, mock_repo, remote_fetcher, shard_merger, circular_detector
    ):
        """Create parent resolver."""
        return ParentResolver(mock_repo, remote_fetcher, shard_merger, circular_detector)

    @pytest.fixture
    def simple_parent_scope(self):
        """Create simple parent scope without grandparent."""
        metadata = ScopeMetadata(name="parent", description="Parent", parent=None)

        commandments = RuleSet()
        cat = Category(key=CategoryKey.from_string("python"), when="When writing Python")
        cat.add_rule(Rule("Use type hints", RuleType.COMMANDMENT))
        commandments.add_category(cat)

        return Scope(
            metadata=metadata,
            commandments=commandments,
            suggestions=RuleSet(),
            source="local",
        )

    @pytest.fixture
    def parent_with_grandparent_scope(self):
        """Create parent scope that has a grandparent."""
        metadata = ScopeMetadata(
            name="parent", description="Parent", parent="grandparent"
        )

        commandments = RuleSet()
        cat = Category(key=CategoryKey.from_string("python"), when="When writing Python")
        cat.add_rule(Rule("Use async/await", RuleType.COMMANDMENT))
        commandments.add_category(cat)

        return Scope(
            metadata=metadata,
            commandments=commandments,
            suggestions=RuleSet(),
            source="local",
        )

    @pytest.fixture
    def grandparent_scope(self):
        """Create grandparent scope."""
        metadata = ScopeMetadata(name="grandparent", description="Grandparent", parent=None)

        commandments = RuleSet()
        cat = Category(key=CategoryKey.from_string("python"), when="When writing Python")
        cat.add_rule(Rule("Follow PEP 8", RuleType.COMMANDMENT))
        commandments.add_category(cat)

        return Scope(
            metadata=metadata,
            commandments=commandments,
            suggestions=RuleSet(),
            source="local",
        )

    def test_resolver_initialization(
        self, mock_repo, remote_fetcher, shard_merger, circular_detector
    ):
        """Test ParentResolver can be initialized with dependencies."""
        resolver = ParentResolver(mock_repo, remote_fetcher, shard_merger, circular_detector)

        assert resolver.local_repo is mock_repo
        assert resolver.remote_fetcher is remote_fetcher
        assert resolver.shard_merger is shard_merger
        assert resolver.circular_detector is circular_detector

    def test_resolve_parent_local_only(
        self, parent_resolver, mock_repo, mock_remote_client, simple_parent_scope
    ):
        """Test resolving parent from local repository only."""
        mock_repo.get_scope.return_value = simple_parent_scope
        mock_remote_client.fetch_scope.return_value = None

        result = parent_resolver.resolve_parent("parent", set(), depth=1)

        assert result is not None
        assert isinstance(result, MergedScope)
        assert result.metadata.name == "parent"
        mock_repo.get_scope.assert_called_once_with("parent")

    def test_resolve_parent_remote_only(
        self, parent_resolver, mock_repo, mock_remote_client, simple_parent_scope
    ):
        """Test resolving parent from remote server only."""
        mock_repo.get_scope.return_value = None
        mock_remote_client.fetch_scope.return_value = simple_parent_scope

        result = parent_resolver.resolve_parent("parent", set(), depth=1)

        assert result is not None
        assert isinstance(result, MergedScope)
        assert result.metadata.name == "parent"

    def test_resolve_parent_not_found(
        self, parent_resolver, mock_repo, mock_remote_client
    ):
        """Test resolving parent that doesn't exist locally or remotely."""
        mock_repo.get_scope.return_value = None
        mock_remote_client.fetch_scope.return_value = None

        result = parent_resolver.resolve_parent("nonexistent", set(), depth=1)

        assert result is None

    def test_resolve_parent_both_sources_merges_shards(
        self, parent_resolver, mock_repo, mock_remote_client
    ):
        """Test resolving parent found in both local and remote merges shards."""
        local_scope = Scope(
            metadata=ScopeMetadata(name="parent", description="Local", parent=None),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        remote_scope = Scope(
            metadata=ScopeMetadata(name="parent", description="Remote", parent=None),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="remote",
        )

        mock_repo.get_scope.return_value = local_scope
        mock_remote_client.fetch_scope.return_value = remote_scope

        result = parent_resolver.resolve_parent("parent", set(), depth=1)

        assert result is not None
        assert "local" in result.sources or "remote" in result.sources

    def test_resolve_parent_with_grandparent(
        self,
        parent_resolver,
        mock_repo,
        mock_remote_client,
        parent_with_grandparent_scope,
        grandparent_scope,
    ):
        """Test resolving parent that has a grandparent."""
        def get_scope_side_effect(name):
            if name == "parent":
                return parent_with_grandparent_scope
            elif name == "grandparent":
                return grandparent_scope
            return None

        mock_repo.get_scope.side_effect = get_scope_side_effect
        mock_remote_client.fetch_scope.return_value = None

        result = parent_resolver.resolve_parent("parent", set(), depth=1)

        assert result is not None
        assert result.metadata.name == "parent"

        python_cat = result.commandments.get_category(CategoryKey.from_string("python"))
        assert python_cat is not None
        rules = [rule.text for rule in python_cat.rules]
        assert "Use async/await" in rules
        assert "Follow PEP 8" in rules

    def test_resolve_parent_three_generation_chain(
        self, parent_resolver, mock_repo, mock_remote_client
    ):
        """Test resolving three-generation inheritance chain."""
        great_grandparent = Scope(
            metadata=ScopeMetadata(name="great-gp", description="GGP", parent=None),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        grandparent = Scope(
            metadata=ScopeMetadata(name="gp", description="GP", parent="great-gp"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        parent = Scope(
            metadata=ScopeMetadata(name="parent", description="Parent", parent="gp"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        def get_scope_side_effect(name):
            if name == "parent":
                return parent
            elif name == "gp":
                return grandparent
            elif name == "great-gp":
                return great_grandparent
            return None

        mock_repo.get_scope.side_effect = get_scope_side_effect
        mock_remote_client.fetch_scope.return_value = None

        result = parent_resolver.resolve_parent("parent", set(), depth=1)

        assert result is not None
        assert result.metadata.name == "parent"
        assert len(result.sources) > 1

    def test_resolve_parent_checks_circular_dependency(
        self, parent_resolver, mock_repo, mock_remote_client
    ):
        """Test that circular dependency is detected."""
        circular_scope = Scope(
            metadata=ScopeMetadata(name="parent", description="Circular", parent="parent"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        mock_repo.get_scope.return_value = circular_scope
        mock_remote_client.fetch_scope.return_value = None

        visited = {"parent"}

        with pytest.raises(CircularDependencyError):
            parent_resolver.resolve_parent("parent", visited, depth=1)

    def test_resolve_parent_enforces_depth_limit(
        self, mock_repo, remote_fetcher, shard_merger, mock_remote_client
    ):
        """Test that depth limit is enforced."""
        shallow_detector = CircularDependencyDetector(max_depth=2)
        resolver = ParentResolver(mock_repo, remote_fetcher, shard_merger, shallow_detector)

        simple_scope = Scope(
            metadata=ScopeMetadata(name="parent", description="Parent", parent=None),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        mock_repo.get_scope.return_value = simple_scope
        mock_remote_client.fetch_scope.return_value = None

        with pytest.raises(InheritanceDepthExceededError):
            resolver.resolve_parent("parent", set(), depth=10)

    def test_resolve_parent_updates_visited_set(
        self, parent_resolver, mock_repo, mock_remote_client, simple_parent_scope
    ):
        """Test that visited set is updated during resolution."""
        mock_repo.get_scope.return_value = simple_parent_scope
        mock_remote_client.fetch_scope.return_value = None

        initial_visited = {"child"}
        result = parent_resolver.resolve_parent("parent", initial_visited, depth=1)

        assert result is not None
        assert initial_visited == {"child"}

    def test_resolve_parent_grandparent_not_found(
        self,
        parent_resolver,
        mock_repo,
        mock_remote_client,
        parent_with_grandparent_scope,
    ):
        """Test resolving parent when grandparent doesn't exist."""
        mock_repo.get_scope.side_effect = lambda name: (
            parent_with_grandparent_scope if name == "parent" else None
        )
        mock_remote_client.fetch_scope.return_value = None

        result = parent_resolver.resolve_parent("parent", set(), depth=1)

        assert result is not None
        assert result.metadata.name == "parent"

    def test_resolve_parent_empty_visited_set(
        self, parent_resolver, mock_repo, mock_remote_client, simple_parent_scope
    ):
        """Test resolving parent with empty visited set."""
        mock_repo.get_scope.return_value = simple_parent_scope
        mock_remote_client.fetch_scope.return_value = None

        result = parent_resolver.resolve_parent("parent", set(), depth=0)

        assert result is not None

    def test_resolve_parent_creates_merged_scope(
        self, parent_resolver, mock_repo, mock_remote_client, simple_parent_scope
    ):
        """Test that resolve_parent returns MergedScope instance."""
        mock_repo.get_scope.return_value = simple_parent_scope
        mock_remote_client.fetch_scope.return_value = None

        result = parent_resolver.resolve_parent("parent", set(), depth=1)

        assert isinstance(result, MergedScope)
        assert hasattr(result, "sources")

    def test_resolve_parent_preserves_metadata(
        self, parent_resolver, mock_repo, mock_remote_client, simple_parent_scope
    ):
        """Test that parent metadata is preserved."""
        mock_repo.get_scope.return_value = simple_parent_scope
        mock_remote_client.fetch_scope.return_value = None

        result = parent_resolver.resolve_parent("parent", set(), depth=1)

        assert result.metadata.name == "parent"
        assert result.metadata.description == "Parent"

    def test_resolve_parent_calls_circular_detector_first(
        self, mock_repo, remote_fetcher, shard_merger, mock_remote_client
    ):
        """Test that circular detector is called before loading scopes."""
        mock_detector = Mock(spec=CircularDependencyDetector)
        mock_detector.check_and_mark.side_effect = CircularDependencyError("Circular")

        resolver = ParentResolver(mock_repo, remote_fetcher, shard_merger, mock_detector)

        with pytest.raises(CircularDependencyError):
            resolver.resolve_parent("parent", {"parent"}, depth=1)

        mock_repo.get_scope.assert_not_called()

    def test_resolve_parent_mixed_sources_in_chain(
        self, parent_resolver, mock_repo, mock_remote_client
    ):
        """Test resolving chain with mixed local and remote sources."""
        local_parent = Scope(
            metadata=ScopeMetadata(name="parent", description="Parent", parent="gp"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        remote_grandparent = Scope(
            metadata=ScopeMetadata(name="gp", description="GP", parent=None),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="remote",
        )

        def get_scope_side_effect(name):
            if name == "parent":
                return local_parent
            return None

        def fetch_scope_side_effect(url, name):
            if name == "gp":
                return remote_grandparent
            return None

        mock_repo.get_scope.side_effect = get_scope_side_effect
        mock_remote_client.fetch_scope.side_effect = fetch_scope_side_effect

        result = parent_resolver.resolve_parent("parent", set(), depth=1)

        assert result is not None
        assert result.metadata.name == "parent"
