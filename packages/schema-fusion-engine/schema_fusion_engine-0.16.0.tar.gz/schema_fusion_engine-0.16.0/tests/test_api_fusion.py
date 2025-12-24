"""Integration tests for fusion API endpoints."""

from unittest.mock import patch

from fastapi.testclient import TestClient


class TestFusionViewEndpoint:
    """Test cases for fusion view endpoints."""

    @patch("src.api.fusion.generate_fusion_from_matches")
    def test_create_fusion_view_success(self, mock_generate, client: TestClient):
        """Test successful fusion view creation."""
        mock_generate.return_value = {
            "status": "success",
            "message": "View created successfully",
            "view_name": "global_users",
            "sql": "CREATE VIEW memory.default.global_users AS SELECT ...",
        }

        response = client.post(
            "/fusion/create-view",
            json={
                "view_name": "global_users",
                "source_a": {
                    "catalog": "postgres",
                    "schema": "public",
                    "table": "users",
                },
                "source_b": {
                    "catalog": "mongo",
                    "schema": "testdb",
                    "table": "customers",
                },
                "matches": [
                    {"source_col": "name", "target_col": "name", "confidence": 1.0},
                    {"source_col": "email", "target_col": "email", "confidence": 1.0},
                ],
                "join_key_a": "id",
                "join_key_b": "_id",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["view_name"] == "global_users"
        assert "sql" in data

    @patch("src.api.fusion.generate_fusion_from_matches")
    def test_create_fusion_view_error(self, mock_generate, client: TestClient):
        """Test error handling in fusion view creation."""
        mock_generate.return_value = {
            "status": "error",
            "message": "Invalid SQL generated",
            "sql": "CREATE VIEW ...",
        }

        response = client.post(
            "/fusion/create-view",
            json={
                "view_name": "invalid_view",
                "source_a": {"catalog": "postgres", "schema": "public", "table": "users"},
                "source_b": {"catalog": "mongo", "schema": "testdb", "table": "customers"},
                "matches": [],
                "join_key_a": "id",
                "join_key_b": "_id",
            },
        )

        assert response.status_code == 400
        assert "Invalid SQL generated" in response.json()["detail"]

    @patch("src.api.fusion.list_tables")
    def test_list_views(self, mock_list_tables, client: TestClient):
        """Test listing fusion views."""
        mock_list_tables.return_value = [
            {"name": "view1"},
            {"name": "view2"},
        ]

        response = client.get("/fusion/views?catalog=memory&schema=default")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["views"]) == 2

    @patch("src.api.fusion.drop_trino_view")
    def test_delete_view(self, mock_drop_view, client: TestClient):
        """Test deleting a fusion view."""
        mock_drop_view.return_value = {
            "status": "success",
            "message": "View memory.default.test_view dropped successfully",
            "view_name": "test_view",
        }

        response = client.delete("/fusion/views/test_view?catalog=memory&schema=default")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "test_view" in data["message"]
        mock_drop_view.assert_called_once_with("test_view", "memory", "default")

    @patch("src.api.fusion.drop_trino_view")
    def test_delete_view_error(self, mock_drop_view, client: TestClient):
        """Test error handling when deleting a view."""
        mock_drop_view.side_effect = Exception("View does not exist")

        response = client.delete("/fusion/views/nonexistent?catalog=memory&schema=default")

        assert response.status_code == 400
        assert "Failed to drop view" in response.json()["detail"]

    @patch("src.api.fusion.update_fusion_view")
    def test_update_view_success(self, mock_update, client: TestClient):
        """Test successful fusion view update."""
        mock_update.return_value = {
            "status": "success",
            "message": "View test_view updated successfully",
            "view_name": "test_view",
            "sql": "CREATE OR REPLACE VIEW memory.default.test_view AS SELECT ...",
        }

        response = client.put(
            "/fusion/views/test_view",
            json={
                "view_name": "test_view",
                "source_a": {
                    "catalog": "postgres",
                    "schema": "public",
                    "table": "users",
                },
                "source_b": {
                    "catalog": "mongo",
                    "schema": "testdb",
                    "table": "customers",
                },
                "matches": [
                    {"source_col": "name", "target_col": "name", "confidence": 1.0},
                ],
                "join_key_a": "id",
                "join_key_b": "_id",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "updated" in data["message"].lower()
        assert data["view_name"] == "test_view"

    @patch("src.api.fusion.update_fusion_view")
    def test_update_view_name_mismatch(self, mock_update, client: TestClient):
        """Test update fails when view name in path doesn't match request body."""
        response = client.put(
            "/fusion/views/test_view",
            json={
                "view_name": "different_view",
                "source_a": {"catalog": "postgres", "schema": "public", "table": "users"},
                "source_b": {"catalog": "mongo", "schema": "testdb", "table": "customers"},
                "matches": [],
                "join_key_a": "id",
                "join_key_b": "_id",
            },
        )

        assert response.status_code == 400
        assert "does not match" in response.json()["detail"]
