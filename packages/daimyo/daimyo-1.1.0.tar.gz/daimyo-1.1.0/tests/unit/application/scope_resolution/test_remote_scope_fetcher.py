"""Tests for RemoteScopeFetcher component."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from daimyo.application.scope_resolution.remote_scope_fetcher import RemoteScopeFetcher
from daimyo.domain import (
    RemoteScopeClient,
    RemoteScopeUnavailableError,
    RemoteServerError,
    Scope,
    ScopeMetadata,
)


class TestRemoteScopeFetcher:
    """Test suite for RemoteScopeFetcher."""

    def test_fetcher_initialization_with_client(self):
        """Test fetcher can be initialized with client and URL."""
        mock_client = Mock(spec=RemoteScopeClient)
        fetcher = RemoteScopeFetcher(
            remote_client=mock_client, master_url="https://example.com"
        )

        assert fetcher.remote_client is mock_client
        assert fetcher.master_url == "https://example.com"

    def test_fetcher_initialization_without_client(self):
        """Test fetcher can be initialized without client."""
        fetcher = RemoteScopeFetcher(remote_client=None, master_url="https://example.com")

        assert fetcher.remote_client is None
        assert fetcher.master_url == "https://example.com"

    def test_fetcher_initialization_without_url(self):
        """Test fetcher can be initialized without URL."""
        mock_client = Mock(spec=RemoteScopeClient)
        fetcher = RemoteScopeFetcher(remote_client=mock_client, master_url=None)

        assert fetcher.remote_client is mock_client
        assert fetcher.master_url is None

    def test_fetch_scope_success(self, sample_scope):
        """Test successful scope fetch from remote server."""
        mock_client = Mock(spec=RemoteScopeClient)
        mock_client.fetch_scope.return_value = sample_scope

        fetcher = RemoteScopeFetcher(
            remote_client=mock_client, master_url="https://example.com"
        )

        result = fetcher.fetch_scope("test-scope")

        assert result is sample_scope
        mock_client.fetch_scope.assert_called_once_with("https://example.com", "test-scope")

    def test_fetch_scope_no_client_returns_none(self):
        """Test fetch returns None when no client configured."""
        fetcher = RemoteScopeFetcher(remote_client=None, master_url="https://example.com")

        result = fetcher.fetch_scope("test-scope")

        assert result is None

    def test_fetch_scope_no_url_returns_none(self):
        """Test fetch returns None when no URL configured."""
        mock_client = Mock(spec=RemoteScopeClient)
        fetcher = RemoteScopeFetcher(remote_client=mock_client, master_url=None)

        result = fetcher.fetch_scope("test-scope")

        assert result is None
        mock_client.fetch_scope.assert_not_called()

    def test_fetch_scope_no_client_no_url_returns_none(self):
        """Test fetch returns None when neither client nor URL configured."""
        fetcher = RemoteScopeFetcher(remote_client=None, master_url=None)

        result = fetcher.fetch_scope("test-scope")

        assert result is None

    def test_fetch_scope_remote_unavailable_returns_none(self):
        """Test fetch returns None when remote scope is unavailable."""
        mock_client = Mock(spec=RemoteScopeClient)
        mock_client.fetch_scope.side_effect = RemoteScopeUnavailableError(
            "Service temporarily unavailable"
        )

        fetcher = RemoteScopeFetcher(
            remote_client=mock_client, master_url="https://example.com"
        )

        result = fetcher.fetch_scope("test-scope")

        assert result is None
        mock_client.fetch_scope.assert_called_once()

    def test_fetch_scope_remote_server_error_returns_none(self):
        """Test fetch returns None when remote server returns error."""
        mock_client = Mock(spec=RemoteScopeClient)
        mock_client.fetch_scope.side_effect = RemoteServerError(
            "Server error", url="https://example.com", status_code=500
        )

        fetcher = RemoteScopeFetcher(
            remote_client=mock_client, master_url="https://example.com"
        )

        result = fetcher.fetch_scope("test-scope")

        assert result is None

    def test_fetch_scope_connection_error_returns_none(self):
        """Test fetch returns None on connection errors."""
        mock_client = Mock(spec=RemoteScopeClient)
        mock_client.fetch_scope.side_effect = ConnectionError("Cannot connect to remote")

        fetcher = RemoteScopeFetcher(
            remote_client=mock_client, master_url="https://example.com"
        )

        result = fetcher.fetch_scope("test-scope")

        assert result is None

    def test_fetch_scope_timeout_returns_none(self):
        """Test fetch returns None on timeout."""
        mock_client = Mock(spec=RemoteScopeClient)
        mock_client.fetch_scope.side_effect = TimeoutError("Request timed out")

        fetcher = RemoteScopeFetcher(
            remote_client=mock_client, master_url="https://example.com"
        )

        result = fetcher.fetch_scope("test-scope")

        assert result is None

    def test_fetch_scope_generic_exception_returns_none(self):
        """Test fetch returns None on any unexpected exception."""
        mock_client = Mock(spec=RemoteScopeClient)
        mock_client.fetch_scope.side_effect = Exception("Unexpected error")

        fetcher = RemoteScopeFetcher(
            remote_client=mock_client, master_url="https://example.com"
        )

        result = fetcher.fetch_scope("test-scope")

        assert result is None

    def test_fetch_scope_none_return_from_client(self):
        """Test fetch handles None return from client gracefully."""
        mock_client = Mock(spec=RemoteScopeClient)
        mock_client.fetch_scope.return_value = None

        fetcher = RemoteScopeFetcher(
            remote_client=mock_client, master_url="https://example.com"
        )

        result = fetcher.fetch_scope("test-scope")

        assert result is None

    def test_fetch_scope_passes_correct_parameters(self):
        """Test fetch passes correct URL and scope name to client."""
        mock_client = Mock(spec=RemoteScopeClient)
        master_url = "https://master.example.com/api"
        scope_name = "python-general"

        fetcher = RemoteScopeFetcher(remote_client=mock_client, master_url=master_url)
        fetcher.fetch_scope(scope_name)

        mock_client.fetch_scope.assert_called_once_with(master_url, scope_name)

    def test_fetch_multiple_scopes(self, sample_scope):
        """Test fetching multiple scopes in sequence."""
        mock_client = Mock(spec=RemoteScopeClient)

        scope_a = Scope(
            metadata=ScopeMetadata(name="scope-a", description="Scope A"),
            source="remote",
        )
        scope_b = Scope(
            metadata=ScopeMetadata(name="scope-b", description="Scope B"),
            source="remote",
        )

        mock_client.fetch_scope.side_effect = [scope_a, scope_b]

        fetcher = RemoteScopeFetcher(
            remote_client=mock_client, master_url="https://example.com"
        )

        result_a = fetcher.fetch_scope("scope-a")
        result_b = fetcher.fetch_scope("scope-b")

        assert result_a is scope_a
        assert result_b is scope_b
        assert mock_client.fetch_scope.call_count == 2

    def test_fetch_scope_with_empty_name(self):
        """Test fetch with empty scope name."""
        mock_client = Mock(spec=RemoteScopeClient)
        mock_client.fetch_scope.return_value = None

        fetcher = RemoteScopeFetcher(
            remote_client=mock_client, master_url="https://example.com"
        )

        result = fetcher.fetch_scope("")

        assert result is None
        mock_client.fetch_scope.assert_called_once_with("https://example.com", "")
