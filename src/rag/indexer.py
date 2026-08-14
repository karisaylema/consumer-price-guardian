"""
Lambda handler: chunk the Consumer Protection Law text and index it into
OpenSearch Serverless.

Flow:
  1. Triggered on a new object under s3://<raw-bucket>/consumer-law-text/
     (a UTF-8 text extraction of the official gob.ec PDF; extraction is an
     upstream preprocessing step so this stays a pure text pipeline)
  2. Chunk by article (src/rag/chunker.py) — one chunk per Art. N
  3. Embed each chunk via Bedrock (src/rag/embeddings.py)
  4. Bulk index vectors + citation metadata into OpenSearch Serverless

Re-running on the same document is idempotent: each chunk's document id is
derived from its article number, so a re-index overwrites rather than dupes.

Run locally against a sandbox:
    python -m src.rag.indexer --key consumer-law-text/ley-2000-21.txt
"""

from __future__ import annotations

from src.rag.chunker import ArticleChunk, chunk_law
from src.rag.embeddings import embed_text
from src.rag.opensearch import ensure_index, get_client
from src.shared.clients import s3
from src.shared.config import config


def _doc(chunk: ArticleChunk) -> dict:
    return {
        "article_number": chunk.article_number,
        "label": chunk.label,
        "titulo": chunk.titulo,
        "capitulo": chunk.capitulo,
        "text": chunk.text,
        "embedding": embed_text(chunk.text),
    }


def index_text(text: str) -> int:
    """Chunk, embed, and index a full law document. Returns the chunk count."""
    chunks = chunk_law(text)
    if not chunks:
        raise ValueError("No articles found in the supplied law text")

    client = get_client()
    ensure_index(client)

    # opensearchpy bulk NDJSON: action line + source line per doc.
    bulk: list[dict] = []
    for chunk in chunks:
        bulk.append({"index": {"_index": config.opensearch_index_name,
                               "_id": f"art-{chunk.article_number}"}})
        bulk.append(_doc(chunk))
    client.bulk(body=bulk)
    return len(chunks)


def index_from_s3(bucket: str, key: str) -> int:
    obj = s3().get_object(Bucket=bucket, Key=key)
    text = obj["Body"].read().decode("utf-8")
    return index_text(text)


def handler(event: dict, context) -> dict:
    """S3-trigger entrypoint. Indexes every object in the event record set."""
    config.require("raw_data_bucket", "opensearch_collection_endpoint")
    total = 0
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        total += index_from_s3(bucket, key)
    return {"indexed_articles": total}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True,
                        help="S3 key of the law text under the raw bucket")
    args = parser.parse_args()
    config.require("raw_data_bucket", "opensearch_collection_endpoint")
    count = index_from_s3(config.raw_data_bucket, args.key)
    print(f"Indexed {count} articles")


if __name__ == "__main__":
    main()
