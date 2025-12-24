"""Tests for enhanced query validation."""

from src.core.query.query_validation import (
    analyze_query_complexity,
    validate_query,
    validate_query_complexity,
    validate_query_whitelist,
)


class TestQueryComplexityAnalysis:
    """Test cases for query complexity analysis."""

    def test_analyze_simple_query(self):
        """Test complexity analysis of a simple query."""
        sql = "SELECT * FROM users"
        complexity = analyze_query_complexity(sql)

        assert complexity["join_count"] == 0
        assert complexity["subquery_count"] == 0
        assert complexity["union_count"] == 0
        assert complexity["table_count"] == 1
        assert complexity["condition_count"] == 0
        assert complexity["query_length"] == len(sql)

    def test_analyze_query_with_joins(self):
        """Test complexity analysis with JOINs."""
        sql = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id"
        complexity = analyze_query_complexity(sql)

        assert complexity["join_count"] == 1
        assert complexity["table_count"] == 2

    def test_analyze_query_with_subqueries(self):
        """Test complexity analysis with subqueries."""
        sql = "SELECT * FROM (SELECT id FROM users) AS sub"
        complexity = analyze_query_complexity(sql)

        assert complexity["subquery_count"] == 1

    def test_analyze_query_with_unions(self):
        """Test complexity analysis with UNION."""
        sql = "SELECT * FROM users UNION ALL SELECT * FROM customers"
        complexity = analyze_query_complexity(sql)

        assert complexity["union_count"] == 1
        assert complexity["table_count"] == 2

    def test_analyze_query_with_where_clause(self):
        """Test complexity analysis with WHERE conditions."""
        sql = "SELECT * FROM users WHERE id = 1 AND name = 'test' OR email IS NULL"
        complexity = analyze_query_complexity(sql)

        assert complexity["condition_count"] >= 3  # WHERE + AND + OR


class TestQueryWhitelist:
    """Test cases for query whitelist validation."""

    def test_validate_select_allowed(self):
        """Test that SELECT queries are allowed."""
        sql = "SELECT * FROM users"
        is_valid, error = validate_query_whitelist(sql, allowed_operations=["SELECT"])
        assert is_valid
        assert error == ""

    def test_validate_insert_not_allowed(self):
        """Test that INSERT queries are rejected."""
        sql = "INSERT INTO users VALUES (1, 'test')"
        is_valid, error = validate_query_whitelist(sql, allowed_operations=["SELECT"])
        assert not is_valid
        assert "SELECT" in error

    def test_validate_delete_not_allowed(self):
        """Test that DELETE queries are rejected."""
        sql = "DELETE FROM users WHERE id = 1"
        is_valid, error = validate_query_whitelist(sql, allowed_operations=["SELECT"])
        assert not is_valid

    def test_validate_update_not_allowed(self):
        """Test that UPDATE queries are rejected."""
        sql = "UPDATE users SET name = 'test' WHERE id = 1"
        is_valid, error = validate_query_whitelist(sql, allowed_operations=["SELECT"])
        assert not is_valid

    def test_validate_multiple_allowed_operations(self):
        """Test validation with multiple allowed operations."""
        sql = "SELECT * FROM users"
        is_valid, error = validate_query_whitelist(sql, allowed_operations=["SELECT", "WITH"])
        assert is_valid

        sql2 = "WITH temp AS (SELECT 1) SELECT * FROM temp"
        is_valid2, error2 = validate_query_whitelist(sql2, allowed_operations=["SELECT", "WITH"])
        assert is_valid2


class TestQueryComplexityValidation:
    """Test cases for query complexity validation."""

    def test_validate_max_joins(self):
        """Test validation of maximum JOIN count."""
        sql = "SELECT * FROM a JOIN b ON a.id = b.id JOIN c ON b.id = c.id"
        is_valid, error = validate_query_complexity(sql, max_joins=1)
        assert not is_valid
        assert "JOIN" in error

        is_valid2, error2 = validate_query_complexity(sql, max_joins=3)
        assert is_valid2

    def test_validate_max_subqueries(self):
        """Test validation of maximum subquery count."""
        sql = "SELECT * FROM (SELECT * FROM (SELECT 1))"
        is_valid, error = validate_query_complexity(sql, max_subqueries=1)
        assert not is_valid
        assert "subquery" in error.lower()

    def test_validate_max_unions(self):
        """Test validation of maximum UNION count."""
        sql = "SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3"
        is_valid, error = validate_query_complexity(sql, max_unions=1)
        assert not is_valid
        assert "UNION" in error

    def test_validate_max_tables(self):
        """Test validation of maximum table count."""
        sql = "SELECT * FROM a JOIN b ON a.id = b.id JOIN c ON b.id = c.id"
        is_valid, error = validate_query_complexity(sql, max_tables=2)
        assert not is_valid
        assert "table" in error.lower()

    def test_validate_max_query_length(self):
        """Test validation of maximum query length."""
        long_query = "SELECT " + ", ".join([f"col{i}" for i in range(1000)])
        is_valid, error = validate_query_complexity(long_query, max_query_length=100)
        assert not is_valid
        assert "length" in error.lower()

    def test_validate_no_limits(self):
        """Test validation with no limits (all None)."""
        sql = "SELECT * FROM a JOIN b JOIN c JOIN d"
        is_valid, error = validate_query_complexity(
            sql,
            max_joins=None,
            max_subqueries=None,
            max_unions=None,
            max_tables=None,
            max_query_length=None,
        )
        assert is_valid


class TestComprehensiveQueryValidation:
    """Test cases for comprehensive query validation."""

    def test_validate_empty_query(self):
        """Test validation of empty query."""
        is_valid, error = validate_query("")
        assert not is_valid
        assert "empty" in error.lower()

    def test_validate_whitespace_only_query(self):
        """Test validation of whitespace-only query."""
        is_valid, error = validate_query("   ")
        assert not is_valid

    def test_validate_select_query(self):
        """Test validation of valid SELECT query."""
        sql = "SELECT * FROM users"
        is_valid, error = validate_query(sql, require_select=True)
        assert is_valid
        assert error == ""

    def test_validate_non_select_query_with_require_select(self):
        """Test validation rejects non-SELECT queries when require_select=True."""
        sql = "INSERT INTO users VALUES (1, 'test')"
        is_valid, error = validate_query(sql, require_select=True)
        assert not is_valid
        assert "SELECT" in error

    def test_validate_non_select_query_without_require_select(self):
        """Test validation allows non-SELECT queries when require_select=False."""
        sql = "INSERT INTO users VALUES (1, 'test')"
        is_valid, error = validate_query(sql, require_select=False)
        # Should pass whitelist check but may fail complexity if limits are set
        # Since we're not setting complexity limits, it should pass
        assert is_valid

    def test_validate_query_with_complexity_limits(self):
        """Test validation with complexity limits."""
        sql = "SELECT * FROM a JOIN b JOIN c JOIN d JOIN e"
        is_valid, error = validate_query(sql, max_joins=3)
        assert not is_valid
        assert "JOIN" in error

    def test_validate_complex_query_within_limits(self):
        """Test validation of complex query within limits."""
        sql = """
        SELECT u.id, u.name, o.total
        FROM users u
        JOIN orders o ON u.id = o.user_id
        WHERE u.active = true
        """
        is_valid, error = validate_query(
            sql,
            require_select=True,
            max_joins=5,
            max_tables=10,
            max_query_length=10000,
        )
        assert is_valid
