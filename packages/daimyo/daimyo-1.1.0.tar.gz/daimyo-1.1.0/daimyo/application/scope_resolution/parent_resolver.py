"""Parent scope resolution with recursive inheritance chain handling."""

from daimyo.domain import MergedScope, ScopeRepository
from daimyo.infrastructure.logging import get_logger

from daimyo.application.scope_resolution.circular_dependency_detector import CircularDependencyDetector
from daimyo.application.scope_resolution.remote_scope_fetcher import RemoteScopeFetcher
from daimyo.application.scope_resolution.shard_merger import ShardMerger

logger = get_logger(__name__)


class ParentResolver:
    """Resolves parent scopes recursively with inheritance chain support."""

    def __init__(
        self,
        local_repo: ScopeRepository,
        remote_fetcher: RemoteScopeFetcher,
        shard_merger: ShardMerger,
        circular_detector: CircularDependencyDetector,
    ):
        self.local_repo = local_repo
        self.remote_fetcher = remote_fetcher
        self.shard_merger = shard_merger
        self.circular_detector = circular_detector

    def resolve_parent(
        self, parent_name: str, visited: set[str], depth: int
    ) -> MergedScope | None:
        """Resolve parent scope by name, checking both local and remote sources.

        Algorithm:
        1. Try to load parent locally
        2. Try to load parent from master server (if configured)
        3. If found in both places, merge them (parent sharding)
        4. Recursively resolve the parent's parent chain
        5. Return the fully merged parent

        :param parent_name: Name of the parent scope
        :type parent_name: str
        :param visited: Set of visited scopes (for cycle detection)
        :type visited: set[str]
        :param depth: Current recursion depth
        :type depth: int
        :returns: Merged parent scope if found, None otherwise
        :rtype: MergedScope | None
        """
        visited = self.circular_detector.check_and_mark(parent_name, visited, depth)

        logger.debug(f"Resolving parent '{parent_name}' at depth {depth}")

        local_parent = self.local_repo.get_scope(parent_name)
        remote_parent = self.remote_fetcher.fetch_scope(parent_name)

        if local_parent is None and remote_parent is None:
            logger.warning(f"Parent scope '{parent_name}' not found locally or remotely")
            return None

        if local_parent and remote_parent:
            logger.debug(f"Merging local and remote shards of parent '{parent_name}'")
            parent_scope = self.shard_merger.merge_parent_shards(local_parent, remote_parent)
        elif local_parent:
            logger.debug(f"Using local parent '{parent_name}'")
            parent_scope = local_parent
        else:
            logger.debug(f"Using remote parent '{parent_name}'")
            parent_scope = remote_parent

        result = MergedScope.from_scope(parent_scope)

        if parent_scope.metadata.parent:
            grandparent_name = parent_scope.metadata.parent
            logger.debug(f"Parent '{parent_name}' has grandparent: {grandparent_name}")

            grandparent_merged = self.resolve_parent(grandparent_name, visited, depth + 1)

            if grandparent_merged:
                result = self.shard_merger.merge_child_with_parent(result, grandparent_merged)

        return result


__all__ = ["ParentResolver"]
