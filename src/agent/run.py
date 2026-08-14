"""
CLI entry point: python -m src.agent.run --query "..."

Runs one question through the LangGraph agent and prints the answer. Requires a
deployed sandbox (Athena tables + OpenSearch index) and Bedrock model access —
see docs/setup.md.
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask Consumer Price Guardian a question.")
    parser.add_argument("--query", required=True, help="Natural-language question")
    parser.add_argument("--model-id", default=None, help="Override the Bedrock model id")
    args = parser.parse_args()

    # Imported here so --help works without the LLM stack installed/configured.
    from src.agent.graph import answer

    print(answer(args.query, model_id=args.model_id))


if __name__ == "__main__":
    main()
