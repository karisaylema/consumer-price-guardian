"""
RAG pipeline: indexing and retrieval over the Ley Orgánica de Defensa del
Consumidor (Ecuador's Consumer Protection Law, Ley No. 2000-21).

- indexer.py: Lambda handler that chunks the law by article, generates
  embeddings via Bedrock, and writes vectors + metadata to OpenSearch
  Serverless.
- retriever.py: Lambda handler (also importable directly by the agent) that
  embeds a query and returns the top-k most relevant articles.
"""
