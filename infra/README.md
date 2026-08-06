# Infrastructure

Terraform modules for all AWS resources this project uses.

## Modules

- `modules/data_lake` — S3 buckets (raw, processed), bucket policies
- `modules/glue` — Glue database, crawlers, job definitions (planned)
- `modules/opensearch` — OpenSearch Serverless collection + access policy (planned)
- `modules/lambda_rag` — Lambda functions for indexing/retrieval + IAM roles (planned)

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
