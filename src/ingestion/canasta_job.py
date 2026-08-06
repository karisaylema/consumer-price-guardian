"""
Glue ETL job stub: INEC Canasta Familiar Básica / Vital

Responsibilities (planned):
  1. Read raw monthly release from s3://<raw-bucket>/canasta/
     (published as "Canasta Formato CSV" plus a national/by-city XLSX)
  2. Normalize schema to the shared PriceRecord format (see src/shared/schemas.py)
  3. Write partitioned Parquet to s3://<processed-bucket>/canasta/
  4. Update Glue Data Catalog table via boto3 glue client

Not yet implemented — see docs/roadmap.md Phase 2.
"""


def run(glue_context, args):
    raise NotImplementedError("See docs/roadmap.md Phase 2")
