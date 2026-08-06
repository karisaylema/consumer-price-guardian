"""
Central configuration.

Reads settings from the environment (populated from .env via python-dotenv in
local dev, or from real environment variables in Lambda/Glue). Keeping every
resource identifier in one place means the ingestion jobs, RAG functions, and
agent tools all resolve names the same way instead of each reaching for
os.environ ad hoc.

See .env.example for the full list of variables. Values that don't exist until
`terraform apply` has run (bucket names, endpoints) default to empty strings so
importing this module never fails — the consuming code is responsible for
asserting what it actually needs.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    bedrock_model_id: str = os.getenv(
        "BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"
    )

    # Filled in after `terraform apply` (see infra/outputs.tf)
    raw_data_bucket: str = os.getenv("RAW_DATA_BUCKET", "")
    processed_data_bucket: str = os.getenv("PROCESSED_DATA_BUCKET", "")
    glue_database_name: str = os.getenv("GLUE_DATABASE_NAME", "")
    athena_workgroup: str = os.getenv("ATHENA_WORKGROUP", "")
    athena_output_location: str = os.getenv("ATHENA_OUTPUT_LOCATION", "")
    opensearch_collection_endpoint: str = os.getenv("OPENSEARCH_COLLECTION_ENDPOINT", "")
    opensearch_index_name: str = os.getenv("OPENSEARCH_INDEX_NAME", "consumer-law-text")

    def require(self, *names: str) -> None:
        """Assert that the named settings are non-empty, else raise.

        Call this at the top of code paths that need infra to be deployed, so
        the failure is a clear 'set RAW_DATA_BUCKET' rather than an opaque AWS
        error deeper in a boto3 call.
        """
        missing = [n for n in names if not getattr(self, n)]
        if missing:
            raise RuntimeError(
                f"Missing required config: {', '.join(missing)}. "
                "Did you copy .env.example to .env and run `terraform apply`?"
            )


config = Config()
