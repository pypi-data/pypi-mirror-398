"""Scopes API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from daimyo.application.filtering import CategoryFilterService
from daimyo.application.formatters import (
    CategoryTreeBuilder,
    JsonFormatter,
    MarkdownFormatter,
    YamlMultiDocFormatter,
)
from daimyo.application.scope_service import ScopeResolutionService
from daimyo.domain import DaimyoError, ScopeNotFoundError
from daimyo.infrastructure.logging import get_logger
from daimyo.presentation.rest.dependencies import (
    get_category_filter_service,
    get_scope_service,
)
from daimyo.presentation.rest.models import CategorySummary, ErrorResponse, IndexResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/scopes", tags=["scopes"])


def _format_index_as_markdown(
    scope_name: str, description: str, commandments: list, suggestions: list, sources: list
) -> str:
    lines = [f"# Index of rule categories for scope {scope_name}\n"]

    if description:
        lines.append(f"{description}\n")

    if sources:
        lines.append(f"**Sources**: {', '.join(sources)}\n")

    all_categories = {}
    for cat in commandments + suggestions:
        key = cat.category
        if key not in all_categories:
            all_categories[key] = cat.when

    category_list = [(key, when) for key, when in sorted(all_categories.items())]
    category_tree = CategoryTreeBuilder.build_index_tree(category_list)

    def format_tree(tree: dict, depth: int = 0) -> list[str]:
        result = []
        indent = "  " * depth

        for key, node in sorted(tree.items()):
            full_key = node["_key"]
            when_desc = node.get("_when", "")

            if when_desc:
                result.append(f"{indent}- `{full_key}`: {when_desc}")
            else:
                result.append(f"{indent}- `{full_key}`")

            children = node.get("_children", {})
            if children:
                result.extend(format_tree(children, depth + 1))

        return result

    lines.extend(format_tree(category_tree))

    return "\n".join(lines)


@router.get(
    "/{name}/index",
    response_model=None,
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "scope_name": "python-general",
                        "description": "General Python rules",
                        "commandments": [],
                        "suggestions": [],
                        "sources": ["local"]
                    }
                },
                "text/markdown": {
                    "example": "# Index of rule categories for scope python-general\n\n- `python`\n  - `python.web`: When building web applications"
                },
            }
        },
        404: {"model": ErrorResponse},
        406: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get category index for a scope",
    description=(
        "Returns a summary of all categories in the scope with their descriptions via Accept header. "
        "Supports application/json and text/markdown. "
        "Helps agents determine which categories are relevant before requesting full rules."
    ),
)
async def get_scope_index(
    request: Request,
    name: str,
    scope_service: Annotated[ScopeResolutionService, Depends(get_scope_service)],
) -> Response | IndexResponse:
    """Get category index for a scope.

    :param request: HTTP request object
    :type request: Request
    :param name: Scope name
    :type name: str
    :param scope_service: Scope resolution service
    :type scope_service: ScopeResolutionService
    :returns: Index with all categories and descriptions in JSON or Markdown format
    :rtype: Response | IndexResponse
    """
    accept_header = request.headers.get("accept", "application/json")

    format_type = "json"
    if "text/markdown" in accept_header:
        format_type = "markdown"
    elif "application/json" not in accept_header:
        raise HTTPException(
            status_code=406,
            detail="Not Acceptable. Supported media types: application/json, text/markdown",
        )

    try:
        logger.info(f"GET /api/v1/scopes/{name}/index Accept={accept_header}")
        merged_scope = scope_service.resolve_scope(name)

        commandment_summaries = [
            CategorySummary(category=str(cat.key), when=cat.when, rule_count=len(cat.rules))
            for cat in merged_scope.commandments.categories.values()
        ]

        suggestion_summaries = [
            CategorySummary(category=str(cat.key), when=cat.when, rule_count=len(cat.rules))
            for cat in merged_scope.suggestions.categories.values()
        ]

        if format_type == "markdown":
            content = _format_index_as_markdown(
                scope_name=name,
                description=merged_scope.metadata.description,
                commandments=commandment_summaries,
                suggestions=suggestion_summaries,
                sources=merged_scope.sources,
            )
            return Response(content=content, media_type="text/markdown")
        else:
            return IndexResponse(
                scope_name=name,
                description=merged_scope.metadata.description,
                commandments=commandment_summaries,
                suggestions=suggestion_summaries,
                sources=merged_scope.sources,
            )

    except ScopeNotFoundError as e:
        logger.warning(f"Scope not found: {name}")
        raise HTTPException(status_code=404, detail=str(e))
    except DaimyoError as e:
        logger.error(f"Error resolving scope {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in get_scope_index: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{name}/rules",
    response_model=None,
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "metadata": {"name": "python-general", "description": "General Python rules"},
                        "commandments": {},
                        "suggestions": {}
                    }
                },
                "application/x-yaml": {
                    "example": "---\nmetadata:\n  name: python-general\n---\ncommandments: {}\n---\nsuggestions: {}"
                },
                "text/markdown": {
                    "example": "# Rules for python-general\n\n## python\n\n- **MUST**: Use type hints\n- **SHOULD**: Add docstrings"
                },
            }
        },
        404: {"model": ErrorResponse},
        406: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get rules for a scope",
    description=(
        "Returns rules for a scope in the requested format via Accept header. "
        "Supports application/json, application/x-yaml, and text/markdown."
    ),
)
async def get_scope_rules(
    request: Request,
    name: str,
    scope_service: Annotated[ScopeResolutionService, Depends(get_scope_service)],
    filter_service: Annotated[CategoryFilterService, Depends(get_category_filter_service)],
    categories: Annotated[
        str | None,
        Query(description="Comma-separated category filters (e.g., 'python.web,python.testing')"),
    ] = None,
) -> Response | dict:
    """Get rules for a scope.

    :param request: HTTP request object
    :type request: Request
    :param name: Scope name
    :type name: str
    :param scope_service: Scope resolution service
    :type scope_service: ScopeResolutionService
    :param filter_service: Category filter service
    :type filter_service: CategoryFilterService
    :param categories: Comma-separated list of category prefixes (uses prefix matching)
    :type categories: str | None
    :returns: YAML multi-document, JSON, or Markdown with structured data
    :rtype: Response | dict
    """
    accept_header = request.headers.get("accept", "application/x-yaml")

    content_type_map = {
        "application/json": ("json", JsonFormatter, "application/json"),
        "application/x-yaml": ("yaml", YamlMultiDocFormatter, "application/x-yaml"),
        "application/yaml": ("yaml", YamlMultiDocFormatter, "application/x-yaml"),
        "text/markdown": ("markdown", MarkdownFormatter, "text/markdown"),
    }

    formatter_info = None
    for mime_type, info in content_type_map.items():
        if mime_type in accept_header:
            formatter_info = info
            break

    if formatter_info is None:
        raise HTTPException(
            status_code=406,
            detail=f"Not Acceptable. Supported media types: {', '.join(content_type_map.keys())}",
        )

    format_name, formatter_class, content_type = formatter_info

    try:
        logger.info(f"GET /api/v1/scopes/{name}/rules?categories={categories} Accept={accept_header}")

        merged_scope = scope_service.resolve_scope(name)
        merged_scope = filter_service.filter_from_string(merged_scope, categories)

        formatter = formatter_class()
        content = formatter.format(merged_scope)

        if format_name == "json":
            return content
        else:
            return Response(content=content, media_type=content_type)

    except ScopeNotFoundError as e:
        logger.warning(f"Scope not found: {name}")
        raise HTTPException(status_code=404, detail=str(e))
    except DaimyoError as e:
        logger.error(f"Error resolving scope {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in get_scope_rules: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


__all__ = ["router"]
