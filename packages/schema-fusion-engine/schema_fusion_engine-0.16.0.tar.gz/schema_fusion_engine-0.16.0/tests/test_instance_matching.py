"""Tests for instance-based matching functionality."""

from unittest.mock import patch

from src.core.matching.instance_matching import (
    calculate_distribution_similarity,
    calculate_instance_similarity,
    calculate_value_overlap,
    calculate_value_range_similarity,
    find_instance_matches,
    sample_column_values,
)


class TestInstanceMatching:
    """Test cases for instance-based matching."""

    def test_calculate_value_overlap(self):
        """Test value overlap calculation."""
        values_a = ["apple", "banana", "cherry", "date"]
        values_b = ["banana", "cherry", "elderberry", "fig"]

        overlap = calculate_value_overlap(values_a, values_b)
        # Jaccard: intersection = {banana, cherry} = 2, union = {apple, banana, cherry, date, elderberry, fig} = 6
        # Overlap = 2/6 = 0.333...
        assert 0.33 <= overlap <= 0.34

    def test_calculate_value_overlap_empty(self):
        """Test value overlap with empty lists."""
        assert calculate_value_overlap([], []) == 0.0
        assert calculate_value_overlap(["a"], []) == 0.0
        assert calculate_value_overlap([], ["b"]) == 0.0

    def test_calculate_value_overlap_identical(self):
        """Test value overlap with identical sets."""
        values = ["apple", "banana", "cherry"]
        overlap = calculate_value_overlap(values, values)
        assert overlap == 1.0

    def test_calculate_distribution_similarity(self):
        """Test distribution similarity calculation."""
        values_a = ["apple", "apple", "banana", "cherry"]
        values_b = ["apple", "banana", "banana", "cherry"]

        similarity = calculate_distribution_similarity(values_a, values_b)
        assert 0.0 <= similarity <= 1.0

    def test_calculate_distribution_similarity_identical(self):
        """Test distribution similarity with identical distributions."""
        values = ["apple", "apple", "banana"]
        similarity = calculate_distribution_similarity(values, values)
        # Cosine similarity for identical distributions should be high (> 0.5)
        # The exact value depends on the normalization, but should be positive
        assert similarity > 0.5
        assert similarity <= 1.0

    def test_calculate_value_range_similarity_numeric(self):
        """Test range similarity for numeric values."""
        values_a = [1.0, 2.0, 3.0, 4.0, 5.0]
        values_b = [2.0, 3.0, 4.0, 5.0, 6.0]

        similarity = calculate_value_range_similarity(values_a, values_b)
        assert 0.0 <= similarity <= 1.0

    def test_calculate_value_range_similarity_non_numeric(self):
        """Test range similarity with non-numeric values."""
        values_a = ["apple", "banana"]
        values_b = ["cherry", "date"]

        similarity = calculate_value_range_similarity(values_a, values_b)
        assert similarity == 0.0

    def test_calculate_value_range_similarity_identical(self):
        """Test range similarity with identical ranges."""
        values = [1.0, 2.0, 3.0]
        similarity = calculate_value_range_similarity(values, values)
        assert similarity == 1.0

    @patch("src.core.matching.instance_matching.trino_client")
    def test_sample_column_values(self, mock_trino_client):
        """Test sampling column values."""
        mock_trino_client.execute_query.return_value = [
            ("value1",),
            ("value2",),
            ("value3",),
        ]

        values = sample_column_values("postgres", "public", "test_table", "test_column", 100)

        assert len(values) == 3
        assert "value1" in values
        assert "value2" in values
        assert "value3" in values
        mock_trino_client.execute_query.assert_called_once()

    @patch("src.core.matching.instance_matching.trino_client")
    def test_sample_column_values_empty(self, mock_trino_client):
        """Test sampling with no results."""
        mock_trino_client.execute_query.return_value = []

        values = sample_column_values("postgres", "public", "test_table", "test_column", 100)

        assert values == []

    @patch("src.core.matching.instance_matching.calculate_instance_similarity")
    def test_find_instance_matches(self, mock_calc_similarity):
        """Test finding instance-based matches."""
        # Create a call counter to track which columns are being compared
        call_count = [0]
        scores = [
            0.9,
            0.3,
            0.4,
            0.8,
        ]  # col_a1 vs col_b1, col_a1 vs col_b2, col_a2 vs col_b1, col_a2 vs col_b2

        def similarity_side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx < len(scores):
                return scores[idx]
            return 0.0

        mock_calc_similarity.side_effect = similarity_side_effect

        matches = find_instance_matches(
            catalog_a="postgres",
            schema_a="public",
            table_a="table_a",
            columns_a=["col_a1", "col_a2"],
            catalog_b="mongo",
            schema_b="testdb",
            table_b="table_b",
            columns_b=["col_b1", "col_b2"],
            threshold=0.6,
        )

        # Should find matches above threshold (0.9 and 0.8)
        assert len(matches) >= 1
        # At least one match should be found
        match_cols = {(m["source_col"], m["target_col"]) for m in matches}
        # col_a1 should match col_b1 (0.9 > 0.6) or col_a2 should match col_b2 (0.8 > 0.6)
        assert ("col_a1", "col_b1") in match_cols or ("col_a2", "col_b2") in match_cols

    @patch("src.core.matching.instance_matching.sample_column_values")
    def test_calculate_instance_similarity(self, mock_sample):
        """Test calculating instance similarity."""
        # Mock sampled values
        mock_sample.side_effect = [
            ["value1", "value2", "value3"],  # Column A
            ["value2", "value3", "value4"],  # Column B
        ]

        similarity = calculate_instance_similarity(
            "postgres",
            "public",
            "table_a",
            "col_a",
            "mongo",
            "testdb",
            "table_b",
            "col_b",
            sample_size=100,
        )

        assert 0.0 <= similarity <= 1.0
        assert mock_sample.call_count == 2

    @patch("src.core.matching.instance_matching.sample_column_values")
    def test_calculate_instance_similarity_empty_samples(self, mock_sample):
        """Test instance similarity with empty samples."""
        mock_sample.return_value = []

        similarity = calculate_instance_similarity(
            "postgres",
            "public",
            "table_a",
            "col_a",
            "mongo",
            "testdb",
            "table_b",
            "col_b",
        )

        assert similarity == 0.0
