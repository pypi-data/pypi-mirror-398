"""Scope resolution service orchestrating inheritance and sharding."""

from cachetools import TTLCache, cachedmethod

from daimyo.application.rule_service import RuleMergingService
from daimyo.config import settings
from daimyo.domain import MergedScope, RemoteScopeClient, ScopeNotFoundError, ScopeRepository
from daimyo.infrastructure.logging import get_logger

from daimyo.application.scope_resolution.circular_dependency_detector import CircularDependencyDetector
from daimyo.application.scope_resolution.multi_parent_resolver import MultiParentResolver
from daimyo.application.scope_resolution.parent_resolver import ParentResolver
from daimyo.application.scope_resolution.remote_scope_fetcher import RemoteScopeFetcher
from daimyo.application.scope_resolution.shard_merger import ShardMerger

logger = get_logger(__name__)

SCOPE_CACHE_TTL = 1200
SCOPE_CACHE_MAXSIZE = 100


class ScopeResolutionService:
    """Service for resolving scopes with full inheritance and sharding support.

    Handles:
    - Local scope loading
    - Parent scope inheritance
    - Remote scope sharding (same scope name on remote + local)
    - Circular dependency detection
    - Graceful handling of unavailable remote servers
    """

    def __init__(
        self,
        local_repo: ScopeRepository,
        remote_client: RemoteScopeClient | None = None,
        max_depth: int | None = None,
    ):
        self.local_repo = local_repo
        max_inheritance_depth = max_depth or settings.MAX_INHERITANCE_DEPTH

        self.circular_detector = CircularDependencyDetector(max_inheritance_depth)
        self.remote_fetcher = RemoteScopeFetcher(remote_client, settings.MASTER_SERVER_URL)
        self.shard_merger = ShardMerger(RuleMergingService())
        self.parent_resolver = ParentResolver(
            local_repo, self.remote_fetcher, self.shard_merger, self.circular_detector
        )
        self.multi_parent_resolver = MultiParentResolver(self.parent_resolver, self.shard_merger)
        self._cache: TTLCache = TTLCache(maxsize=SCOPE_CACHE_MAXSIZE, ttl=SCOPE_CACHE_TTL)

    @cachedmethod(cache=lambda self: self._cache)
    def resolve_scope(self, name: str) -> MergedScope:
        """Resolve a scope with full inheritance and sharding (cached for 20 minutes).

        Algorithm:
        1. Load local scope
        2. Recursively resolve parent chain
        3. Merge all scopes (parent chain first, then local)

        :param name: Scope name to resolve
        :type name: str
        :returns: Merged scope with all inheritance applied
        :rtype: MergedScope
        :raises ScopeNotFoundError: If scope doesn't exist locally
        :raises CircularDependencyError: If circular parent reference detected
        :raises InheritanceDepthExceededError: If max depth exceeded
        """
        logger.info(f"Resolving scope: {name}")

        visited: set[str] = set()
        visited = self.circular_detector.check_and_mark(name, visited, depth=0)

        local_scope = self.local_repo.get_scope(name)
        if local_scope is None:
            raise ScopeNotFoundError(name)

        result = MergedScope.from_scope(local_scope)

        parent_list = local_scope.metadata.get_parent_list()

        if parent_list:
            if len(parent_list) == 1:
                parent_name = parent_list[0]
                logger.debug(f"Scope '{name}' has single parent: {parent_name}")
                parent_merged = self.parent_resolver.resolve_parent(parent_name, visited, depth=1)
            else:
                logger.debug(f"Scope '{name}' has {len(parent_list)} parents: {parent_list}")
                parent_merged = self.multi_parent_resolver.resolve_multiple_parents(
                    parent_list, visited, depth=1
                )

            if parent_merged:
                result = self.shard_merger.merge_child_with_parent(result, parent_merged)

        logger.info(f"Resolved scope '{name}' with {len(result.sources)} sources: {result.sources}")
        return result


__all__ = ["ScopeResolutionService"]
