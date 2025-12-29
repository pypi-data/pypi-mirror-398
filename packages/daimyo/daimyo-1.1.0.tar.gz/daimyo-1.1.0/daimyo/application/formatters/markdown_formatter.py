"""Markdown formatter for MCP API responses."""

from daimyo.application.formatters.tree_builder import CategoryTreeBuilder
from daimyo.domain import Category, MergedScope, RuleSet


class MarkdownFormatter:
    """Format merged scope as markdown with hierarchy and MUST/SHOULD markers.

    Features:
    - Nested headings for category hierarchy (## python, ### web, #### testing)
    - MUST markers for commandments, SHOULD markers for suggestions
    - Include 'when' descriptions for each category
    """

    def format(self, scope: MergedScope) -> str:
        """Format merged scope as markdown.

        :param scope: The merged scope to format
        :type scope: MergedScope
        :returns: Markdown-formatted string
        :rtype: str
        """
        lines = []

        lines.append(f"# Rules for {scope.metadata.name}\n")
        if scope.metadata.description:
            lines.append(f"{scope.metadata.description}\n")

        merged_tree = CategoryTreeBuilder.merge_trees(
            list(scope.commandments.categories.values()),
            list(scope.suggestions.categories.values())
        )

        lines.extend(self._format_merged_tree(merged_tree, depth=2))

        return "\n".join(lines)

    def _format_merged_tree(
        self, tree: dict[str, dict], depth: int, path: str = ""
    ) -> list[str]:
        """Format merged category tree with both MUST and SHOULD rules.

        :param tree: Merged category tree
        :type tree: Dict[str, Dict]
        :param depth: Current heading depth
        :type depth: int
        :param path: Current category path
        :type path: str
        :returns: List of markdown lines
        :rtype: List[str]
        """
        lines = []

        for key, node in sorted(tree.items()):
            heading = "#" * depth
            current_path = f"{path}.{key}" if path else key
            lines.append(f"{heading} {key}\n")

            commandments = node.get("_commandments", [])
            suggestions = node.get("_suggestions", [])

            when_description = None
            for category in commandments:
                if category.when:
                    when_description = category.when
                    break
            if not when_description:
                for category in suggestions:
                    if category.when:
                        when_description = category.when
                        break

            if when_description:
                lines.append(f"*{when_description}*\n")

            for category in commandments:
                for rule in category.rules:
                    lines.append(f"- **MUST**: {rule.text}")

            for category in suggestions:
                for rule in category.rules:
                    lines.append(f"- **SHOULD**: {rule.text}")

            if commandments or suggestions:
                lines.append("")

            children = node.get("_children", {})
            if children:
                lines.extend(self._format_merged_tree(children, depth + 1, current_path))

        return lines

    def _format_ruleset_markdown(self, ruleset: RuleSet, marker: str) -> str:
        """Format a ruleset as markdown with hierarchical headings.

        :param ruleset: The ruleset to format
        :type ruleset: RuleSet
        :param marker: The marker to use (MUST or SHOULD)
        :type marker: str
        :returns: Markdown string
        :rtype: str
        """
        lines = []

        category_tree = CategoryTreeBuilder.build_tree(list(ruleset.categories.values()))

        lines.extend(self._format_tree(category_tree, marker, depth=3))

        return "\n".join(lines)

    def _format_tree(
        self, tree: dict[str, dict], marker: str, depth: int, path: str = ""
    ) -> list[str]:
        """Recursively format category tree as markdown.

        :param tree: Category tree
        :type tree: Dict[str, Dict]
        :param marker: MUST or SHOULD
        :type marker: str
        :param depth: Current heading depth
        :type depth: int
        :param path: Current category path
        :type path: str
        :returns: List of markdown lines
        :rtype: List[str]
        """
        lines = []

        for key, node in sorted(tree.items()):
            heading = "#" * depth
            current_path = f"{path}.{key}" if path else key
            lines.append(f"{heading} {key}\n")

            for category in node.get("_categories", []):
                lines.append(f"*{category.when}*\n")

                for rule in category.rules:
                    lines.append(f"- **{marker}**: {rule.text}")
                lines.append("")

            children = node.get("_children", {})
            if children:
                lines.extend(self._format_tree(children, marker, depth + 1, current_path))

        return lines


__all__ = ["MarkdownFormatter"]
