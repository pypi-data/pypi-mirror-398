import pandas as pd
import pytest
from analysis3054.utils import conditional_column_merge

def test_conditional_column_merge_unsorted_index():
    # df with unsorted index
    # Index 2 -> 'a'
    # Index 0 -> 'b'
    # Index 1 -> 'c'
    df = pd.DataFrame({'key': ['a', 'b', 'c']}, index=[2, 0, 1])
    other = pd.DataFrame({'key': ['a', 'b', 'c'], 'val': [10, 20, 30]})

    # Expected result:
    # Index 2 ('a') -> 10
    # Index 0 ('b') -> 20
    # Index 1 ('c') -> 30

    result = conditional_column_merge(
        df, other,
        df_key='key', other_key='key',
        columns='val',
        multiple=True
    )

    expected_val = pd.Series([10, 20, 30], index=[2, 0, 1], name='val')
    pd.testing.assert_series_equal(result['val'], expected_val, check_names=False)

def test_conditional_column_merge_duplicate_index():
    # df with duplicate index
    df = pd.DataFrame({'key': ['a', 'b']}, index=[0, 0])
    other = pd.DataFrame({'key': ['a', 'b'], 'val': [10, 20]})

    # Expected result:
    # Index 0 ('a') -> 10
    # Index 0 ('b') -> 20

    result = conditional_column_merge(
        df, other,
        df_key='key', other_key='key',
        columns='val',
        multiple=True
    )

    expected_val = pd.Series([10, 20], index=[0, 0], name='val')
    pd.testing.assert_series_equal(result['val'], expected_val, check_names=False)
