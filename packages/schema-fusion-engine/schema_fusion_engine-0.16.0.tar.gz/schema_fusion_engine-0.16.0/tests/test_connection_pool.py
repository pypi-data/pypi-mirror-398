"""Unit tests for TrinoConnectionPool catalog/schema matching logic."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from src.core.infrastructure.connection_pool import TrinoConnectionPool


class FakeConnection:
    """Simple fake Trino connection used for pooling tests.

    It records the (catalog, schema) context it was created with and
    exposes minimal ``cursor`` and ``close`` methods required by the pool's
    health checks.
    """

    def __init__(self, context: tuple[str | None, str | None]) -> None:
        self.context = context
        self.closed = False

    def cursor(self) -> object:
        """Return a dummy cursor object.

        The pool only needs this call to succeed for health checks.
        """

        return object()

    def close(self) -> None:
        """Mark the connection as closed."""

        self.closed = True


@patch("src.core.infrastructure.connection_pool.trino.dbapi.connect")
def test_pool_reuses_connection_for_same_catalog_and_schema(mock_connect) -> None:
    """Connections are reused when catalog and schema match.

    The pool should create a single underlying connection for a given
    (catalog, schema) pair and return that same connection on subsequent
    requests with the identical context.
    """

    created: list[FakeConnection] = []

    def _factory(*_: Any, **kwargs: Any) -> FakeConnection:
        ctx = (kwargs.get("catalog"), kwargs.get("schema"))
        conn = FakeConnection(ctx)
        created.append(conn)
        return conn

    mock_connect.side_effect = _factory

    pool = TrinoConnectionPool(host="localhost", port=8080, user="test", pool_size=5)

    with pool.get_connection(catalog="catalog_a", schema="schema_x") as conn1:
        first = conn1

    with pool.get_connection(catalog="catalog_a", schema="schema_x") as conn2:
        second = conn2

    # Same underlying connection object should be reused from the pool.
    assert first is second
    # Only a single physical connection should have been created.
    assert mock_connect.call_count == 1
    assert len(created) == 1
    assert created[0].context == ("catalog_a", "schema_x")


@patch("src.core.infrastructure.connection_pool.trino.dbapi.connect")
def test_pool_separates_connections_by_catalog_and_schema(mock_connect) -> None:
    """Connections with different contexts are not incorrectly shared.

    When requesting connections for different (catalog, schema) pairs, the
    pool must create and maintain distinct underlying connections and reuse
    them only for matching contexts.
    """

    created: list[FakeConnection] = []

    def _factory(*_: Any, **kwargs: Any) -> FakeConnection:
        ctx = (kwargs.get("catalog"), kwargs.get("schema"))
        conn = FakeConnection(ctx)
        created.append(conn)
        return conn

    mock_connect.side_effect = _factory

    pool = TrinoConnectionPool(host="localhost", port=8080, user="test", pool_size=5)

    # First round: create two distinct connections for different contexts.
    with pool.get_connection(catalog="catalog_a", schema="schema_x") as conn_ax_1:
        conn_ax_first = conn_ax_1
    with pool.get_connection(catalog="catalog_b", schema="schema_x") as conn_bx_1:
        conn_bx_first = conn_bx_1

    assert conn_ax_first is not conn_bx_first
    assert mock_connect.call_count == 2
    assert {c.context for c in created} == {
        ("catalog_a", "schema_x"),
        ("catalog_b", "schema_x"),
    }

    # Second round: requests with the same contexts should reuse the
    # previously created connections and not call ``connect`` again.
    with pool.get_connection(catalog="catalog_a", schema="schema_x") as conn_ax_2:
        conn_ax_second = conn_ax_2
    with pool.get_connection(catalog="catalog_b", schema="schema_x") as conn_bx_2:
        conn_bx_second = conn_bx_2

    assert conn_ax_second is conn_ax_first
    assert conn_bx_second is conn_bx_first
    # Still only two underlying physical connections.
    assert mock_connect.call_count == 2
    assert len(created) == 2
