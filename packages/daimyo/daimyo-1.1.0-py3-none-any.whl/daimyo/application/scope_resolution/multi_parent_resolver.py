"""Multi-parent resolution and merging logic."""

from daimyo.domain import MergedScope
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)


class MultiParentResolver:
    """Resolves and merges multiple parents in priority order."""

    def __init__(self, parent_resolver, shard_merger):
        """Initialize multi-parent resolver.

        :param parent_resolver: ParentResolver instance
        :type parent_resolver: ParentResolver
        :param shard_merger: ShardMerger instance
        :type shard_merger: ShardMerger
        """
        self.parent_resolver = parent_resolver
        self.shard_merger = shard_merger

    def resolve_multiple_parents(
        self, parent_names: list[str], visited: set[str], depth: int
    ) -> MergedScope | None:
        """Resolve multiple parents and merge them in priority order.

        Merge order: parents = [scope1, scope2, scope3]
        - First merge scope3 (lowest priority)
        - Then merge scope2 onto scope3
        - Then merge scope1 onto (scope2+scope3)
        - Result: scope1 overrides scope2 overrides scope3

        :param parent_names: List of parent names in priority order (first = highest)
        :type parent_names: list[str]
        :param visited: Set of visited scopes for cycle detection
        :type visited: set[str]
        :param depth: Current recursion depth
        :type depth: int
        :returns: Merged parent scope or None if no parents found
        :rtype: MergedScope | None
        """
        if not parent_names:
            return None

        logger.debug(f"Resolving {len(parent_names)} parents: {parent_names}")

        resolved_parents: list[MergedScope] = []

        for parent_name in parent_names:
            logger.debug(f"Resolving parent '{parent_name}' at depth {depth}")
            parent_merged = self.parent_resolver.resolve_parent(parent_name, visited, depth)

            if parent_merged is not None:
                resolved_parents.append(parent_merged)
            else:
                logger.warning(f"Parent '{parent_name}' not found, skipping")

        if not resolved_parents:
            logger.warning("No parents found")
            return None

        if len(resolved_parents) == 1:
            logger.debug("Single parent resolved, returning directly")
            return resolved_parents[0]

        logger.debug(f"Merging {len(resolved_parents)} parents in priority order")

        result = resolved_parents[-1]

        for i in range(len(resolved_parents) - 2, -1, -1):
            current_parent = resolved_parents[i]
            result = self.shard_merger.merge_child_with_parent(current_parent, result)
            logger.debug(f"Merged parent {i} ('{parent_names[i]}') with accumulated parents")

        logger.debug(f"Multi-parent merge complete: {len(result.sources)} total sources")
        return result


__all__ = ["MultiParentResolver"]
