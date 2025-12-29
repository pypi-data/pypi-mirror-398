"""Tests for YAML parser."""

import pytest
from pathlib import Path

from daimyo.domain import InvalidScopeError, RuleType, YAMLParseError
from daimyo.infrastructure.filesystem.yaml_parser import (
    parse_metadata,
    parse_rules,
    parse_yaml_file,
    validate_scope_name,
)


class TestYAMLParser:
    """Tests for YAML parsing functions."""

    def test_parse_yaml_file_valid(self, tmp_path):
        """Test parsing a valid YAML file."""
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text("key: value\nnumber: 42")

        result = parse_yaml_file(yaml_file)
        assert result == {"key": "value", "number": 42}

    def test_parse_yaml_file_empty(self, tmp_path):
        """Test parsing an empty YAML file."""
        yaml_file = tmp_path / "empty.yml"
        yaml_file.write_text("")

        result = parse_yaml_file(yaml_file)
        assert result == {}

    def test_parse_yaml_file_not_found(self, tmp_path):
        """Test parsing a non-existent file."""
        yaml_file = tmp_path / "notfound.yml"

        with pytest.raises(YAMLParseError, match="Failed to read"):
            parse_yaml_file(yaml_file)

    def test_parse_metadata_valid(self):
        """Test parsing valid metadata."""
        metadata_dict = {
            "description": "Test scope",
            "parent": "https://remote.com/parent",
            "tags": {"type": "test"},
        }

        metadata = parse_metadata(metadata_dict, "test-scope")
        assert metadata.name == "test-scope"
        assert metadata.description == "Test scope"
        assert metadata.parent == "https://remote.com/parent"
        assert metadata.tags == {"type": "test"}

    def test_parse_metadata_minimal(self):
        """Test parsing minimal metadata."""
        metadata_dict = {}

        metadata = parse_metadata(metadata_dict, "test-scope")
        assert metadata.name == "test-scope"
        assert metadata.description == ""
        assert metadata.parent is None
        assert metadata.tags == {}

    def test_parse_metadata_with_parents_list(self):
        """Test parsing metadata with parents list."""
        metadata_dict = {
            "description": "Test scope",
            "parents": ["parent1", "parent2"],
            "tags": {"type": "test"},
        }

        metadata = parse_metadata(metadata_dict, "test-scope")
        assert metadata.parents == ["parent1", "parent2"]
        assert metadata.parent is None
        assert metadata.get_parent_list() == ["parent1", "parent2"]

    def test_parse_metadata_with_single_parent_in_list(self):
        """Test parsing metadata with single parent in list."""
        metadata_dict = {
            "description": "Test scope",
            "parents": ["parent1"],
        }

        metadata = parse_metadata(metadata_dict, "test-scope")
        assert metadata.parents == ["parent1"]
        assert metadata.get_parent_list() == ["parent1"]

    def test_parse_metadata_parents_not_list(self):
        """Test parsing fails when parents is not a list."""
        metadata_dict = {"parents": "parent1"}

        with pytest.raises(InvalidScopeError, match="must be a list"):
            parse_metadata(metadata_dict, "test-scope")

    def test_parse_metadata_parents_empty_list(self):
        """Test parsing fails when parents is empty list."""
        metadata_dict = {"parents": []}

        with pytest.raises(InvalidScopeError, match="cannot be an empty list"):
            parse_metadata(metadata_dict, "test-scope")

    def test_parse_metadata_parents_non_string_element(self):
        """Test parsing fails when parents contains non-string."""
        metadata_dict = {"parents": ["parent1", 123]}

        with pytest.raises(InvalidScopeError, match="must be a string"):
            parse_metadata(metadata_dict, "test-scope")

    def test_parse_metadata_parents_duplicates(self):
        """Test parsing fails when parents has duplicates."""
        metadata_dict = {"parents": ["parent1", "parent2", "parent1"]}

        with pytest.raises(InvalidScopeError, match="duplicate"):
            parse_metadata(metadata_dict, "test-scope")

    def test_parse_metadata_both_parent_and_parents(self):
        """Test parsing fails when both parent and parents specified."""
        metadata_dict = {
            "parent": "parent1",
            "parents": ["parent2"],
        }

        with pytest.raises(InvalidScopeError, match="both"):
            parse_metadata(metadata_dict, "test-scope")

    def test_parse_metadata_backward_compatible(self):
        """Test old parent field still works."""
        metadata_dict = {"parent": "parent1"}

        metadata = parse_metadata(metadata_dict, "test-scope")
        assert metadata.parent == "parent1"
        assert metadata.parents is None
        assert metadata.get_parent_list() == ["parent1"]

    def test_parse_rules_nested_structure(self):
        """Test parsing nested rule structure."""
        rules_dict = {
            "python": {
                "web": {
                    "testing": {
                        "when": "When testing web apps",
                        "ruleset": ["Use playwright", "Write E2E tests"],
                    }
                }
            }
        }

        ruleset = parse_rules(rules_dict, RuleType.COMMANDMENT)
        assert len(ruleset.categories) == 1

        from daimyo.domain import CategoryKey

        category = ruleset.categories[CategoryKey.from_string("python.web.testing")]
        assert category.when == "When testing web apps"
        assert len(category.rules) == 2
        assert all(r.rule_type == RuleType.COMMANDMENT for r in category.rules)

    def test_parse_rules_multiple_categories(self):
        """Test parsing multiple categories."""
        rules_dict = {
            "python": {"when": "Python code", "ruleset": ["Use PEP 8"]},
            "javascript": {"when": "JS code", "ruleset": ["Use ESLint"]},
        }

        ruleset = parse_rules(rules_dict, RuleType.SUGGESTION)
        assert len(ruleset.categories) == 2

    def test_validate_scope_name_valid(self):
        """Test validating valid scope names."""
        assert validate_scope_name("test-scope") is True
        assert validate_scope_name("team_backend") is True
        assert validate_scope_name("project123") is True

    def test_validate_scope_name_empty(self):
        """Test validating empty scope name."""
        with pytest.raises(InvalidScopeError, match="cannot be empty"):
            validate_scope_name("")

    def test_validate_scope_name_path_traversal(self):
        """Test validating scope name with path traversal."""
        with pytest.raises(InvalidScopeError, match="path traversal"):
            validate_scope_name("../etc/passwd")

        with pytest.raises(InvalidScopeError, match="path traversal"):
            validate_scope_name("test/../scope")

    def test_validate_scope_name_invalid_chars(self):
        """Test validating scope name with invalid characters."""
        with pytest.raises(InvalidScopeError, match="only alphanumeric"):
            validate_scope_name("test@scope")

        with pytest.raises(InvalidScopeError, match="only alphanumeric"):
            validate_scope_name("test scope")


class TestFilesystemScopeLoader:
    """Tests for FilesystemScopeRepository."""

    def test_load_scope(self, temp_rules_dir):
        """Test loading a scope from filesystem."""
        from daimyo.infrastructure.filesystem import FilesystemScopeRepository

        repo = FilesystemScopeRepository(rules_path=str(temp_rules_dir))
        scope = repo.get_scope("test-scope")

        assert scope is not None
        assert scope.metadata.name == "test-scope"
        assert len(scope.commandments.categories) == 2
        assert len(scope.suggestions.categories) == 1

    def test_load_nonexistent_scope(self, temp_rules_dir):
        """Test loading a non-existent scope."""
        from daimyo.infrastructure.filesystem import FilesystemScopeRepository

        repo = FilesystemScopeRepository(rules_path=str(temp_rules_dir))
        scope = repo.get_scope("nonexistent")

        assert scope is None

    def test_list_scopes(self, temp_rules_dir):
        """Test listing all scopes."""
        from daimyo.infrastructure.filesystem import FilesystemScopeRepository

        repo = FilesystemScopeRepository(rules_path=str(temp_rules_dir))
        scopes = repo.list_scopes()

        assert "test-scope" in scopes


__all__ = ["TestYAMLParser", "TestFilesystemScopeLoader"]
