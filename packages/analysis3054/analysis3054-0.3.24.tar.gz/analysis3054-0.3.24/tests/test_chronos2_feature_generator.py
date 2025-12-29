import pandas as pd

from analysis3054 import forecasting


def test_feature_generator_adds_calendar_and_static_future():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=4, freq="D"),
            "target": [1.0, 2.0, 3.0, 4.0],
            "driver": [10, 11, 12, 13],
            "region": ["east"] * 4,
        }
    )

    bundle = forecasting.chronos2_feature_generator(
        df,
        date_col="date",
        target_col="target",
        covariate_cols=["driver"],
        static_covariate_cols=["region"],
        prediction_length=2,
    )

    expected_date_cols = {
        "date_year",
        "date_month",
        "date_day",
        "date_dayofweek",
        "date_dayofyear",
        "date_weekofyear",
        "date_hour",
    }
    assert expected_date_cols.issubset(set(bundle.context_df.columns))
    assert bundle.id_column == "__item_id__"
    assert bundle.future_df is not None
    assert len(bundle.future_df) == 2
    assert set(["id", "timestamp", "driver", "region", *expected_date_cols]) <= set(bundle.future_df.columns)
    assert set(bundle.future_df["region"]) == {"east"}


def test_feature_generator_respects_provided_future_covariates():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=3, freq="D"),
            "target": [5, 6, 7],
            "temp": [50, 51, 52],
            "series_id": ["a"] * 3,
        }
    )
    future_cov = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-04", periods=2, freq="D"),
            "temp": [53, 54],
            "series_id": ["a", "a"],
        }
    )

    bundle = forecasting.chronos2_feature_generator(
        df,
        date_col="date",
        target_col="target",
        covariate_cols=["temp"],
        future_cov_df=future_cov,
        prediction_length=2,
        id_col="series_id",
    )

    assert bundle.future_df is not None
    assert list(bundle.future_df["temp"]) == [53, 54]
    assert bundle.id_column == "series_id"
