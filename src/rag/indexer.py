"""
Lambda handler: chunk the Consumer Protection Law text and index into
OpenSearch Serverless.

Planned flow:
  1. Triggered on new object upload to s3://<raw-bucket>/consumer-law-text/
  2. Extract text (source is the official PDF from gob.ec)
  3. Chunk by article (Art. 1, Art. 39, Art. 66, etc.) rather than fixed
     token windows — an article is the natural citation unit for legal text,
     and chunking any other way risks splitting a single provision across
     two retrieved chunks
  4. Generate embeddings via Bedrock (Titan Embeddings or similar)
  5. Bulk index into OpenSearch Serverless with metadata: article number,
     chapter/title, short description

Not yet implemented — see docs/roadmap.md Phase 3.
"""


def handler(event, context):
    raise NotImplementedError("See docs/roadmap.md Phase 3")
