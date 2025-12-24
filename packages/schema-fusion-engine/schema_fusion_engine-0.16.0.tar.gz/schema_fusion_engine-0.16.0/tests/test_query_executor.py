import importlib
from collections import deque
from contextlib import contextmanager
from typing import Any

import pytest

from src.core.query.query_executor import QueryExecutor


class FakeCursor:
    def __init__(self, calls: deque[str]) -> None:
        self._calls = calls
        self.description = [("col",)]  # minimal non-empty description

    def execute(self, sql: str) -> None:  # noqa: D401 - simple recorder
        """Record executed SQL instead of sending it to Trino."""
        self._calls.append(sql)

    def fetchmany(self, size: int) -> list[list[Any]]:  # noqa: D401
        """Return an empty result set."""
        return []


class FakeConnection:
    def __init__(self, calls: deque[str]) -> None:
        self._calls = calls

    def cursor(self) -> FakeCursor:  # noqa: D401
        """Return a cursor that records all executions."""
        return FakeCursor(self._calls)

    def close(self) -> None:  # noqa: D401
        """No-op close for compatibility with pool."""
        return None


class FakeTrinoClient:
    def __init__(self, calls: deque[str]) -> None:
        self._calls = calls

    @contextmanager
    def get_connection(self, catalog: str | None = None, schema: str | None = None):  # type: ignore[override]
        # Mimic the real API but just yield a fake connection.
        conn = FakeConnection(self._calls)
        try:
            yield conn
        finally:
            conn.close()


@pytest.mark.parametrize("use_async", [False, True])
@pytest.mark.anyio
async def test_query_executor_scopes_session_with_use_statement(
    monkeypatch: pytest.MonkeyPatch, use_async: bool
) -> None:
    """When both catalog and schema are provided, QueryExecutor must issue a USE statement first.

    This directly exercises the internal _execute_query / _execute_query_async paths instead of
    mocking QueryExecutor, ensuring the new USE logic is covered.
    """

    calls: deque[str] = deque()
    fake_client = FakeTrinoClient(calls)

    # Patch the module-level trino_client used inside QueryExecutor internals.
    # The attribute lives on the module, not on the QueryExecutor instance.
    query_executor_module = importlib.import_module("src.core.query.query_executor")
    monkeypatch.setattr(query_executor_module, "trino_client", fake_client)

    executor = QueryExecutor(enable_validation=False, enable_cache=False)

    if use_async:
        await executor.execute_async(
            query="SELECT customer_name FROM customers",
            catalog="postgres",
            schema="public",
            max_rows=10,
        )
    else:
        executor.execute(
            query="SELECT customer_name FROM customers",
            catalog="postgres",
            schema="public",
            max_rows=10,
        )

    # We expect the first statement to scope the session, followed by the actual query.
    assert list(calls)[0:2] == [
        'USE "postgres"."public"',
        "SELECT customer_name FROM customers",
    ]


@pytest.mark.anyio
async def test_query_executor_escapes_identifier_quotes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Catalog and schema names with quotes are safely escaped in USE statement."""

    calls: deque[str] = deque()
    fake_client = FakeTrinoClient(calls)

    query_executor_module = importlib.import_module("src.core.query.query_executor")
    monkeypatch.setattr(query_executor_module, "trino_client", fake_client)

    executor = QueryExecutor(enable_validation=False, enable_cache=False)

    await executor.execute_async(
        query="SELECT 1",
        catalog='cat"alog',
        schema='sch"ema',
        max_rows=1,
    )

    # First call should be a USE statement with identifiers properly escaped.
    assert list(calls)[0] == 'USE "cat""alog"."sch""ema"'


@pytest.mark.anyio
async def test_query_executor_does_not_emit_use_for_catalog_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When only catalog is provided, no USE statement is issued.

    The Trino connection itself is created with the catalog parameter, so
    QueryExecutor should not prepend an explicit USE statement.
    """

    calls: deque[str] = deque()
    fake_client = FakeTrinoClient(calls)

    query_executor_module = importlib.import_module("src.core.query.query_executor")
    monkeypatch.setattr(query_executor_module, "trino_client", fake_client)

    executor = QueryExecutor(enable_validation=False, enable_cache=False)

    await executor.execute_async(
        query="SELECT 1",
        catalog="postgres",
        schema=None,
        max_rows=1,
    )

    # Only the query itself should be executed, with no preceding USE.
    assert list(calls) == ["SELECT 1"]
