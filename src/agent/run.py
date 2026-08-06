"""
CLI entry point: python -m src.agent.run --query "..."

Not yet implemented — see docs/roadmap.md Phase 4.
"""

import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.parse_args()
    raise NotImplementedError("See docs/roadmap.md Phase 4")


if __name__ == "__main__":
    main()
