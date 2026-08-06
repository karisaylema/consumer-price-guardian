"""Sanity tests for the shared PriceRecord schema.

These pass with no AWS access — they're here so CI has something real to run
from commit 1, and so future ingestion jobs have a schema contract to test
against.
"""

import pytest
from pydantic import ValidationError

from src.shared.schemas import PriceRecord


def test_price_record_construction():
    record = PriceRecord(
        source="canasta_basica",
        city="Quito",
        region="Sierra",
        year=2026,
        month=6,
        category="Canasta Familiar Básica",
        metric="cost_usd",
        value=552.16,
        unit="usd",
    )
    assert record.source == "canasta_basica"
    assert record.city == "Quito"
    assert record.value == 552.16


def test_price_record_national_aggregate():
    # Some IPC rows are national aggregates rather than city-specific
    record = PriceRecord(
        source="ipc",
        city="Nacional",
        region="Nacional",
        year=2026,
        month=6,
        category="Alimentos y Bebidas No Alcohólicas",
        metric="monthly_variation_pct",
        value=0.79,
        unit="pct",
    )
    assert record.city == "Nacional"
    assert record.value == 0.79


def test_price_record_rejects_bad_month():
    # Validation happens at the ingestion boundary — a month outside 1..12 is
    # exactly the kind of INEC-format glitch we want to fail loudly on.
    with pytest.raises(ValidationError):
        PriceRecord(
            source="ipc",
            city="Quito",
            region="Sierra",
            year=2026,
            month=13,
            category="Alimentos y Bebidas No Alcohólicas",
            metric="monthly_variation_pct",
            value=0.79,
            unit="pct",
        )


def test_price_record_rejects_unknown_source():
    with pytest.raises(ValidationError):
        PriceRecord(
            source="not_a_real_source",
            city="Quito",
            region="Sierra",
            year=2026,
            month=6,
            category="Alimentos y Bebidas No Alcohólicas",
            metric="monthly_variation_pct",
            value=0.79,
            unit="pct",
        )
