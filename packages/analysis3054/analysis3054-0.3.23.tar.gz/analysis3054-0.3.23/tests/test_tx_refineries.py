from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

MODULE_PATH = Path(__file__).resolve().parents[1] / "analysis3054" / "tx_refineries.py"
spec = importlib.util.spec_from_file_location("tx_refineries", MODULE_PATH)
tx_refineries = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tx_refineries
spec.loader.exec_module(tx_refineries)


def test_build_statement_url():
    url = tx_refineries._build_statement_url(2025, 2)
    assert (
        url
        == "https://www.rrc.texas.gov/oil-and-gas/research-and-statistics/refinery-statements/"
        "refineries-statements-2025/refinery-statements-2-2025/"
    )


def test_iter_statement_months():
    months = list(tx_refineries._iter_statement_months(2024, 2025, 2))
    assert months[0] == (2024, 1)
    assert months[-1] == (2025, 2)
    assert (2024, 12) in months
    assert (2025, 1) in months


def test_parse_statement_period_from_name():
    parsed = tx_refineries._parse_statement_period_from_name(
        "https://www.rrc.texas.gov/media/wlskqq0o/2025-january-08-2869.pdf"
    )
    assert parsed == (2025, 1)


def test_extract_statement_links_from_html():
    html = """
    <table>
      <tr><th>Facility Number</th><th>Operator Name</th></tr>
      <tr><td>08-2869</td><td><a href="/media/test.pdf">ALON USA LP</a></td></tr>
    </table>
    """
    links = tx_refineries._extract_statement_links(
        html,
        "https://www.rrc.texas.gov/oil-and-gas/research-and-statistics/refinery-statements/refineries-statements-2025/refinery-statements-1-2025/",
        2025,
        1,
    )
    assert len(links) == 1
    assert links[0].facility_number == "08-2869"
    assert links[0].pdf_url == "https://www.rrc.texas.gov/media/test.pdf"


def test_build_table_from_words_basic():
    def word(text: str, x0: float, top: float) -> dict:
        return {"text": text, "x0": x0, "top": top, "bottom": top + 5}

    words = [
        word("Name", 50, 150),
        word("Material", 80, 150),
        word("Code", 200, 150),
        word("Storage", 240, 145),
        word("Beginning", 240, 155),
        word("Receipts", 320, 150),
        word("Input", 380, 145),
        word("Runs", 400, 155),
        word("Products", 460, 145),
        word("Manufactured", 460, 155),
        word("Fuel", 540, 150),
        word("Used", 540, 155),
        word("Deliveries", 600, 150),
        word("Storage", 670, 150),
        word("End", 700, 150),
        word("Month", 710, 150),
        word("Propane", 50, 185),
        word("1", 200, 185),
        word("10", 240, 185),
        word("20", 320, 185),
        word("30", 380, 185),
        word("40", 460, 185),
        word("50", 540, 185),
        word("60", 600, 185),
        word("70", 700, 185),
    ]

    df = tx_refineries._build_table_from_words(words)
    assert list(df.columns) == tx_refineries.TABLE_COLUMNS
    propane_row = df.loc[df["Code"] == 1.0].iloc[0]
    assert propane_row["Name of Material"] == "Propane"
    assert propane_row["Receipts"] == 20.0
    assert propane_row["Storage End of Month"] == 70.0
    assert str(df["Receipts"].dtype) == "float64"


def test_parse_numeric_value():
    assert tx_refineries._parse_numeric_value("1,234") == 1234.0
    assert tx_refineries._parse_numeric_value("(1,234)") == -1234.0
    assert tx_refineries._parse_numeric_value("- 450,948") == -450948.0
    assert tx_refineries._parse_numeric_value("-") == 0.0


def test_normalize_facility_number():
    assert tx_refineries._normalize_facility_number("4-161") == "04-0161"
    assert tx_refineries._normalize_facility_number("10-0026") == "10-0026"


def test_normalize_table_splits_code_storage():
    raw = pd.DataFrame(
        {
            "Name of Material": ["Propane"],
            "Code": ["1 1,181"],
            "Storage Beginning of Month": [""],
            "Receipts": [""],
            "Input Runs to Stills and/or Blends": [""],
            "Products Manufactured": [""],
            "Fuel Used": [""],
            "Deliveries": [""],
            "Storage End of Month": [""],
        }
    )
    normalized = tx_refineries._normalize_table(raw)
    propane_row = normalized.loc[normalized["Code"] == 1.0].iloc[0]
    assert propane_row["Storage Beginning of Month"] == 1181.0


def test_normalize_table_matches_materials():
    raw = pd.DataFrame(
        {
            "Name of Material": ["Propune"],
            "Code": ["0"],
            "Storage Beginning of Month": [""],
            "Receipts": [""],
            "Input Runs to Stills and/or Blends": [""],
            "Products Manufactured": [""],
            "Fuel Used": [""],
            "Deliveries": [""],
            "Storage End of Month": [""],
        }
    )
    normalized = tx_refineries._normalize_table(raw)
    propane_row = normalized.loc[normalized["Code"] == 1.0].iloc[0]
    assert propane_row["Name of Material"] == "Propane"


def test_normalize_table_row_order_codes():
    rows = []
    for _ in range(24):
        rows.append(
            {
                "Name of Material": "X",
                "Code": "0",
                "Storage Beginning of Month": "",
                "Receipts": "",
                "Input Runs to Stills and/or Blends": "",
                "Products Manufactured": "",
                "Fuel Used": "",
                "Deliveries": "",
                "Storage End of Month": "",
            }
        )
    raw = pd.DataFrame(rows)
    normalized = tx_refineries._normalize_table(raw)
    assert normalized.loc[normalized["Code"] == 1.0].shape[0] == 1
    assert normalized.loc[normalized["Code"] == 2.0].shape[0] == 1


def test_assemble_flat_adds_refinery_id():
    raw = pd.DataFrame(
        {
            "facility_number": ["04-0161", "04-0161"],
            "statement_date": pd.to_datetime(["2025-01-01", "2025-01-01"]),
            "statement_year": [2025, 2025],
            "statement_month": [1, 1],
            "statement_month_name": ["january", "january"],
            "Name of Material": ["Propane", "Butane"],
            "Code": [1.0, 2.0],
            "Storage Beginning of Month": [0.0, 0.0],
            "Receipts": [0.0, 0.0],
            "Input Runs to Stills and/or Blends": [0.0, 0.0],
            "Products Manufactured": [0.0, 0.0],
            "Fuel Used": [0.0, 0.0],
            "Deliveries": [0.0, 0.0],
            "Storage End of Month": [0.0, 0.0],
        }
    )
    flat = tx_refineries._assemble_flat(raw)
    assert "refinery_id" in flat.columns
    assert flat.loc[0, "refinery_id"] == "04-0161"
