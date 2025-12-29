import numpy as np
import pandas as pd
import pytest

sklearn = pytest.importorskip("sklearn")

from analysis3054.auto_ml_forecasting import (
    auto_generate_features,
    _future_index,
    _split_features_targets,
    FeatureEngineeringResult,
    bayesian_ridge_covariate_forecast,
    fourier_ridge_seasonal_forecast,
    hist_gradient_direct_forecast,
    gradient_boosting_covariate_forecast,
    huber_covariate_forecast,
    ridge_covariate_forecast,
)


def _build_weekly_data(n: int = 24) -> pd.DataFrame:
    dates = pd.date_range("2024-01-07", periods=n, freq="W-SUN")
    df = pd.DataFrame(
        {
            "date": dates,
            "load": [50 + i * 0.5 for i in range(n)],
            "temp": [20 + (i % 5) for i in range(n)],
        }
    )
    return df


def test_future_index_infers_weekly_frequency():
    df = _build_weekly_data(6)
    idx = _future_index(df["date"], periods=3, freq=None)
    assert len(idx) == 3
    assert pd.infer_freq(idx) == "W-SUN"


def test_feature_builder_excludes_custom_date_column():
    df = _build_weekly_data(15).rename(columns={"date": "timestamp"})
    X, _ = _split_features_targets(
        df[["timestamp", "load", "temp"]],
        date_col="timestamp",
        target_col="load",
        lags=3,
        covariate_cols=["temp"],
    )
    assert "timestamp" not in X.columns
    assert X.select_dtypes(exclude=[np.number]).empty


def test_auto_feature_generation_builds_expected_signals():
    df = _build_weekly_data(20)
    result = auto_generate_features(
        df=df,
        date_col="date",
        target_col="load",
        lags=3,
        rolling_windows=(2, 4),
        fourier_order=1,
    )
    assert isinstance(result, FeatureEngineeringResult)
    assert result.metadata["frequency"] == "W-SUN"
    assert {"lag_1", "lag_2", "lag_3"}.issubset(result.features.columns)
    assert {"roll_mean_2", "roll_mean_4", "dayofweek", "fourier_sin_1", "fourier_cos_1"}.issubset(
        result.features.columns
    )
    assert len(result.features) == len(result.target) > 0


def test_future_index_honours_explicit_frequency():
    df = _build_weekly_data(4)
    idx = _future_index(df["date"], periods=2, freq="D")
    assert idx.freqstr == "D"
    assert idx[0] == df["date"].iloc[-1] + pd.Timedelta(days=1)


def test_gradient_boosting_respects_covariates_and_horizon():
    df = _build_weekly_data(18)
    res = gradient_boosting_covariate_forecast(
        df=df,
        date_col="date",
        target_col="load",
        horizon=4,
    )
    assert len(res.forecasts) == 4
    assert pd.infer_freq(res.forecasts.index) == "W-SUN"


def test_ridge_forecast_error_correction_runs():
    df = _build_weekly_data(20)
    res = ridge_covariate_forecast(
        df=df,
        date_col="date",
        target_col="load",
        horizon=3,
    )
    assert res.forecasts.isna().sum() == 0
    assert res.forecasts.index.is_monotonic_increasing


def test_huber_handles_outliers_and_freq_inference():
    df = _build_weekly_data(26)
    df.loc[5, "load"] = 10_000
    res = huber_covariate_forecast(
        df=df,
        date_col="date",
        target_col="load",
        horizon=2,
    )
    assert len(res.forecasts) == 2
    assert res.forecasts.index.freqstr == "W-SUN"


def test_bayesian_ridge_respects_covariates():
    df = _build_weekly_data(22)
    res = bayesian_ridge_covariate_forecast(
        df=df,
        date_col="date",
        target_col="load",
        horizon=2,
    )
    assert res.metadata.get("model") is not None
    assert len(res.forecasts) == 2


def test_hist_gradient_direct_multioutput_produces_horizon_length():
    df = _build_weekly_data(40)
    res = hist_gradient_direct_forecast(
        df=df,
        date_col="date",
        target_col="load",
        horizon=5,
    )
    assert len(res.forecasts) == 5
    assert res.forecasts.index[0] > df["date"].max()


def test_fourier_ridge_adds_seasonality_terms():
    df = _build_weekly_data(30)
    res = fourier_ridge_seasonal_forecast(
        df=df,
        date_col="date",
        target_col="load",
        horizon=4,
    )
    assert res.forecasts.isna().sum() == 0
    assert res.metadata["fourier_terms"]
