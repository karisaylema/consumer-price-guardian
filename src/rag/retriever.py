"""
Retrieval over the indexed Consumer Protection Law.

Given a natural-language query, embeds it and runs a k-NN search against the
OpenSearch Serverless index, returning the top-k article chunks with their
citation metadata so the agent can cite a specific article (e.g. "Art. 39 —
Facturación de Consumo Excesivo") rather than paraphrasing without attribution.

Importable directly by the agent's retrieval_tool, and also exposed as a Lambda
handler for a standalone retrieval endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.rag.embeddings import embed_text
from src.rag.opensearch import get_client
from src.shared.config import config


@dataclass
class RetrievedArticle:
    article_number: int
    label: str
    titulo: str | None
    capitulo: str | None
    text: str
    score: float


def retrieve(query: str, k: int = 5) -> list[RetrievedArticle]:
    """Return the top-k most relevant law articles for `query`."""
    if not query or not query.strip():
        raise ValueError("Empty query")
    config.require("opensearch_collection_endpoint")

    vector = embed_text(query)
    body = {
        "size": k,
        "query": {"knn": {"embedding": {"vector": vector, "k": k}}},
        "_source": ["article_number", "label", "titulo", "capitulo", "text"],
    }
    resp = get_client().search(index=config.opensearch_index_name, body=body)
    return [_hit_to_article(h) for h in resp["hits"]["hits"]]


def _hit_to_article(hit: dict) -> RetrievedArticle:
    src = hit["_source"]
    return RetrievedArticle(
        article_number=src["article_number"],
        label=src["label"],
        titulo=src.get("titulo"),
        capitulo=src.get("capitulo"),
        text=src["text"],
        score=hit["_score"],
    )


def handler(event: dict, context) -> dict:
    """Lambda entrypoint: {"query": "...", "k": 5} -> {"articles": [...]}."""
    query = event["query"]
    k = int(event.get("k", 5))
    articles = retrieve(query, k=k)
    return {"articles": [a.__dict__ for a in articles]}
