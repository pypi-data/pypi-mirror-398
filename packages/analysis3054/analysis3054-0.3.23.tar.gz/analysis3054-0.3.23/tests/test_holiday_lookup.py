import pandas as pd
from datetime import date

import analysis3054.holiday_lookup as holiday_lookup
from analysis3054.holiday_lookup import (
    get_market_code,
    is_financial_holiday,
    is_holiday,
    is_platts_holiday,
    resolve_iso_code,
)


def test_resolve_iso_code_handles_overrides_and_fuzzy():
    assert resolve_iso_code("Europe") == "EU"
    assert resolve_iso_code("united states") == "US"
    # Uses fuzzy search when manual overrides do not apply
    assert resolve_iso_code("Republic of Korea") in {"KR", "KP"}


def test_is_holiday_detects_windowed_matches():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-07-03", "2024-07-04", "2024-07-05"]),
            "country": ["US", "US", ["Canada", "United States"]],
        }
    )

    result = is_holiday(df, "date", "country", window=1, specific=True)

    assert list(result) == ["Independence Day", "Independence Day", "Independence Day"]


def test_is_holiday_returns_nan_when_country_unknown():
    df = pd.DataFrame({"date": pd.to_datetime(["2024-07-04"]), "country": ["Atlantis"]})

    result = is_holiday(df, "date", "country", window=1, specific=False)

    assert result.isna().all()


def test_is_financial_holiday_maps_country_to_market():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-03-15"]),
            "country": [["XNYS", "United States"], ["ICE", "United States"]],
        }
    )

    result = is_financial_holiday(df, "date", "country", include_half_days=True, specific=False)

    assert result.iloc[0] == "Yes"
    assert result.iloc[1] == "No"


def test_is_financial_holiday_handles_direct_mic_and_multiple_choices():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-07-04"]),
            "country": [["XNAS", "XNYS"]],
        }
    )

    result = is_financial_holiday(df, "date", "country", window=3, specific=True)

    assert result.iloc[0] == "Independence Day"


def test_financial_holiday_uses_window_and_specific():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-11-28", "2024-11-29"]),
            "country": ["US", "US"],
        }
    )

    result = is_financial_holiday(df, "date", "country", window=3, include_half_days=False, specific=True)

    assert result.iloc[0] == "Thanksgiving Day"
    assert result.iloc[1] in {"No", "Thanksgiving Day"}


def test_is_financial_holiday_handles_half_days(monkeypatch):
    class DummyFinancial(dict):
        def get(self, key):
            return super().get(key)

    dummy_calendar = DummyFinancial({date(2024, 1, 1): "Sample Half Day"})

    monkeypatch.setattr(
        "analysis3054.holiday_lookup.holidays.financial_holidays",
        lambda market, years=None: dummy_calendar,
    )

    df = pd.DataFrame({"date": pd.to_datetime(["2024-01-01"]), "country": ["US"]})

    result = is_financial_holiday(df, "date", "country", include_half_days=False)

    assert result.iloc[0] == "No"
    assert get_market_code("US") == "XNYS"


def test_is_financial_holiday_returns_nan_when_no_market():
    df = pd.DataFrame({"date": pd.to_datetime(["2024-01-01"]), "country": ["Atlantis"]})

    result = is_financial_holiday(df, "date", "country")

    assert result.isna().all()


def test_is_platts_holiday_returns_nan_when_download_empty(monkeypatch):
    monkeypatch.setattr(
        "analysis3054.holiday_lookup._download_and_parse_platts",
        lambda years_to_check=None: pd.DataFrame(columns=["Date", "Exchanges", "Holiday"]),
    )
    monkeypatch.setattr(holiday_lookup, "_PLATTS_CACHE", {})

    df = pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-01-02"])})

    result = is_platts_holiday(df, "date", refresh=True)

    assert result.isna().all()


def test_is_platts_holiday_matches_exchanges_and_window(monkeypatch):
    sample = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01", "2024-01-05"]),
            "Exchanges": ["CME", "ICE"],
            "Holiday": ["New Year", "Winter Break"],
        }
    )

    monkeypatch.setattr(
        "analysis3054.holiday_lookup._download_and_parse_platts",
        lambda years_to_check=None: sample,
    )
    monkeypatch.setattr(holiday_lookup, "_PLATTS_CACHE", {})

    df = pd.DataFrame({"date": pd.to_datetime(["2024-01-02", "2024-01-06"])})

    result = is_platts_holiday(df, "date", window=1, exchanges=["CME", "ICE"], refresh=True)

    assert list(result) == ["New Year", "Winter Break"]


def test_is_platts_holiday_returns_nan_for_missing_year(monkeypatch):
    sample = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01"]),
            "Exchanges": ["CME"],
            "Holiday": ["New Year"],
        }
    )

    monkeypatch.setattr(
        "analysis3054.holiday_lookup._download_and_parse_platts",
        lambda years_to_check=None: sample,
    )
    monkeypatch.setattr(holiday_lookup, "_PLATTS_CACHE", {})

    df = pd.DataFrame({"date": pd.to_datetime(["2030-01-01"])})

    result = is_platts_holiday(df, "date", window=0, exchanges=["CME"], refresh=True)

    assert result.isna().all()
