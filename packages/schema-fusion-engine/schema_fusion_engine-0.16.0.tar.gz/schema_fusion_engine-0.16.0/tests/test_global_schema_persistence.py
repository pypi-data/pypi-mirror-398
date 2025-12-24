"""Tests for global schema persistence (fusion view metadata storage)."""

import os
import tempfile
from unittest.mock import patch

import pytest

from src.core.fusion.fusion_persistence import (
    delete_fusion_view,
    get_fusion_view,
    list_fusion_views,
    persist_fusion_view,
)
from src.core.infrastructure.models import init_db


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(db_path)
    yield db_path
    os.unlink(db_path)


class TestFusionViewPersistence:
    """Test cases for fusion view persistence."""

    def test_persist_fusion_view_join(self, temp_db):
        """Test persisting a JOIN fusion view."""
        with patch("src.core.fusion.fusion_persistence.get_session") as mock_session:
            from src.core.infrastructure.models import get_session

            session = get_session(temp_db)
            mock_session.return_value = session

            sources = [
                {"catalog": "postgres", "schema": "public", "table": "users"},
                {"catalog": "mongo", "schema": "testdb", "table": "customers"},
            ]
            matches = [
                {"source_col": "email", "target_col": "email", "confidence": 1.0},
                {"source_col": "name", "target_col": "name", "confidence": 1.0},
            ]
            join_keys = [
                {"source": "a", "column": "id"},
                {"source": "b", "column": "_id"},
            ]
            view_sql = "CREATE OR REPLACE VIEW memory.default.test_view AS SELECT ..."

            result = persist_fusion_view(
                view_name="test_view",
                fusion_type="join",
                sources=sources,
                matches=matches,
                view_sql=view_sql,
                view_catalog="memory",
                view_schema="default",
                join_keys=join_keys,
                enable_type_coercion=True,
                description="Test fusion view",
            )

            assert result["status"] == "success"
            session.close()

    def test_persist_fusion_view_union(self, temp_db):
        """Test persisting a UNION ALL fusion view."""
        with patch("src.core.fusion.fusion_persistence.get_session") as mock_session:
            from src.core.infrastructure.models import get_session

            session = get_session(temp_db)
            mock_session.return_value = session

            sources = [
                {"catalog": "postgres", "schema": "public", "table": "users"},
                {"catalog": "mongo", "schema": "testdb", "table": "customers"},
            ]
            matches = [
                {"source_col": "email", "target_col": "email", "confidence": 1.0},
            ]

            result = persist_fusion_view(
                view_name="test_union_view",
                fusion_type="union",
                sources=sources,
                matches=matches,
                view_sql="CREATE OR REPLACE VIEW memory.default.test_union_view AS ...",
                view_catalog="memory",
                view_schema="default",
                join_keys=None,
                enable_type_coercion=True,
            )

            assert result["status"] == "success"
            session.close()

    def test_list_fusion_views(self, temp_db):
        """Test listing all fusion views."""
        with patch("src.core.fusion.fusion_persistence.get_session") as mock_session:
            from src.core.infrastructure.models import get_session

            session = get_session(temp_db)
            mock_session.return_value = session

            # Persist a view first
            persist_fusion_view(
                view_name="view1",
                fusion_type="join",
                sources=[{"catalog": "postgres", "schema": "public", "table": "t1"}],
                matches=[],
                view_sql="CREATE VIEW ...",
                view_catalog="memory",
                view_schema="default",
            )

            views = list_fusion_views()
            assert len(views) >= 1
            assert any(v["view_name"] == "view1" for v in views)
            session.close()

    def test_get_fusion_view(self, temp_db):
        """Test retrieving a specific fusion view."""
        with patch("src.core.fusion.fusion_persistence.get_session") as mock_session:
            from src.core.infrastructure.models import get_session

            session = get_session(temp_db)
            mock_session.return_value = session

            # Persist a view first
            persist_fusion_view(
                view_name="test_get_view",
                fusion_type="join",
                sources=[{"catalog": "postgres", "schema": "public", "table": "t1"}],
                matches=[{"source_col": "id", "target_col": "id"}],
                view_sql="CREATE VIEW test_get_view AS SELECT ...",
                view_catalog="memory",
                view_schema="default",
            )

            view = get_fusion_view("test_get_view")
            assert view is not None
            assert view["view_name"] == "test_get_view"
            assert view["fusion_type"] == "join"
            assert "view_sql" in view
            session.close()

    def test_get_fusion_view_not_found(self, temp_db):
        """Test retrieving a non-existent fusion view."""
        with patch("src.core.fusion.fusion_persistence.get_session") as mock_session:
            from src.core.infrastructure.models import get_session

            session = get_session(temp_db)
            mock_session.return_value = session

            view = get_fusion_view("nonexistent_view")
            assert view is None
            session.close()

    def test_delete_fusion_view(self, temp_db):
        """Test deleting a fusion view."""
        with patch("src.core.fusion.fusion_persistence.get_session") as mock_session:
            from src.core.infrastructure.models import get_session

            session = get_session(temp_db)
            mock_session.return_value = session

            # Persist a view first
            persist_fusion_view(
                view_name="test_delete_view",
                fusion_type="join",
                sources=[{"catalog": "postgres", "schema": "public", "table": "t1"}],
                matches=[],
                view_sql="CREATE VIEW ...",
                view_catalog="memory",
                view_schema="default",
            )

            result = delete_fusion_view("test_delete_view")
            assert result["status"] == "success"

            # Verify it's deleted
            view = get_fusion_view("test_delete_view")
            assert view is None
            session.close()

    def test_delete_fusion_view_not_found(self, temp_db):
        """Test deleting a non-existent fusion view."""
        with patch("src.core.fusion.fusion_persistence.get_session") as mock_session:
            from src.core.infrastructure.models import get_session

            session = get_session(temp_db)
            mock_session.return_value = session

            result = delete_fusion_view("nonexistent_view")
            assert result["status"] == "error"
            assert "not found" in result["message"].lower()
            session.close()

    def test_update_existing_fusion_view(self, temp_db):
        """Test updating an existing fusion view."""
        with patch("src.core.fusion.fusion_persistence.get_session") as mock_session:
            from src.core.infrastructure.models import get_session

            session = get_session(temp_db)
            mock_session.return_value = session

            # Create initial view
            persist_fusion_view(
                view_name="test_update_view",
                fusion_type="join",
                sources=[{"catalog": "postgres", "schema": "public", "table": "t1"}],
                matches=[],
                view_sql="CREATE VIEW ...",
                view_catalog="memory",
                view_schema="default",
            )

            # Update it
            result = persist_fusion_view(
                view_name="test_update_view",
                fusion_type="union",
                sources=[
                    {"catalog": "postgres", "schema": "public", "table": "t1"},
                    {"catalog": "mongo", "schema": "testdb", "table": "t2"},
                ],
                matches=[{"source_col": "id", "target_col": "id"}],
                view_sql="CREATE VIEW updated ...",
                view_catalog="memory",
                view_schema="default",
            )

            assert result["status"] == "success"

            # Verify update
            view = get_fusion_view("test_update_view")
            assert view is not None
            assert view["fusion_type"] == "union"
            assert len(view["sources"]) == 2
            session.close()
