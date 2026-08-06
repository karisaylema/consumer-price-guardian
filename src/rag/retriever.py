"""
Retrieval over the indexed Consumer Protection Law.

Given a natural language query, embeds it and performs a k-NN search against
the OpenSearch Serverless index, returning the top-k article chunks so the
agent can cite the specific article (e.g. "Art. 39 — Facturación de Consumo
Excesivo") in its answer rather than paraphrasing without attribution.

Not yet implemented — see docs/roadmap.md Phase 3.
"""


def retrieve(query: str, k: int = 5):
    raise NotImplementedError("See docs/roadmap.md Phase 3")
