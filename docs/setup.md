# Local setup

## Prerequisites

- Python 3.11+
- AWS CLI configured with a profile that has access to a sandbox account
- Terraform 1.7+
- An AWS account with Bedrock model access enabled (Claude models)

## 1. Clone and install

```bash
git clone https://github.com/<your-username>/consumer-price-guardian.git
cd consumer-price-guardian
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure AWS

```bash
export AWS_PROFILE=consumer-price-guardian-sandbox
export AWS_REGION=us-east-1
```

Copy `.env.example` to `.env` and fill in bucket names / resource identifiers once infra is deployed (step 3).

## 3. Deploy infrastructure

```bash
cd infra
terraform init
terraform plan
terraform apply
```

This provisions: S3 buckets for raw/processed data, the Glue Data Catalog and jobs, an OpenSearch Serverless collection, and the Lambda functions for RAG indexing/retrieval. See `infra/README.md` for module-level details.

## 4. Load sample data _(Phase 2 — work in progress)_

```bash
python scripts/load_sample_data.py
```

Intended to upload a small sample of INEC IPC / Canasta data to the raw bucket
for local testing without hitting ecuadorencifras.gob.ec directly. This helper
is currently a stub (see [docs/roadmap.md](roadmap.md) Phase 2) — until it lands,
upload sample files to the raw bucket manually, e.g.:

```bash
aws s3 cp ./data/raw/ "s3://$RAW_DATA_BUCKET/" --recursive
```

## 5. Run the agent locally

```bash
python -m src.agent.run --query "¿Cuánto ha subido la canasta básica en Quito este año?"
```

## Running tests

```bash
pytest tests/unit          # no AWS access needed
pytest tests/integration   # requires deployed sandbox infra
```

## Cost note

OpenSearch Serverless and Bedrock both bill by usage. Tear down the sandbox (`terraform destroy`) when not actively developing to avoid idle OpenSearch OCU charges.

## Data note

INEC publishes IPC and Canasta Familiar data monthly at ecuadorencifras.gob.ec,
in a mix of CSV and Excel formats depending on the release. File naming and
column structure has shifted over the years — see the note in
docs/roadmap.md Phase 2 about normalizing this in the ETL layer rather than
assuming a stable schema.
