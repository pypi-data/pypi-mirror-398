"""FastMCP server for Daimyo rules."""

from fastmcp import FastMCP

from daimyo.application.formatters import MarkdownFormatter
from daimyo.domain import DaimyoError, ScopeNotFoundError
from daimyo.infrastructure.di import get_container
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)

mcp = FastMCP("Daimyo Rules Server")


@mcp.tool()
def get_rules(scope_name: str, categories: str | None = None) -> str:
    """Get rules for a scope in markdown format.

    :param scope_name: Name of the scope to retrieve (e.g., 'python-general', 'team-backend')
    :type scope_name: str
    :param categories: Optional comma-separated category filters (e.g., 'python.web,python.testing')
    :type categories: str | None
    :returns: Markdown-formatted rules with hierarchy, MUST/SHOULD markers, and descriptions
    :rtype: str

    Examples::

        get_rules("python-general")
        get_rules("team-backend", "python.web")
    """
    try:
        logger.info(f"MCP get_rules: scope={scope_name}, categories={categories}")

        container = get_container()
        scope_service = container.scope_service()
        filter_service = container.category_filter_service()

        merged_scope = scope_service.resolve_scope(scope_name)
        merged_scope = filter_service.filter_from_string(merged_scope, categories)

        formatter = MarkdownFormatter()
        result = formatter.format(merged_scope)

        logger.info(f"Successfully retrieved rules for scope '{scope_name}'")
        return result

    except ScopeNotFoundError:
        error_msg = f"Error: Scope '{scope_name}' not found"
        logger.warning(error_msg)
        return error_msg
    except DaimyoError as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.exception(error_msg)
        return error_msg


@mcp.tool()
def list_scopes() -> str:
    """List all available scopes.

    :returns: Formatted list of available scope names
    :rtype: str

    Examples::

        list_scopes()
    """
    try:
        logger.info("MCP list_scopes")
        container = get_container()
        repo = container.scope_repository()
        scopes = repo.list_scopes()

        if not scopes:
            return "No scopes found in the rules directory."

        result = "Available scopes:\n\n"
        for scope_name in scopes:
            result += f"- {scope_name}\n"

        return result

    except Exception as e:
        error_msg = f"Error listing scopes: {str(e)}"
        logger.exception(error_msg)
        return error_msg


@mcp.prompt()
def apply_scope_rules(scope_name: str, categories: str | None = None) -> str:
    """Prompt template to apply scope rules to an agent.

    :param scope_name: Name of the scope to apply
    :type scope_name: str
    :param categories: Optional comma-separated category filters
    :type categories: str | None
    :returns: Formatted prompt with rules for the agent to follow
    :rtype: str
    """
    try:
        logger.info(f"MCP apply_scope_rules: scope={scope_name}, categories={categories}")
        rules = get_rules(scope_name, categories)

        prompt = f"""You are an AI agent that must follow these rules from the '{scope_name}' scope.

{rules}

Instructions:
1. **MUST rules (Commandments)**: These are mandatory and cannot be violated
2. **SHOULD rules (Suggestions)**: These are strong recommendations you should
   follow unless you have a good reason not to

Apply these rules to all your actions, recommendations, and code generation.
When rules conflict, commandments take precedence over suggestions.
"""
        return prompt

    except Exception as e:
        error_msg = f"Error generating prompt: {str(e)}"
        logger.exception(error_msg)
        return error_msg


__all__ = ["mcp"]
