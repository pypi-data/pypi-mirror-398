"""Integration tests for matching API endpoint."""

from unittest.mock import patch

from fastapi.testclient import TestClient


class TestMatchingEndpoint:
    """Test cases for POST /fusion/match endpoint."""

    @patch("src.api.matching.match_tables_with_cache")
    def test_match_schemas_success(self, mock_match, client: TestClient):
        """Test successful schema matching."""
        mock_match.return_value = {
            "source": {
                "catalog": "postgres",
                "schema": "public",
                "table": "users",
                "columns": ["id", "name", "email"],
            },
            "target": {
                "catalog": "mongo",
                "schema": "testdb",
                "table": "customers",
                "columns": ["_id", "name", "email"],
            },
            "matches": [
                {"source_col": "name", "target_col": "name", "confidence": 1.0},
                {"source_col": "email", "target_col": "email", "confidence": 1.0},
            ],
            "match_count": 2,
            "threshold": 0.8,
        }

        response = client.post(
            "/fusion/match",
            json={
                "source_catalog": "postgres",
                "source_schema": "public",
                "source_table": "users",
                "target_catalog": "mongo",
                "target_schema": "testdb",
                "target_table": "customers",
                "threshold": 0.8,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["match_count"] == 2
        assert len(data["matches"]) == 2
        assert data["threshold"] == 0.8
        mock_match.assert_called_once()

    @patch("src.api.matching.match_tables_with_cache")
    def test_match_schemas_error(self, mock_match, client: TestClient):
        """Test error handling in schema matching."""
        mock_match.side_effect = Exception("Table not found")

        response = client.post(
            "/fusion/match",
            json={
                "source_catalog": "postgres",
                "source_schema": "public",
                "source_table": "nonexistent",
                "target_catalog": "mongo",
                "target_schema": "testdb",
                "target_table": "nonexistent",
                "threshold": 0.8,
            },
        )

        assert response.status_code == 400
        assert "Failed to match schemas" in response.json()["detail"]
