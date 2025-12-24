"""Unit tests for schema matching engine."""

from unittest.mock import patch

import pytest

from src.core.matching.matching import find_matches, match_tables


class TestFindMatches:
    """Test cases for find_matches function."""

    def test_exact_matches(self):
        """Test finding exact column name matches."""
        source_cols = ["id", "name", "email"]
        target_cols = ["id", "name", "email"]

        matches = find_matches(source_cols, target_cols, threshold=0.8)

        assert len(matches) == 3
        assert all(m["confidence"] == 1.0 for m in matches)
        assert matches[0]["source_col"] == "id"
        assert matches[0]["target_col"] == "id"

    def test_similar_matches(self):
        """Test finding similar column name matches."""
        source_cols = ["user_name", "user_email"]
        target_cols = ["username", "email"]

        matches = find_matches(source_cols, target_cols, threshold=0.7)

        assert len(matches) >= 1
        # Should find matches based on similarity

    def test_no_matches_below_threshold(self):
        """Test that no matches are returned when similarity is below threshold."""
        source_cols = ["abc", "def"]
        target_cols = ["xyz", "uvw"]

        matches = find_matches(source_cols, target_cols, threshold=0.8)

        assert len(matches) == 0

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        source_cols = ["UserName", "Email"]
        target_cols = ["username", "email"]

        matches = find_matches(source_cols, target_cols, threshold=0.8)

        assert len(matches) == 2
        assert all(m["confidence"] == 1.0 for m in matches)

    def test_one_to_one_matching(self):
        """Test that each source column matches to at most one target column."""
        source_cols = ["id", "name"]
        target_cols = ["id", "name", "id_alt"]

        matches = find_matches(source_cols, target_cols, threshold=0.8)

        # Each source column should match only once
        target_cols_used = {m["target_col"] for m in matches}
        assert len(target_cols_used) == len(matches)


class TestMatchTables:
    """Test cases for match_tables function."""

    @patch("src.core.matching.matching.trino_client")
    def test_match_tables_success(self, mock_client, sample_table_info):
        """Test successful table matching."""
        # Mock table info for both tables
        mock_client.get_table_info.side_effect = [
            sample_table_info,
            {
                "catalog": "mongo",
                "schema": "testdb",
                "table": "customers",
                "columns": [
                    {"name": "_id", "type": "objectid"},
                    {"name": "name", "type": "string"},
                    {"name": "email", "type": "string"},
                ],
            },
        ]

        result = match_tables(
            catalog_a="postgres",
            schema_a="public",
            table_a="users",
            catalog_b="mongo",
            schema_b="testdb",
            table_b="customers",
            threshold=0.8,
        )

        assert result["source"]["catalog"] == "postgres"
        assert result["target"]["catalog"] == "mongo"
        assert "matches" in result
        assert result["match_count"] == len(result["matches"])
        assert result["threshold"] == 0.8

    @patch("src.core.matching.matching.trino_client")
    def test_match_tables_with_matches(self, mock_client):
        """Test table matching that finds column matches."""
        mock_client.get_table_info.side_effect = [
            {
                "catalog": "postgres",
                "schema": "public",
                "table": "users",
                "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "name", "type": "varchar"},
                    {"name": "email", "type": "varchar"},
                ],
            },
            {
                "catalog": "mongo",
                "schema": "testdb",
                "table": "customers",
                "columns": [
                    {"name": "_id", "type": "objectid"},
                    {"name": "name", "type": "string"},
                    {"name": "email", "type": "string"},
                ],
            },
        ]

        result = match_tables(
            catalog_a="postgres",
            schema_a="public",
            table_a="users",
            catalog_b="mongo",
            schema_b="testdb",
            table_b="customers",
            threshold=0.8,
        )

        # Should find at least name and email matches
        match_cols = {m["source_col"] for m in result["matches"]}
        assert "name" in match_cols or "email" in match_cols

    @patch("src.core.matching.matching.trino_client")
    def test_match_tables_error_handling(self, mock_client):
        """Test error handling in match_tables."""
        mock_client.get_table_info.side_effect = Exception("Table not found")

        with pytest.raises(Exception, match="Failed to fetch columns"):
            match_tables(
                catalog_a="postgres",
                schema_a="public",
                table_a="nonexistent",
                catalog_b="mongo",
                schema_b="testdb",
                table_b="nonexistent",
            )
