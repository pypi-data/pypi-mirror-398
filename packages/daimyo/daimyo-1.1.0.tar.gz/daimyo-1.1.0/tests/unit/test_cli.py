"""Tests for CLI commands."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from daimyo.__main__ import app
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


class TestCLI:
    """Test suite for CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def sample_scope(self):
        """Create sample scope for testing."""
        metadata = ScopeMetadata(
            name="test-scope",
            description="Test scope",
            parent="parent-scope",
            tags={"type": "test"},
        )

        commandments = RuleSet()
        cmd_cat = Category(key=CategoryKey.from_string("python"), when="When writing Python")
        cmd_cat.add_rule(Rule("Use type hints", RuleType.COMMANDMENT))
        commandments.add_category(cmd_cat)

        suggestions = RuleSet()

        return MergedScope(
            metadata=metadata,
            commandments=commandments,
            suggestions=suggestions,
            sources=["local"],
        )

    def test_cli_version(self, runner):
        """Test version command."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "daimyo version" in result.stdout

    def test_cli_help(self, runner):
        """Test help command."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Daimyo" in result.stdout

    @patch("daimyo.__main__.get_container")
    def test_list_scopes_success(self, mock_get_container, runner):
        """Test list-scopes command with scopes."""
        mock_container = Mock()
        mock_repo = Mock()
        mock_repo.list_scopes.return_value = ["scope-a", "scope-b", "scope-c"]

        mock_container.scope_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container

        result = runner.invoke(app, ["list-scopes"])

        assert result.exit_code == 0
        assert "scope-a" in result.stdout
        assert "scope-b" in result.stdout
        assert "scope-c" in result.stdout

    @patch("daimyo.__main__.get_container")
    def test_list_scopes_empty(self, mock_get_container, runner):
        """Test list-scopes with no scopes."""
        mock_container = Mock()
        mock_repo = Mock()
        mock_repo.list_scopes.return_value = []

        mock_container.scope_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container

        result = runner.invoke(app, ["list-scopes"])

        assert result.exit_code == 0
        assert "No scopes found" in result.stdout

    @patch("daimyo.__main__.get_container")
    def test_list_scopes_error(self, mock_get_container, runner):
        """Test list-scopes handles errors."""
        mock_container = Mock()
        mock_repo = Mock()
        mock_repo.list_scopes.side_effect = Exception("Error listing")

        mock_container.scope_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container

        result = runner.invoke(app, ["list-scopes"])

        assert result.exit_code != 0

    @patch("daimyo.__main__.get_container")
    def test_show_scope_success(self, mock_get_container, runner, sample_scope):
        """Test show command with existing scope."""
        mock_container = Mock()
        mock_repo = Mock()
        mock_repo.get_scope.return_value = sample_scope

        mock_container.scope_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container

        result = runner.invoke(app, ["show", "test-scope"])

        assert result.exit_code == 0
        assert "test-scope" in result.stdout
        assert "Test scope" in result.stdout

    @patch("daimyo.__main__.get_container")
    def test_show_scope_not_found(self, mock_get_container, runner):
        """Test show command with non-existent scope."""
        mock_container = Mock()
        mock_repo = Mock()
        mock_repo.get_scope.return_value = None

        mock_container.scope_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container

        result = runner.invoke(app, ["show", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    @patch("daimyo.__main__.get_container")
    def test_show_scope_with_parent(self, mock_get_container, runner, sample_scope):
        """Test show displays parent information."""
        mock_container = Mock()
        mock_repo = Mock()
        mock_repo.get_scope.return_value = sample_scope

        mock_container.scope_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container

        result = runner.invoke(app, ["show", "test-scope"])

        assert result.exit_code == 0
        assert "Parent" in result.stdout
        assert "parent-scope" in result.stdout

    @patch("daimyo.__main__.get_container")
    def test_show_scope_with_tags(self, mock_get_container, runner, sample_scope):
        """Test show displays tags."""
        mock_container = Mock()
        mock_repo = Mock()
        mock_repo.get_scope.return_value = sample_scope

        mock_container.scope_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container

        result = runner.invoke(app, ["show", "test-scope"])

        assert result.exit_code == 0
        assert "Tags" in result.stdout

    @patch("daimyo.__main__.get_container")
    def test_show_scope_commandments_count(self, mock_get_container, runner, sample_scope):
        """Test show displays commandments count."""
        mock_container = Mock()
        mock_repo = Mock()
        mock_repo.get_scope.return_value = sample_scope

        mock_container.scope_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container

        result = runner.invoke(app, ["show", "test-scope"])

        assert result.exit_code == 0
        assert "Commandments" in result.stdout

    @patch("daimyo.__main__.get_container")
    def test_show_scope_suggestions_count(self, mock_get_container, runner, sample_scope):
        """Test show displays suggestions count."""
        mock_container = Mock()
        mock_repo = Mock()
        mock_repo.get_scope.return_value = sample_scope

        mock_container.scope_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container

        result = runner.invoke(app, ["show", "test-scope"])

        assert result.exit_code == 0
        assert "Suggestions" in result.stdout

    @patch("daimyo.__main__.get_container")
    def test_show_scope_error(self, mock_get_container, runner):
        """Test show handles errors."""
        mock_container = Mock()
        mock_repo = Mock()
        mock_repo.get_scope.side_effect = Exception("Error retrieving scope")

        mock_container.scope_repository.return_value = mock_repo
        mock_get_container.return_value = mock_container

        result = runner.invoke(app, ["show", "test-scope"])

        assert result.exit_code == 1
        assert "Error" in result.stdout

    def test_show_requires_scope_name(self, runner):
        """Test show command requires scope name argument."""
        result = runner.invoke(app, ["show"])

        assert result.exit_code != 0

    def test_serve_command_exists(self, runner):
        """Test serve command is available."""
        result = runner.invoke(app, ["serve", "--help"])

        assert result.exit_code == 0
        assert "REST API server" in result.stdout or "serve" in result.stdout.lower()

    def test_mcp_command_exists(self, runner):
        """Test mcp command is available."""
        result = runner.invoke(app, ["mcp", "--help"])

        assert result.exit_code == 0
        assert "MCP" in result.stdout or "mcp" in result.stdout.lower()

    @patch("daimyo.__main__.uvicorn.run")
    @patch("daimyo.__main__.setup_logging")
    def test_serve_command_with_defaults(self, mock_setup_logging, mock_uvicorn_run, runner):
        """Test serve command uses default settings."""
        result = runner.invoke(app, ["serve"], catch_exceptions=False)

        mock_setup_logging.assert_called_once()
        mock_uvicorn_run.assert_called_once()

    @patch("daimyo.__main__.uvicorn.run")
    @patch("daimyo.__main__.setup_logging")
    def test_serve_command_with_custom_host_port(
        self, mock_setup_logging, mock_uvicorn_run, runner
    ):
        """Test serve command with custom host and port."""
        result = runner.invoke(
            app, ["serve", "--host", "0.0.0.0", "--port", "9000"], catch_exceptions=False
        )

        mock_uvicorn_run.assert_called_once()
        call_args = mock_uvicorn_run.call_args
        assert call_args.kwargs["host"] == "0.0.0.0"
        assert call_args.kwargs["port"] == 9000

    @patch("daimyo.__main__.uvicorn.run")
    @patch("daimyo.__main__.setup_logging")
    def test_serve_command_with_reload(
        self, mock_setup_logging, mock_uvicorn_run, runner
    ):
        """Test serve command with reload flag."""
        result = runner.invoke(app, ["serve", "--reload"], catch_exceptions=False)

        mock_uvicorn_run.assert_called_once()
        call_args = mock_uvicorn_run.call_args
        assert call_args.kwargs["reload"] is True

    def test_app_has_name(self):
        """Test CLI app has name."""
        assert hasattr(app.info, "name")
        assert app.info.name == "daimyo"

    def test_app_has_help(self):
        """Test CLI app has help text."""
        assert hasattr(app.info, "help")
        assert "Daimyo" in app.info.help
