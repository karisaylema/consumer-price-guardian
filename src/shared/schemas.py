"""
Shared data schemas.

PriceRecord defines the normalized shape both ingestion jobs (IPC, Canasta)
write to, regardless of INEC's month-to-month format quirks. Keeping this in
one place means the Athena queries in the SQL tool don't need to know which
release format a row originally came from.

Modeled with pydantic so validation happens at the ingestion boundary — the
place most exposed to INEC's shifting CSV/XLSX formats. A malformed month or
an unexpected source should fail loudly here, not silently land a bad row in
the data lake.
"""

from typing import Literal

from pydantic import BaseModel, Field

Source = Literal["ipc", "canasta_basica", "canasta_vital"]
Region = Literal["Sierra", "Costa", "Nacional"]


class PriceRecord(BaseModel):
    """One normalized price observation from an INEC release."""

    source: Source                         # which INEC dataset the row came from
    city: str                              # e.g. "Quito", "Guayaquil", or "Nacional"
    region: Region                         # "Sierra" | "Costa" | "Nacional"
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    category: str                          # IPC division/group, or basket name
    metric: str                            # e.g. "cost_usd", "monthly_variation_pct"
    value: float
    unit: str
