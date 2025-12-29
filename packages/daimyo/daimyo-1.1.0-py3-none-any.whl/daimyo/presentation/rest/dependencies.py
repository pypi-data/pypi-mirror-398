"""Dependency injection for FastAPI."""

from daimyo.application.filtering import CategoryFilterService
from daimyo.application.rule_service import RuleMergingService
from daimyo.application.scope_resolution import ScopeResolutionService
from daimyo.domain import RemoteScopeClient, ScopeRepository
from daimyo.infrastructure.di import get_container


def get_scope_repository() -> ScopeRepository:
    """Get the scope repository from DI container."""
    return get_container().scope_repository()


def get_remote_client() -> RemoteScopeClient:
    """Get the remote client from DI container."""
    return get_container().remote_client()


def get_scope_service() -> ScopeResolutionService:
    """Get the scope resolution service from DI container."""
    return get_container().scope_service()


def get_rule_service() -> RuleMergingService:
    """Get the rule merging service from DI container."""
    return get_container().rule_service()


def get_category_filter_service() -> CategoryFilterService:
    """Get the category filter service from DI container."""
    return get_container().category_filter_service()


__all__ = [
    "get_scope_repository",
    "get_remote_client",
    "get_scope_service",
    "get_rule_service",
    "get_category_filter_service",
]
