from pathlib import Path
from typing import List, Optional

import pandas as pd

from .normalize import normalize_text, normalize_unit

REQUIRED_BASE_COLUMNS = {"descripcion", "unidad", "precio_unitario"}
REQUIRED_PROJECT_COLUMNS = {"descripcion_proyecto", "unidad"}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [normalize_text(col).replace(" ", "_") for col in df.columns]
    return df


def read_price_base(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df = _normalize_columns(df)
    missing = REQUIRED_BASE_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing base columns: {sorted(missing)}")
    df["descripcion"] = df["descripcion"].fillna("")
    df["unidad"] = df["unidad"].fillna("")
    df["precio_unitario"] = pd.to_numeric(df["precio_unitario"], errors="coerce")
    df["descripcion_norm"] = df["descripcion"].apply(normalize_text)
    df["unidad_norm"] = df["unidad"].apply(normalize_unit)
    return df


def read_project_excel(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df = _normalize_columns(df)
    missing = REQUIRED_PROJECT_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing project columns: {sorted(missing)}")
    if "cantidad" not in df.columns:
        df["cantidad"] = 1.0
    df["descripcion_proyecto"] = df["descripcion_proyecto"].fillna("")
    df["unidad"] = df["unidad"].fillna("")
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").fillna(1.0)
    df["descripcion_norm"] = df["descripcion_proyecto"].apply(normalize_text)
    df["unidad_norm"] = df["unidad"].apply(normalize_unit)
    return df


def _rows_to_dataframe(rows: List[List[str]]) -> Optional[pd.DataFrame]:
    if not rows:
        return None
    max_len = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (max_len - len(row)) for row in rows]
    df = pd.DataFrame(normalized_rows)
    return df


def read_project_pdf(path: Path) -> pd.DataFrame:
    try:
        import pdfplumber  # type: ignore
    except ImportError as exc:
        raise ImportError("pdfplumber is required to read PDF files.") from exc

    tables: List[List[str]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            extracted_tables = page.extract_tables() or []
            for table in extracted_tables:
                for row in table:
                    cleaned = [cell or "" for cell in row]
                    tables.append(cleaned)

    df = _rows_to_dataframe(tables)
    if df is None:
        raise ValueError("No tables found in PDF. Consider OCR or a structured PDF.")

    df.columns = [f"col_{idx}" for idx in range(len(df.columns))]
    df["descripcion_proyecto"] = df["col_0"].astype(str)
    df["unidad"] = df.get("col_1", "").astype(str)
    df["cantidad"] = pd.to_numeric(df.get("col_2", 1), errors="coerce").fillna(1.0)
    df["descripcion_norm"] = df["descripcion_proyecto"].apply(normalize_text)
    df["unidad_norm"] = df["unidad"].apply(normalize_unit)
    return df[["descripcion_proyecto", "unidad", "cantidad", "descripcion_norm", "unidad_norm"]]


def read_project_file(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return read_project_excel(path)
    if path.suffix.lower() == ".pdf":
        return read_project_pdf(path)
    raise ValueError("Unsupported project file format. Use Excel or PDF.")
