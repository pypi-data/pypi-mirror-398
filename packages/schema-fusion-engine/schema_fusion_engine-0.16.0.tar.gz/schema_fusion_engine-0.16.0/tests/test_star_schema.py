"""Integration tests for star schema functionality."""

from unittest.mock import MagicMock, patch

from src.core.fusion.star_schema import (
    create_star_schema,
    delete_star_schema,
    generate_star_schema_query,
    get_star_schema,
    list_star_schemas,
)


class TestCreateStarSchema:
    """Test cases for create_star_schema function."""

    @patch("src.core.fusion.star_schema.trino_client")
    @patch("src.core.fusion.star_schema.get_session")
    def test_create_star_schema_success(self, mock_get_session, mock_trino_client):
        """Test successful star schema creation."""
        # Mock Trino client
        mock_trino_client.get_tables.return_value = [
            {"name": "test_fusion_view"},
            {"name": "customer_fusion_view"},
        ]
        mock_trino_client.execute_query.return_value = None

        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            None  # No existing schema
        )

        star_schema_def = {
            "name": "sales_star",
            "fact_table": {
                "name": "sales_facts",
                "source_view": "test_fusion_view",
                "measures": [
                    {"name": "total_sales", "aggregation": "SUM", "source_column": "amount"}
                ],
                "dimension_keys": ["customer_id"],
            },
            "dimensions": [
                {
                    "name": "customer_dim",
                    "source_view": "customer_fusion_view",
                    "key_column": "customer_id",
                    "attributes": [{"name": "customer_name", "source_column": "name"}],
                }
            ],
        }

        result = create_star_schema(star_schema_def)

        assert result["status"] == "success"
        assert "sales_star" in result["message"]
        assert result["sql"] is not None
        assert "CREATE OR REPLACE VIEW" in result["sql"]
        assert mock_trino_client.execute_query.call_count == 2  # Dimension view + fact view

    @patch("src.core.fusion.star_schema.trino_client")
    def test_create_star_schema_missing_source_view(self, mock_trino_client):
        """Test star schema creation with missing source view."""
        mock_trino_client.get_tables.return_value = []

        star_schema_def = {
            "name": "sales_star",
            "fact_table": {
                "name": "sales_facts",
                "source_view": "nonexistent_view",
                "measures": [],
                "dimension_keys": [],
            },
            "dimensions": [],
        }

        result = create_star_schema(star_schema_def)

        assert result["status"] == "error"
        assert "does not exist" in result["message"]

    def test_create_star_schema_missing_name(self):
        """Test star schema creation without name."""
        star_schema_def = {
            "fact_table": {
                "name": "sales_facts",
                "source_view": "test_view",
                "measures": [],
                "dimension_keys": [],
            },
            "dimensions": [],
        }

        result = create_star_schema(star_schema_def)

        assert result["status"] == "error"
        assert "name is required" in result["message"]


class TestGenerateStarSchemaQuery:
    """Test cases for generate_star_schema_query function."""

    @patch("src.core.fusion.star_schema.get_session")
    def test_generate_star_schema_query_success(self, mock_get_session):
        """Test successful OLAP query generation."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_schema = MagicMock()
        mock_schema.name = "sales_star"
        mock_schema.fact_table_def = {
            "name": "sales_facts",
            "source_view": "test_fusion_view",
            "measures": [{"name": "total_sales", "aggregation": "SUM", "source_column": "amount"}],
            "dimension_keys": ["customer_id"],
        }
        mock_schema.dimensions_def = [
            {
                "name": "customer_dim",
                "source_view": "customer_fusion_view",
                "key_column": "customer_id",
                "attributes": [{"name": "customer_name", "source_column": "name"}],
            }
        ]
        mock_schema.fact_view_name = "sales_star_sales_facts"
        mock_schema.dimension_view_names = ["sales_star_customer_dim"]

        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_schema

        result = generate_star_schema_query(
            star_schema_name="sales_star",
            measures=["total_sales"],
            dimensions=["customer_name"],
        )

        assert result["status"] == "success"
        assert result["sql"] is not None
        assert "SELECT" in result["sql"]
        assert "SUM(total_sales)" in result["sql"] or "SUM" in result["sql"]
        assert "GROUP BY" in result["sql"]

    @patch("src.core.fusion.star_schema.get_session")
    def test_generate_star_schema_query_not_found(self, mock_get_session):
        """Test query generation for non-existent star schema."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result = generate_star_schema_query(
            star_schema_name="nonexistent",
            measures=["total_sales"],
        )

        assert result["status"] == "error"
        assert "not found" in result["message"]


class TestListStarSchemas:
    """Test cases for list_star_schemas function."""

    @patch("src.core.fusion.star_schema.get_session")
    def test_list_star_schemas_success(self, mock_get_session):
        """Test listing star schemas."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        from datetime import datetime

        mock_schema1 = MagicMock()
        mock_schema1.name = "sales_star"
        mock_schema1.fact_table_def = {"name": "sales_facts"}
        mock_schema1.dimensions_def = [{"name": "customer_dim"}]
        mock_schema1.created_at = datetime(2025, 1, 1)

        mock_schema2 = MagicMock()
        mock_schema2.name = "orders_star"
        mock_schema2.fact_table_def = {"name": "orders_facts"}
        mock_schema2.dimensions_def = []
        mock_schema2.created_at = datetime(2025, 1, 2)

        mock_session.query.return_value.all.return_value = [mock_schema1, mock_schema2]

        result = list_star_schemas()

        assert len(result) == 2
        assert result[0]["name"] == "sales_star"
        assert result[0]["fact_table"] == "sales_facts"
        assert result[0]["dimension_count"] == 1
        assert result[1]["name"] == "orders_star"
        assert result[1]["dimension_count"] == 0


class TestGetStarSchema:
    """Test cases for get_star_schema function."""

    @patch("src.core.fusion.star_schema.get_session")
    def test_get_star_schema_success(self, mock_get_session):
        """Test getting star schema by name."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        from datetime import datetime

        mock_schema = MagicMock()
        mock_schema.name = "sales_star"
        mock_schema.description = "Sales star schema"
        mock_schema.fact_table_def = {"name": "sales_facts"}
        mock_schema.dimensions_def = [{"name": "customer_dim"}]
        mock_schema.fact_view_name = "sales_star_sales_facts"
        mock_schema.dimension_view_names = ["sales_star_customer_dim"]
        mock_schema.created_at = datetime(2025, 1, 1)
        mock_schema.updated_at = datetime(2025, 1, 2)

        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_schema

        result = get_star_schema("sales_star")

        assert result is not None
        assert result["name"] == "sales_star"
        assert result["description"] == "Sales star schema"
        assert result["fact_table"]["name"] == "sales_facts"

    @patch("src.core.fusion.star_schema.get_session")
    def test_get_star_schema_not_found(self, mock_get_session):
        """Test getting non-existent star schema."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result = get_star_schema("nonexistent")

        assert result is None


class TestDeleteStarSchema:
    """Test cases for delete_star_schema function."""

    @patch("src.core.fusion.star_schema.trino_client")
    @patch("src.core.fusion.star_schema.get_session")
    def test_delete_star_schema_success(self, mock_get_session, mock_trino_client):
        """Test successful star schema deletion."""
        mock_trino_client.execute_query.return_value = None

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_schema = MagicMock()
        mock_schema.fact_view_name = "sales_star_sales_facts"
        mock_schema.dimension_view_names = ["sales_star_customer_dim"]

        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_schema

        result = delete_star_schema("sales_star")

        assert result["status"] == "success"
        assert "deleted successfully" in result["message"]
        assert mock_trino_client.execute_query.call_count == 2  # Fact view + dimension view
        mock_session.delete.assert_called_once_with(mock_schema)
        mock_session.commit.assert_called_once()

    @patch("src.core.fusion.star_schema.get_session")
    def test_delete_star_schema_not_found(self, mock_get_session):
        """Test deleting non-existent star schema."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result = delete_star_schema("nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["message"]
