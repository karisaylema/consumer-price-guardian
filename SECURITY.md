# Security

## Reporting a vulnerability

This is a personal portfolio project, not a production service. If you spot a
security issue, please open a GitHub issue (for non-sensitive reports) or contact
the maintainer directly for anything sensitive. There is no formal SLA.

## Security posture

Design choices worth calling out:

- **No secrets in the repo.** `.env` is gitignored; `.env.example` only documents
  variable names. Resource identifiers are produced by `terraform apply`, not
  committed. CI runs a gitleaks secret scan on every push and PR.
- **LLM-generated SQL is guarded.** The agent's SQL tool runs every query through
  `assert_read_only` (`src/agent/athena.py`), which strips comments, rejects
  stacked statements, and allows only single `SELECT`/`WITH` queries — a hard
  invariant, not a prompt-level hope. It is unit-tested.
- **Least-privilege IAM.** The RAG Lambda roles are scoped to the specific Bedrock
  embeddings model and to OpenSearch data-plane access only.
- **Encryption.** S3 buckets use SSE at rest, enforce TLS in transit via a
  bucket policy, block all public access, and version objects. The Athena
  workgroup encrypts query results. OpenSearch Serverless uses an encryption
  policy.
- **Dependency & IaC scanning.** CI runs `pip-audit` on dependencies and `tfsec`
  on the Terraform, and Dependabot keeps pip / GitHub Actions / Terraform
  versions current.

## Known sandbox trade-offs

- OpenSearch Serverless network access defaults to public (still SigV4
  authenticated). Set `allow_public_network_access = false` and front it with a
  VPC endpoint for anything beyond a solo sandbox.
- Terraform state is local. Move to an S3 backend with DynamoDB locking before
  collaborating (see `infra/versions.tf`).
