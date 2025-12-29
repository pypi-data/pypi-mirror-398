"""Filesystem-based scope repository implementation."""

from pathlib import Path

from daimyo.config import settings
from daimyo.domain import (
    RuleType,
    Scope,
    ScopeMetadata,
)
from daimyo.infrastructure.filesystem.yaml_parser import (
    parse_metadata,
    parse_rules,
    parse_yaml_file,
    validate_scope_name,
)
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)


class FilesystemScopeRepository:
    """Repository for loading scopes from the filesystem.

    Scopes are stored as directories under the rules path, each containing:
    - metadata.yml: Scope metadata
    - commandments.yml: Mandatory rules
    - suggestions.yml: Recommended rules
    """

    def __init__(self, rules_path: str | None = None):
        """Initialize the repository.

        :param rules_path: Path to the rules directory (defaults to config setting)
        :type rules_path: Optional[str]
        """
        self.rules_path = Path(rules_path or settings.RULES_PATH)
        logger.info(f"Initialized FilesystemScopeRepository with path: {self.rules_path}")

    def get_scope(self, name: str) -> Scope | None:
        """Load a scope from the filesystem.

        :param name: Scope name (directory name)
        :type name: str
        :returns: Scope instance if found, None otherwise
        :rtype: Optional[Scope]
        :raises InvalidScopeError: If scope data is malformed
        :raises YAMLParseError: If YAML parsing fails
        """
        validate_scope_name(name)

        scope_dir = self.rules_path / name

        if not scope_dir.exists() or not scope_dir.is_dir():
            logger.debug(f"Scope directory not found: {scope_dir}")
            return None

        logger.debug(f"Loading scope '{name}' from {scope_dir}")

        metadata_file = scope_dir / "metadata.yml"
        if not metadata_file.exists():
            logger.warning(f"Scope '{name}' missing metadata.yml, using defaults")
            metadata = ScopeMetadata(name=name, description="")
        else:
            metadata_dict = parse_yaml_file(metadata_file)
            metadata = parse_metadata(metadata_dict, name)

        scope = Scope(metadata=metadata, source="local")

        commandments_file = scope_dir / "commandments.yml"
        if commandments_file.exists():
            commandments_dict = parse_yaml_file(commandments_file)
            scope.commandments = parse_rules(commandments_dict, RuleType.COMMANDMENT)
            logger.debug(f"Loaded {len(scope.commandments.categories)} commandment categories")
        else:
            logger.debug(f"No commandments.yml found for scope '{name}'")

        suggestions_file = scope_dir / "suggestions.yml"
        if suggestions_file.exists():
            suggestions_dict = parse_yaml_file(suggestions_file)
            scope.suggestions = parse_rules(suggestions_dict, RuleType.SUGGESTION)
            logger.debug(f"Loaded {len(scope.suggestions.categories)} suggestion categories")
        else:
            logger.debug(f"No suggestions.yml found for scope '{name}'")

        logger.info(f"Successfully loaded scope '{name}'")
        return scope

    def list_scopes(self) -> list[str]:
        """List all available scope names.

        :returns: List of scope directory names
        :rtype: list[str]
        """
        if not self.rules_path.exists():
            logger.warning(f"Rules path does not exist: {self.rules_path}")
            return []

        scopes = []
        for item in self.rules_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                try:
                    validate_scope_name(item.name)
                    scopes.append(item.name)
                except Exception as e:
                    logger.warning(f"Skipping invalid scope directory '{item.name}': {e}")

        logger.debug(f"Found {len(scopes)} scopes in {self.rules_path}")
        return sorted(scopes)


__all__ = ["FilesystemScopeRepository"]
