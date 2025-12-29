"""Tests for ScopeResolutionService."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from daimyo.application.scope_resolution import ScopeResolutionService
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
    ScopeNotFoundError,
    ScopeRepository,
)


class TestScopeResolutionService:
    """Test suite for ScopeResolutionService."""

    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        return Mock(spec=ScopeRepository)

    @pytest.fixture
    def mock_remote_client(self):
        """Create mock remote client."""
        return Mock(spec=RemoteScopeClient)

    @pytest.fixture
    def service(self, mock_repo, mock_remote_client):
        """Create service instance."""
        return ScopeResolutionService(
            local_repo=mock_repo, remote_client=mock_remote_client, max_depth=10
        )

    @pytest.fixture
    def simple_scope(self):
        """Create simple scope without parent."""
        metadata = ScopeMetadata(name="simple", description="Simple scope", parent=None)

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
    def child_scope(self):
        """Create child scope with parent."""
        metadata = ScopeMetadata(name="child", description="Child scope", parent="parent")

        commandments = RuleSet()
        cat = Category(key=CategoryKey.from_string("python.web"), when="When writing web code")
        cat.add_rule(Rule("Use FastAPI", RuleType.COMMANDMENT))
        commandments.add_category(cat)

        return Scope(
            metadata=metadata,
            commandments=commandments,
            suggestions=RuleSet(),
            source="local",
        )

    @pytest.fixture
    def parent_scope(self):
        """Create parent scope."""
        metadata = ScopeMetadata(name="parent", description="Parent scope", parent=None)

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

    def test_service_initialization(self, mock_repo, mock_remote_client):
        """Test service can be initialized."""
        service = ScopeResolutionService(
            local_repo=mock_repo, remote_client=mock_remote_client, max_depth=5
        )

        assert service.local_repo is mock_repo
        assert service.circular_detector is not None
        assert service.remote_fetcher is not None
        assert service.shard_merger is not None
        assert service.parent_resolver is not None

    def test_service_initialization_without_remote_client(self, mock_repo):
        """Test service can be initialized without remote client."""
        service = ScopeResolutionService(local_repo=mock_repo)

        assert service.local_repo is mock_repo
        assert service.circular_detector is not None

    def test_resolve_simple_scope_without_parent(
        self, service, mock_repo, mock_remote_client, simple_scope
    ):
        """Test resolving simple scope without parent."""
        mock_repo.get_scope.return_value = simple_scope
        mock_remote_client.fetch_scope.return_value = None

        result = service.resolve_scope("simple")

        assert isinstance(result, MergedScope)
        assert result.metadata.name == "simple"
        mock_repo.get_scope.assert_called_once_with("simple")

    def test_resolve_scope_not_found_raises_exception(
        self, service, mock_repo
    ):
        """Test resolving non-existent scope raises ScopeNotFoundError."""
        mock_repo.get_scope.return_value = None

        with pytest.raises(ScopeNotFoundError) as exc_info:
            service.resolve_scope("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_resolve_scope_with_parent(
        self, service, mock_repo, mock_remote_client, child_scope, parent_scope
    ):
        """Test resolving scope with parent inheritance."""
        def get_scope_side_effect(name):
            if name == "child":
                return child_scope
            elif name == "parent":
                return parent_scope
            return None

        mock_repo.get_scope.side_effect = get_scope_side_effect
        mock_remote_client.fetch_scope.return_value = None

        result = service.resolve_scope("child")

        assert result.metadata.name == "child"

        python_cat = result.commandments.get_category(CategoryKey.from_string("python"))
        assert python_cat is not None
        rules = [rule.text for rule in python_cat.rules]
        assert "Follow PEP 8" in rules

        web_cat = result.commandments.get_category(CategoryKey.from_string("python.web"))
        assert web_cat is not None
        rules = [rule.text for rule in web_cat.rules]
        assert "Use FastAPI" in rules

    def test_resolve_scope_with_missing_parent(
        self, service, mock_repo, mock_remote_client, child_scope
    ):
        """Test resolving scope when parent doesn't exist."""
        def get_scope_side_effect(name):
            if name == "child":
                return child_scope
            return None

        mock_repo.get_scope.side_effect = get_scope_side_effect
        mock_remote_client.fetch_scope.return_value = None

        result = service.resolve_scope("child")

        assert result.metadata.name == "child"

    def test_resolve_scope_circular_dependency(
        self, service, mock_repo, mock_remote_client
    ):
        """Test circular dependency detection."""
        circular_scope = Scope(
            metadata=ScopeMetadata(name="circular", description="Circular", parent="circular"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        mock_repo.get_scope.return_value = circular_scope
        mock_remote_client.fetch_scope.return_value = None

        with pytest.raises(CircularDependencyError):
            service.resolve_scope("circular")

    def test_resolve_scope_depth_exceeded(
        self, mock_repo, mock_remote_client
    ):
        """Test that depth limit is enforced."""
        service = ScopeResolutionService(
            local_repo=mock_repo, remote_client=mock_remote_client, max_depth=1
        )

        child = Scope(
            metadata=ScopeMetadata(name="child", description="Child", parent="parent"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        parent = Scope(
            metadata=ScopeMetadata(name="parent", description="Parent", parent="grandparent"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        grandparent = Scope(
            metadata=ScopeMetadata(name="grandparent", description="Grandparent", parent=None),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        def get_scope_side_effect(name):
            if name == "child":
                return child
            elif name == "parent":
                return parent
            elif name == "grandparent":
                return grandparent
            return None

        mock_repo.get_scope.side_effect = get_scope_side_effect
        mock_remote_client.fetch_scope.return_value = None

        with pytest.raises(InheritanceDepthExceededError):
            service.resolve_scope("child")

    def test_resolve_scope_three_generation_chain(
        self, service, mock_repo, mock_remote_client
    ):
        """Test resolving three-generation inheritance chain."""
        great_grandparent = Scope(
            metadata=ScopeMetadata(name="ggp", description="GGP", parent=None),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        grandparent = Scope(
            metadata=ScopeMetadata(name="gp", description="GP", parent="ggp"),
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

        child = Scope(
            metadata=ScopeMetadata(name="child", description="Child", parent="parent"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        def get_scope_side_effect(name):
            if name == "child":
                return child
            elif name == "parent":
                return parent
            elif name == "gp":
                return grandparent
            elif name == "ggp":
                return great_grandparent
            return None

        mock_repo.get_scope.side_effect = get_scope_side_effect
        mock_remote_client.fetch_scope.return_value = None

        result = service.resolve_scope("child")

        assert result.metadata.name == "child"
        assert len(result.sources) == 4

    def test_resolve_scope_caching(
        self, service, mock_repo, mock_remote_client, simple_scope
    ):
        """Test that scope resolution is cached."""
        mock_repo.get_scope.return_value = simple_scope
        mock_remote_client.fetch_scope.return_value = None

        result1 = service.resolve_scope("simple")
        result2 = service.resolve_scope("simple")

        assert result1 is result2
        mock_repo.get_scope.assert_called_once()

    def test_resolve_scope_different_scopes_not_cached_together(
        self, service, mock_repo, mock_remote_client, simple_scope
    ):
        """Test that different scopes have separate cache entries."""
        scope_a = Scope(
            metadata=ScopeMetadata(name="scope-a", description="Scope A", parent=None),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        scope_b = Scope(
            metadata=ScopeMetadata(name="scope-b", description="Scope B", parent=None),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            source="local",
        )

        def get_scope_side_effect(name):
            if name == "scope-a":
                return scope_a
            elif name == "scope-b":
                return scope_b
            return None

        mock_repo.get_scope.side_effect = get_scope_side_effect
        mock_remote_client.fetch_scope.return_value = None

        result_a = service.resolve_scope("scope-a")
        result_b = service.resolve_scope("scope-b")

        assert result_a.metadata.name == "scope-a"
        assert result_b.metadata.name == "scope-b"
        assert result_a is not result_b

    def test_resolve_scope_returns_merged_scope(
        self, service, mock_repo, mock_remote_client, simple_scope
    ):
        """Test that resolve_scope returns MergedScope instance."""
        mock_repo.get_scope.return_value = simple_scope
        mock_remote_client.fetch_scope.return_value = None

        result = service.resolve_scope("simple")

        assert isinstance(result, MergedScope)
        assert hasattr(result, "sources")

    def test_resolve_scope_preserves_metadata(
        self, service, mock_repo, mock_remote_client, simple_scope
    ):
        """Test that scope metadata is preserved."""
        mock_repo.get_scope.return_value = simple_scope
        mock_remote_client.fetch_scope.return_value = None

        result = service.resolve_scope("simple")

        assert result.metadata.name == "simple"
        assert result.metadata.description == "Simple scope"

    def test_resolve_scope_includes_sources(
        self, service, mock_repo, mock_remote_client, simple_scope
    ):
        """Test that resolved scope includes sources."""
        mock_repo.get_scope.return_value = simple_scope
        mock_remote_client.fetch_scope.return_value = None

        result = service.resolve_scope("simple")

        assert len(result.sources) > 0
        assert "local" in result.sources

    def test_resolve_scope_empty_scope_name_raises(
        self, service, mock_repo
    ):
        """Test resolving with empty scope name."""
        mock_repo.get_scope.return_value = None

        with pytest.raises(ScopeNotFoundError):
            service.resolve_scope("")

    def test_service_uses_max_depth_from_settings(
        self, mock_repo, mock_remote_client
    ):
        """Test service uses max_depth from settings when not specified."""
        service = ScopeResolutionService(
            local_repo=mock_repo, remote_client=mock_remote_client
        )

        assert service.circular_detector.max_depth > 0

    def test_service_uses_provided_max_depth(
        self, mock_repo, mock_remote_client
    ):
        """Test service uses provided max_depth parameter."""
        service = ScopeResolutionService(
            local_repo=mock_repo, remote_client=mock_remote_client, max_depth=3
        )

        assert service.circular_detector.max_depth == 3
