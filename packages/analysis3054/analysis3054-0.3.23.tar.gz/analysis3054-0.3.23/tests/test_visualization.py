import pandas as pd

from analysis3054.visualization import forecast_plot


def test_forecast_plot_auto_splits_train_and_test_segments():
    """The plot should separate train/test when df spans the forecast horizon."""

    dates = pd.date_range("2024-01-01", periods=6, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "value": range(len(dates)),
    })
    forecast_index = pd.date_range("2024-01-06", periods=2, freq="D")
    forecast_df = pd.DataFrame({"value": [6, 7]}, index=forecast_index)

    fig = forecast_plot(date="date", df=df, forecast=forecast_df)

    trace_names = {trace.name for trace in fig.data}
    assert any("train" in name for name in trace_names)
    assert any("test" in name for name in trace_names)
    assert any("forecast" in name for name in trace_names)
