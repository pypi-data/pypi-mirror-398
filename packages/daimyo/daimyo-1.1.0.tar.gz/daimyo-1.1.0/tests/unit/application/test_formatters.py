"""Tests for output formatters."""

import pytest
import yaml

from daimyo.application.formatters import (
    JsonFormatter,
    MarkdownFormatter,
    YamlMultiDocFormatter,
)
from daimyo.domain import Category, CategoryKey, MergedScope, Rule, RuleSet, RuleType, ScopeMetadata


class TestYamlMultiDocFormatter:
    """Tests for YAML multi-document formatter."""

    def test_format_basic(self, sample_scope):
        """Test basic YAML multi-doc formatting."""
        from daimyo.domain import MergedScope

        merged = MergedScope.from_scope(sample_scope)
        formatter = YamlMultiDocFormatter()
        result = formatter.format(merged)

        documents = list(yaml.safe_load_all(result))
        assert len(documents) == 3

        assert "metadata" in documents[0]
        assert documents[0]["metadata"]["name"] == "test-scope"

        assert "commandments" in documents[1]

        assert "suggestions" in documents[2]


class TestJsonFormatter:
    """Tests for JSON formatter."""

    def test_format_basic(self, sample_scope):
        """Test basic JSON formatting."""
        from daimyo.domain import MergedScope

        merged = MergedScope.from_scope(sample_scope)
        formatter = JsonFormatter()
        result = formatter.format(merged)

        assert "metadata" in result
        assert "commandments" in result
        assert "suggestions" in result
        assert result["metadata"]["name"] == "test-scope"


class TestMarkdownFormatter:
    """Tests for Markdown formatter."""

    def test_format_basic(self, sample_scope):
        """Test basic Markdown formatting."""
        from daimyo.domain import MergedScope

        merged = MergedScope.from_scope(sample_scope)
        formatter = MarkdownFormatter()
        result = formatter.format(merged)

        assert "# Rules for test-scope" in result
        assert "## Commandments" in result

    def test_format_with_hierarchy(self):
        """Test Markdown formatting with hierarchy."""
        metadata = ScopeMetadata(name="test", description="Test")
        merged = MergedScope(
            metadata=metadata,
            commandments=RuleSet(),
            suggestions=RuleSet(),
            sources=["local"],
        )

        cat1 = Category(CategoryKey.from_string("python"), when="Python")
        cat1.add_rule(Rule("Rule 1", RuleType.COMMANDMENT))
        merged.commandments.add_category(cat1)

        cat2 = Category(CategoryKey.from_string("python.web"), when="Web")
        cat2.add_rule(Rule("Rule 2", RuleType.COMMANDMENT))
        merged.commandments.add_category(cat2)

        formatter = MarkdownFormatter()
        result = formatter.format(merged)

        assert "### python" in result
        assert "#### web" in result
        assert "MUST" in result


__all__ = ["TestYamlMultiDocFormatter", "TestJsonFormatter", "TestMarkdownFormatter"]
