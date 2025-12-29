import pandas as pd
import pytest

from analysis3054.holiday_calendars import (
    available_holiday_calendars,
    get_holidays,
    get_holidays_between,
)


def test_available_holiday_calendars_lists_expected_options():
    calendars = available_holiday_calendars()
    assert {"us_federal", "cme", "ice", "ice_europe", "platts_us"}.issubset(calendars.keys())
    assert all(isinstance(desc, str) and desc for desc in calendars.values())


def test_get_holidays_single_calendar_returns_sorted_index():
    holidays = get_holidays(2024, calendars="us_federal")
    assert isinstance(holidays, pd.DatetimeIndex)
    assert list(holidays) == sorted(holidays.tolist())
    # Federal holidays include Thanksgiving but not Good Friday
    assert pd.Timestamp("2024-11-28") in holidays
    assert pd.Timestamp("2024-03-29") not in holidays


def test_get_holidays_combines_multiple_calendars_and_maps_membership():
    holiday_map = get_holidays([2024], calendars=["cme", "us_federal"], return_map=True)
    assert isinstance(holiday_map, pd.DataFrame)
    assert set(holiday_map.columns) == {"cme", "us_federal"}

    # Good Friday is a CME/ICE holiday but not a U.S. federal holiday
    assert bool(holiday_map.loc[pd.Timestamp("2024-03-29"), "cme"])
    assert not bool(holiday_map.loc[pd.Timestamp("2024-03-29"), "us_federal"])

    # Veterans Day is federal but not a CME holiday
    assert bool(holiday_map.loc[pd.Timestamp("2024-11-11"), "us_federal"])
    assert not bool(holiday_map.loc[pd.Timestamp("2024-11-11"), "cme"])

    # Combined index should include the union of both calendars
    assert pd.Timestamp("2024-01-01") in holiday_map.index
    assert pd.Timestamp("2024-12-25") in holiday_map.index


def test_ice_europe_calendar_includes_bank_holidays_and_observance():
    holidays = get_holidays([2024, 2025], calendars="ice_europe")

    # Standard UK-style bank holidays
    assert pd.Timestamp("2024-05-06") in holidays  # Early May bank holiday
    assert pd.Timestamp("2024-05-27") in holidays  # Spring bank holiday
    assert pd.Timestamp("2024-08-26") in holidays  # Summer bank holiday

    # Weekend Christmas/Boxing Day shift forward
    holidays_2021 = get_holidays(2021, calendars="ice_europe")
    assert pd.Timestamp("2021-12-27") in holidays_2021  # Christmas on Saturday observed Monday
    assert pd.Timestamp("2021-12-28") in holidays_2021  # Boxing Day on Sunday observed Tuesday

    # Sunday holidays should observe on Monday when free (e.g., New Year's Day 2023)
    holidays_2023 = get_holidays(2023, calendars="ice_europe")
    assert pd.Timestamp("2023-01-02") in holidays_2023
    assert pd.Timestamp("2023-01-03") not in holidays_2023


def test_unknown_calendar_raises_key_error():
    with pytest.raises(KeyError):
        get_holidays(2024, calendars="unknown_calendar")


def test_get_holidays_handles_past_and_future_years():
    holidays = get_holidays([1950, 2050], calendars="cme")

    # Independence Day 1950 (Tuesday) and Christmas Day 2050 (Saturday observed Monday)
    assert pd.Timestamp("1950-07-04") in holidays
    assert pd.Timestamp("2050-12-26") in holidays


def test_get_holidays_between_supports_date_ranges_and_membership():
    holiday_map = get_holidays_between(
        "2023-11-01", "2025-02-01", calendars=["platts_us", "us_federal"], return_map=True
    )

    assert isinstance(holiday_map, pd.DataFrame)
    assert set(holiday_map.columns) == {"platts_us", "us_federal"}

    # Thanksgiving 2024 and Good Friday 2024 fall inside the window
    assert pd.Timestamp("2024-11-28") in holiday_map.index
    assert pd.Timestamp("2024-03-29") in holiday_map.index
    assert holiday_map.loc[pd.Timestamp("2024-03-29"), "platts_us"]
    assert not holiday_map.loc[pd.Timestamp("2024-03-29"), "us_federal"]
