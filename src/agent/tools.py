"""
Tools the LangGraph agent can call.

- sql_tool: runs a validated read-only query against Athena over the Glue tables
  populated by src/ingestion/*. The LLM writes the SQL; assert_read_only (in
  athena.py) is the hard guard that keeps it read-only.
- retrieval_tool: semantic search over the Consumer Protection Law via
  src/rag/retriever.py, returning cited articles.

Both are wrapped as LangChain tools so create_react_agent can bind them. They
return human-readable strings (not raw objects) because the model reads the
result to decide its next step and to write the final answer.
"""

from __future__ import annotations

import json

from langchain_core.tools import tool

from src.agent.athena import SqlNotAllowed, run_query
from src.rag.retriever import retrieve

# Schema hint injected into the system prompt so the model writes valid SQL
# without a round-trip to describe the tables.
TABLE_SCHEMA_HINT = """\
Athena tables (one row per city/category/metric/month):
  ipc(city, region, category, metric, value, unit, year, month)
  canasta_basica(city, region, category, metric, value, unit, year, month)
  canasta_vital(city, region, category, metric, value, unit, year, month)
Partition columns: year (int), month (string, zero-padded e.g. '06').
Common metrics: 'index', 'monthly_variation_pct', 'annual_variation_pct',
'cost_usd'. Cities include 'Quito', 'Guayaquil', 'Nacional'."""


@tool
def sql_tool(query: str) -> str:
    """Run a read-only SQL SELECT against the INEC price tables (ipc,
    canasta_basica, canasta_vital) on Athena and return rows as JSON. Use this
    for questions about price levels, costs, and trends over time by city or
    category."""
    try:
        rows = run_query(query)
    except SqlNotAllowed as e:
        return f"Query rejected: {e}. Only read-only SELECT/WITH queries are allowed."
    except Exception as e:  # surface the error to the model so it can retry
        return f"Query failed: {e}"
    if not rows:
        return "No rows returned."
    return json.dumps(rows, ensure_ascii=False)


@tool
def retrieval_tool(query: str) -> str:
    """Search the text of Ecuador's Ley Orgánica de Defensa del Consumidor and
    return the most relevant articles with their citations. Use this for
    questions about consumer rights, protections, billing disputes, or what the
    law says."""
    try:
        articles = retrieve(query, k=5)
    except Exception as e:
        return f"Retrieval failed: {e}"
    if not articles:
        return "No relevant articles found."
    parts = []
    for a in articles:
        header = a.label
        if a.capitulo:
            header += f" ({a.capitulo})"
        parts.append(f"{header}\n{a.text}")
    return "\n\n---\n\n".join(parts)


TOOLS = [sql_tool, retrieval_tool]
