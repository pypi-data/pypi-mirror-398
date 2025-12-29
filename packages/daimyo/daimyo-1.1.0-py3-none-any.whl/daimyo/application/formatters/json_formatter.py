"""JSON formatter for API responses."""

from typing import Any

from daimyo.domain import MergedScope, RuleSet


class JsonFormatter:
    """Format merged scope as JSON.

    Output contains structured JSON with metadata, commandments, and suggestions.
    """

    def format(self, scope: MergedScope) -> dict[str, Any]:
        """Format merged scope as JSON-serializable dictionary.

        :param scope: The merged scope to format
        :type scope: MergedScope
        :returns: Dictionary ready for JSON serialization
        :rtype: Dict[str, Any]
        """
        return {
            "metadata": {
                "name": scope.metadata.name,
                "description": scope.metadata.description,
                "parent": scope.metadata.parent,
                "tags": scope.metadata.tags,
                "sources": scope.sources,
            },
            "commandments": self._format_ruleset(scope.commandments),
            "suggestions": self._format_ruleset(scope.suggestions),
        }

    def _format_ruleset(self, ruleset: RuleSet) -> dict[str, dict[str, Any]]:
        """Format a ruleset as flat dictionary with category keys.

        :param ruleset: The ruleset to format
        :type ruleset: RuleSet
        :returns: Dictionary mapping category keys to their data
        :rtype: Dict[str, Dict[str, Any]]
        """
        result = {}

        for category in ruleset.categories.values():
            result[str(category.key)] = {
                "when": category.when,
                "rules": [rule.text for rule in category.rules],
            }

        return result


__all__ = ["JsonFormatter"]
