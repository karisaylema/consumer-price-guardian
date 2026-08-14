"""Unit tests for the INEC normalization layer.

These run offline (no AWS) and are the real safety net for the transformation
logic — the part most exposed to INEC's shifting release formats. Fixtures use
synthetic frames that mimic the format variants seen across months: accented vs
plain headers, numeric vs Spanish-name months, comma decimals, CSV vs XLSX.
"""

import io

import pandas as pd
import pytest

from src.ingestion.normalize import (
    infer_region,
    normalize_canasta,
    normalize_ipc,
    parse_month,
    read_raw,
    resolve_columns,
    validate,
)

# --------------------------------------------------------------------------- #
# Helpers / low-level
# --------------------------------------------------------------------------- #

def test_canon_resolves_accented_and_spaced_headers():
    df = pd.DataFrame(columns=["Ciudad", "Año", "Variación Mensual (%)"])
    cols = resolve_columns(df)
    assert cols["city"] == "Ciudad"
    assert cols["year"] == "Año"
    # "Variación Mensual (%)" is a value column, not in the canonical field map
    assert "category" not in cols


@pytest.mark.parametrize("value,expected", [
    (6, 6), ("6", 6), ("Junio", 6), ("junio", 6), ("DICIEMBRE", 12),
])
def test_parse_month_variants(value, expected):
    assert parse_month(value) == expected


@pytest.mark.parametrize("bad", [0, 13, "Smarch", "abc"])
def test_parse_month_rejects_bad(bad):
    with pytest.raises(ValueError):
        parse_month(bad)


@pytest.mark.parametrize("city,region", [
    ("Quito", "Sierra"), ("Guayaquil", "Costa"), ("Nacional", "Nacional"),
    ("Cuenca", "Sierra"), ("Manta", "Costa"), ("Unknownville", "Nacional"),
])
def test_infer_region(city, region):
    assert infer_region(city) == region


# --------------------------------------------------------------------------- #
# IPC
# --------------------------------------------------------------------------- #

def test_normalize_ipc_melts_metrics_and_infers_region():
    df = pd.DataFrame({
        "Ciudad": ["Quito", "Guayaquil"],
        "Año": [2026, 2026],
        "Mes": ["Junio", "Junio"],
        "Division": ["Alimentos y Bebidas No Alcohólicas", "Transporte"],
        "Indice": [112.5, 108.2],
        "Variación Mensual (%)": ["0,79", "-0,12"],
    })
    records = normalize_ipc(df)
    # 2 rows x 2 value columns = 4 records
    assert len(records) == 4

    quito_var = next(r for r in records
                     if r.city == "Quito" and r.metric == "monthly_variation_pct")
    assert quito_var.region == "Sierra"
    assert quito_var.value == pytest.approx(0.79)  # comma decimal parsed
    assert quito_var.unit == "pct"

    gye_index = next(r for r in records
                     if r.city == "Guayaquil" and r.metric == "index")
    assert gye_index.region == "Costa"
    assert gye_index.value == pytest.approx(108.2)
    assert gye_index.category == "Transporte"


def test_normalize_ipc_uses_period_column_when_no_year_month():
    df = pd.DataFrame({
        "Ciudad": ["Nacional"],
        "Periodo": ["Junio 2026"],
        "Grupo": ["Pan y Cereales"],
        "Variacion Anual": [3.4],
    })
    records = normalize_ipc(df)
    assert len(records) == 1
    r = records[0]
    assert (r.year, r.month) == (2026, 6)
    assert r.metric == "annual_variation_pct"


def test_normalize_ipc_uses_default_year_month_when_columns_absent():
    df = pd.DataFrame({
        "Descripcion": ["IPC General"],
        "Indice": [110.0],
    })
    records = normalize_ipc(df, year=2026, month=6)
    assert records[0].city == "Nacional"
    assert (records[0].year, records[0].month) == (2026, 6)


def test_normalize_ipc_skips_blank_values_but_keeps_others():
    df = pd.DataFrame({
        "Ciudad": ["Quito"],
        "Año": [2026], "Mes": [6],
        "Division": ["Salud"],
        "Indice": [None],                 # blank -> skipped
        "Variacion Mensual": [0.5],       # kept
    })
    records = normalize_ipc(df)
    assert len(records) == 1
    assert records[0].metric == "monthly_variation_pct"


def test_normalize_ipc_raises_without_value_columns():
    df = pd.DataFrame({"Ciudad": ["Quito"], "Año": [2026], "Mes": [6]})
    with pytest.raises(ValueError, match="No recognized value columns"):
        normalize_ipc(df)


# --------------------------------------------------------------------------- #
# Canasta
# --------------------------------------------------------------------------- #

def test_normalize_canasta_sets_basket_category():
    df = pd.DataFrame({
        "Ciudad": ["Quito", "Guayaquil"],
        "Año": [2026, 2026], "Mes": [6, 6],
        "Costo": ["764,71", "760,05"],
        "Ingreso Familiar": [830.0, 830.0],
    })
    records = normalize_canasta(df, kind="canasta_basica")
    costs = [r for r in records if r.metric == "cost_usd"]
    assert all(r.category == "Canasta Familiar Básica" for r in costs)
    assert all(r.source == "canasta_basica" for r in records)
    quito_cost = next(r for r in costs if r.city == "Quito")
    assert quito_cost.value == pytest.approx(764.71)


def test_normalize_canasta_rejects_unknown_kind():
    df = pd.DataFrame({"Ciudad": ["Quito"], "Año": [2026], "Mes": [6], "Costo": [700]})
    with pytest.raises(ValueError, match="Unknown canasta kind"):
        normalize_canasta(df, kind="canasta_de_pan")


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

def test_validate_passes_good_batch():
    df = pd.DataFrame({
        "Ciudad": ["Quito"], "Año": [2026], "Mes": [6],
        "Costo": [764.71],
    })
    records = normalize_canasta(df)
    assert validate(records) is records


def test_validate_rejects_implausible_percentage():
    df = pd.DataFrame({
        "Ciudad": ["Quito"], "Año": [2026], "Mes": [6],
        "Variacion Mensual": [9999],
    })
    records = normalize_ipc(df)
    with pytest.raises(ValueError, match="Implausible percentage"):
        validate(records)


def test_validate_rejects_empty_batch():
    with pytest.raises(ValueError):
        validate([])


# --------------------------------------------------------------------------- #
# read_raw format handling
# --------------------------------------------------------------------------- #

def test_read_raw_csv_semicolon_separated():
    csv = "Ciudad;Año;Mes;Indice\nQuito;2026;6;112,5\n"
    df = read_raw(io.StringIO(csv), fmt="csv")
    assert list(df.columns) == ["Ciudad", "Año", "Mes", "Indice"]
    assert df.iloc[0]["Ciudad"] == "Quito"


def test_read_raw_xlsx_roundtrip(tmp_path):
    src = pd.DataFrame({"Ciudad": ["Quito"], "Año": [2026], "Mes": [6], "Costo": [764.71]})
    path = tmp_path / "canasta.xlsx"
    src.to_excel(path, index=False)
    df = read_raw(path)  # fmt inferred from .xlsx extension
    records = validate(normalize_canasta(df))
    assert records[0].value == pytest.approx(764.71)


def test_read_raw_rejects_unknown_format():
    with pytest.raises(ValueError, match="Unsupported release format"):
        read_raw(io.BytesIO(b""), fmt="parquet")
