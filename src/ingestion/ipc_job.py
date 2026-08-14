"""
Glue Python-Shell job: INEC IPC (Índice de Precios al Consumidor).

Flow:
  1. Read the raw monthly release from s3://<raw-bucket>/ipc/<key>
     (INEC publishes CSV or XLSX depending on the month — read_raw handles both)
  2. Normalize to the shared PriceRecord shape (src/ingestion/normalize.py)
  3. Validate against the known-good contract before writing anything
  4. Write partitioned Parquet to s3://<processed-bucket>/ipc/year=/month=/
  5. Register the partition in the Glue Data Catalog so Athena sees it

Known data quirk: INEC's IPC hierarchy (División > Grupo > Clase > Subclase >
Producto > Artículo) and column naming have shifted across years. The alias
maps in normalize.py absorb that — don't special-case it here.

Run locally (against a sandbox):
    python -m src.ingestion.ipc_job --raw-key ipc/2026-06.xlsx --year 2026 --month 6

As a Glue Python-Shell job, arguments arrive via getResolvedOptions; see main().
"""

from __future__ import annotations

from src.ingestion.normalize import normalize_ipc, validate
from src.ingestion.writer import read_raw_from_s3, register_partition, write_parquet
from src.shared.config import config


def run(*, raw_key: str, year: int | None = None, month: int | None = None) -> str:
    """Ingest one IPC release. Returns the s3:// URI of the written Parquet."""
    config.require("raw_data_bucket", "processed_data_bucket")
    df = read_raw_from_s3(config.raw_data_bucket, raw_key)
    records = validate(normalize_ipc(df, year=year, month=month))
    location = write_parquet(records)
    first = records[0]
    register_partition("ipc", first.year, first.month, location)
    return location


def main() -> None:
    # Imported here so the module stays importable (and testable) without the
    # Glue runtime, which only exists inside the Glue Python-Shell environment.
    import sys

    from awsglue.utils import getResolvedOptions  # type: ignore

    opts = getResolvedOptions(sys.argv, ["raw_key", "year", "month"])
    location = run(raw_key=opts["raw_key"], year=int(opts["year"]),
                   month=int(opts["month"]))
    print(f"Wrote {location}")


if __name__ == "__main__":
    main()
