"""
Tool definitions the LangGraph agent can call.

- sql_tool: runs a validated read-only query against Athena over the Glue
  Data Catalog tables populated by src/ingestion/*.
- retrieval_tool: wraps src/rag/retriever.py for semantic search over the
  Consumer Protection Law text.

Not yet implemented — see docs/roadmap.md Phase 4.
"""


def sql_tool(query: str):
    raise NotImplementedError("See docs/roadmap.md Phase 4")


def retrieval_tool(query: str):
    raise NotImplementedError("See docs/roadmap.md Phase 4")
