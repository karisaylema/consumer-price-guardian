"""
Defensive normalization of INEC releases into the shared PriceRecord shape.

This module is deliberately free of any AWS or Glue imports so it can be unit
tested locally against fixture files — the transformation logic is where the
real risk lives (INEC's formats shift month to month), so it's the part that
most needs fast, offline tests.

Design:
  - `read_raw` handles the CSV / XLS / XLSX format mix INEC publishes in.
  - `resolve_columns` maps whatever headers a given release happens to use to
    our canonical field names, via alias sets. When INEC renames a column, you
    add an alias here rather than touching the job logic.
  - `normalize_ipc` / `normalize_canasta` melt each source's wide layout into
    long-form PriceRecord rows (one row per metric).
  - `validate` enforces a known-good contract *before* anything is written, so
    a malformed release fails loudly in the ETL instead of silently landing bad
    rows in the data lake.

The alias maps below encode the column names seen in INEC releases to date.
They are intentionally the one place you tune when a new release format shows
up — see docs/roadmap.md Phase 2.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import IO

import pandas as pd

from src.shared.schemas import PriceRecord

# --------------------------------------------------------------------------- #
# Reference data
# --------------------------------------------------------------------------- #

SPANISH_MONTHS: dict[str, int] = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

# INEC publishes the IPC/Canasta for a fixed set of self-representing cities.
# Region (Sierra/Costa) isn't always a column, so we infer it from the city.
CITY_REGION: dict[str, str] = {
    "quito": "Sierra", "cuenca": "Sierra", "ambato": "Sierra", "loja": "Sierra",
    "riobamba": "Sierra", "latacunga": "Sierra",
    "guayaquil": "Costa", "machala": "Costa", "manta": "Costa",
    "esmeraldas": "Costa", "santo domingo": "Costa", "quevedo": "Costa",
    "nacional": "Nacional",
}

# Canonical field -> the header variants seen for it. Compared after _canon().
_ALIASES: dict[str, set[str]] = {
    "city": {"ciudad", "ciudades", "dominio", "ciudad_dominio", "city"},
    "region": {"region", "zona"},
    "year": {"anio", "ano", "year", "periodo_anio", "gestion"},
    # month may arrive as a number, a Spanish name, or inside a "periodo" cell
    "month": {"mes", "month", "periodo_mes"},
    "period": {"periodo", "fecha", "period"},
    "category": {
        "division", "grupo", "clase", "subclase", "producto", "articulo",
        "descripcion", "nombre", "categoria", "agrupacion",
    },
}

# Value columns are matched separately: each maps to the PriceRecord "metric"
# it represents. A single wide row can yield several PriceRecords.
_METRIC_COLUMNS: dict[str, tuple[str, str]] = {
    # canon(header): (metric, unit)
    "indice": ("index", "index_points"),
    "indice_ipc": ("index", "index_points"),
    "variacion_mensual": ("monthly_variation_pct", "pct"),
    "variacion_mensual_pct": ("monthly_variation_pct", "pct"),
    "variacion_anual": ("annual_variation_pct", "pct"),
    "variacion_acumulada": ("ytd_variation_pct", "pct"),
    "costo": ("cost_usd", "usd"),
    "costo_usd": ("cost_usd", "usd"),
    "costo_canasta": ("cost_usd", "usd"),
    "ingreso_familiar": ("family_income_usd", "usd"),
    "restriccion": ("restriction_usd", "usd"),
    "recuperacion": ("recovery_pct", "pct"),
}


# --------------------------------------------------------------------------- #
# Low-level helpers
# --------------------------------------------------------------------------- #

def _canon(text: object) -> str:
    """Normalize a header or token: strip accents, lowercase, collapse spaces.

    "Variación Mensual (%)" -> "variacion_mensual". This is what lets the alias
    sets stay small — every reasonable spelling collapses to one key.
    """
    s = str(text).strip().lower()
    s = "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )
    # drop anything that isn't alphanumeric, turn runs of separators into "_"
    out, prev_sep = [], False
    for c in s:
        if c.isalnum():
            out.append(c)
            prev_sep = False
        else:
            if not prev_sep:
                out.append("_")
            prev_sep = True
    return "".join(out).strip("_")


def read_raw(source: str | Path | IO[bytes], fmt: str | None = None) -> pd.DataFrame:
    """Read a raw INEC release into a DataFrame, format-agnostically.

    `fmt` is inferred from the extension when a path is given; pass it
    explicitly for file-like objects. Handles the .csv / .xls / .xlsx mix.
    """
    if fmt is None:
        suffix = Path(str(source)).suffix.lower().lstrip(".")
        fmt = suffix or "csv"
    fmt = fmt.lower()

    if fmt == "csv":
        # INEC CSVs have been seen with both ',' and ';' separators; sniff.
        return pd.read_csv(source, sep=None, engine="python")
    if fmt == "xlsx":
        return pd.read_excel(source, engine="openpyxl")
    if fmt == "xls":
        return pd.read_excel(source, engine="xlrd")
    raise ValueError(f"Unsupported release format: {fmt!r}")


def resolve_columns(df: pd.DataFrame) -> dict[str, str]:
    """Map canonical field names to the actual column present in this release.

    Returns only the canonical fields that were found. Missing ones are handled
    by the caller (e.g. region is inferred, month may come from `period`).
    """
    canon_to_actual = {_canon(col): col for col in df.columns}
    resolved: dict[str, str] = {}
    for field, aliases in _ALIASES.items():
        for alias in aliases:
            if alias in canon_to_actual:
                resolved[field] = canon_to_actual[alias]
                break
    return resolved


def _metric_columns(df: pd.DataFrame) -> dict[str, tuple[str, str]]:
    """Return {actual_column: (metric, unit)} for every value column present."""
    found: dict[str, tuple[str, str]] = {}
    for col in df.columns:
        spec = _METRIC_COLUMNS.get(_canon(col))
        if spec is not None:
            found[col] = spec
    return found


def parse_month(value: object) -> int:
    """Parse a month from an int, numeric string, or Spanish month name."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        m = int(value)
    else:
        token = _canon(value)
        if token in SPANISH_MONTHS:
            m = SPANISH_MONTHS[token]
        elif token.isdigit():
            m = int(token)
        else:
            raise ValueError(f"Unrecognized month: {value!r}")
    if not 1 <= m <= 12:
        raise ValueError(f"Month out of range: {value!r}")
    return m


def _parse_period(value: object) -> tuple[int, int]:
    """Extract (year, month) from a free-form period cell.

    Handles "2026-06", "2026/6", "Junio 2026", "junio-2026".
    """
    token = _canon(value)  # e.g. "junio_2026" or "2026_06"
    parts = [p for p in token.split("_") if p]
    year = month = None
    for p in parts:
        if p.isdigit() and len(p) == 4:
            year = int(p)
        elif p in SPANISH_MONTHS:
            month = SPANISH_MONTHS[p]
        elif p.isdigit() and month is None:
            month = int(p)
    if year is None or month is None:
        raise ValueError(f"Cannot parse period: {value!r}")
    if not 1 <= month <= 12:
        raise ValueError(f"Month out of range in period: {value!r}")
    return year, month


def infer_region(city: str) -> str:
    """Infer Sierra/Costa/Nacional from the city name; default to Nacional."""
    return CITY_REGION.get(_canon(city).replace("_", " "), "Nacional")


def _coerce_float(value: object) -> float | None:
    """Coerce an INEC numeric cell to float, tolerating ',' decimals and blanks."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    if s == "" or s.lower() in {"nan", "n/d", "s/d", "-"}:
        return None
    s = s.replace("%", "").strip()
    # If it looks like "1.234,56" treat '.' as thousands and ',' as decimal.
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Per-source normalization
# --------------------------------------------------------------------------- #

def _row_period(row: pd.Series, cols: dict[str, str],
                default_year: int | None, default_month: int | None) -> tuple[int, int]:
    """Resolve (year, month) for a row from explicit columns, a period cell,
    or the job-level defaults, in that order of preference."""
    if "year" in cols and "month" in cols:
        return int(row[cols["year"]]), parse_month(row[cols["month"]])
    if "period" in cols:
        return _parse_period(row[cols["period"]])
    if default_year is not None and default_month is not None:
        return default_year, default_month
    raise ValueError("Row has no year/month and no defaults were provided")


def _normalize(df: pd.DataFrame, source: str, *,
               default_year: int | None, default_month: int | None,
               fixed_category: str | None) -> list[PriceRecord]:
    """Shared melt: for each row, emit one PriceRecord per value column found."""
    cols = resolve_columns(df)
    metric_cols = _metric_columns(df)
    if not metric_cols:
        raise ValueError(
            f"No recognized value columns in {source} release; "
            f"headers were: {list(df.columns)}"
        )

    records: list[PriceRecord] = []
    for _, row in df.iterrows():
        year, month = _row_period(row, cols, default_year, default_month)
        city = str(row[cols["city"]]) if "city" in cols else "Nacional"
        region = str(row[cols["region"]]) if "region" in cols else infer_region(city)
        category = (
            fixed_category
            if fixed_category is not None
            else str(row[cols["category"]]) if "category" in cols else source
        )
        for col, (metric, unit) in metric_cols.items():
            value = _coerce_float(row[col])
            if value is None:
                continue  # skip blanks rather than inventing a 0
            records.append(PriceRecord(
                source=source, city=city.strip(), region=region.strip(),
                year=year, month=month, category=category.strip(),
                metric=metric, value=value, unit=unit,
            ))
    return records


def normalize_ipc(df: pd.DataFrame, *, year: int | None = None,
                  month: int | None = None) -> list[PriceRecord]:
    """Normalize an IPC release. Category comes from the INEC hierarchy column."""
    return _normalize(df, "ipc", default_year=year, default_month=month,
                      fixed_category=None)


def normalize_canasta(df: pd.DataFrame, *, kind: str = "canasta_basica",
                      year: int | None = None,
                      month: int | None = None) -> list[PriceRecord]:
    """Normalize a Canasta Familiar release.

    `kind` is "canasta_basica" or "canasta_vital"; the category is the basket
    name (there is no product hierarchy for the basket total).
    """
    if kind not in ("canasta_basica", "canasta_vital"):
        raise ValueError(f"Unknown canasta kind: {kind!r}")
    label = "Canasta Familiar Básica" if kind == "canasta_basica" else "Canasta Familiar Vital"
    return _normalize(df, kind, default_year=year, default_month=month,
                      fixed_category=label)


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

def validate(records: list[PriceRecord], *, min_rows: int = 1) -> list[PriceRecord]:
    """Assert a batch of normalized records meets the known-good contract.

    Raises ValueError on anything that shouldn't reach the data lake. This is
    the "validate against a known-good sample" gate from the roadmap: cheap,
    and it turns a silent bad-release into a loud job failure.
    """
    if len(records) < min_rows:
        raise ValueError(f"Expected at least {min_rows} record(s), got {len(records)}")
    for r in records:
        # PriceRecord (pydantic) already validated types/ranges on construction;
        # here we check cross-field/data-quality invariants.
        if r.unit == "pct" and abs(r.value) > 1000:
            raise ValueError(f"Implausible percentage {r.value} in {r!r}")
        if r.unit == "usd" and r.value < 0:
            raise ValueError(f"Negative USD value in {r!r}")
        if not r.city:
            raise ValueError(f"Empty city in {r!r}")
    return records
