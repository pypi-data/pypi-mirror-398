import pandas as pd
import numpy as np

from analysis3054.forecast_engine import build_default_engine
from analysis3054.forecasting import forecast_distillate_burn
from analysis3054.ensembles import model_leaderboard, simple_ensemble


def test_forecast_engine_harmonic_runs():
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    df = pd.DataFrame({"date": dates, "value": np.sin(np.linspace(0, 2, 20))})
    engine = build_default_engine()
    res = engine.forecast(df, date_col="date", target_cols=["value"], horizon=4, model="harmonic")
    assert res.forecasts.shape[0] == 4
    assert "value" in res.forecasts.columns


def test_forecast_distillate_burn_baseline():
    dates = pd.date_range("2024-01-01", periods=6, freq="h")
    burn_df = pd.DataFrame({"date": dates, "burn": np.linspace(10, 12, len(dates))})
    load_future_dates = pd.date_range(dates[-1] + pd.Timedelta(hours=1), periods=3, freq="h")
    load_dates = pd.Index(dates).append(load_future_dates)
    load_df = pd.DataFrame({"date": load_dates, "load": np.linspace(100, 115, len(load_dates))})
    result = forecast_distillate_burn(burn_df, load_df, method="baseline", horizon=3)
    assert result.forecasts.shape[0] == 3
    assert result.method == "baseline"


def test_leaderboard_and_ensemble():
    idx = pd.date_range("2024-01-01", periods=3, freq="D")
    actual = pd.DataFrame({"y": [1.0, 2.0, 3.0]}, index=idx)
    forecasts = {
        "model_a": pd.DataFrame({"y": [1.1, 1.9, 3.1]}, index=idx),
        "model_b": pd.DataFrame({"y": [0.9, 2.1, 2.9]}, index=idx),
    }
    leaderboard = model_leaderboard(actual, forecasts)
    assert not leaderboard.empty
    ensemble = simple_ensemble(forecasts)
    assert ensemble.shape == actual.shape
