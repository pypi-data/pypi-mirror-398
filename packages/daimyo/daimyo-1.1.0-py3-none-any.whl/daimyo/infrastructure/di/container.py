"""Dependency injection container for Daimyo services."""

from dataclasses import dataclass, field
from typing import Callable

from daimyo.application.filtering import CategoryFilterService
from daimyo.application.rule_service import RuleMergingService
from daimyo.application.scope_resolution import ScopeResolutionService
from daimyo.config import settings
from daimyo.domain import RemoteScopeClient, ScopeRepository
from daimyo.infrastructure.filesystem import FilesystemScopeRepository
from daimyo.infrastructure.remote import HttpRemoteScopeClient


@dataclass
class ServiceContainer:
    """Dependency injection container for Daimyo services."""

    rules_path: str = field(default_factory=lambda: settings.RULES_PATH)
    remote_timeout: int = field(default_factory=lambda: settings.REMOTE_TIMEOUT_SECONDS)
    remote_max_retries: int = field(default_factory=lambda: settings.REMOTE_MAX_RETRIES)
    max_inheritance_depth: int = field(default_factory=lambda: settings.MAX_INHERITANCE_DEPTH)

    _scope_repository: ScopeRepository | None = field(default=None, init=False, repr=False)
    _remote_client: RemoteScopeClient | None = field(default=None, init=False, repr=False)
    _scope_service: ScopeResolutionService | None = field(default=None, init=False, repr=False)
    _rule_service: RuleMergingService | None = field(default=None, init=False, repr=False)
    _category_filter_service: CategoryFilterService | None = field(
        default=None, init=False, repr=False
    )

    _scope_repository_factory: Callable[[], ScopeRepository] | None = field(
        default=None, init=False, repr=False
    )
    _remote_client_factory: Callable[[], RemoteScopeClient] | None = field(
        default=None, init=False, repr=False
    )

    def scope_repository(self) -> ScopeRepository:
        """Get or create scope repository (singleton)."""
        if self._scope_repository is None:
            if self._scope_repository_factory:
                self._scope_repository = self._scope_repository_factory()
            else:
                self._scope_repository = FilesystemScopeRepository(self.rules_path)
        return self._scope_repository

    def remote_client(self) -> RemoteScopeClient:
        """Get or create remote client (singleton)."""
        if self._remote_client is None:
            if self._remote_client_factory:
                self._remote_client = self._remote_client_factory()
            else:
                self._remote_client = HttpRemoteScopeClient(
                    timeout=self.remote_timeout,
                    max_retries=self.remote_max_retries,
                )
        return self._remote_client

    def scope_service(self) -> ScopeResolutionService:
        """Get or create scope resolution service (singleton)."""
        if self._scope_service is None:
            self._scope_service = ScopeResolutionService(
                local_repo=self.scope_repository(),
                remote_client=self.remote_client(),
                max_depth=self.max_inheritance_depth,
            )
        return self._scope_service

    def rule_service(self) -> RuleMergingService:
        """Get or create rule merging service (singleton)."""
        if self._rule_service is None:
            self._rule_service = RuleMergingService()
        return self._rule_service

    def category_filter_service(self) -> CategoryFilterService:
        """Get or create category filter service (singleton)."""
        if self._category_filter_service is None:
            self._category_filter_service = CategoryFilterService(self.rule_service())
        return self._category_filter_service

    def override_scope_repository(self, factory: Callable[[], ScopeRepository]) -> None:
        """Override scope repository factory (for testing)."""
        self._scope_repository_factory = factory
        self._scope_repository = None

    def override_remote_client(self, factory: Callable[[], RemoteScopeClient]) -> None:
        """Override remote client factory (for testing)."""
        self._remote_client_factory = factory
        self._remote_client = None

    def reset(self) -> None:
        """Reset all cached instances (for testing)."""
        self._scope_repository = None
        self._remote_client = None
        self._scope_service = None
        self._rule_service = None
        self._category_filter_service = None


_container: ServiceContainer | None = None


def get_container() -> ServiceContainer:
    """Get the global service container."""
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


def reset_container() -> None:
    """Reset the global container (for testing)."""
    global _container
    if _container is not None:
        _container.reset()
    _container = None


__all__ = ["ServiceContainer", "get_container", "reset_container"]
