import sys
import types
from datetime import timedelta

import pandas as pd

from analysis3054 import forecasting


def _install_dummy_chronos(monkeypatch, predict_df_fn):
    class DummyPipeline:
        def __init__(self):
            self.calls = []

        @classmethod
        def from_pretrained(cls, model_name, device_map=None):
            return cls()

        def predict_df(self, context_df, future_df=None, prediction_length=None, quantile_levels=None, **kwargs):
            # record call arguments for inspection inside tests
            self.calls.append(
                {
                    "prediction_length": prediction_length,
                    "quantile_levels": quantile_levels,
                    "id": context_df["id"].iloc[0],
                }
            )
            return predict_df_fn(context_df, prediction_length, quantile_levels)

    dummy_module = types.SimpleNamespace(Chronos2Pipeline=DummyPipeline)
    monkeypatch.setitem(sys.modules, "chronos", dummy_module)
    return DummyPipeline


def test_chronos2_uses_requested_quantiles_and_returns_series(monkeypatch):
    quantiles_seen = {}

    def predict_df_fn(context_df, prediction_length, quantile_levels):
        quantiles_seen["passed"] = quantile_levels
        start = context_df["timestamp"].max()
        timestamps = pd.date_range(start + timedelta(days=1), periods=prediction_length, freq="D")
        return pd.DataFrame(
            {
                "id": [context_df["id"].iloc[0]] * prediction_length,
                "timestamp": timestamps,
                "predictions": [1.0] * prediction_length,
                "0.1": [0.5] * prediction_length,
                0.9: [1.5] * prediction_length,
            }
        )

    _install_dummy_chronos(monkeypatch, predict_df_fn)

    df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=4, freq="D"), "value": [1.0, 2.0, 3.0, 4.0]})
    res = forecasting.chronos2_forecast(
        df,
        date_col="date",
        target_col="value",
        prediction_length=2,
        quantile_levels=[0.1, 0.9],
    )

    # 0.5 should be injected automatically to ensure median predictions
    assert quantiles_seen["passed"] == [0.1, 0.5, 0.9]
    # Ensure quantile forecasts returned for all requested levels and the median
    assert set(res.quantile_forecasts.columns.get_level_values("quantile")) == {0.1, 0.5, 0.9}
    pd.testing.assert_series_equal(
        res.quantile_forecasts["series_1", 0.1],
        pd.Series([0.5, 0.5], index=res.forecasts.index),
        check_names=False,
    )


def test_chronos2_handles_float_named_quantile_columns(monkeypatch):
    def predict_df_fn(context_df, prediction_length, quantile_levels):
        start = context_df["timestamp"].max()
        timestamps = pd.date_range(start + timedelta(hours=1), periods=prediction_length, freq="H")
        return pd.DataFrame(
            {
                "id": [context_df["id"].iloc[0]] * prediction_length,
                "timestamp": timestamps,
                "predictions": [2.0] * prediction_length,
                0.025: [1.0] * prediction_length,
                0.975: [3.0] * prediction_length,
            }
        )

    _install_dummy_chronos(monkeypatch, predict_df_fn)

    df = pd.DataFrame({"date": pd.date_range("2024-02-01", periods=3, freq="H"), "metric": [1, 2, 3]})
    res = forecasting.chronos2_univariate_forecast(df, date_col="date", target_col="metric", prediction_length=2)

    # Default quantiles should be requested, and float-named outputs should be parsed
    assert set(res.quantile_forecasts.columns.get_level_values("quantile")) == {0.025, 0.5, 0.975}
    pd.testing.assert_series_equal(
        res.lower_conf_int["series_1"], pd.Series([1.0, 1.0], index=res.forecasts.index), check_names=False
    )
    pd.testing.assert_series_equal(
        res.upper_conf_int["series_1"], pd.Series([3.0, 3.0], index=res.forecasts.index), check_names=False
    )
