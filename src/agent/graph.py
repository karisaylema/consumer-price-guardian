"""
LangGraph agent: routes each question to the SQL and/or retrieval tool and
synthesizes an answer.

Built on create_react_agent (a prebuilt tool-calling loop) with Claude on
Bedrock. The model decides per query whether it needs price data (sql_tool),
legal text (retrieval_tool), both, or neither — the two-pipeline architecture
surfaces here as two independent tools it can compose.

The system prompt carries the project's hard constraint: this agent explains
and cites what the law says; it never gives legal advice or predicts whether a
user would win a case.
"""

from __future__ import annotations

from src.agent.tools import TABLE_SCHEMA_HINT, TOOLS
from src.shared.config import config

SYSTEM_PROMPT = f"""You are Consumer Price Guardian, an assistant that helps \
people in Ecuador understand consumer price trends and their rights under \
Ecuadorian consumer protection law.

You have two tools:
- sql_tool: read-only SQL over official INEC price statistics (IPC and the \
Canasta Familiar Básica/Vital), by city, region, and category, over time.
- retrieval_tool: semantic search over the Ley Orgánica de Defensa del \
Consumidor (Ley No. 2000-21).

How to work:
- For questions about prices, costs, or trends, use sql_tool. Write a single \
read-only SELECT. {TABLE_SCHEMA_HINT}
- For questions about rights, protections, billing, or what the law says, use \
retrieval_tool, then cite the specific article(s) it returns (e.g. "Art. 39").
- Many questions need both: get the price trend AND the applicable article, \
then reason over the combination.
- Answer in the language the user asked in (usually Spanish).

Hard rules — do not break these:
- You explain and cite what the law says. You do NOT give legal advice and you \
do NOT tell a user whether they would win a case or a claim. If asked to, \
explain that you can describe what the law says and cite the relevant article, \
but that assessing a specific case requires a qualified lawyer.
- Cite articles by number whenever you rely on the law. Do not invent article \
numbers or statistics — if a tool returns nothing, say so.
- Ground price claims in sql_tool results; do not estimate figures yourself."""


def build_graph(model_id: str | None = None):
    """Construct the compiled LangGraph agent. Imports the AWS/LLM stack lazily
    so importing this module (e.g. for tests) doesn't require langchain-aws."""
    from langchain_aws import ChatBedrock
    from langgraph.prebuilt import create_react_agent

    llm = ChatBedrock(
        model_id=model_id or config.bedrock_model_id,
        region_name=config.aws_region,
    )
    return create_react_agent(llm, TOOLS, prompt=SYSTEM_PROMPT)


def answer(question: str, model_id: str | None = None) -> str:
    """Run one question through the agent and return the final text answer."""
    graph = build_graph(model_id)
    result = graph.invoke({"messages": [("user", question)]})
    return result["messages"][-1].content
