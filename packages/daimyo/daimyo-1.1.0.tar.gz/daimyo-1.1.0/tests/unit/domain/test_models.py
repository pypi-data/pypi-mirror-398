"""Unit tests for domain models."""

import pytest

from daimyo.domain import (
    Category,
    CategoryKey,
    MergedScope,
    Rule,
    RuleSet,
    RuleType,
    Scope,
    ScopeMetadata,
)


class TestRule:
    """Tests for Rule model."""

    def test_rule_creation(self):
        """Test creating a rule."""
        rule = Rule(text="Use type hints", rule_type=RuleType.COMMANDMENT)
        assert rule.text == "Use type hints"
        assert rule.rule_type == RuleType.COMMANDMENT

    def test_rule_str_commandment(self):
        """Test string representation of commandment."""
        rule = Rule(text="Use type hints", rule_type=RuleType.COMMANDMENT)
        assert str(rule) == "MUST: Use type hints"

    def test_rule_str_suggestion(self):
        """Test string representation of suggestion."""
        rule = Rule(text="Consider dataclasses", rule_type=RuleType.SUGGESTION)
        assert str(rule) == "SHOULD: Consider dataclasses"

    def test_rule_immutability(self):
        """Test that rules are immutable."""
        rule = Rule(text="Use type hints", rule_type=RuleType.COMMANDMENT)
        with pytest.raises(AttributeError):
            rule.text = "Something else"


class TestCategoryKey:
    """Tests for CategoryKey model."""

    def test_from_string(self):
        """Test creating CategoryKey from string."""
        key = CategoryKey.from_string("python.web.testing")
        assert key.parts == ("python", "web", "testing")

    def test_from_string_single_part(self):
        """Test creating CategoryKey with single part."""
        key = CategoryKey.from_string("python")
        assert key.parts == ("python",)

    def test_from_string_with_plus_prefix(self):
        """Test creating CategoryKey with + prefix (should be stripped)."""
        key = CategoryKey.from_string("+python.testing")
        assert key.parts == ("python", "testing")

    def test_str_conversion(self):
        """Test converting CategoryKey back to string."""
        key = CategoryKey.from_string("python.web.testing")
        assert str(key) == "python.web.testing"

    def test_matches_prefix_true(self):
        """Test prefix matching when it matches."""
        key = CategoryKey.from_string("python.web.testing")
        prefix = CategoryKey.from_string("python.web")
        assert key.matches_prefix(prefix) is True

    def test_matches_prefix_false(self):
        """Test prefix matching when it doesn't match."""
        key = CategoryKey.from_string("python.testing")
        prefix = CategoryKey.from_string("python.web")
        assert key.matches_prefix(prefix) is False

    def test_matches_prefix_exact(self):
        """Test prefix matching with exact match."""
        key = CategoryKey.from_string("python.web")
        prefix = CategoryKey.from_string("python.web")
        assert key.matches_prefix(prefix) is True

    def test_matches_prefix_longer(self):
        """Test prefix matching when prefix is longer."""
        key = CategoryKey.from_string("python")
        prefix = CategoryKey.from_string("python.web")
        assert key.matches_prefix(prefix) is False

    def test_depth(self):
        """Test depth calculation."""
        key = CategoryKey.from_string("python.web.testing")
        assert key.depth() == 3

    def test_immutability(self):
        """Test that CategoryKey is immutable."""
        key = CategoryKey.from_string("python.testing")
        with pytest.raises(AttributeError):
            key.parts = ("java", "testing")


class TestCategory:
    """Tests for Category model."""

    def test_category_creation(self):
        """Test creating a category."""
        key = CategoryKey.from_string("python.testing")
        category = Category(key=key, when="When writing tests")
        assert category.key == key
        assert category.when == "When writing tests"
        assert len(category.rules) == 0

    def test_add_rule(self):
        """Test adding rules to a category."""
        category = Category(
            key=CategoryKey.from_string("python.testing"),
            when="When writing tests",
        )
        rule = Rule("Use pytest", RuleType.COMMANDMENT)
        category.add_rule(rule)
        assert len(category.rules) == 1
        assert category.rules[0] == rule

    def test_copy(self):
        """Test copying a category."""
        category = Category(
            key=CategoryKey.from_string("python.testing"),
            when="When writing tests",
        )
        category.add_rule(Rule("Use pytest", RuleType.COMMANDMENT))

        copied = category.copy()
        assert copied.key == category.key
        assert copied.when == category.when
        assert len(copied.rules) == len(category.rules)
        assert copied.rules is not category.rules


class TestRuleSet:
    """Tests for RuleSet model."""

    def test_ruleset_creation(self):
        """Test creating an empty ruleset."""
        ruleset = RuleSet()
        assert len(ruleset.categories) == 0

    def test_add_category(self):
        """Test adding a category to ruleset."""
        ruleset = RuleSet()
        category = Category(
            key=CategoryKey.from_string("python.testing"),
            when="When writing tests",
        )
        ruleset.add_category(category)
        assert len(ruleset.categories) == 1
        assert CategoryKey.from_string("python.testing") in ruleset.categories

    def test_get_matching_categories_all(self):
        """Test getting all categories when no filter."""
        ruleset = RuleSet()
        ruleset.add_category(
            Category(CategoryKey.from_string("python"), when="Python code")
        )
        ruleset.add_category(
            Category(CategoryKey.from_string("python.testing"), when="Testing")
        )

        matches = ruleset.get_matching_categories(None)
        assert len(matches) == 2

    def test_get_matching_categories_prefix(self):
        """Test getting categories with prefix filter."""
        ruleset = RuleSet()
        ruleset.add_category(
            Category(CategoryKey.from_string("python"), when="Python code")
        )
        ruleset.add_category(
            Category(CategoryKey.from_string("python.testing"), when="Testing")
        )
        ruleset.add_category(
            Category(CategoryKey.from_string("javascript"), when="JS code")
        )

        matches = ruleset.get_matching_categories("python")
        assert len(matches) == 2
        match_keys = [str(c.key) for c in matches]
        assert "python" in match_keys
        assert "python.testing" in match_keys
        assert "javascript" not in match_keys

    def test_copy(self):
        """Test copying a ruleset."""
        ruleset = RuleSet()
        category = Category(
            key=CategoryKey.from_string("python.testing"),
            when="When writing tests",
        )
        category.add_rule(Rule("Use pytest", RuleType.COMMANDMENT))
        ruleset.add_category(category)

        copied = ruleset.copy()
        assert len(copied.categories) == len(ruleset.categories)
        assert copied.categories is not ruleset.categories


class TestScopeMetadata:
    """Tests for ScopeMetadata model."""

    def test_metadata_creation(self):
        """Test creating scope metadata."""
        metadata = ScopeMetadata(
            name="test-scope",
            description="Test description",
            parent="https://remote.com/parent",
            tags={"type": "test"},
        )
        assert metadata.name == "test-scope"
        assert metadata.description == "Test description"
        assert metadata.parent == "https://remote.com/parent"
        assert metadata.tags == {"type": "test"}

    def test_metadata_defaults(self):
        """Test metadata with default values."""
        metadata = ScopeMetadata(name="test-scope", description="Test")
        assert metadata.parent is None
        assert metadata.tags == {}


class TestScope:
    """Tests for Scope model."""

    def test_scope_creation(self):
        """Test creating a scope."""
        metadata = ScopeMetadata(name="test-scope", description="Test")
        scope = Scope(metadata=metadata)
        assert scope.metadata == metadata
        assert len(scope.commandments.categories) == 0
        assert len(scope.suggestions.categories) == 0
        assert scope.source == "local"

    def test_get_all_category_keys(self):
        """Test getting all unique category keys."""
        metadata = ScopeMetadata(name="test-scope", description="Test")
        scope = Scope(metadata=metadata)

        scope.commandments.add_category(
            Category(CategoryKey.from_string("python"), when="Python")
        )
        scope.commandments.add_category(
            Category(CategoryKey.from_string("python.testing"), when="Testing")
        )

        scope.suggestions.add_category(
            Category(CategoryKey.from_string("python"), when="Python")
        )
        scope.suggestions.add_category(
            Category(CategoryKey.from_string("javascript"), when="JS")
        )

        keys = scope.get_all_category_keys()
        assert len(keys) == 3
        assert CategoryKey.from_string("python") in keys
        assert CategoryKey.from_string("python.testing") in keys
        assert CategoryKey.from_string("javascript") in keys


class TestMergedScope:
    """Tests for MergedScope model."""

    def test_from_scope(self):
        """Test creating MergedScope from Scope."""
        metadata = ScopeMetadata(name="test-scope", description="Test")
        scope = Scope(metadata=metadata, source="local")
        scope.commandments.add_category(
            Category(CategoryKey.from_string("python"), when="Python")
        )

        merged = MergedScope.from_scope(scope)
        assert merged.metadata == scope.metadata
        assert len(merged.commandments.categories) == len(scope.commandments.categories)
        assert len(merged.suggestions.categories) == len(scope.suggestions.categories)
        assert merged.sources == ["local"]


__all__ = [
    "TestRule",
    "TestCategoryKey",
    "TestCategory",
    "TestRuleSet",
    "TestScopeMetadata",
    "TestScope",
    "TestMergedScope",
]
