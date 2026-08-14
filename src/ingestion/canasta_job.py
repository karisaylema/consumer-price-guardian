"""
Glue Python-Shell job: INEC Canasta Familiar Básica / Vital.

Flow mirrors ipc_job:
  1. Read the raw monthly release from s3://<raw-bucket>/canasta/<key>
     (published as a CSV plus a national/by-city XLSX depending on the month)
  2. Normalize to the shared PriceRecord shape (category = the basket name)
  3. Validate against the known-good contract
  4. Write partitioned Parquet to s3://<processed-bucket>/<kind>/year=/month=/
  5. Register the partition in the Glue Data Catalog

`kind` selects Básica vs Vital; each lands in its own catalog table so Athena
queries can target one basket without filtering.

Run locally (against a sandbox):
    python -m src.ingestion.canasta_job --raw-key canasta/2026-06.xlsx \
        --kind canasta_basica --year 2026 --month 6
"""

from __future__ import annotations

from src.ingestion.normalize import normalize_canasta, validate
from src.ingestion.writer import read_raw_from_s3, register_partition, write_parquet
from src.shared.config import config


def run(*, raw_key: str, kind: str = "canasta_basica",
        year: int | None = None, month: int | None = None) -> str:
    """Ingest one Canasta release. Returns the s3:// URI of the written Parquet."""
    config.require("raw_data_bucket", "processed_data_bucket")
    df = read_raw_from_s3(config.raw_data_bucket, raw_key)
    records = validate(normalize_canasta(df, kind=kind, year=year, month=month))
    location = write_parquet(records)
    first = records[0]
    register_partition(first.source, first.year, first.month, location)
    return location


def main() -> None:
    import sys

    from awsglue.utils import getResolvedOptions  # type: ignore

    opts = getResolvedOptions(sys.argv, ["raw_key", "kind", "year", "month"])
    location = run(raw_key=opts["raw_key"], kind=opts["kind"],
                   year=int(opts["year"]), month=int(opts["month"]))
    print(f"Wrote {location}")


if __name__ == "__main__":
    main()
