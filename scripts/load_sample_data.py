"""
Load a small sample of INEC IPC / Canasta data into the raw S3 bucket for local
testing, so you can exercise the ingestion + query path without hitting
ecuadorencifras.gob.ec directly.

Planned flow:
  1. Read the configured raw-data bucket from src.shared.config
  2. Upload the bundled sample files (a CSV and an XLSX release, mirroring
     INEC's real format mix) under s3://<raw-bucket>/ipc/ and /canasta/
  3. Print the object keys so you can point an ETL run at them

Usage:
    python scripts/load_sample_data.py

Not yet implemented — see docs/roadmap.md Phase 2.
"""

from src.shared.config import config


def main() -> None:
    config.require("raw_data_bucket")
    raise NotImplementedError("See docs/roadmap.md Phase 2")


if __name__ == "__main__":
    main()
