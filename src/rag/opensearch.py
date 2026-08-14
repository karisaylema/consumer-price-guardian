"""
OpenSearch Serverless client + index helpers for the legal-text vector store.

Builds a SigV4-signed client (Serverless uses the `aoss` service) and centralizes
the index mapping so the indexer and retriever agree on field names and the knn
vector dimension.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from src.rag.embeddings import EMBED_DIM
from src.shared.config import config

# knn index mapping. `embedding` is the vector; the rest is citation metadata
# the agent surfaces alongside the retrieved text.
INDEX_MAPPING: dict[str, Any] = {
    "settings": {"index": {"knn": True}},
    "mappings": {
        "properties": {
            "embedding": {
                "type": "knn_vector",
                "dimension": EMBED_DIM,
                "method": {
                    "name": "hnsw",
                    "engine": "faiss",
                    "space_type": "cosinesimil",
                },
            },
            "article_number": {"type": "integer"},
            "label": {"type": "text"},
            "titulo": {"type": "keyword"},
            "capitulo": {"type": "keyword"},
            "text": {"type": "text"},
        }
    },
}


@lru_cache(maxsize=1)
def get_client():
    """Build a signed OpenSearch client for the configured Serverless endpoint."""
    # Imported lazily so unit tests that only touch mappings don't need the
    # opensearch/aws4auth stack installed.
    import boto3
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from requests_aws4auth import AWS4Auth

    config.require("opensearch_collection_endpoint")
    creds = boto3.Session().get_credentials()
    auth = AWS4Auth(
        creds.access_key, creds.secret_key, config.aws_region, "aoss",
        session_token=creds.token,
    )
    host = config.opensearch_collection_endpoint.replace("https://", "")
    return OpenSearch(
        hosts=[{"host": host, "port": 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_maxsize=20,
    )


def ensure_index(client: Any | None = None) -> None:
    """Create the index with the knn mapping if it doesn't already exist."""
    client = client or get_client()
    name = config.opensearch_index_name
    if not client.indices.exists(index=name):
        client.indices.create(index=name, body=INDEX_MAPPING)
