"""Circular dependency detection for scope resolution."""

from daimyo.domain import CircularDependencyError, InheritanceDepthExceededError
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)


class CircularDependencyDetector:
    """Detects circular dependencies and enforces inheritance depth limits."""

    def __init__(self, max_depth: int):
        self.max_depth = max_depth

    def check_and_mark(self, scope_name: str, visited: set[str], depth: int) -> set[str]:
        """Check for circular dependency and depth limit, then mark scope as visited.

        :param scope_name: Scope name to check
        :type scope_name: str
        :param visited: Set of already visited scopes
        :type visited: set[str]
        :param depth: Current recursion depth
        :type depth: int
        :returns: New visited set with scope_name added
        :rtype: set[str]
        :raises CircularDependencyError: If scope is already in visited set
        :raises InheritanceDepthExceededError: If depth exceeds max_depth
        """
        if scope_name in visited:
            raise CircularDependencyError(
                f"Circular dependency detected: '{scope_name}' already in chain"
            )

        if depth > self.max_depth:
            raise InheritanceDepthExceededError(
                f"Maximum inheritance depth ({self.max_depth}) exceeded"
            )

        logger.debug(f"Marking scope '{scope_name}' as visited at depth {depth}")
        new_visited = visited.copy()
        new_visited.add(scope_name)
        return new_visited


__all__ = ["CircularDependencyDetector"]
