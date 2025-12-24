"""Integration tests for query API endpoint."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


class TestQueryEndpoint:
    """Test cases for POST /fusion/query endpoint."""

    @patch("src.api.query.query_executor")
    def test_execute_query_success(self, mock_executor, client: TestClient, sample_query_result):
        """Test successful query execution."""
        from src.core.query.query_executor import QueryResult

        columns, rows = sample_query_result
        mock_executor.execute_async = AsyncMock(
            return_value=QueryResult(
                query="SELECT * FROM postgres.public.users LIMIT 10",
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time_ms=45.2,
                error=None,
            )
        )

        response = client.post(
            "/fusion/query",
            json={
                "query": "SELECT * FROM postgres.public.users LIMIT 10",
                "catalog": "postgres",
                "schema": "public",
                "max_rows": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "SELECT * FROM postgres.public.users LIMIT 10"
        assert data["columns"] == columns
        assert data["row_count"] == len(rows)
        assert data["execution_time_ms"] is not None
        assert data["error"] is None

    @patch("src.api.query.query_executor")
    def test_execute_query_with_max_rows(self, mock_executor, client: TestClient):
        """Test query execution respects max_rows limit."""
        from src.core.query.query_executor import QueryResult

        columns = ["id", "name"]
        rows = [[1, "Alice"], [2, "Bob"]]

        mock_executor.execute_async = AsyncMock(
            return_value=QueryResult(
                query="SELECT * FROM test",
                columns=columns,
                rows=rows,
                row_count=2,
                execution_time_ms=12.5,
                error=None,
            )
        )

        response = client.post(
            "/fusion/query",
            json={
                "query": "SELECT * FROM test",
                "max_rows": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["row_count"] == 2
        mock_executor.execute_async.assert_called_once_with(
            query="SELECT * FROM test",
            catalog=None,
            schema=None,
            max_rows=2,
        )

    @patch("src.api.query.query_executor")
    def test_execute_query_error_handling(self, mock_executor, client: TestClient):
        """Test error handling in query execution."""
        from src.core.query.query_executor import QueryResult

        mock_executor.execute_async = AsyncMock(
            return_value=QueryResult(
                query="SELECT * FROM nonexistent",
                columns=None,
                rows=None,
                row_count=0,
                execution_time_ms=12.5,
                error="Connection failed",
            )
        )

        response = client.post(
            "/fusion/query",
            json={
                "query": "SELECT * FROM nonexistent",
                "max_rows": 100,
            },
        )

        assert response.status_code == 200  # Returns 200 with error in body
        data = response.json()
        assert data["error"] is not None
        assert "Connection failed" in data["error"]
        assert data["columns"] is None
        assert data["rows"] is None
        assert data["execution_time_ms"] is not None

    @patch("src.api.query.query_executor")
    def test_execute_query_without_catalog_schema(self, mock_executor, client: TestClient):
        """Test query execution without catalog and schema."""
        from src.core.query.query_executor import QueryResult

        columns = ["id"]
        rows = [[1]]

        mock_executor.execute_async = AsyncMock(
            return_value=QueryResult(
                query="SELECT 1",
                columns=columns,
                rows=rows,
                row_count=1,
                execution_time_ms=5.0,
                error=None,
            )
        )

        response = client.post(
            "/fusion/query",
            json={
                "query": "SELECT 1",
                "catalog": None,
                "schema": None,
                "max_rows": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None

    @patch("src.api.query.query_executor")
    def test_execute_query_empty_result(self, mock_executor, client: TestClient):
        """Test query execution with empty result set."""
        from src.core.query.query_executor import QueryResult

        mock_executor.execute_async = AsyncMock(
            return_value=QueryResult(
                query="SELECT * FROM empty_table",
                columns=["id"],
                rows=[],
                row_count=0,
                execution_time_ms=8.0,
                error=None,
            )
        )

        response = client.post(
            "/fusion/query",
            json={
                "query": "SELECT * FROM empty_table",
                "max_rows": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["row_count"] == 0
        assert data["rows"] == []

    @patch("src.api.query.query_executor")
    def test_query_validation_rejects_non_select(self, mock_executor, client: TestClient):
        """Test that query validation rejects non-SELECT queries when enabled."""
        from src.core.query.query_executor import QueryResult

        mock_executor.execute_async = AsyncMock(
            return_value=QueryResult(
                query="INSERT INTO users VALUES (1, 'test')",
                columns=None,
                rows=None,
                row_count=0,
                execution_time_ms=0.0,
                error="Query validation failed: Query must start with one of: SELECT",
            )
        )

        response = client.post(
            "/fusion/query",
            json={
                "query": "INSERT INTO users VALUES (1, 'test')",
                "max_rows": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["error"] is not None
        assert "validation failed" in data["error"].lower()
        assert data["row_count"] == 0

    @patch("src.api.query.query_executor")
    def test_query_validation_rejects_too_many_joins(self, mock_executor, client: TestClient):
        """Test that query validation rejects queries with too many JOINs."""
        from src.core.query.query_executor import QueryResult

        # Query with 3 JOINs
        query = "SELECT * FROM a JOIN b ON a.id = b.id JOIN c ON b.id = c.id JOIN d ON c.id = d.id"

        mock_executor.execute_async = AsyncMock(
            return_value=QueryResult(
                query=query,
                columns=None,
                rows=None,
                row_count=0,
                execution_time_ms=0.0,
                error="Query validation failed: Query exceeds maximum JOIN count (2): 4 JOINs found",
            )
        )

        response = client.post(
            "/fusion/query",
            json={
                "query": query,
                "max_rows": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["error"] is not None
        assert "JOIN" in data["error"]
        assert data["row_count"] == 0

    @patch("src.api.query.query_executor")
    def test_query_validation_allows_valid_query(self, mock_executor, client: TestClient):
        """Test that query validation allows valid queries."""
        from src.core.query.query_executor import QueryResult

        columns = ["id"]
        rows = [[1]]

        mock_executor.execute_async = AsyncMock(
            return_value=QueryResult(
                query="SELECT * FROM users",
                columns=columns,
                rows=rows,
                row_count=1,
                execution_time_ms=15.0,
                error=None,
            )
        )

        response = client.post(
            "/fusion/query",
            json={
                "query": "SELECT * FROM users",
                "max_rows": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert data["row_count"] == 1
