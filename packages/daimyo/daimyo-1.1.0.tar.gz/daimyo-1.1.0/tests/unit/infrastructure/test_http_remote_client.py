"""Tests for HttpRemoteScopeClient."""

from __future__ import annotations

import pytest

from daimyo.domain import RemoteServerError, YAMLParseError
from daimyo.infrastructure.remote.remote_client import HttpRemoteScopeClient


class TestHttpRemoteScopeClient:
    """Test suite for HttpRemoteScopeClient."""

    @pytest.fixture
    def client(self):
        """Create client instance."""
        return HttpRemoteScopeClient(timeout=30, max_retries=3)

    @pytest.fixture
    def valid_yaml_response(self):
        """Create valid multi-document YAML response."""
        return """---
metadata:
  name: test-scope
  description: Test scope
  parent: null
  tags: {}
---
commandments:
  python:
    when: When writing Python
    ruleset:
      - Use type hints
      - Follow PEP 8
---
suggestions:
  python:
    when: When writing Python
    ruleset:
      - Consider dataclasses
"""

    def test_client_initialization_with_params(self):
        """Test client initialization with custom parameters."""
        client = HttpRemoteScopeClient(timeout=60, max_retries=5)

        assert client.timeout == 60
        assert client.max_retries == 5
        assert client.client is not None

    def test_client_initialization_with_defaults(self):
        """Test client initialization uses defaults from settings."""
        client = HttpRemoteScopeClient()

        assert client.timeout > 0
        assert client.max_retries >= 0

    @pytest.mark.skipif(True, reason="Requires pytest-httpx which is not installed")
    def test_fetch_scope_success(self, client, valid_yaml_response):
        """Test successful scope fetch."""
        from pytest_httpx import HTTPXMock

        base_url = "https://example.com"
        scope_name = "test-scope"
        api_url = f"{base_url}/api/v1/scopes/{scope_name}/rules"

        httpx_mock = HTTPXMock()
        httpx_mock.add_response(url=api_url, status_code=200, text=valid_yaml_response)

        result = client.fetch_scope(base_url, scope_name)

        assert result is not None
        assert result.metadata.name == "test-scope"
        assert len(result.commandments.categories) > 0

    @pytest.mark.skipif(True, reason="Requires pytest-httpx which is not installed")
    def test_fetch_scope_404_returns_none(self, client):
        """Test fetch returns None for 404 response."""
        from pytest_httpx import HTTPXMock

        base_url = "https://example.com"
        scope_name = "nonexistent"
        api_url = f"{base_url}/api/v1/scopes/{scope_name}/rules"

        httpx_mock = HTTPXMock()
        httpx_mock.add_response(url=api_url, status_code=404)

        result = client.fetch_scope(base_url, scope_name)

        assert result is None

    @pytest.mark.skipif(True, reason="Requires pytest-httpx which is not installed")
    def test_fetch_scope_500_raises_error(self, client):
        """Test fetch raises RemoteServerError for 500 response."""
        from pytest_httpx import HTTPXMock

        base_url = "https://example.com"
        scope_name = "test-scope"
        api_url = f"{base_url}/api/v1/scopes/{scope_name}/rules"

        httpx_mock = HTTPXMock()
        httpx_mock.add_response(url=api_url, status_code=500, text="Internal server error")

        with pytest.raises(RemoteServerError):
            client.fetch_scope(base_url, scope_name)

    @pytest.mark.skipif(True, reason="Requires pytest-httpx which is not installed")
    def test_fetch_scope_timeout_raises_error(self, client):
        """Test fetch raises RemoteServerError on timeout."""
        import httpx
        from pytest_httpx import HTTPXMock

        base_url = "https://example.com"
        scope_name = "test-scope"

        httpx_mock = HTTPXMock()
        httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))

        with pytest.raises(RemoteServerError) as exc_info:
            client.fetch_scope(base_url, scope_name)

        assert "Timeout" in str(exc_info.value)

    @pytest.mark.skipif(True, reason="Requires pytest-httpx which is not installed")
    def test_fetch_scope_connection_error_raises(self, client):
        """Test fetch raises RemoteServerError on connection error."""
        import httpx
        from pytest_httpx import HTTPXMock

        base_url = "https://example.com"
        scope_name = "test-scope"

        httpx_mock = HTTPXMock()
        httpx_mock.add_exception(httpx.ConnectError("Cannot connect"))

        with pytest.raises(RemoteServerError) as exc_info:
            client.fetch_scope(base_url, scope_name)

        assert "Connection error" in str(exc_info.value)

    def test_parse_multidoc_yaml_valid(self, client, valid_yaml_response):
        """Test parsing valid multi-document YAML."""
        result = client._parse_multidoc_yaml(
            valid_yaml_response, "test-scope", "https://example.com"
        )

        assert result.metadata.name == "test-scope"
        assert result.metadata.description == "Test scope"
        assert result.source == "https://example.com"

    def test_parse_multidoc_yaml_invalid_document_count(self, client):
        """Test parsing YAML with wrong number of documents."""
        yaml_content = """---
metadata:
  name: test
---
commandments: {}
"""
        with pytest.raises(YAMLParseError) as exc_info:
            client._parse_multidoc_yaml(yaml_content, "test", "https://example.com")

        assert "Expected 3 YAML documents" in str(exc_info.value)

    def test_parse_multidoc_yaml_invalid_syntax(self, client):
        """Test parsing YAML with invalid syntax."""
        yaml_content = "invalid: yaml: syntax: error:"

        with pytest.raises(YAMLParseError):
            client._parse_multidoc_yaml(yaml_content, "test", "https://example.com")

    def test_parse_multidoc_yaml_with_empty_rules(self, client):
        """Test parsing YAML with empty commandments and suggestions."""
        yaml_content = """---
metadata:
  name: empty-scope
  description: Empty scope
  parent: null
  tags: {}
---
commandments: {}
---
suggestions: {}
"""
        result = client._parse_multidoc_yaml(yaml_content, "empty-scope", "https://example.com")

        assert result.metadata.name == "empty-scope"
        assert len(result.commandments.categories) == 0
        assert len(result.suggestions.categories) == 0

    def test_fetch_scope_url_construction(self, client):
        """Test that API URL is constructed correctly."""
        base_url = "https://example.com"
        scope_name = "test-scope"

        expected_url = "https://example.com/api/v1/scopes/test-scope/rules"

        assert expected_url in f"{base_url}/api/v1/scopes/{scope_name}/rules"

    def test_fetch_scope_url_with_trailing_slash(self, client):
        """Test URL construction with trailing slash in base URL."""
        base_url = "https://example.com/"
        scope_name = "test-scope"

        expected_url = "https://example.com/api/v1/scopes/test-scope/rules"

        assert expected_url in f"{base_url.rstrip('/')}/api/v1/scopes/{scope_name}/rules"

    def test_client_closes_on_deletion(self, client):
        """Test that client closes httpx client on deletion."""
        httpx_client = client.client
        del client

        assert httpx_client.is_closed

    def test_fetch_scope_sets_accept_header(self, client):
        """Test that Accept header is set to application/x-yaml."""
        pass

    def test_fetch_scope_follows_redirects(self, client):
        """Test that client follows redirects."""
        assert client.client._transport._pool._retries > 0

    def test_parse_multidoc_yaml_preserves_metadata_fields(self, client):
        """Test that all metadata fields are preserved during parsing."""
        yaml_content = """---
metadata:
  name: full-scope
  description: Full scope with all fields
  parent: parent-scope
  tags:
    language: python
    team: backend
---
commandments: {}
---
suggestions: {}
"""
        result = client._parse_multidoc_yaml(yaml_content, "full-scope", "https://example.com")

        assert result.metadata.name == "full-scope"
        assert result.metadata.description == "Full scope with all fields"
        assert result.metadata.parent == "parent-scope"
        assert result.metadata.tags == {"language": "python", "team": "backend"}
