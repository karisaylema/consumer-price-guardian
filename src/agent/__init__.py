"""
LangGraph agent that orchestrates the SQL tool and retrieval tool.

The agent decides, per incoming query, whether it needs structured price
data (via Athena), consumer law text (via OpenSearch retrieval), or both —
then synthesizes a final answer that combines the observed price trend with
the specific legal article that applies.

Explicitly not a legal advice generator: the agent cites and explains what
the law says, and does not tell a user whether they have a winning case.
See docs/roadmap.md "Deliberately out of scope."
"""
