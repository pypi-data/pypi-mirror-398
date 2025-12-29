"""Shard merging logic for scope resolution."""

from daimyo.application.rule_service import RuleMergingService
from daimyo.domain import MergedScope, Scope
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ShardMerger:
    """Merges scope shards and handles parent-child scope merging."""

    def __init__(self, rule_merger: RuleMergingService):
        self.rule_merger = rule_merger

    def merge_parent_shards(self, local_parent: Scope, remote_parent: Scope) -> Scope:
        """Merge local and remote shards of a parent scope.

        Remote shard is treated as the base, local shard extends it.

        :param local_parent: Local version of the parent scope
        :type local_parent: Scope
        :param remote_parent: Remote version of the parent scope
        :type remote_parent: Scope
        :returns: Merged scope
        :rtype: Scope
        """
        logger.debug(
            f"Merging parent shards: local={local_parent.source}, remote={remote_parent.source}"
        )

        merged_commandments = self.rule_merger.merge_commandments(
            remote_parent.commandments, local_parent.commandments
        )

        merged_suggestions = self.rule_merger.merge_suggestions(
            remote_parent.suggestions, local_parent.suggestions
        )

        merged_scope = Scope(
            metadata=local_parent.metadata,
            commandments=merged_commandments,
            suggestions=merged_suggestions,
            source=f"{remote_parent.source}+{local_parent.source}",
        )

        return merged_scope

    def merge_child_with_parent(self, child: MergedScope, parent: MergedScope) -> MergedScope:
        """Merge child scope with parent scope.

        Child takes precedence for metadata.
        Rules are merged according to merging algorithm.

        :param child: Child scope (higher precedence)
        :type child: MergedScope
        :param parent: Parent scope (lower precedence)
        :type parent: MergedScope
        :returns: Merged scope
        :rtype: MergedScope
        """
        logger.debug(
            f"Merging scopes: parent sources={parent.sources}, child sources={child.sources}"
        )

        merged_commandments = self.rule_merger.merge_commandments(
            parent.commandments, child.commandments
        )

        merged_suggestions = self.rule_merger.merge_suggestions(
            parent.suggestions, child.suggestions
        )

        return MergedScope(
            metadata=child.metadata,
            commandments=merged_commandments,
            suggestions=merged_suggestions,
            sources=parent.sources + child.sources,
        )


__all__ = ["ShardMerger"]
