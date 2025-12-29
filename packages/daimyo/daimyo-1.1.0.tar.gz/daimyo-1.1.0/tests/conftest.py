"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import Mock

from daimyo.domain import (
    Category,
    CategoryKey,
    MergedScope,
    Rule,
    RuleSet,
    RuleType,
    Scope,
    ScopeMetadata,
    ScopeRepository,
    RemoteScopeClient,
)
from daimyo.infrastructure.di import ServiceContainer, reset_container


@pytest.fixture
def sample_rule_commandment():
    """Sample commandment rule."""
    return Rule(text="Use type hints for all functions", rule_type=RuleType.COMMANDMENT)


@pytest.fixture
def sample_rule_suggestion():
    """Sample suggestion rule."""
    return Rule(text="Consider using dataclasses", rule_type=RuleType.SUGGESTION)


@pytest.fixture
def sample_category():
    """Sample category with rules."""
    category = Category(
        key=CategoryKey.from_string("python.testing"),
        when="When writing Python tests",
    )
    category.add_rule(Rule("Use pytest framework", RuleType.COMMANDMENT))
    category.add_rule(Rule("Aim for 80% coverage", RuleType.COMMANDMENT))
    return category


@pytest.fixture
def sample_ruleset():
    """Sample ruleset with multiple categories."""
    ruleset = RuleSet()

    python_cat = Category(
        key=CategoryKey.from_string("python"),
        when="When writing Python code",
    )
    python_cat.add_rule(Rule("Use PEP 8", RuleType.COMMANDMENT))
    ruleset.add_category(python_cat)

    testing_cat = Category(
        key=CategoryKey.from_string("python.testing"),
        when="When writing tests",
    )
    testing_cat.add_rule(Rule("Use pytest", RuleType.COMMANDMENT))
    ruleset.add_category(testing_cat)

    return ruleset


@pytest.fixture
def sample_metadata():
    """Sample scope metadata."""
    return ScopeMetadata(
        name="test-scope",
        description="Test scope for unit tests",
        parent=None,
        tags={"type": "test", "language": "python"},
    )


@pytest.fixture
def sample_scope(sample_metadata, sample_ruleset):
    """Sample scope with metadata and rules."""
    scope = Scope(metadata=sample_metadata)
    scope.commandments = sample_ruleset
    return scope


@pytest.fixture
def temp_rules_dir(tmp_path):
    """Create a temporary rules directory with test scopes."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    test_scope_dir = rules_dir / "test-scope"
    test_scope_dir.mkdir()

    (test_scope_dir / "metadata.yml").write_text(
        """name: test-scope
description: Test scope
parent: null
tags:
  type: test
"""
    )

    (test_scope_dir / "commandments.yml").write_text(
        """python:
  when: When writing Python code
  ruleset:
    - Use type hints
    - Follow PEP 8

python.testing:
  when: When writing tests
  ruleset:
    - Use pytest
    - Write unit tests
"""
    )

    (test_scope_dir / "suggestions.yml").write_text(
        """python:
  when: When writing Python code
  ruleset:
    - Consider using dataclasses
    - Use f-strings
"""
    )

    return rules_dir


@pytest.fixture(autouse=True)
def reset_di_container():
    """Reset DI container between tests to ensure isolation."""
    reset_container()
    yield
    reset_container()


@pytest.fixture
def mock_scope_repository():
    """Mock scope repository for testing."""
    return Mock(spec=ScopeRepository)


@pytest.fixture
def mock_remote_client():
    """Mock remote client for testing."""
    return Mock(spec=RemoteScopeClient)


@pytest.fixture
def test_container(mock_scope_repository, mock_remote_client):
    """ServiceContainer with mocked dependencies for testing."""
    container = ServiceContainer()
    container.override_scope_repository(lambda: mock_scope_repository)
    container.override_remote_client(lambda: mock_remote_client)
    return container


@pytest.fixture
def sample_parent_metadata():
    """Sample parent scope metadata."""
    return ScopeMetadata(
        name="parent-scope",
        description="Parent scope for testing inheritance",
        parent=None,
        tags={"type": "parent"},
    )


@pytest.fixture
def sample_parent_scope(sample_parent_metadata):
    """Sample parent scope with rules."""
    parent_ruleset = RuleSet()

    python_cat = Category(
        key=CategoryKey.from_string("python"),
        when="When writing Python code",
    )
    python_cat.add_rule(Rule("Use type hints", RuleType.COMMANDMENT))
    python_cat.add_rule(Rule("Follow PEP 8", RuleType.COMMANDMENT))
    parent_ruleset.add_category(python_cat)

    testing_cat = Category(
        key=CategoryKey.from_string("python.testing"),
        when="When writing tests",
    )
    testing_cat.add_rule(Rule("Use pytest", RuleType.SUGGESTION))
    parent_ruleset.add_category(testing_cat)

    return Scope(
        metadata=sample_parent_metadata,
        commandments=parent_ruleset,
        suggestions=RuleSet(),
        source="local",
    )


@pytest.fixture
def sample_metadata_with_parent():
    """Sample child scope metadata with parent."""
    return ScopeMetadata(
        name="child-scope",
        description="Child scope for testing inheritance",
        parent="parent-scope",
        tags={"type": "child"},
    )


@pytest.fixture
def sample_scope_with_parent(sample_metadata_with_parent):
    """Sample child scope with parent reference."""
    child_ruleset = RuleSet()

    python_cat = Category(
        key=CategoryKey.from_string("python"),
        when="When writing Python code",
    )
    python_cat.add_rule(Rule("Use async/await", RuleType.COMMANDMENT))
    child_ruleset.add_category(python_cat)

    web_cat = Category(
        key=CategoryKey.from_string("python.web"),
        when="When writing web code",
    )
    web_cat.add_rule(Rule("Use FastAPI", RuleType.COMMANDMENT))
    child_ruleset.add_category(web_cat)

    return Scope(
        metadata=sample_metadata_with_parent,
        commandments=child_ruleset,
        suggestions=RuleSet(),
        source="local",
    )


@pytest.fixture
def sample_merged_scope(sample_metadata):
    """Sample merged scope for formatter testing."""
    merged_commandments = RuleSet()
    merged_suggestions = RuleSet()

    python_cat = Category(
        key=CategoryKey.from_string("python"),
        when="When writing Python code",
    )
    python_cat.add_rule(Rule("Use type hints", RuleType.COMMANDMENT))
    merged_commandments.add_category(python_cat)

    testing_cat = Category(
        key=CategoryKey.from_string("python.testing"),
        when="When writing tests",
    )
    testing_cat.add_rule(Rule("Aim for 80% coverage", RuleType.SUGGESTION))
    merged_suggestions.add_category(testing_cat)

    return MergedScope(
        metadata=sample_metadata,
        commandments=merged_commandments,
        suggestions=merged_suggestions,
        sources=["local", "remote"],
    )


@pytest.fixture
def sample_metadata_with_multi_parents():
    """Sample metadata with multiple parents."""
    return ScopeMetadata(
        name="multi-child-scope",
        description="Child scope with multiple parents",
        parents=["parent1", "parent2"],
        tags={"type": "multi-parent-test"},
    )


@pytest.fixture
def sample_first_parent_scope():
    """Sample first parent scope (higher priority)."""
    parent_ruleset = RuleSet()

    python_cat = Category(
        key=CategoryKey.from_string("python"),
        when="When writing Python code (parent1)",
    )
    python_cat.add_rule(Rule("Use parent1 style guide", RuleType.COMMANDMENT))
    python_cat.add_rule(Rule("Parent1 specific rule", RuleType.COMMANDMENT))
    parent_ruleset.add_category(python_cat)

    testing_cat = Category(
        key=CategoryKey.from_string("python.testing"),
        when="When writing tests (parent1)",
    )
    testing_cat.add_rule(Rule("Use parent1 test framework", RuleType.SUGGESTION))
    parent_ruleset.add_category(testing_cat)

    metadata = ScopeMetadata(
        name="parent1",
        description="First parent scope (higher priority)",
        parent=None,
        tags={"priority": "high"},
    )

    return Scope(
        metadata=metadata,
        commandments=parent_ruleset,
        suggestions=RuleSet(),
        source="local",
    )


@pytest.fixture
def sample_second_parent_scope():
    """Sample second parent scope (lower priority)."""
    parent_ruleset = RuleSet()

    python_cat = Category(
        key=CategoryKey.from_string("python"),
        when="When writing Python code (parent2)",
    )
    python_cat.add_rule(Rule("Use parent2 style guide", RuleType.COMMANDMENT))
    parent_ruleset.add_category(python_cat)

    web_cat = Category(
        key=CategoryKey.from_string("python.web"),
        when="When writing web code (parent2)",
    )
    web_cat.add_rule(Rule("Use parent2 web framework", RuleType.COMMANDMENT))
    parent_ruleset.add_category(web_cat)

    metadata = ScopeMetadata(
        name="parent2",
        description="Second parent scope (lower priority)",
        parent=None,
        tags={"priority": "low"},
    )

    return Scope(
        metadata=metadata,
        commandments=parent_ruleset,
        suggestions=RuleSet(),
        source="local",
    )


__all__ = [
    "sample_rule_commandment",
    "sample_rule_suggestion",
    "sample_category",
    "sample_ruleset",
    "sample_metadata",
    "sample_scope",
    "temp_rules_dir",
    "reset_di_container",
    "mock_scope_repository",
    "mock_remote_client",
    "test_container",
    "sample_parent_metadata",
    "sample_parent_scope",
    "sample_metadata_with_parent",
    "sample_scope_with_parent",
    "sample_merged_scope",
    "sample_metadata_with_multi_parents",
    "sample_first_parent_scope",
    "sample_second_parent_scope",
]
