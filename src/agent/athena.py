"""
Athena execution layer for the SQL tool.

Two responsibilities, kept small and separate so the risky bits are testable:

  - `assert_read_only`: a defensive guard that rejects anything that isn't a
    single read-only SELECT/WITH statement. The agent's LLM generates the SQL,
    so this is the boundary that stops a hallucinated DROP/INSERT/UPDATE from
    ever reaching Athena. Pure function, unit-tested.
  - `run_query`: submit to Athena, poll to completion, page results into a list
    of dict rows. Thin boto3 wrapper.

The LLM is told (in the agent system prompt) to only read; this guard makes
that a hard invariant rather than a hope.
"""

from __future__ import annotations

import re
import time
from typing import Any

from src.shared.config import config

# Statements that must never run through the read-only tool.
_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE|"
    r"MSCK|UNLOAD|REPLACE|CALL)\b",
    re.IGNORECASE,
)

_TERMINAL_STATES = {"SUCCEEDED", "FAILED", "CANCELLED"}


class SqlNotAllowed(ValueError):
    """Raised when a query isn't a single read-only statement."""


def _strip_sql(sql: str) -> str:
    """Remove comments and trailing semicolons so the guard can't be fooled by
    a commented-out prefix or a stacked second statement."""
    no_block = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    no_line = re.sub(r"--[^\n]*", " ", no_block)
    return no_line.strip().rstrip(";").strip()


def assert_read_only(sql: str) -> str:
    """Validate and return a normalized single read-only query, else raise.

    Rejects: empty input, stacked statements (a `;` between two statements),
    any DDL/DML keyword, and anything not starting with SELECT or WITH.
    """
    cleaned = _strip_sql(sql)
    if not cleaned:
        raise SqlNotAllowed("Empty query")
    # After stripping the single allowed trailing ';', no ';' should remain —
    # its presence means a second (stacked) statement.
    if ";" in cleaned:
        raise SqlNotAllowed("Multiple statements are not allowed")
    if not re.match(r"(?is)^\s*(SELECT|WITH)\b", cleaned):
        raise SqlNotAllowed("Only SELECT / WITH queries are allowed")
    if _FORBIDDEN.search(cleaned):
        raise SqlNotAllowed("Query contains a non-read-only keyword")
    return cleaned


def run_query(sql: str, *, max_rows: int = 200, poll_seconds: float = 1.0,
              timeout_seconds: float = 60.0) -> list[dict[str, Any]]:
    """Run a read-only query on Athena and return up to `max_rows` dict rows."""
    query = assert_read_only(sql)
    config.require("glue_database_name", "athena_workgroup")
    # Imported lazily so assert_read_only (the security-critical guard) stays
    # importable and unit-testable without boto3 / AWS configured.
    from src.shared.clients import athena
    client = athena()

    start = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": config.glue_database_name},
        WorkGroup=config.athena_workgroup,
    )
    execution_id = start["QueryExecutionId"]

    deadline = time.monotonic() + timeout_seconds
    while True:
        info = client.get_query_execution(QueryExecutionId=execution_id)
        state = info["QueryExecution"]["Status"]["State"]
        if state in _TERMINAL_STATES:
            break
        if time.monotonic() > deadline:
            client.stop_query_execution(QueryExecutionId=execution_id)
            raise TimeoutError(f"Athena query timed out after {timeout_seconds}s")
        time.sleep(poll_seconds)

    if state != "SUCCEEDED":
        reason = info["QueryExecution"]["Status"].get("StateChangeReason", state)
        raise RuntimeError(f"Athena query {state}: {reason}")

    return _fetch_rows(client, execution_id, max_rows)


def _fetch_rows(client: Any, execution_id: str, max_rows: int) -> list[dict[str, Any]]:
    """Read the result set, mapping the header row onto each data row."""
    result = client.get_query_results(
        QueryExecutionId=execution_id, MaxResults=min(max_rows + 1, 1000)
    )
    rows = result["ResultSet"]["Rows"]
    if not rows:
        return []
    header = [c.get("VarCharValue", "") for c in rows[0]["Data"]]
    out: list[dict[str, Any]] = []
    for row in rows[1:]:
        values = [c.get("VarCharValue") for c in row["Data"]]
        out.append(dict(zip(header, values)))
        if len(out) >= max_rows:
            break
    return out
