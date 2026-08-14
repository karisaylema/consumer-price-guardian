# Infrastructure

Terraform modules for all AWS resources this project uses.

## Modules

- `modules/data_lake` — S3 buckets (raw, processed): versioning, SSE-S3, public-access block
- `modules/glue` — Glue database + partitioned Parquet tables (ipc, canasta_basica, canasta_vital) + Athena workgroup
- `modules/iam` — execution roles for the RAG Lambdas (kept separate to avoid a module dependency cycle)
- `modules/opensearch` — OpenSearch Serverless VECTORSEARCH collection + encryption/network/data-access policies
- `modules/lambda_rag` — indexer + retriever Lambda functions and the S3 → indexer trigger

The RAG Lambdas deploy a build artifact (`infra/build/rag_lambda.zip`) produced
by `scripts/build_lambda.sh` — build it before `terraform apply`.

## State

State is currently local for solo development. If this grows into something
collaborated on, move to an S3 backend with DynamoDB locking (see comment in
`versions.tf`).

## Applying changes

```bash
terraform init
terraform plan
terraform apply
```

Always run `plan` and read it before `apply` — several of these resources
(OpenSearch Serverless, Glue) bill by usage even when idle.
