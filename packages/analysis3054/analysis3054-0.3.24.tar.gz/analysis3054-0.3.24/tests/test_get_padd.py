import numpy as np
import pandas as pd

from analysis3054.utils import get_padd


def test_get_padd_specific_labels():
    identifiers = pd.Series(["Texas", "NY", 12, "northern mariana islands", 1, " unknown "])

    mapped = get_padd(identifiers)

    expected = pd.Series([
        "PADD 3",
        "PADD 1-Northeast",
        "PADD 1-Southeast",
        "PADD 7",
        "PADD 3",
        np.nan,
    ])

    pd.testing.assert_series_equal(mapped, expected)


def test_get_padd_collapsed_padd_one():
    identifiers = pd.Series(["pa", "South Carolina", 72])

    mapped = get_padd(identifiers, specific=False)

    expected = pd.Series(["PADD 1", "PADD 1", "PADD 6"])

    pd.testing.assert_series_equal(mapped, expected)
