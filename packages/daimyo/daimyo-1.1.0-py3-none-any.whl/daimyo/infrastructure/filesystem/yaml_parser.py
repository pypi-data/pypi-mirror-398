"""YAML parsing and validation utilities."""

from pathlib import Path
from typing import Any

import yaml

from daimyo.domain import (
    Category,
    CategoryKey,
    InvalidScopeError,
    Rule,
    RuleSet,
    RuleType,
    ScopeMetadata,
    YAMLParseError,
)


def parse_yaml_file(file_path: Path) -> dict[str, Any]:
    """Parse a YAML file safely.

    :param file_path: Path to the YAML file
    :type file_path: Path
    :returns: Parsed YAML content as dictionary
    :rtype: Dict[str, Any]
    :raises YAMLParseError: If parsing fails
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                return {}
            if not isinstance(data, dict):
                raise YAMLParseError(
                    f"Expected dictionary in {file_path}, got {type(data).__name__}"
                )
            return data
    except yaml.YAMLError as e:
        raise YAMLParseError(f"Failed to parse {file_path}: {e}")
    except OSError as e:
        raise YAMLParseError(f"Failed to read {file_path}: {e}")


def parse_metadata(metadata_dict: dict[str, Any], scope_name: str) -> ScopeMetadata:
    """Parse scope metadata from dictionary.

    :param metadata_dict: Dictionary containing metadata
    :type metadata_dict: Dict[str, Any]
    :param scope_name: Name of the scope
    :type scope_name: str
    :returns: ScopeMetadata instance
    :rtype: ScopeMetadata
    :raises InvalidScopeError: If metadata is invalid
    """
    try:
        description = metadata_dict.get("description", "")
        parent = metadata_dict.get("parent")
        parents = metadata_dict.get("parents")
        tags = metadata_dict.get("tags", {})

        if not isinstance(description, str):
            raise InvalidScopeError("Metadata 'description' must be a string")

        if parent is not None and not isinstance(parent, str):
            raise InvalidScopeError("Metadata 'parent' must be a string or null")

        if parents is not None:
            if not isinstance(parents, list):
                raise InvalidScopeError("Metadata 'parents' must be a list")

            if len(parents) == 0:
                raise InvalidScopeError(
                    "Metadata 'parents' cannot be an empty list (omit field or set to null)"
                )

            for idx, p in enumerate(parents):
                if not isinstance(p, str):
                    raise InvalidScopeError(
                        f"Metadata 'parents[{idx}]' must be a string, got {type(p).__name__}"
                    )

            if len(parents) != len(set(parents)):
                raise InvalidScopeError("Metadata 'parents' contains duplicate entries")

        if parent is not None and parents is not None:
            raise InvalidScopeError("Cannot specify both 'parent' and 'parents' fields")

        if not isinstance(tags, dict):
            raise InvalidScopeError("Metadata 'tags' must be a dictionary")

        return ScopeMetadata(
            name=scope_name, description=description, parent=parent, parents=parents, tags=tags
        )
    except KeyError as e:
        raise InvalidScopeError(f"Missing required metadata field: {e}")


def parse_rules(rules_dict: dict[str, Any], rule_type: RuleType, prefix: str = "") -> RuleSet:
    """Parse rules from nested dictionary structure.

    :param rules_dict: Dictionary containing rules (can be nested)
    :type rules_dict: Dict[str, Any]
    :param rule_type: Whether these are commandments or suggestions
    :type rule_type: RuleType
    :param prefix: Current category prefix (for recursion)
    :type prefix: str
    :returns: RuleSet containing all categories and rules
    :rtype: RuleSet
    :raises InvalidScopeError: If rule structure is invalid
    """
    ruleset = RuleSet()

    def _parse_recursive(data: dict[str, Any], cat_prefix: str) -> None:
        """Recursively parse nested categories.

        :param data: Dictionary containing category data
        :type data: Dict[str, Any]
        :param cat_prefix: Current category prefix
        :type cat_prefix: str
        :rtype: None
        """
        for key, value in data.items():
            if not isinstance(value, dict):
                continue

            current_path = f"{cat_prefix}.{key}" if cat_prefix else key

            if "when" in value and "ruleset" in value:
                when_text = value["when"]
                ruleset_list = value["ruleset"]

                if not isinstance(when_text, str):
                    raise InvalidScopeError(f"'when' must be a string in category {current_path}")

                if not isinstance(ruleset_list, list):
                    raise InvalidScopeError(f"'ruleset' must be a list in category {current_path}")

                category_key = CategoryKey.from_string(current_path)
                category = Category(key=category_key, when=when_text)

                for rule_text in ruleset_list:
                    if not isinstance(rule_text, str):
                        raise InvalidScopeError(f"Rule must be a string in category {current_path}")
                    category.add_rule(Rule(text=rule_text, rule_type=rule_type))

                ruleset.add_category(category)
            else:
                _parse_recursive(value, current_path)

    _parse_recursive(rules_dict, prefix)
    return ruleset


def validate_scope_name(name: str) -> bool:
    """Validate scope name format.

    Scope names should be:
    - Alphanumeric with hyphens and underscores
    - No path traversal characters
    - Not empty

    :param name: Scope name to validate
    :type name: str
    :returns: True if valid
    :rtype: bool
    :raises InvalidScopeError: If name is invalid
    """
    if not name:
        raise InvalidScopeError("Scope name cannot be empty")

    if ".." in name or "/" in name or "\\" in name:
        raise InvalidScopeError(f"Invalid scope name '{name}': path traversal not allowed")

    if not all(c.isalnum() or c in "-_" for c in name):
        raise InvalidScopeError(
            f"Invalid scope name '{name}': only alphanumeric, hyphens, and underscores allowed"
        )

    return True


__all__ = [
    "parse_yaml_file",
    "parse_metadata",
    "parse_rules",
    "validate_scope_name",
]
