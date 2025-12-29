"""Domain-specific exceptions."""

from __future__ import annotations


class DaimyoError(Exception):
    """Base exception for all Daimyo errors."""

class ScopeNotFoundError(DaimyoError):
    """Raised when a requested scope does not exist."""

    def __init__(self, scope_name: str, available_scopes: list[str] | None = None):
        self.scope_name = scope_name
        self.available_scopes = available_scopes

        msg = f"Scope '{scope_name}' not found"
        if available_scopes:
            msg += f". Available scopes: {', '.join(available_scopes[:5])}"
            if len(available_scopes) > 5:
                msg += f" (and {len(available_scopes) - 5} more)"

        super().__init__(msg)

class InvalidScopeError(DaimyoError):
    """Raised when scope data is malformed or invalid."""

class CircularDependencyError(DaimyoError):
    """Raised when a circular parent reference is detected."""

class InheritanceDepthExceededError(CircularDependencyError):
    """Raised when maximum inheritance depth is exceeded."""

class RemoteServerError(DaimyoError):
    """Raised when communication with a remote server fails."""

    def __init__(self, message: str, url: str | None = None, status_code: int | None = None):
        self.url = url
        self.status_code = status_code
        super().__init__(message)

class RemoteScopeUnavailableError(RemoteServerError):
    """Raised when a remote scope is temporarily unavailable."""

class ScopeMergingError(DaimyoError):
    """Raised when merging scopes fails."""

class FormatterError(DaimyoError):
    """Raised when formatting a scope fails."""

class InvalidCategoryError(DaimyoError):
    """Raised when a category specification is invalid."""

class YAMLParseError(DaimyoError):
    """Raised when YAML parsing fails."""

__all__ = [
    "DaimyoError",
    "ScopeNotFoundError",
    "InvalidScopeError",
    "CircularDependencyError",
    "InheritanceDepthExceededError",
    "RemoteServerError",
    "RemoteScopeUnavailableError",
    "ScopeMergingError",
    "FormatterError",
    "InvalidCategoryError",
    "YAMLParseError",
]
