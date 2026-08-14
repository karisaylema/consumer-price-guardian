"""Unit tests for the read-only SQL guard on the Athena tool.

The agent's LLM writes the SQL, so this guard is a security boundary, not a
nicety — every way a write could sneak through is a test here.
"""

import pytest

from src.agent.athena import SqlNotAllowed, assert_read_only


@pytest.mark.parametrize("sql", [
    "SELECT * FROM ipc WHERE year = 2026",
    "  select city, value from canasta_basica ",
    "WITH t AS (SELECT * FROM ipc) SELECT * FROM t",
    "SELECT * FROM ipc;",  # single trailing semicolon is fine
    "/* comment */ SELECT 1",
])
def test_accepts_read_only(sql):
    assert assert_read_only(sql)


@pytest.mark.parametrize("sql", [
    "INSERT INTO ipc VALUES (1)",
    "UPDATE ipc SET value = 0",
    "DELETE FROM ipc",
    "DROP TABLE ipc",
    "CREATE TABLE x (a int)",
    "ALTER TABLE ipc ADD COLUMN z int",
    "TRUNCATE TABLE ipc",
    "MSCK REPAIR TABLE ipc",
    "UNLOAD (SELECT * FROM ipc) TO 's3://x'",
])
def test_rejects_writes_and_ddl(sql):
    with pytest.raises(SqlNotAllowed):
        assert_read_only(sql)


def test_rejects_stacked_statements():
    with pytest.raises(SqlNotAllowed, match="Multiple statements"):
        assert_read_only("SELECT * FROM ipc; DROP TABLE ipc")


def test_rejects_commented_out_prefix_hiding_write():
    # The SELECT is commented out; the real statement is a DELETE.
    with pytest.raises(SqlNotAllowed):
        assert_read_only("-- SELECT 1\nDELETE FROM ipc")


def test_rejects_empty():
    with pytest.raises(SqlNotAllowed, match="Empty"):
        assert_read_only("   ")


def test_strips_trailing_semicolon_and_returns_clean_sql():
    assert assert_read_only("SELECT 1;") == "SELECT 1"
