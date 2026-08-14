"""
Shared I/O for the ingestion jobs: read a raw release from S3, write the
normalized records back as partitioned Parquet, and register the partition in
the Glue Data Catalog so Athena sees it.

Kept separate from normalize.py so the transformation logic stays free of AWS
imports and unit-testable offline. Everything here is thin glue around boto3 /
pyarrow; the interesting logic lives in normalize.py.
"""

from __future__ import annotations

import io

import pandas as pd

from src.ingestion.normalize import read_raw
from src.shared.clients import glue, s3
from src.shared.config import config
from src.shared.schemas import PriceRecord


def read_raw_from_s3(bucket: str, key: str) -> pd.DataFrame:
    """Download an object and parse it, choosing the reader by key extension."""
    obj = s3().get_object(Bucket=bucket, Key=key)
    body = io.BytesIO(obj["Body"].read())
    fmt = key.rsplit(".", 1)[-1].lower() if "." in key else "csv"
    return read_raw(body, fmt=fmt)


def _partition_prefix(source: str, year: int, month: int) -> str:
    # Hive-style partitioning so Glue/Athena pick up source/year/month for free.
    return f"{source}/year={year}/month={month:02d}"


def write_parquet(records: list[PriceRecord], *, bucket: str | None = None) -> str:
    """Write records to processed S3 as a single partitioned Parquet object.

    Assumes all records share one (source, year, month) — the ingestion jobs
    process one monthly release at a time. Returns the s3:// URI written.
    """
    if not records:
        raise ValueError("Refusing to write an empty record set")
    if bucket is None:
        config.require("processed_data_bucket")
        bucket = config.processed_data_bucket

    first = records[0]
    if any((r.source, r.year, r.month) != (first.source, first.year, first.month)
           for r in records):
        raise ValueError("write_parquet expects one (source, year, month) batch")

    # Drop the columns encoded in the partition path (source is the table,
    # year/month are the Hive partition keys) so the Parquet schema doesn't
    # collide with the Glue table's partition keys.
    df = pd.DataFrame([r.model_dump() for r in records])
    df = df[["city", "region", "category", "metric", "value", "unit"]]
    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow", index=False)
    buffer.seek(0)

    prefix = _partition_prefix(first.source, first.year, first.month)
    key = f"{prefix}/data.parquet"
    s3().put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())
    return f"s3://{bucket}/{key}"


def register_partition(source: str, year: int, month: int, location: str,
                       *, database: str | None = None) -> None:
    """Add the year/month partition to the Glue table so Athena can query it.

    No-op-safe: an AlreadyExistsException is swallowed so re-runs are idempotent.
    The table itself is created by Terraform (infra glue module, Phase 2 infra).
    """
    if database is None:
        config.require("glue_database_name")
        database = config.glue_database_name
    client = glue()
    partition_dir = location.rsplit("/", 1)[0] + "/"
    try:
        client.create_partition(
            DatabaseName=database,
            TableName=source,
            PartitionInput={
                "Values": [str(year), f"{month:02d}"],
                "StorageDescriptor": {"Location": partition_dir},
            },
        )
    except client.exceptions.AlreadyExistsException:
        pass
