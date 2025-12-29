"""Tests for rule merging service."""

import pytest

from daimyo.application.rule_service import RuleMergingService
from daimyo.domain import Category, CategoryKey, Rule, RuleSet, RuleType


class TestRuleMergingService:
    """Tests for RuleMergingService."""

    def setup_method(self):
        """Setup for each test."""
        self.service = RuleMergingService()

    def test_merge_commandments_additive(self):
        """Test that commandments merge additively."""
        parent = RuleSet()
        parent_cat = Category(
            CategoryKey.from_string("python.testing"), when="Testing"
        )
        parent_cat.add_rule(Rule("Use pytest", RuleType.COMMANDMENT))
        parent.add_category(parent_cat)

        child = RuleSet()
        child_cat = Category(
            CategoryKey.from_string("python.testing"), when="Testing updated"
        )
        child_cat.add_rule(Rule("Write unit tests", RuleType.COMMANDMENT))
        child.add_category(child_cat)

        result = self.service.merge_commandments(parent, child)

        testing_cat = result.categories[CategoryKey.from_string("python.testing")]
        assert len(testing_cat.rules) == 2
        rule_texts = [r.text for r in testing_cat.rules]
        assert "Use pytest" in rule_texts
        assert "Write unit tests" in rule_texts
        assert testing_cat.when == "Testing updated"

    def test_merge_commandments_different_categories(self):
        """Test merging commandments with different categories."""
        parent = RuleSet()
        parent.add_category(
            Category(CategoryKey.from_string("python"), when="Python code")
        )

        child = RuleSet()
        child.add_category(
            Category(CategoryKey.from_string("javascript"), when="JS code")
        )

        result = self.service.merge_commandments(parent, child)

        assert len(result.categories) == 2
        assert CategoryKey.from_string("python") in result.categories
        assert CategoryKey.from_string("javascript") in result.categories

    def test_merge_suggestions_override_default(self):
        """Test that suggestions override by default."""
        parent = RuleSet()
        parent_cat = Category(
            CategoryKey.from_string("python.testing"), when="Testing"
        )
        parent_cat.add_rule(Rule("Use unittest", RuleType.SUGGESTION))
        parent.add_category(parent_cat)

        child = RuleSet()
        child_cat = Category(
            CategoryKey.from_string("python.testing"), when="Testing updated"
        )
        child_cat.add_rule(Rule("Use pytest", RuleType.SUGGESTION))
        child.add_category(child_cat)

        result = self.service.merge_suggestions(parent, child)

        testing_cat = result.categories[CategoryKey.from_string("python.testing")]
        assert len(testing_cat.rules) == 1
        assert testing_cat.rules[0].text == "Use pytest"

    def test_merge_suggestions_append_with_plus(self):
        """Test that suggestions with + prefix append."""
        parent = RuleSet()
        parent_cat = Category(
            CategoryKey.from_string("python.testing"), when="Testing"
        )
        parent_cat.add_rule(Rule("Use pytest", RuleType.SUGGESTION))
        parent.add_category(parent_cat)

        child = RuleSet()
        child_cat = Category(
            CategoryKey.from_string("+python.testing"), when="Testing updated"
        )
        child_cat.add_rule(Rule("Use fixtures", RuleType.SUGGESTION))
        child.add_category(child_cat)

        result = self.service.merge_suggestions(parent, child)

        testing_cat = result.categories[CategoryKey.from_string("python.testing")]
        assert len(testing_cat.rules) == 2
        rule_texts = [r.text for r in testing_cat.rules]
        assert "Use pytest" in rule_texts
        assert "Use fixtures" in rule_texts

    def test_merge_suggestions_plus_no_parent(self):
        """Test + prefix when no parent category exists."""
        parent = RuleSet()

        child = RuleSet()
        child_cat = Category(
            CategoryKey.from_string("+python.testing"), when="Testing"
        )
        child_cat.add_rule(Rule("Use pytest", RuleType.SUGGESTION))
        child.add_category(child_cat)

        result = self.service.merge_suggestions(parent, child)

        assert CategoryKey.from_string("python.testing") in result.categories
        testing_cat = result.categories[CategoryKey.from_string("python.testing")]
        assert len(testing_cat.rules) == 1

    def test_filter_categories_all(self):
        """Test filtering with empty filter (returns all)."""
        ruleset = RuleSet()
        ruleset.add_category(
            Category(CategoryKey.from_string("python"), when="Python")
        )
        ruleset.add_category(
            Category(CategoryKey.from_string("javascript"), when="JS")
        )

        result = self.service.filter_categories(ruleset, [])

        assert len(result.categories) == len(ruleset.categories)

    def test_filter_categories_prefix(self):
        """Test filtering by prefix."""
        ruleset = RuleSet()
        ruleset.add_category(
            Category(CategoryKey.from_string("python"), when="Python")
        )
        ruleset.add_category(
            Category(CategoryKey.from_string("python.testing"), when="Testing")
        )
        ruleset.add_category(
            Category(CategoryKey.from_string("python.web"), when="Web")
        )
        ruleset.add_category(
            Category(CategoryKey.from_string("javascript"), when="JS")
        )

        result = self.service.filter_categories(ruleset, ["python"])

        assert len(result.categories) == 3
        for key in result.categories.keys():
            assert str(key).startswith("python")

    def test_filter_categories_multiple_filters(self):
        """Test filtering with multiple filters."""
        ruleset = RuleSet()
        ruleset.add_category(
            Category(CategoryKey.from_string("python.testing"), when="Testing")
        )
        ruleset.add_category(
            Category(CategoryKey.from_string("python.web"), when="Web")
        )
        ruleset.add_category(
            Category(CategoryKey.from_string("javascript"), when="JS")
        )

        result = self.service.filter_categories(ruleset, ["python.testing", "javascript"])

        assert len(result.categories) == 2
        assert CategoryKey.from_string("python.testing") in result.categories
        assert CategoryKey.from_string("javascript") in result.categories


__all__ = ["TestRuleMergingService"]
