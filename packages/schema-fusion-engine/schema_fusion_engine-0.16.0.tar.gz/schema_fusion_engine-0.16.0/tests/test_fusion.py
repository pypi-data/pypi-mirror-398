"""Unit tests for fusion engine."""

from unittest.mock import patch

from src.core.fusion.fusion import (
    apply_fusion,
    generate_fusion_from_matches,
    generate_view_sql,
    update_fusion_view,
    validate_sql,
)
from src.utils.type_converters import (
    TYPE_COERCION_MAP,
    get_common_type,
    normalize_trino_type,
)


class TestGenerateViewSQL:
    """Test cases for generate_view_sql function."""

    def test_generate_view_sql_with_join(self):
        """Test generating SQL for a view with JOIN (vertical partitioning)."""
        mappings = [
            {"global": "id", "source_a": "id", "source_b": "_id"},
            {"global": "name", "source_a": "name", "source_b": "name"},
            {"global": "email", "source_a": "email", "source_b": "email"},
        ]
        source_a = {"catalog": "postgres", "schema": "public", "table": "users"}
        source_b = {"catalog": "mongo", "schema": "testdb", "table": "customers"}
        join_condition = "p.id = m._id"

        sql = generate_view_sql(
            view_name="global_users",
            mappings=mappings,
            source_a=source_a,
            source_b=source_b,
            join_condition=join_condition,
        )

        assert "CREATE OR REPLACE VIEW" in sql
        assert "global_users" in sql
        assert "postgres.public.users" in sql
        assert "mongo.testdb.customers" in sql
        assert "JOIN" in sql
        assert "p.id = m._id" in sql

    def test_generate_view_sql_without_join(self):
        """Test generating SQL for a view without JOIN (horizontal partitioning)."""
        mappings = [
            {"global": "name", "source_a": "name", "source_b": None},
            {"global": "email", "source_a": None, "source_b": "email"},
        ]
        source_a = {"catalog": "postgres", "schema": "public", "table": "users"}
        source_b = {"catalog": "mongo", "schema": "testdb", "table": "customers"}

        sql = generate_view_sql(
            view_name="combined_users",
            mappings=mappings,
            source_a=source_a,
            source_b=source_b,
            join_condition=None,
        )

        assert "CREATE OR REPLACE VIEW" in sql
        assert "UNION ALL" in sql
        assert "postgres.public.users" in sql
        assert "mongo.testdb.customers" in sql

    def test_generate_view_sql_with_coalesce(self):
        """Test generating SQL with COALESCE for matched columns."""
        mappings = [
            {"global": "email", "source_a": "email", "source_b": "email"},
        ]
        source_a = {"catalog": "postgres", "schema": "public", "table": "users"}
        source_b = {"catalog": "mongo", "schema": "testdb", "table": "customers"}
        join_condition = "p.id = m._id"

        sql = generate_view_sql(
            view_name="test_view",
            mappings=mappings,
            source_a=source_a,
            source_b=source_b,
            join_condition=join_condition,
        )

        assert "COALESCE" in sql or "p.email" in sql


class TestApplyFusion:
    """Test cases for apply_fusion function."""

    @patch("src.core.fusion.fusion.trino_client")
    def test_apply_fusion_success(self, mock_client):
        """Test successful view creation."""
        mock_client.execute_query.return_value = None

        view_sql = "CREATE OR REPLACE VIEW memory.default.test_view AS SELECT 1"
        result = apply_fusion(view_sql)

        assert result["status"] == "success"
        assert "message" in result
        assert "sql" in result
        mock_client.execute_query.assert_called_once_with(view_sql)

    @patch("src.core.fusion.fusion.trino_client")
    def test_apply_fusion_error(self, mock_client):
        """Test error handling in view creation."""
        mock_client.execute_query.side_effect = Exception("View creation failed")

        view_sql = "CREATE OR REPLACE VIEW memory.default.test_view AS SELECT 1"
        result = apply_fusion(view_sql)

        assert result["status"] == "error"
        assert "error" in result["message"].lower() or "failed" in result["message"].lower()
        assert result["sql"] == view_sql


class TestGenerateFusionFromMatches:
    """Test cases for generate_fusion_from_matches function."""

    @patch("src.core.fusion.fusion.apply_fusion")
    @patch("src.core.fusion.fusion.generate_view_sql")
    def test_generate_fusion_from_matches_success(
        self,
        mock_generate_sql,
        mock_apply_fusion,
        sample_matches,
    ):
        """Test successful fusion view generation from matches."""
        mock_generate_sql.return_value = "CREATE VIEW test_view AS SELECT 1"
        mock_apply_fusion.return_value = {
            "status": "success",
            "message": "View created successfully",
            "view_name": "test_view",
            "sql": "CREATE VIEW test_view AS SELECT 1",
        }

        source_a = {"catalog": "postgres", "schema": "public", "table": "users"}
        source_b = {"catalog": "mongo", "schema": "testdb", "table": "customers"}

        result = generate_fusion_from_matches(
            view_name="test_view",
            matches=sample_matches,
            source_a=source_a,
            source_b=source_b,
            join_key_a="id",
            join_key_b="_id",
        )

        assert result["status"] == "success"
        assert "view_name" in result
        mock_generate_sql.assert_called_once()
        mock_apply_fusion.assert_called_once()

    @patch("src.core.fusion.fusion.generate_view_sql")
    def test_generate_fusion_from_matches_mongo_casting(self, mock_generate_sql):
        """Test that MongoDB ObjectId casting is applied correctly."""
        mock_generate_sql.return_value = "CREATE VIEW test_view AS SELECT 1"

        source_a = {"catalog": "postgres", "schema": "public", "table": "users"}
        source_b = {"catalog": "mongo", "schema": "testdb", "table": "customers"}

        generate_fusion_from_matches(
            view_name="test_view",
            matches=[{"source_col": "id", "target_col": "_id", "confidence": 1.0}],
            source_a=source_a,
            source_b=source_b,
            join_key_a="id",
            join_key_b="_id",
        )

        # Check that generate_view_sql was called with a join condition
        call_args = mock_generate_sql.call_args
        assert call_args is not None
        join_condition = call_args[1]["join_condition"]
        # Should contain CAST for MongoDB ObjectId
        assert "CAST" in join_condition or "VARCHAR" in join_condition


class TestTypeCoercion:
    """Test cases for type coercion functionality."""

    def test_normalize_trino_type(self):
        """Test Trino type normalization."""
        assert normalize_trino_type("varchar(255)") == "varchar"
        assert normalize_trino_type("integer") == "integer"
        assert normalize_trino_type("array(varchar)") == "array"
        assert normalize_trino_type("") == "VARCHAR"

    def test_get_common_type_same_types(self):
        """Test getting common type when types are the same."""
        assert get_common_type("varchar", "varchar", TYPE_COERCION_MAP) == "VARCHAR"
        assert get_common_type("integer", "integer", TYPE_COERCION_MAP) == "DOUBLE"

    def test_get_common_type_different_types(self):
        """Test getting common type when types differ."""
        # Numeric types should map to DOUBLE
        assert get_common_type("integer", "bigint", TYPE_COERCION_MAP) in ["DOUBLE", "VARCHAR"]
        # String types should map to VARCHAR
        assert get_common_type("varchar", "char", TYPE_COERCION_MAP) == "VARCHAR"


class TestSQLValidation:
    """Test cases for SQL validation."""

    def test_validate_sql_empty(self):
        """Test validation of empty SQL."""
        is_valid, error = validate_sql("")
        assert not is_valid
        assert "empty" in error.lower()

    def test_validate_sql_create_view(self):
        """Test validation of CREATE VIEW statement."""
        sql = "CREATE OR REPLACE VIEW memory.default.test AS SELECT 1"
        is_valid, error = validate_sql(sql)
        assert is_valid
        assert error == ""

    def test_validate_sql_drop_view(self):
        """Test validation of DROP VIEW statement."""
        sql = "DROP VIEW IF EXISTS memory.default.test"
        is_valid, error = validate_sql(sql)
        assert is_valid
        assert error == ""

    def test_validate_sql_dangerous_operations(self):
        """Test validation rejects dangerous operations."""
        dangerous_sqls = [
            "DROP DATABASE test",
            "DELETE FROM users",
            "UPDATE users SET name = 'test'",
            "TRUNCATE TABLE users",
        ]

        for sql in dangerous_sqls:
            is_valid, error = validate_sql(sql)
            assert not is_valid
            assert "dangerous" in error.lower() or "operation" in error.lower()

    def test_validate_sql_unbalanced_parentheses(self):
        """Test validation detects unbalanced parentheses."""
        sql = "CREATE VIEW test AS SELECT (1 + 2"
        is_valid, error = validate_sql(sql)
        assert not is_valid
        assert "parentheses" in error.lower()


class TestUpdateFusionView:
    """Test cases for update_fusion_view function."""

    @patch("src.core.fusion.fusion.apply_fusion")
    @patch("src.core.fusion.fusion.generate_view_sql")
    def test_update_fusion_view_success(
        self,
        mock_generate_sql,
        mock_apply_fusion,
    ):
        """Test successful view update."""
        mock_generate_sql.return_value = "CREATE OR REPLACE VIEW test_view AS SELECT 1"
        mock_apply_fusion.return_value = {
            "status": "success",
            "message": "View created successfully",
            "view_name": "test_view",
            "sql": "CREATE OR REPLACE VIEW test_view AS SELECT 1",
        }

        mappings = [
            {"global": "id", "source_a": "id", "source_b": "_id"},
        ]
        source_a = {"catalog": "postgres", "schema": "public", "table": "users"}
        source_b = {"catalog": "mongo", "schema": "testdb", "table": "customers"}

        result = update_fusion_view(
            view_name="test_view",
            mappings=mappings,
            source_a=source_a,
            source_b=source_b,
            join_condition="p.id = m._id",
        )

        assert result["status"] == "success"
        assert "updated" in result["message"].lower()
        mock_generate_sql.assert_called_once()
        mock_apply_fusion.assert_called_once()
        # Check that validation was enabled
        assert mock_apply_fusion.call_args[1]["validate"] is True
