"""Integration tests for REST API."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(temp_rules_dir, monkeypatch):
    """Create a test client with temporary rules directory."""
    monkeypatch.setenv("DAIMYO_RULES_PATH", str(temp_rules_dir))

    from daimyo.presentation.rest.app import app

    return TestClient(app)


class TestRestAPI:
    """Integration tests for REST API endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "Daimyo" in data["service"]

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_get_scope_index(self, client):
        """Test getting scope index."""
        response = client.get("/api/v1/scopes/test-scope/index")
        assert response.status_code == 200
        data = response.json()

        assert data["scope_name"] == "test-scope"
        assert "commandments" in data
        assert "suggestions" in data
        assert isinstance(data["commandments"], list)
        assert isinstance(data["suggestions"], list)

    def test_get_scope_index_not_found(self, client):
        """Test getting index for non-existent scope."""
        response = client.get("/api/v1/scopes/nonexistent/index")
        assert response.status_code == 404

    def test_get_scope_rules_yaml(self, client):
        """Test getting rules in YAML format."""
        response = client.get("/api/v1/scopes/test-scope/rules?format=yaml-multi-doc")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-yaml; charset=utf-8"
        assert "---" in response.text  # Multi-document separator

    def test_get_scope_rules_json(self, client):
        """Test getting rules in JSON format."""
        response = client.get("/api/v1/scopes/test-scope/rules?format=json")
        assert response.status_code == 200
        data = response.json()

        assert "metadata" in data
        assert "commandments" in data
        assert "suggestions" in data

    def test_get_scope_rules_with_filter(self, client):
        """Test getting rules with category filter."""
        response = client.get(
            "/api/v1/scopes/test-scope/rules?format=json&categories=python.testing"
        )
        assert response.status_code == 200
        data = response.json()

        commandments = data["commandments"]
        assert "python.testing" in commandments

    def test_get_scope_rules_invalid_format(self, client):
        """Test getting rules with invalid format."""
        response = client.get("/api/v1/scopes/test-scope/rules?format=invalid")
        assert response.status_code == 400

    def test_api_docs_available(self, client):
        """Test that API documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200


__all__ = ["TestRestAPI"]
