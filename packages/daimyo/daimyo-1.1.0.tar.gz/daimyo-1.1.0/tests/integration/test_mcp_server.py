"""Integration tests for MCP server."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from daimyo.domain import (
    Category,
    CategoryKey,
    MergedScope,
    Rule,
    RuleSet,
    RuleType,
    Scope,
    ScopeMetadata,
    ScopeNotFoundError,
)
from daimyo.presentation.mcp import server


class TestMCPServer:
    """Test suite for MCP server tools."""

    @pytest.fixture
    def sample_merged_scope(self):
        """Create sample merged scope for testing."""
        metadata = ScopeMetadata(
            name="test-scope", description="Test scope", parent=None, tags={"type": "test"}
        )

        commandments = RuleSet()
        cmd_cat = Category(key=CategoryKey.from_string("python"), when="When writing Python")
        cmd_cat.add_rule(Rule("Use type hints", RuleType.COMMANDMENT))
        cmd_cat.add_rule(Rule("Follow PEP 8", RuleType.COMMANDMENT))
        commandments.add_category(cmd_cat)

        suggestions = RuleSet()
        sug_cat = Category(key=CategoryKey.from_string("python"), when="When writing Python")
        sug_cat.add_rule(Rule("Consider dataclasses", RuleType.SUGGESTION))
        suggestions.add_category(sug_cat)

        return MergedScope(
            metadata=metadata,
            commandments=commandments,
            suggestions=suggestions,
            sources=["local"],
        )

    @patch("daimyo.presentation.mcp.server.get_container")
    def test_get_rules_success(self, mock_get_container, sample_merged_scope):
        """Test get_rules returns formatted rules."""
        mock_container = Mock()
        mock_scope_service = Mock()
        mock_scope_service.resolve_scope.return_value = sample_merged_scope

        mock_container.scope_service.return_value = mock_scope_service
        mock_get_container.return_value = mock_container

        result = server.get_rules("test-scope")

        assert isinstance(result, str)
        assert "test-scope" in result.lower() or "Test scope" in result
        assert len(result) > 0
        mock_scope_service.resolve_scope.assert_called_once_with("test-scope")

    @patch("daimyo.presentation.mcp.server.get_container")
    def test_get_rules_with_categories(self, mock_get_container, sample_merged_scope):
        """Test get_rules with category filtering."""
        mock_container = Mock()
        mock_scope_service = Mock()
        mock_rule_service = Mock()

        mock_scope_service.resolve_scope.return_value = sample_merged_scope
        mock_rule_service.filter_categories.return_value = RuleSet()

        mock_container.scope_service.return_value = mock_scope_service
        mock_container.rule_service.return_value = mock_rule_service
        mock_get_container.return_value = mock_container

        result = server.get_rules("test-scope", categories="python.web,python.testing")

        assert isinstance(result, str)
        mock_rule_service.filter_categories.assert_called()

    @patch("daimyo.presentation.mcp.server.get_container")
    def test_get_rules_scope_not_found(self, mock_get_container):
        """Test get_rules handles ScopeNotFoundError."""
        mock_container = Mock()
        mock_scope_service = Mock()
        mock_scope_service.resolve_scope.side_effect = ScopeNotFoundError("test-scope")

        mock_container.scope_service.return_value = mock_scope_service
        mock_get_container.return_value = mock_container

        result = server.get_rules("nonexistent")

        assert "not found" in result.lower()
        assert "nonexistent" in result

    @patch("daimyo.presentation.mcp.server.get_container")
    def test_get_rules_unexpected_error(self, mock_get_container):
        """Test get_rules handles unexpected errors."""
        mock_container = Mock()
        mock_scope_service = Mock()
        mock_scope_service.resolve_scope.side_effect = Exception("Unexpected error")

        mock_container.scope_service.return_value = mock_scope_service
        mock_get_container.return_value = mock_container

        result = server.get_rules("test-scope")

        assert "error" in result.lower()

    @patch("daimyo.presentation.mcp.server.get_container")
    def test_list_scopes_success(self, mock_get_container):
        """Test list_scopes returns formatted list."""
        mock_container = Mock()
        mock_repo = Mock()
        mock_repo.list_scopes.return_value = ["scope-a", "scope-b", "scope-c"]

        mock_container.scope_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container

        result = server.list_scopes()

        assert isinstance(result, str)
        assert "scope-a" in result
        assert "scope-b" in result
        assert "scope-c" in result
        mock_repo.list_scopes.assert_called_once()

    @patch("daimyo.presentation.mcp.server.get_container")
    def test_list_scopes_empty(self, mock_get_container):
        """Test list_scopes with no scopes."""
        mock_container = Mock()
        mock_repo = Mock()
        mock_repo.list_scopes.return_value = []

        mock_container.scope_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container

        result = server.list_scopes()

        assert "No scopes found" in result

    @patch("daimyo.presentation.mcp.server.get_container")
    def test_list_scopes_error(self, mock_get_container):
        """Test list_scopes handles errors."""
        mock_container = Mock()
        mock_repo = Mock()
        mock_repo.list_scopes.side_effect = Exception("Error listing scopes")

        mock_container.scope_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container

        result = server.list_scopes()

        assert "Error" in result

    @patch("daimyo.presentation.mcp.server.get_rules")
    def test_apply_scope_rules_success(self, mock_get_rules):
        """Test apply_scope_rules prompt template."""
        mock_get_rules.return_value = "# Test Rules\n\nRule 1\nRule 2"

        result = server.apply_scope_rules("test-scope")

        assert isinstance(result, str)
        assert "test-scope" in result
        assert "MUST rules" in result
        assert "SHOULD rules" in result
        mock_get_rules.assert_called_once_with("test-scope", None)

    @patch("daimyo.presentation.mcp.server.get_rules")
    def test_apply_scope_rules_with_categories(self, mock_get_rules):
        """Test apply_scope_rules with category filters."""
        mock_get_rules.return_value = "# Filtered Rules"

        result = server.apply_scope_rules("test-scope", categories="python.web")

        assert isinstance(result, str)
        mock_get_rules.assert_called_once_with("test-scope", "python.web")

    @patch("daimyo.presentation.mcp.server.get_rules")
    def test_apply_scope_rules_error(self, mock_get_rules):
        """Test apply_scope_rules handles errors."""
        mock_get_rules.side_effect = Exception("Error generating prompt")

        result = server.apply_scope_rules("test-scope")

        assert "Error" in result

    def test_mcp_server_instance_exists(self):
        """Test that mcp server instance exists."""
        assert server.mcp is not None
        assert hasattr(server.mcp, "name")

    def test_mcp_tools_are_registered(self):
        """Test that MCP tools are registered."""
        assert hasattr(server, "get_rules")
        assert hasattr(server, "list_scopes")
        assert callable(server.get_rules)
        assert callable(server.list_scopes)

    def test_mcp_prompts_are_registered(self):
        """Test that MCP prompts are registered."""
        assert hasattr(server, "apply_scope_rules")
        assert callable(server.apply_scope_rules)

    @patch("daimyo.presentation.mcp.server.get_container")
    def test_get_rules_formatting_includes_commandments(
        self, mock_get_container, sample_merged_scope
    ):
        """Test that get_rules output includes commandments."""
        mock_container = Mock()
        mock_scope_service = Mock()
        mock_scope_service.resolve_scope.return_value = sample_merged_scope

        mock_container.scope_service.return_value = mock_scope_service
        mock_get_container.return_value = mock_container

        result = server.get_rules("test-scope")

        assert "Use type hints" in result or "commandment" in result.lower()

    @patch("daimyo.presentation.mcp.server.get_container")
    def test_get_rules_formatting_includes_suggestions(
        self, mock_get_container, sample_merged_scope
    ):
        """Test that get_rules output includes suggestions."""
        mock_container = Mock()
        mock_scope_service = Mock()
        mock_scope_service.resolve_scope.return_value = sample_merged_scope

        mock_container.scope_service.return_value = mock_scope_service
        mock_get_container.return_value = mock_container

        result = server.get_rules("test-scope")

        assert "Consider dataclasses" in result or "suggestion" in result.lower()
