"""Category tree building utilities for formatters."""

from __future__ import annotations

from daimyo.domain import Category


class CategoryTreeBuilder:
    """Utility for building hierarchical category trees."""

    @staticmethod
    def build_tree(categories: list[Category]) -> dict[str, dict]:
        """Build a hierarchical tree from flat category list.

        :param categories: List of categories
        :type categories: list[Category]
        :returns: Nested dictionary representing category hierarchy
        :rtype: dict[str, dict]
        """
        tree: dict[str, dict] = {}

        for category in categories:
            parts = category.key.parts
            current = tree

            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {"_categories": [], "_children": {}}

                if i == len(parts) - 1:
                    current[part]["_categories"].append(category)
                else:
                    current = current[part]["_children"]

        return tree

    @staticmethod
    def merge_trees(commandments: list[Category], suggestions: list[Category]) -> dict[str, dict]:
        """Merge commandment and suggestion categories into a single tree.

        :param commandments: List of commandment categories
        :type commandments: list[Category]
        :param suggestions: List of suggestion categories
        :type suggestions: list[Category]
        :returns: Merged tree with both commandments and suggestions
        :rtype: dict[str, dict]
        """
        tree: dict[str, dict] = {}

        for category in commandments:
            parts = category.key.parts
            current = tree

            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {"_commandments": [], "_suggestions": [], "_children": {}}

                if i == len(parts) - 1:
                    current[part]["_commandments"].append(category)
                else:
                    current = current[part]["_children"]

        for category in suggestions:
            parts = category.key.parts
            current = tree

            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {"_commandments": [], "_suggestions": [], "_children": {}}

                if i == len(parts) - 1:
                    current[part]["_suggestions"].append(category)
                else:
                    current = current[part]["_children"]

        return tree

    @staticmethod
    def build_index_tree(categories: list[tuple[str, str]]) -> dict[str, dict]:
        """Build tree for index display from category key-when pairs.

        :param categories: List of (category_key, when_description) tuples
        :type categories: list[tuple[str, str]]
        :returns: Nested dictionary for rendering category index
        :rtype: dict[str, dict]
        """
        tree: dict[str, dict] = {}

        for category_key, when_desc in categories:
            parts = category_key.split(".")
            current = tree

            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {"_children": {}, "_key": ".".join(parts[: i + 1])}

                if i == len(parts) - 1:
                    current[part]["_when"] = when_desc

                current = current[part]["_children"]

        return tree


__all__ = ["CategoryTreeBuilder"]
