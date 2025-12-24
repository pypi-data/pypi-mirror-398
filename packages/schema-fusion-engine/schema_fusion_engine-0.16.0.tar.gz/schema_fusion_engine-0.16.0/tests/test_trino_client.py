"""Unit tests for Trino client."""

from unittest.mock import Mock, patch

import pytest

from src.core.query.trino_client import TrinoClient


class TestTrinoClient:
    """Test cases for TrinoClient class."""

    def test_init_with_defaults(self, monkeypatch):
        """Test TrinoClient initialization with default settings."""
        with patch("src.core.query.trino_client.settings") as mock_settings:
            mock_settings.trino_host = "localhost"
            mock_settings.trino_port = 8080
            mock_settings.trino_user = "test_user"
            mock_settings.connection_pool_size = 5

            client = TrinoClient()
            assert client.host == "localhost"
            assert client.port == 8080
            assert client.user == "test_user"

    def test_init_with_custom_params(self):
        """Test TrinoClient initialization with custom parameters."""
        client = TrinoClient(host="custom_host", port=9000, user="custom_user")
        assert client.host == "custom_host"
        assert client.port == 9000
        assert client.user == "custom_user"

    @patch("trino.dbapi.connect")
    def test_get_connection(self, mock_connect):
        """Test getting a Trino connection."""
        mock_conn = Mock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_connect.return_value = mock_conn

        client = TrinoClient(host="localhost", port=8080, user="test", use_pool=False)
        with client.get_connection(catalog="test_catalog", schema="test_schema") as conn:
            assert conn == mock_conn

        mock_connect.assert_called_once_with(
            host="localhost",
            port=8080,
            user="test",
            catalog="test_catalog",
            schema="test_schema",
        )
        mock_conn.close.assert_called_once()

    @patch("trino.dbapi.connect")
    def test_execute_query(self, mock_connect):
        """Test executing a query."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.description = [("col1",), ("col2",)]
        mock_cursor.fetchall.return_value = [("value1", "value2"), ("value3", "value4")]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_connect.return_value = mock_conn

        client = TrinoClient(host="localhost", port=8080, user="test")
        results = client.execute_query("SELECT * FROM test", catalog="test_catalog")

        assert results == [("value1", "value2"), ("value3", "value4")]
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test")
        mock_cursor.fetchall.assert_called_once()

    @patch("src.core.query.trino_client.TrinoClient.execute_query")
    def test_get_catalogs(self, mock_execute):
        """Test getting list of catalogs."""
        mock_execute.return_value = [("postgres",), ("mongo",), ("memory",)]

        client = TrinoClient()
        catalogs = client.get_catalogs()

        assert catalogs == ["postgres", "mongo", "memory"]
        mock_execute.assert_called_once_with("SHOW CATALOGS")

    @patch("src.core.query.trino_client.TrinoClient.execute_query")
    def test_get_schemas(self, mock_execute):
        """Test getting list of schemas for a catalog."""
        mock_execute.return_value = [("public",), ("test",)]

        client = TrinoClient()
        schemas = client.get_schemas("postgres")

        assert schemas == ["public", "test"]
        mock_execute.assert_called_once_with("SHOW SCHEMAS FROM postgres")

    @patch("src.core.query.trino_client.TrinoClient.execute_query")
    def test_get_tables(self, mock_execute):
        """Test getting list of tables."""
        mock_execute.return_value = [("users",), ("orders",)]

        client = TrinoClient()
        tables = client.get_tables("postgres", "public")

        assert tables == [{"name": "users"}, {"name": "orders"}]
        mock_execute.assert_called_once_with("SHOW TABLES FROM postgres.public")

    @patch("src.core.query.trino_client.TrinoClient.execute_query")
    def test_get_table_info(self, mock_execute):
        """Test getting table information."""
        mock_execute.return_value = [
            ("id", "integer", None, None),
            ("name", "varchar", None, None),
            ("email", "varchar", None, "User email"),
        ]

        client = TrinoClient()
        table_info = client.get_table_info("postgres", "public", "users")

        assert table_info["catalog"] == "postgres"
        assert table_info["schema"] == "public"
        assert table_info["table"] == "users"
        assert len(table_info["columns"]) == 3
        assert table_info["columns"][0]["name"] == "id"
        assert table_info["columns"][0]["type"] == "integer"
        assert table_info["columns"][2]["comment"] == "User email"

    @patch("src.core.query.trino_client.TrinoClient.execute_query")
    def test_get_catalogs_error_handling(self, mock_execute):
        """Test error handling in get_catalogs."""
        mock_execute.side_effect = Exception("Connection failed")

        client = TrinoClient()
        with pytest.raises(Exception, match="Failed to fetch catalogs"):
            client.get_catalogs()
