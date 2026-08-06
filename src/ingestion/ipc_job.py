"""
Glue ETL job stub: INEC IPC (Índice de Precios al Consumidor)

Responsibilities (planned):
  1. Read raw monthly release from s3://<raw-bucket>/ipc/
     (INEC publishes as CSV or XLSX depending on the month — normalize both)
  2. Normalize schema to the shared PriceRecord format (see src/shared/schemas.py)
  3. Write partitioned Parquet to s3://<processed-bucket>/ipc/
  4. Update Glue Data Catalog table via boto3 glue client

Known data quirk: INEC's IPC hierarchy (División > Grupo > Clase > Subclase >
Producto > Artículo) and column naming have shifted across years. Don't
assume a stable schema — validate against a known-good sample before
trusting a new month's release.

Not yet implemented — see docs/roadmap.md Phase 2.
"""


def run(glue_context, args):
    raise NotImplementedError("See docs/roadmap.md Phase 2")
