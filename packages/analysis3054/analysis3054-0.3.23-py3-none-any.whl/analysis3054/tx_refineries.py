"""Utilities for downloading Texas refinery statement data."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from difflib import SequenceMatcher
from urllib.parse import urljoin

import httpx
import pandas as pd

logger = logging.getLogger("TX_Refineries_Scraper")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

BASE_STATEMENT_URL = (
    "https://www.rrc.texas.gov/oil-and-gas/research-and-statistics/refinery-statements/"
)

TABLE_COLUMNS = [
    "Name of Material",
    "Code",
    "Storage Beginning of Month",
    "Receipts",
    "Input Runs to Stills and/or Blends",
    "Products Manufactured",
    "Fuel Used",
    "Deliveries",
    "Storage End of Month",
]

NUMERIC_COLUMNS = [col for col in TABLE_COLUMNS if col != "Name of Material"]

MATERIAL_REFERENCE = [
    (1, "Propane"),
    (2, "Butane"),
    (3, "Butane-Propane"),
    (4, "Motor Gasoline"),
    (5, "Kerosene"),
    (6, "Home Heating Oil"),
    (7, "Diesel Fuel"),
    (8, "Other Middle Distillates"),
    (9, "Aviation Gasoline"),
    (10, "Kerosene-Type Jet Fuel"),
    (11, "Naptha - Type Jet Fuel"),
    (12, "Fuel Oil #4 For Utility Use"),
    (13, "Fuel Oils #5, #6 For Utility Use"),
    (14, "Fuel Oil #4 For Utility Use"),
    (15, "Fuel Oil #5, #6 For Utility Use"),
    (16, "Bunker C"),
    (17, "Navy Special"),
    (18, "Other Residual Fuels"),
    (19, "Petrochemical Feedstocks"),
    (20, "Lubricants"),
    (21, "Petrochemical Feedstocks"),
    (22, "Solvent Products"),
    (23, "Miscellaneous"),
    (24, "Crude Oil"),
]

MATERIAL_CODE_MAP = {code: name for code, name in MATERIAL_REFERENCE}

HEADER_KEYWORDS = {
    "name",
    "material",
    "code",
    "edoc",
    "storage",
    "beginning",
    "month",
    "receipts",
    "input",
    "runs",
    "to",
    "stills",
    "and/or",
    "and",
    "blends",
    "products",
    "manufactured",
    "fuel",
    "used",
    "deliveries",
    "end",
    "of",
}

MONTH_NAME_TO_NUMBER = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

NUMBER_TO_MONTH_NAME = {value: key for key, value in MONTH_NAME_TO_NUMBER.items()}


class TXRefineryError(Exception):
    """Raised when the Texas refinery statement scraper fails."""


class TableParseError(TXRefineryError):
    """Raised when a refinery statement table cannot be parsed."""


@dataclass(frozen=True)
class RefineryStatementLink:
    facility_number: str
    operator_name: str
    pdf_url: str
    statement_year: int
    statement_month: int


def _build_statement_url(year: int, month: int) -> str:
    return (
        f"{BASE_STATEMENT_URL}refineries-statements-{year}/"
        f"refinery-statements-{month}-{year}/"
    )


def _iter_statement_months(
    start_year: int,
    end_year: int,
    end_month: int,
) -> Iterable[Tuple[int, int]]:
    for year in range(start_year, end_year + 1):
        month_start = 1
        month_end = end_month if year == end_year else 12
        for month in range(month_start, month_end + 1):
            yield year, month


def _parse_statement_period_from_name(name: str) -> Optional[Tuple[int, int]]:
    basename = Path(name).name.lower()
    month_match = re.search(
        r"(january|february|march|april|may|june|july|august|september|october|november|december)",
        basename,
    )
    year_match = re.search(r"(20\d{2})", basename)
    if not month_match or not year_match:
        return None
    month = MONTH_NAME_TO_NUMBER.get(month_match.group(1))
    year = int(year_match.group(1))
    if month is None:
        return None
    return year, month


def _normalize_facility_number(value: str) -> str:
    text = str(value or "").strip()
    match = re.search(r"(\d{1,2})-(\d{1,4})", text)
    if match:
        return f"{int(match.group(1)):02d}-{int(match.group(2)):04d}"
    return text


def _extract_facility_number_from_url(url: str) -> str:
    basename = Path(url).name
    match = re.search(r"(\d{1,2})-(\d{1,4})", basename)
    if match:
        return _normalize_facility_number(f"{match.group(1)}-{match.group(2)}")
    return ""


def _normalize_column_name(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(name)).strip().lower()
    if "name" in cleaned and "material" in cleaned:
        return "Name of Material"
    if "code" in cleaned:
        return "Code"
    if "storage" in cleaned and "begin" in cleaned:
        return "Storage Beginning of Month"
    if "receipts" in cleaned:
        return "Receipts"
    if "runs" in cleaned or "stills" in cleaned or "blends" in cleaned or "input" in cleaned:
        return "Input Runs to Stills and/or Blends"
    if "products" in cleaned or "manufactured" in cleaned:
        return "Products Manufactured"
    if "fuel" in cleaned and "used" in cleaned:
        return "Fuel Used"
    if "deliveries" in cleaned:
        return "Deliveries"
    if "storage" in cleaned and "end" in cleaned:
        return "Storage End of Month"
    return str(name).strip()


def _parse_numeric_value(value: str) -> float:
    if value is None:
        return 0.0
    text = str(value).strip()
    if text in {"", "-", "—"}:
        return 0.0
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]
    text = text.replace(",", "").replace(" ", "")
    if text.startswith("-"):
        negative = True
        text = text[1:]
    if text == "":
        return 0.0
    try:
        number = float(text)
    except ValueError:
        return 0.0
    return -number if negative else number


def _clean_material_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9#&/().\\-\\s]", " ", str(name))
    cleaned = re.sub(r"\\s+", " ", cleaned).strip()
    return cleaned


def _match_material_name(name: str) -> Optional[Tuple[int, str]]:
    candidate = _clean_material_name(name).lower()
    if not candidate:
        return None
    best_ratio = 0.0
    best_match: Optional[Tuple[int, str]] = None
    for code, material in MATERIAL_REFERENCE:
        ratio = SequenceMatcher(None, candidate, material.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = (code, material)
    if best_match and best_ratio >= 0.6:
        return best_match
    return None


def _normalize_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise TableParseError("Parsed table is empty.")
    df = df.rename(columns={col: _normalize_column_name(col) for col in df.columns})

    for col in TABLE_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df = df[TABLE_COLUMNS]
    df["Name of Material"] = df["Name of Material"].fillna("").astype(str).str.strip()
    df = df[df["Name of Material"].str.len() > 0].reset_index(drop=True)
    if df.empty:
        raise TableParseError("No material rows found after cleaning.")

    # Fix rows where Code and Storage Beginning were merged into a single cell.
    def split_code_storage(row: pd.Series) -> pd.Series:
        raw_code = row.get("Code", "")
        raw_storage = row.get("Storage Beginning of Month", "")
        if isinstance(raw_code, str):
            tokens = re.findall(r"[-()0-9,]+", raw_code)
            if len(tokens) >= 2 and (raw_storage in ("", None, "-", "—")):
                row["Code"] = tokens[0]
                row["Storage Beginning of Month"] = tokens[1]
        return row

    df = df.apply(split_code_storage, axis=1)

    df["Code"] = df["Code"].astype(str).str.strip()
    df["Code"] = df["Code"].replace({"": "0", "-": "0"})
    for col in NUMERIC_COLUMNS:
        df[col] = df[col].apply(_parse_numeric_value)
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0).astype("float64")

    df["Code"] = df["Code"].where(df["Code"].between(1, 30), 0.0)

    # Clean material names and restore canonical labels when possible.
    df["Name of Material"] = df["Name of Material"].apply(_clean_material_name)
    for idx, row in df.iterrows():
        code = int(row.get("Code", 0))
        if code in MATERIAL_CODE_MAP:
            df.at[idx, "Name of Material"] = MATERIAL_CODE_MAP[code]
            continue
        match = _match_material_name(row.get("Name of Material", ""))
        if match:
            df.at[idx, "Code"] = float(match[0])
            df.at[idx, "Name of Material"] = match[1]

    # If OCR failed to capture codes, fall back to row order for standard materials.
    if len(df) >= len(MATERIAL_REFERENCE):
        zero_ratio = (df["Code"] == 0).mean()
        if zero_ratio >= 0.5:
            for row_idx, (code, name) in enumerate(MATERIAL_REFERENCE):
                if row_idx >= len(df):
                    break
                if df.iloc[row_idx]["Code"] == 0:
                    df.at[row_idx, "Code"] = float(code)
                    if not df.at[row_idx, "Name of Material"]:
                        df.at[row_idx, "Name of Material"] = name
                    elif _match_material_name(df.at[row_idx, "Name of Material"]) is None:
                        df.at[row_idx, "Name of Material"] = name

    numeric_sum = df[NUMERIC_COLUMNS].sum(axis=1)
    df = df[(df["Code"] != 0) | (numeric_sum != 0)]
    if df["Code"].duplicated().any():
        df = (
            df.assign(_numeric_sum=numeric_sum)
            .sort_values("_numeric_sum", ascending=False)
            .drop_duplicates(subset=["Code"], keep="first")
            .drop(columns="_numeric_sum")
            .sort_index()
        )

    totals_df = df[df["Code"] == 0].copy()
    df = df[df["Code"] != 0].copy()

    base_df = pd.DataFrame(MATERIAL_REFERENCE, columns=["Code", "Name of Material"])
    base_df["Code"] = base_df["Code"].astype("float64")
    for col in NUMERIC_COLUMNS:
        if col not in base_df.columns:
            base_df[col] = 0.0

    df = (
        base_df.merge(df, on="Code", how="left", suffixes=("_base", ""))
        .assign(**{col: lambda x, c=col: x[c].fillna(0.0) for col in NUMERIC_COLUMNS})
    )
    if "Name of Material_base" in df.columns:
        df["Name of Material"] = df["Name of Material"].fillna(df["Name of Material_base"])
        df = df.drop(columns=["Name of Material_base"])
    base_numeric_cols = [f"{col}_base" for col in NUMERIC_COLUMNS if f"{col}_base" in df.columns]
    if base_numeric_cols:
        df = df.drop(columns=base_numeric_cols)

    if not totals_df.empty:
        df = pd.concat([df, totals_df], ignore_index=True)

    df = df[TABLE_COLUMNS]
    return df.reset_index(drop=True)


def _find_header_top(
    words: Sequence[Dict[str, float]],
    x_limit: Optional[float],
    top_tolerance: float,
) -> float:
    name_candidates = [
        w
        for w in words
        if str(w.get("text", "")).lower() == "name"
        and w.get("top", 0) > 50
        and (x_limit is None or w.get("x0", 0) < x_limit)
    ]
    for candidate in sorted(name_candidates, key=lambda w: w["top"]):
        if any(
            str(w.get("text", "")).lower().startswith("material")
            and abs(w.get("top", 0) - candidate["top"]) <= top_tolerance
            for w in words
        ):
            return candidate["top"]
    if name_candidates:
        return name_candidates[0]["top"]
    raise TableParseError("Unable to locate the table header.")


def _build_table_from_words(words: Sequence[Dict[str, float]]) -> pd.DataFrame:
    if not words:
        raise TableParseError("No words available for table extraction.")

    page_width = max(
        (w.get("x1", w.get("x0", 0)) for w in words),
        default=0,
    )
    page_height = max((w.get("bottom", w.get("top", 0)) for w in words), default=0)
    header_band = max(45.0, page_height * 0.06)
    x_limit = page_width * 0.25 if page_width else None
    top_tolerance = max(3.0, page_height * 0.01)
    header_top = _find_header_top(words, x_limit, top_tolerance)
    header_words = [
        w
        for w in words
        if header_top - header_band <= w.get("top", 0) <= header_top + header_band
        and str(w.get("text", "")).lower() in HEADER_KEYWORDS
    ]
    if not header_words:
        raise TableParseError("Header words could not be detected.")

    header_bottom = max(w["bottom"] for w in header_words)

    def lower_text(word: Dict[str, float]) -> str:
        return str(word.get("text", "")).lower()

    def min_x_contains(tokens: Sequence[str]) -> Optional[float]:
        xs = [w["x0"] for w in header_words if any(t in lower_text(w) for t in tokens)]
        return min(xs) if xs else None

    def min_x_exact(tokens: Sequence[str]) -> Optional[float]:
        xs = [w["x0"] for w in header_words if lower_text(w) in tokens]
        return min(xs) if xs else None

    def max_x_exact(tokens: Sequence[str]) -> Optional[float]:
        xs = [w["x0"] for w in header_words if lower_text(w) in tokens]
        return max(xs) if xs else None

    anchors = {
        "Name of Material": min_x_contains(["name", "material"]),
        "Code": min_x_exact(["code", "edoc"]),
        "Storage Beginning of Month": min_x_contains(["beginning"]),
        "Receipts": min_x_contains(["receipts"]),
        "Input Runs to Stills and/or Blends": min_x_contains(["input", "runs", "stills", "blends"]),
        "Products Manufactured": min_x_contains(["products", "manufactured"]),
        "Fuel Used": min_x_contains(["fuel", "used"]),
        "Deliveries": min_x_contains(["deliveries"]),
        "Storage End of Month": max_x_exact(["end", "month"]),
    }

    if anchors["Name of Material"] is None:
        raise TableParseError("Missing required table anchor for Name of Material.")

    if anchors["Code"] is None:
        left = anchors["Name of Material"]
        right = anchors.get("Storage Beginning of Month") or anchors.get("Receipts")
        if right is None:
            candidates = [
                value
                for key, value in anchors.items()
                if key not in {"Name of Material", "Code"} and value is not None
            ]
            right = min(candidates) if candidates else None
        if left is not None and right is not None:
            anchors["Code"] = (left + right) / 2
        else:
            raise TableParseError("Missing required table anchor for Code.")

    ordered_anchors = [(col, anchors[col]) for col in TABLE_COLUMNS if anchors[col] is not None]
    ordered_anchors.sort(key=lambda item: item[1])

    column_names = [col for col, _ in ordered_anchors]
    column_x = [x for _, x in ordered_anchors]

    data_words = [w for w in words if w.get("top", 0) > header_bottom + 2]
    data_words.sort(key=lambda w: (w.get("top", 0), w.get("x0", 0)))

    rows: List[List[Dict[str, float]]] = []
    current_row: List[Dict[str, float]] = []
    current_top: Optional[float] = None
    tolerance = 2.0

    for word in data_words:
        top = word.get("top", 0)
        if current_top is None or abs(top - current_top) <= tolerance:
            current_row.append(word)
            current_top = top if current_top is None else (current_top + top) / 2
        else:
            rows.append(current_row)
            current_row = [word]
            current_top = top
    if current_row:
        rows.append(current_row)

    table_rows: List[List[str]] = []
    for row in rows:
        cells = {name: [] for name in column_names}
        for word in row:
            idx = min(range(len(column_x)), key=lambda i: abs(word["x0"] - column_x[i]))
            cells[column_names[idx]].append(str(word.get("text", "")).strip())
        row_values = [" ".join(cells[name]).strip() for name in column_names]
        if any(row_values):
            table_rows.append(row_values)

    if not table_rows:
        raise TableParseError("No table rows found in parsed word data.")

    df = pd.DataFrame(table_rows, columns=column_names)
    return _normalize_table(df)


def _extract_table_from_pdfplumber(page) -> pd.DataFrame:
    table = page.extract_table(
        {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "intersection_tolerance": 5,
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 3,
            "min_words_vertical": 1,
            "min_words_horizontal": 1,
        }
    )
    if not table or len(table) < 2:
        raise TableParseError("No table detected using pdfplumber extraction.")
    df = pd.DataFrame(table[1:], columns=table[0])
    return _normalize_table(df)


def _extract_words_with_ocr(page, angle: int = 0) -> Sequence[Dict[str, float]]:
    try:
        import pytesseract
    except ImportError as exc:  # pragma: no cover - optional path
        raise TableParseError(
            "OCR fallback requested but pytesseract is not installed."
        ) from exc
    try:
        pytesseract.get_tesseract_version()
    except Exception as exc:  # pragma: no cover - optional path
        raise TableParseError(
            "OCR fallback requested but the tesseract binary is unavailable."
        ) from exc
    try:
        image = page.to_image(resolution=300).original
        if angle:
            image = image.rotate(angle, expand=True)
    except Exception as exc:  # pragma: no cover - optional path
        raise TableParseError("Unable to render PDF page for OCR.") from exc

    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    words: List[Dict[str, float]] = []
    for idx, text in enumerate(data.get("text", [])):
        if not str(text).strip():
            continue
        x = float(data["left"][idx])
        y = float(data["top"][idx])
        w = float(data["width"][idx])
        h = float(data["height"][idx])
        words.append(
            {
                "text": text,
                "x0": x,
                "x1": x + w,
                "top": y,
                "bottom": y + h,
            }
        )
    return words


def _extract_table_with_ocr(page) -> pd.DataFrame:
    last_error: Optional[Exception] = None
    for angle in (0, 90, 180, 270):
        try:
            words = _extract_words_with_ocr(page, angle=angle)
            return _build_table_from_words(words)
        except TableParseError as exc:
            last_error = exc
            continue
    if last_error is None:
        raise TableParseError("OCR fallback failed to extract any words.")
    raise last_error


def _extract_table_from_pdf_bytes(pdf_bytes: bytes, ocr_fallback: bool) -> pd.DataFrame:
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover - environment specific
        raise ImportError(
            "pdfplumber is required for TX_refineries. Install with `pip install pdfplumber`."
        ) from exc

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        if not pdf.pages:
            raise TableParseError("PDF has no pages.")
        page = pdf.pages[0]
        if not page.chars:
            if ocr_fallback:
                return _extract_table_with_ocr(page)
            raise TableParseError("PDF contains no extractable text.")

        words = page.extract_words()
        try:
            return _build_table_from_words(words)
        except TableParseError as exc:
            try:
                return _extract_table_from_pdfplumber(page)
            except TableParseError:
                if ocr_fallback:
                    return _extract_table_with_ocr(page)
                raise exc


def _extract_statement_links(
    html: str,
    page_url: str,
    statement_year: int,
    statement_month: int,
) -> List[RefineryStatementLink]:
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover - environment specific
        raise ImportError(
            "beautifulsoup4 is required for TX_refineries. Install with `pip install beautifulsoup4`."
        ) from exc

    soup = BeautifulSoup(html, "html.parser")
    table = None
    for candidate in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in candidate.find_all("th")]
        if any("Facility Number" in header for header in headers):
            table = candidate
            break
    if table is None:
        return []

    results: List[RefineryStatementLink] = []
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue
        facility_number = _normalize_facility_number(cells[0].get_text(strip=True))
        link = row.find("a", href=True)
        if link is None:
            continue
        pdf_url = urljoin(page_url, link["href"])
        facility_from_url = _extract_facility_number_from_url(pdf_url)
        if not facility_number:
            facility_number = facility_from_url
        elif facility_from_url and facility_from_url != facility_number:
            logger.debug(
                "Facility number mismatch for %s: page=%s url=%s",
                pdf_url,
                facility_number,
                facility_from_url,
            )
        if not facility_number:
            continue
        operator_name = cells[1].get_text(strip=True)
        results.append(
            RefineryStatementLink(
                facility_number=facility_number,
                operator_name=operator_name,
                pdf_url=pdf_url,
                statement_year=statement_year,
                statement_month=statement_month,
            )
        )
    return results


def _load_existing_data(
    existing_path: Optional[Path],
    refresh_years: int,
) -> Tuple[Optional[pd.DataFrame], set]:
    if existing_path is None or not existing_path.exists():
        return None, set()

    existing_df = pd.read_pickle(existing_path)
    if existing_df.empty:
        return existing_df, set()

    if isinstance(existing_df.index, pd.MultiIndex):
        existing_flat = existing_df.reset_index()
    else:
        existing_flat = existing_df.copy()

    if "row" in existing_flat.columns:
        existing_flat = existing_flat.drop(columns=["row"])

    if "facility_number" not in existing_flat.columns and "refinery_id" in existing_flat.columns:
        existing_flat = existing_flat.rename(columns={"refinery_id": "facility_number"})

    if "facility_number" not in existing_flat.columns:
        if "facility_number" in existing_flat.index.names:
            existing_flat = existing_flat.reset_index()
        else:
            raise TXRefineryError("Existing data missing facility_number index/column.")
    existing_flat["facility_number"] = (
        existing_flat["facility_number"].astype(str).str.strip().apply(_normalize_facility_number)
    )

    if "statement_year" not in existing_flat.columns or "statement_month" not in existing_flat.columns:
        if "statement_date" in existing_flat.columns:
            existing_flat["statement_date"] = pd.to_datetime(
                existing_flat["statement_date"], errors="coerce"
            )
            existing_flat["statement_year"] = existing_flat["statement_date"].dt.year
            existing_flat["statement_month"] = existing_flat["statement_date"].dt.month

    if "statement_year" in existing_flat.columns:
        existing_flat["statement_year"] = pd.to_numeric(
            existing_flat["statement_year"], errors="coerce"
        ).fillna(0).astype("int64")
    if "statement_month" in existing_flat.columns:
        existing_flat["statement_month"] = pd.to_numeric(
            existing_flat["statement_month"], errors="coerce"
        ).fillna(0).astype("int64")

    for col in TABLE_COLUMNS:
        if col not in existing_flat.columns:
            existing_flat[col] = 0

    for col in NUMERIC_COLUMNS:
        existing_flat[col] = pd.to_numeric(existing_flat[col], errors="coerce").fillna(0.0).astype(
            "float64"
        )

    if "statement_month_name" not in existing_flat.columns:
        existing_flat["statement_month_name"] = existing_flat["statement_month"].map(
            NUMBER_TO_MONTH_NAME
        ).fillna("")
    if "statement_date" not in existing_flat.columns:
        existing_flat["statement_date"] = pd.to_datetime(
            dict(
                year=existing_flat["statement_year"],
                month=existing_flat["statement_month"],
                day=1,
            ),
            errors="coerce",
        )

    expected_columns = set(
        TABLE_COLUMNS
        + [
            "facility_number",
            "statement_year",
            "statement_month",
            "statement_month_name",
            "statement_date",
        ]
    )
    existing_flat = existing_flat[[col for col in existing_flat.columns if col in expected_columns]]

    if refresh_years > 0 and "statement_year" in existing_flat.columns:
        max_year = existing_flat["statement_year"].max()
        if pd.notna(max_year):
            cutoff_year = int(max_year) - refresh_years + 1
            existing_flat = existing_flat[existing_flat["statement_year"] < cutoff_year]

    key_source = existing_flat.dropna(
        subset=["facility_number", "statement_year", "statement_month"]
    )
    existing_keys = set(
        zip(
            key_source["facility_number"],
            key_source["statement_year"],
            key_source["statement_month"],
        )
    )

    return existing_flat, existing_keys


def _assemble_multiindex(df: pd.DataFrame) -> pd.DataFrame:
    grouped = {}
    for facility, facility_df in df.groupby("facility_number", sort=True):
        facility_df = facility_df.sort_values(["statement_date", "Code"])
        facility_df = facility_df.set_index(["statement_date", "Code"], drop=False)
        grouped[facility] = facility_df.drop(columns=["facility_number"])
    return pd.concat(grouped, names=["facility_number", "statement_date", "Code"])


def _assemble_flat(df: pd.DataFrame) -> pd.DataFrame:
    flat = df.copy()
    flat["refinery_id"] = flat["facility_number"].astype(str)
    sort_cols = ["refinery_id", "statement_date", "Code"]
    flat = flat.sort_values(sort_cols)
    leading_cols = [
        "refinery_id",
        "facility_number",
        "statement_date",
        "statement_year",
        "statement_month",
        "statement_month_name",
    ] + TABLE_COLUMNS
    trailing_cols = [col for col in flat.columns if col not in leading_cols]
    return flat[leading_cols + trailing_cols].reset_index(drop=True)


async def _fetch_statement_links_for_month(
    client: httpx.AsyncClient,
    year: int,
    month: int,
    semaphore: asyncio.Semaphore,
) -> List[RefineryStatementLink]:
    url = _build_statement_url(year, month)
    async with semaphore:
        response = await client.get(url)
    if response.status_code != 200:
        return []
    return _extract_statement_links(response.text, url, year, month)


async def _download_and_parse_statement(
    client: httpx.AsyncClient,
    link: RefineryStatementLink,
    semaphore: asyncio.Semaphore,
    ocr_fallback: bool,
) -> Tuple[RefineryStatementLink, pd.DataFrame]:
    async with semaphore:
        response = await client.get(link.pdf_url)
    response.raise_for_status()
    table_df = await asyncio.to_thread(_extract_table_from_pdf_bytes, response.content, ocr_fallback)
    return link, table_df


async def fetch_tx_refineries_data(
    start_year: int = 2018,
    end_year: Optional[int] = None,
    end_month: Optional[int] = None,
    existing_path: Optional[Path] = None,
    load_existing: bool = True,
    refresh_years: int = 1,
    return_format: str = "flat",
    concurrency: int = 8,
    timeout: float = 60.0,
    ocr_fallback: bool = False,
    strict: bool = True,
) -> pd.DataFrame:
    if return_format not in {"flat", "multiindex"}:
        raise ValueError("return_format must be 'flat' or 'multiindex'.")
    now = datetime.utcnow()
    resolved_end_year = end_year or now.year
    resolved_end_month = end_month or now.month

    existing_flat, existing_keys = (None, set())
    if load_existing:
        existing_flat, existing_keys = _load_existing_data(existing_path, refresh_years)

    months = list(_iter_statement_months(start_year, resolved_end_year, resolved_end_month))
    if not months:
        return pd.DataFrame()

    limits = httpx.Limits(
        max_connections=concurrency * 2,
        max_keepalive_connections=concurrency,
    )
    timeout_config = httpx.Timeout(timeout)
    headers = {"User-Agent": "analysis3054/tx_refineries"}

    async with httpx.AsyncClient(
        timeout=timeout_config,
        limits=limits,
        headers=headers,
        follow_redirects=True,
    ) as client:
        sem = asyncio.Semaphore(concurrency)
        link_tasks = [
            _fetch_statement_links_for_month(client, year, month, sem)
            for year, month in months
        ]
        link_results = await asyncio.gather(*link_tasks, return_exceptions=True)

        all_links: List[RefineryStatementLink] = []
        for (year, month), result in zip(months, link_results):
            if isinstance(result, Exception):
                message = f"Failed to fetch statements for {month}-{year}: {result}"
                if strict:
                    raise TXRefineryError(message) from result
                logger.warning(message)
                continue
            all_links.extend(result)

        if not all_links:
            logger.warning("No refinery statement links found for the requested period.")
            return pd.DataFrame()

        unique_links = {}
        for link in all_links:
            key = (link.facility_number, link.statement_year, link.statement_month)
            if key in unique_links:
                continue
            unique_links[key] = link

        filtered_links = [
            link for key, link in unique_links.items() if key not in existing_keys
        ]

        if not filtered_links and existing_flat is not None:
            if return_format == "multiindex":
                return _assemble_multiindex(existing_flat)
            return _assemble_flat(existing_flat)

        pdf_sem = asyncio.Semaphore(max(1, concurrency // 2))
        tasks = [
            _download_and_parse_statement(client, link, pdf_sem, ocr_fallback)
            for link in filtered_links
        ]

        results: List[Tuple[RefineryStatementLink, pd.DataFrame]] = []
        errors: List[Tuple[RefineryStatementLink, Exception]] = []

        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        for link, result in zip(filtered_links, task_results):
            if isinstance(result, Exception):  # pragma: no cover - network dependent
                logger.warning("Failed to parse %s: %s", link.pdf_url, result)
                errors.append((link, result))
            else:
                results.append(result)

        if errors and strict:
            error_details = ", ".join(f"{link.pdf_url}: {err}" for link, err in errors[:5])
            raise TXRefineryError(f"{len(errors)} statement(s) failed. Sample: {error_details}")
        if errors and not strict and not ocr_fallback:
            logger.warning(
                "Some statements failed to parse; scanned PDFs may require OCR. "
                "Enable ocr_fallback=True and install pytesseract + tesseract to recover them."
            )

    new_frames: List[pd.DataFrame] = []
    for link, table_df in results:
        statement_period = _parse_statement_period_from_name(link.pdf_url)
        statement_year = link.statement_year
        statement_month = link.statement_month
        if statement_period and statement_period != (statement_year, statement_month):
            logger.info(
                "Statement period mismatch for %s, using page period %s-%s",
                link.pdf_url,
                statement_year,
                statement_month,
            )
        period_name = NUMBER_TO_MONTH_NAME.get(statement_month, "")
        table_df = table_df.copy()
        table_df["statement_year"] = statement_year
        table_df["statement_month"] = statement_month
        table_df["statement_month_name"] = period_name
        table_df["statement_date"] = pd.Timestamp(statement_year, statement_month, 1)
        table_df["facility_number"] = link.facility_number
        new_frames.append(table_df)

    if not new_frames and existing_flat is None:
        return pd.DataFrame()

    combined_frames = new_frames
    if existing_flat is not None and not existing_flat.empty:
        combined_frames.insert(0, existing_flat)

    combined = pd.concat(combined_frames, ignore_index=True)
    combined["facility_number"] = (
        combined["facility_number"].astype(str).str.strip().apply(_normalize_facility_number)
    )
    combined = combined.drop_duplicates(
        subset=[
            "facility_number",
            "statement_year",
            "statement_month",
            "Code",
            "Name of Material",
        ],
        keep="last",
    )

    combined["statement_year"] = pd.to_numeric(
        combined["statement_year"], errors="coerce"
    ).fillna(0).astype("int64")
    combined["statement_month"] = pd.to_numeric(
        combined["statement_month"], errors="coerce"
    ).fillna(0).astype("int64")

    for col in NUMERIC_COLUMNS:
        combined[col] = pd.to_numeric(combined[col], errors="coerce").fillna(0.0).astype("float64")

    sort_cols = ["facility_number", "statement_year", "statement_month", "Code"]
    combined = combined.sort_values(sort_cols)

    if return_format == "multiindex":
        return _assemble_multiindex(combined)
    return _assemble_flat(combined)


def TX_refineries(
    start_year: int = 2018,
    end_year: Optional[int] = None,
    end_month: Optional[int] = None,
    existing_path: Optional[str | Path] = None,
    load_existing: bool = True,
    refresh_years: int = 1,
    return_format: str = "flat",
    output_path: Optional[str | Path] = "tx_refineries.pkl",
    pickle_compression: Optional[str] = None,
    concurrency: int = 8,
    timeout: float = 60.0,
    ocr_fallback: bool = False,
    strict: bool = True,
) -> pd.DataFrame:
    """
    Scrape Texas RRC refinery statements and return a MultiIndex DataFrame.

    Args:
        start_year: First year to scan (default 2018).
        end_year: Optional end year (defaults to current year).
        end_month: Optional end month (defaults to current month).
        existing_path: Optional path to an existing pickle to load.
        load_existing: Whether to load and refresh existing data.
        refresh_years: Number of trailing years to re-fetch when loading existing data.
        return_format: "flat" for a single DataFrame or "multiindex" for facility grouping.
        output_path: Path to write the resulting pickle (set None to skip writing).
        pickle_compression: Optional compression for the pickle (e.g. "xz", "gzip").
        concurrency: Max concurrent HTTP requests.
        timeout: HTTP timeout in seconds.
        ocr_fallback: Enable OCR for scanned PDFs (requires pytesseract + pypdfium2).
        strict: If True, raise when any statement fails to parse.

    Returns:
        pd.DataFrame: Flat or MultiIndex DataFrame depending on return_format.
    """

    if return_format not in {"flat", "multiindex"}:
        raise ValueError("return_format must be 'flat' or 'multiindex'.")

    resolved_existing = Path(existing_path) if existing_path else None
    if resolved_existing is None and output_path:
        output_candidate = Path(output_path)
        if output_candidate.exists():
            resolved_existing = output_candidate

    try:
        df = asyncio.run(
            fetch_tx_refineries_data(
                start_year=start_year,
                end_year=end_year,
                end_month=end_month,
                existing_path=resolved_existing,
                load_existing=load_existing,
                refresh_years=refresh_years,
                return_format=return_format,
                concurrency=concurrency,
                timeout=timeout,
                ocr_fallback=ocr_fallback,
                strict=strict,
            )
        )
    except Exception as exc:
        logger.critical("Critical failure in TX_refineries: %s", exc)
        raise

    if output_path:
        output_target = Path(output_path)
        output_target.parent.mkdir(parents=True, exist_ok=True)
        df.to_pickle(output_target, compression=pickle_compression)

    return df


__all__ = [
    "TX_refineries",
    "TXRefineryError",
    "TableParseError",
    "fetch_tx_refineries_data",
]
