"""
Embedding generation via Amazon Bedrock (Titan Text Embeddings).

Isolated so both the indexer and the retriever embed text the same way — a
query and the documents it's matched against must come from the same model and
dimension or k-NN scores are meaningless.
"""

from __future__ import annotations

import json

from src.shared.clients import bedrock_runtime

# Titan Text Embeddings V2: 1024-dim, good multilingual coverage (the law text
# and user questions are both Spanish). Keep in sync with the index mapping's
# `dimension` in src/rag/opensearch.py.
EMBED_MODEL_ID = "amazon.titan-embed-text-v2:0"
EMBED_DIM = 1024


def embed_text(text: str) -> list[float]:
    """Return the embedding vector for a single piece of text."""
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text")
    body = json.dumps({"inputText": text, "dimensions": EMBED_DIM})
    resp = bedrock_runtime().invoke_model(modelId=EMBED_MODEL_ID, body=body)
    payload = json.loads(resp["body"].read())
    return payload["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed several texts. Titan embeds one input per call, so this loops;
    kept as a single entry point in case a batch-capable model is swapped in."""
    return [embed_text(t) for t in texts]
