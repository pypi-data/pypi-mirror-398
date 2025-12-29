"""Category filtering service for scopes."""

from __future__ import annotations

from daimyo.application.rule_service import RuleMergingService
from daimyo.domain import MergedScope
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)


class CategoryFilterService:
    """Service for filtering categories in scopes."""

    def __init__(self, rule_service: RuleMergingService):
        """Initialize category filter service.

        :param rule_service: Rule merging service for filtering
        :type rule_service: RuleMergingService
        """
        self.rule_service = rule_service

    @staticmethod
    def parse_category_string(categories: str | None) -> list[str]:
        """Parse comma-separated category string into list.

        :param categories: Comma-separated category string (e.g., "python.web,python.testing")
        :type categories: str | None
        :returns: List of category filters, empty list if None
        :rtype: list[str]
        """
        if not categories:
            return []
        return [c.strip() for c in categories.split(",")]

    def apply_filters(
        self, scope: MergedScope, category_filters: list[str] | None
    ) -> MergedScope:
        """Apply category filters to a merged scope.

        Filters both commandments and suggestions by the given category prefixes.
        If no filters provided, returns scope unchanged.

        :param scope: Merged scope to filter
        :type scope: MergedScope
        :param category_filters: List of category prefix filters
        :type category_filters: list[str] | None
        :returns: Scope with filtered categories
        :rtype: MergedScope
        """
        if not category_filters:
            return scope

        logger.debug(f"Filtering scope by categories: {category_filters}")

        scope.commandments = self.rule_service.filter_categories(
            scope.commandments, category_filters
        )
        scope.suggestions = self.rule_service.filter_categories(
            scope.suggestions, category_filters
        )

        return scope

    def filter_from_string(self, scope: MergedScope, categories: str | None) -> MergedScope:
        """Parse category string and apply filters to scope.

        Convenience method combining parse_category_string and apply_filters.

        :param scope: Merged scope to filter
        :type scope: MergedScope
        :param categories: Comma-separated category string
        :type categories: str | None
        :returns: Scope with filtered categories
        :rtype: MergedScope
        """
        category_list = self.parse_category_string(categories)
        return self.apply_filters(scope, category_list)


__all__ = ["CategoryFilterService"]
