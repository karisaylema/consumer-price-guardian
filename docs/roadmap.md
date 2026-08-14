# Roadmap

Tracking what's built vs. planned. Kept honest on purpose — this is a live portfolio project, not a finished product.

## Phase 1: Foundation
- [x] Repo structure and documentation
- [x] Terraform base (S3 buckets, IAM roles, networking)
- [x] CI pipeline skeleton (lint, test, terraform plan on PR)

## Phase 2: Structured data pipeline
- [x] Glue ETL job for INEC IPC (Índice de Precios al Consumidor) monthly CSV/XLSX releases
- [x] Glue ETL job for INEC Canasta Familiar Básica / Vital, by city
- [x] Glue Data Catalog schema definitions
- [x] Athena query layer (read-only guard + execution wrapper) validated in unit tests
- [x] Unit tests for transformation logic
- [x] Handle INEC's format inconsistencies across months (some releases are
      .xls, others .xlsx; column naming has shifted historically — normalized
      defensively via alias maps in `src/ingestion/normalize.py`)

## Phase 3: RAG pipeline
- [x] Ley Orgánica de Defensa del Consumidor text ingestion (chunk by
      article, since that's the natural citation unit — "Art. 39" maps to a
      single retrievable chunk); see `src/rag/chunker.py`
- [x] Lambda: embedding generation via Bedrock (`src/rag/embeddings.py`)
- [x] OpenSearch Serverless collection + index setup (infra + `src/rag/opensearch.py`)
- [x] Lambda: retrieval endpoint (`src/rag/retriever.py`)
- [ ] Retrieval quality evaluation (sample Q&A set built from known articles,
      e.g. Art. 39 excessive billing, Art. 66 technical/quality standards)

## Phase 4: Agent
- [x] LangGraph agent definition (`src/agent/graph.py`)
- [x] SQL tool (Athena wrapper) with read-only guard
- [x] Retrieval tool (OpenSearch wrapper)
- [x] Tool routing logic and system prompt (incl. the "cite, don't advise" constraint)
- [ ] Integration tests: end-to-end query -> answer (requires deployed sandbox)

## Phase 5: Polish
- [ ] Architecture diagram (proper rendered version)
- [ ] Example queries and outputs in README
- [ ] Cost notes (Bedrock + OpenSearch Serverless can add up — document expected spend)
- [ ] Demo video or screenshots

## Deliberately out of scope (for now)
- Multi-user auth / API gateway front end
- Fine-tuning (using Bedrock foundation models as-is)
- Real-time streaming ingestion (INEC releases are monthly, batch is sufficient)
- Legal advice generation — the agent cites and explains what the law says;
  it does not tell a user whether they have a winning case
