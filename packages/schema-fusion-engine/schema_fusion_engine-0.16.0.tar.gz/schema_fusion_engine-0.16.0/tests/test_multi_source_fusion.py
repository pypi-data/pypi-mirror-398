"""Integration tests for multi-source fusion (3+ sources)."""

from unittest.mock import patch

from src.core.fusion.fusion_multi_source import (
    find_multi_source_join_keys,
    generate_multi_source_fusion,
    generate_multi_source_join_sql,
    generate_multi_source_union_sql,
    validate_multi_source_sources,
)


class TestMultiSourceValidation:
    """Test cases for multi-source validation."""

    def test_validate_minimum_sources(self):
        """Test validation fails with less than 2 sources."""
        sources = [{"catalog": "postgres", "schema": "public", "table": "users", "alias": "p"}]
        is_valid, error = validate_multi_source_sources(sources)
        assert not is_valid
        assert "2 sources required" in error

    def test_validate_maximum_sources(self):
        """Test validation fails with more than 10 sources."""
        sources = [
            {"catalog": "postgres", "schema": "public", "table": f"table{i}", "alias": f"t{i}"}
            for i in range(11)
        ]
        is_valid, error = validate_multi_source_sources(sources)
        assert not is_valid
        assert "Maximum 10 sources" in error

    def test_validate_required_fields(self):
        """Test validation fails with missing required fields."""
        sources = [
            {"catalog": "postgres", "schema": "public", "table": "users", "alias": "p"},
            {"catalog": "mongo", "schema": "testdb"},  # Missing table and alias
        ]
        is_valid, error = validate_multi_source_sources(sources)
        assert not is_valid
        assert "missing required fields" in error

    def test_validate_duplicate_aliases(self):
        """Test validation fails with duplicate aliases."""
        sources = [
            {"catalog": "postgres", "schema": "public", "table": "users", "alias": "p"},
            {"catalog": "mongo", "schema": "testdb", "table": "customers", "alias": "p"},
        ]
        is_valid, error = validate_multi_source_sources(sources)
        assert not is_valid
        assert "Duplicate aliases" in error

    def test_validate_valid_sources(self):
        """Test validation passes with valid sources."""
        sources = [
            {"catalog": "postgres", "schema": "public", "table": "users", "alias": "p"},
            {"catalog": "mongo", "schema": "testdb", "table": "customers", "alias": "m"},
            {"catalog": "postgres", "schema": "public", "table": "orders", "alias": "o"},
        ]
        is_valid, error = validate_multi_source_sources(sources)
        assert is_valid
        assert error == ""


class TestMultiSourceJoinSQL:
    """Test cases for multi-source JOIN SQL generation."""

    def test_generate_three_way_join(self):
        """Test generating SQL for 3-way JOIN."""
        sources = [
            {"catalog": "postgres", "schema": "public", "table": "users", "alias": "u"},
            {"catalog": "mongo", "schema": "testdb", "table": "profiles", "alias": "p"},
            {"catalog": "postgres", "schema": "public", "table": "orders", "alias": "o"},
        ]
        matches = [
            {
                "global": "user_id",
                "mappings": [
                    {"source": "u", "column": "id"},
                    {"source": "p", "column": "user_id"},
                    {"source": "o", "column": "user_id"},
                ],
            },
            {
                "global": "name",
                "mappings": [
                    {"source": "u", "column": "name"},
                    {"source": "p", "column": "full_name"},
                ],
            },
        ]
        join_keys = [
            {"source": "u", "column": "id"},
            {"source": "p", "column": "user_id"},
            {"source": "o", "column": "user_id"},
        ]

        sql = generate_multi_source_join_sql("test_view", sources, matches, join_keys)

        assert "CREATE OR REPLACE VIEW" in sql
        assert "test_view" in sql
        assert "postgres.public.users u" in sql
        assert "mongo.testdb.profiles p" in sql
        assert "postgres.public.orders o" in sql
        assert "JOIN" in sql
        assert "u.id = p.user_id" in sql or "p.user_id = u.id" in sql

    def test_generate_join_with_mongo_objectid(self):
        """Test generating JOIN with MongoDB ObjectId casting."""
        sources = [
            {"catalog": "postgres", "schema": "public", "table": "users", "alias": "p"},
            {"catalog": "mongo", "schema": "testdb", "table": "customers", "alias": "m"},
        ]
        matches = [
            {
                "global": "id",
                "mappings": [
                    {"source": "p", "column": "id"},
                    {"source": "m", "column": "_id"},
                ],
            },
        ]
        join_keys = [
            {"source": "p", "column": "id"},
            {"source": "m", "column": "_id"},
        ]

        sql = generate_multi_source_join_sql("test_view", sources, matches, join_keys)

        # Should cast MongoDB _id to VARCHAR for JOIN
        assert "CAST" in sql or "VARCHAR" in sql


class TestMultiSourceUnionSQL:
    """Test cases for multi-source UNION ALL SQL generation."""

    def test_generate_three_way_union(self):
        """Test generating SQL for 3-way UNION ALL."""
        sources = [
            {"catalog": "postgres", "schema": "public", "table": "users", "alias": "p"},
            {"catalog": "mongo", "schema": "testdb", "table": "customers", "alias": "m"},
            {"catalog": "postgres", "schema": "public", "table": "clients", "alias": "c"},
        ]
        matches = [
            {
                "global": "id",
                "mappings": [
                    {"source": "p", "column": "id"},
                    {"source": "m", "column": "_id"},
                    {"source": "c", "column": "client_id"},
                ],
            },
            {
                "global": "name",
                "mappings": [
                    {"source": "p", "column": "name"},
                    {"source": "m", "column": "name"},
                    {"source": "c", "column": "name"},
                ],
            },
        ]

        sql = generate_multi_source_union_sql(
            "test_view", sources, matches, enable_type_coercion=True
        )

        assert "CREATE OR REPLACE VIEW" in sql
        assert "test_view" in sql
        assert "UNION ALL" in sql
        assert sql.count("UNION ALL") == 2  # 3 sources = 2 UNION ALLs
        assert "postgres.public.users" in sql
        assert "mongo.testdb.customers" in sql
        assert "postgres.public.clients" in sql

    def test_generate_union_with_type_coercion(self):
        """Test UNION ALL with type coercion."""
        sources = [
            {"catalog": "postgres", "schema": "public", "table": "table1", "alias": "t1"},
            {"catalog": "postgres", "schema": "public", "table": "table2", "alias": "t2"},
        ]
        matches = [
            {
                "global": "id",
                "mappings": [
                    {"source": "t1", "column": "id"},  # integer
                    {"source": "t2", "column": "id"},  # bigint
                ],
            },
        ]

        with patch("src.core.fusion.fusion_multi_source.get_column_type_map") as mock_type_map:
            mock_type_map.side_effect = [
                {"id": "integer"},  # t1
                {"id": "bigint"},  # t2
            ]

            sql = generate_multi_source_union_sql(
                "test_view", sources, matches, enable_type_coercion=True
            )

            # Should include type coercion
            assert "CAST" in sql or "DOUBLE" in sql


class TestFindJoinKeys:
    """Test cases for automatic join key detection."""

    def test_find_join_keys_by_id_pattern(self):
        """Test finding join keys using ID patterns."""
        sources = [
            {"catalog": "postgres", "schema": "public", "table": "users", "alias": "u"},
            {"catalog": "mongo", "schema": "testdb", "table": "profiles", "alias": "p"},
            {"catalog": "postgres", "schema": "public", "table": "orders", "alias": "o"},
        ]
        matches = [
            {
                "global": "user_id",
                "mappings": [
                    {"source": "u", "column": "id"},
                    {"source": "p", "column": "user_id"},
                    {"source": "o", "column": "user_id"},
                ],
            },
            {
                "global": "name",
                "mappings": [
                    {"source": "u", "column": "name"},
                    {"source": "p", "column": "full_name"},
                ],
            },
        ]

        join_keys = find_multi_source_join_keys(sources, matches)

        assert len(join_keys) > 0
        assert any(key.get("column") in ["id", "user_id"] for key in join_keys)


class TestMultiSourceFusion:
    """Test cases for complete multi-source fusion workflow."""

    @patch("src.core.fusion.fusion_multi_source.apply_fusion")
    def test_generate_multi_source_fusion_join(self, mock_apply_fusion):
        """Test complete multi-source fusion with JOIN."""
        mock_apply_fusion.return_value = {
            "status": "success",
            "message": "View created successfully",
            "view_name": "test_view",
            "sql": "CREATE VIEW test_view AS SELECT ...",
        }

        sources = [
            {"catalog": "postgres", "schema": "public", "table": "users", "alias": "u"},
            {"catalog": "mongo", "schema": "testdb", "table": "profiles", "alias": "p"},
            {"catalog": "postgres", "schema": "public", "table": "orders", "alias": "o"},
        ]
        matches = [
            {
                "global": "user_id",
                "mappings": [
                    {"source": "u", "column": "id"},
                    {"source": "p", "column": "user_id"},
                    {"source": "o", "column": "user_id"},
                ],
            },
        ]
        join_keys = [
            {"source": "u", "column": "id"},
            {"source": "p", "column": "user_id"},
            {"source": "o", "column": "user_id"},
        ]

        result = generate_multi_source_fusion(
            view_name="test_view",
            sources=sources,
            matches=matches,
            join_keys=join_keys,
            fusion_type="join",
        )

        assert result["status"] == "success"
        assert "view_name" in result
        mock_apply_fusion.assert_called_once()

    @patch("src.core.fusion.fusion_multi_source.apply_fusion")
    def test_generate_multi_source_fusion_union(self, mock_apply_fusion):
        """Test complete multi-source fusion with UNION ALL."""
        mock_apply_fusion.return_value = {
            "status": "success",
            "message": "View created successfully",
            "view_name": "test_view",
            "sql": "CREATE VIEW test_view AS SELECT ...",
        }

        sources = [
            {"catalog": "postgres", "schema": "public", "table": "users", "alias": "p"},
            {"catalog": "mongo", "schema": "testdb", "table": "customers", "alias": "m"},
            {"catalog": "postgres", "schema": "public", "table": "clients", "alias": "c"},
        ]
        matches = [
            {
                "global": "id",
                "mappings": [
                    {"source": "p", "column": "id"},
                    {"source": "m", "column": "_id"},
                    {"source": "c", "column": "client_id"},
                ],
            },
        ]

        result = generate_multi_source_fusion(
            view_name="test_view",
            sources=sources,
            matches=matches,
            fusion_type="union",
        )

        assert result["status"] == "success"
        assert "view_name" in result
        mock_apply_fusion.assert_called_once()

    def test_generate_multi_source_fusion_validation_error(self):
        """Test fusion fails with invalid sources."""
        sources = [{"catalog": "postgres", "schema": "public", "table": "users", "alias": "p"}]

        result = generate_multi_source_fusion(
            view_name="test_view",
            sources=sources,
            matches=[],
            fusion_type="join",
        )

        assert result["status"] == "error"
        assert "2 sources required" in result["message"]
