"""Protocol definitions for domain interfaces."""

from __future__ import annotations

from typing import Protocol

from .models import MergedScope, Scope


class ScopeRepository(Protocol):
    """Abstract interface for scope storage and retrieval."""

    def get_scope(self, name: str) -> Scope | None:
        """Retrieve a scope by name.

        :param name: The scope name
        :type name: str
        :returns: The scope if found, None otherwise
        :rtype: Optional[Scope]
        """

    def list_scopes(self) -> list[str]:
        """List all available scope names.

        :returns: List of scope names
        :rtype: list[str]
        """


class RemoteScopeClient(Protocol):
    """Abstract interface for retrieving scopes from remote servers."""

    def fetch_scope(self, url: str, scope_name: str) -> Scope | None:
        """Fetch a scope from a remote server.

        :param url: The base URL of the remote server
        :type url: str
        :param scope_name: The name of the scope to fetch
        :type scope_name: str
        :returns: The scope if found, None otherwise
        :rtype: Optional[Scope]
        :raises RemoteServerError: If the remote server is unreachable or returns an error
        """


class FormatterProtocol(Protocol):
    """Abstract interface for formatting merged scopes."""

    def format(self, scope: MergedScope) -> str | dict:
        """Format a merged scope for output.

        :param scope: The merged scope to format
        :type scope: MergedScope
        :returns: Formatted output as string or dict
        :rtype: str | dict
        """


__all__ = ["ScopeRepository", "RemoteScopeClient", "FormatterProtocol"]
