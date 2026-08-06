# Roadmap

Tracking what's built vs. planned. Kept honest on purpose — this is a live portfolio project, not a finished product.

## Phase 1: Foundation
- [x] Repo structure and documentation
- [ ] Terraform base (S3 buckets, IAM roles, networking)
- [ ] CI pipeline skeleton (lint, test, terraform plan on PR)

## Phase 2: Structured data pipeline
- [ ] Glue ETL job for INEC IPC (Índice de Precios al Consumidor) monthly CSV/XLSX releases
- [ ] Glue ETL job for INEC Canasta Familiar Básica / Vital, by city
- [ ] Glue Data Catalog schema definitions
- [ ] Athena queries validated against sample data
- [ ] Unit tests for transformation logic
- [ ] Handle INEC's format inconsistencies across months (some releases are
      .xls, others .xlsx; column naming has shifted historically — normalize
      in the ETL layer, don't assume a stable schema)

## Phase 3: RAG pipeline
- [ ] Ley Orgánica de Defensa del Consumidor text ingestion (chunk by
      article, since that's the natural citation unit — "Art. 39" needs to
      map to a single retrievable chunk)
- [ ] Lambda: embedding generation via Bedrock
- [ ] OpenSearch Serverless collection + index setup
- [ ] Lambda: retrieval endpoint
- [ ] Retrieval quality evaluation (sample Q&A set built from known articles,
      e.g. Art. 39 excessive billing, Art. 66 technical/quality standards)

## Phase 4: Agent
- [ ] LangGraph agent definition
- [ ] SQL tool (Athena wrapper)
- [ ] Retrieval tool (OpenSearch wrapper)
- [ ] Tool routing logic and system prompt
- [ ] Integration tests: end-to-end query -> answer

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
