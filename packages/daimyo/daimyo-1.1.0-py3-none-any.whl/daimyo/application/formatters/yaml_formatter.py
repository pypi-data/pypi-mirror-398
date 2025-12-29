"""YAML multi-document formatter for server federation."""

from typing import Any

import yaml

from daimyo.domain import MergedScope, RuleSet


class YamlMultiDocFormatter:
    """Format merged scope as multi-document YAML.

    Output contains 3 YAML documents separated by '---':
    1. Metadata document
    2. Commandments document
    3. Suggestions document

    This format is useful for server federation where a server needs to
    parse and overlay rules from another server.
    """

    def format(self, scope: MergedScope) -> str:
        """Format merged scope as multi-document YAML.

        :param scope: The merged scope to format
        :type scope: MergedScope
        :returns: Multi-document YAML string
        :rtype: str
        """
        documents = []

        metadata_doc = {
            "metadata": {
                "name": scope.metadata.name,
                "description": scope.metadata.description,
                "parent": scope.metadata.parent,
                "tags": scope.metadata.tags,
                "sources": scope.sources,
            }
        }
        documents.append(metadata_doc)

        commandments_doc = {"commandments": self._format_ruleset(scope.commandments)}
        documents.append(commandments_doc)

        suggestions_doc = {"suggestions": self._format_ruleset(scope.suggestions)}
        documents.append(suggestions_doc)

        yaml_parts = []
        for doc in documents:
            yaml_str = yaml.dump(doc, default_flow_style=False, allow_unicode=True, sort_keys=False)
            yaml_parts.append(yaml_str)

        return "---\n".join(yaml_parts)

    def _format_ruleset(self, ruleset: RuleSet) -> dict[str, Any]:
        """Format a ruleset as nested dictionary.

        :param ruleset: The ruleset to format
        :type ruleset: RuleSet
        :returns: Nested dictionary representation
        :rtype: Dict[str, Any]
        """
        result: dict[str, Any] = {}

        for category in ruleset.categories.values():
            parts = category.key.parts
            current = result

            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    current[part] = {
                        "when": category.when,
                        "ruleset": [rule.text for rule in category.rules],
                    }
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

        return result


__all__ = ["YamlMultiDocFormatter"]
