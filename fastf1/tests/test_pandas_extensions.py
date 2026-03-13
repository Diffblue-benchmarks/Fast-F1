"""Tests for internals/pandas_extensions.py."""
import numpy as np
import pandas as pd
import pytest

from fastf1.internals.pandas_extensions import (
    _fallback_create_df,
    create_df_fast,
)


class TestFallbackCreateDf:
    def test_basic(self):
        arrays = [np.array([1, 2, 3]), np.array([4.0, 5.0, 6.0])]
        columns = ['a', 'b']
        df = _fallback_create_df(arrays, columns)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ['a', 'b']
        assert len(df) == 3
        assert df['a'].tolist() == [1, 2, 3]

    def test_single_column(self):
        arrays = [np.array([10, 20])]
        columns = ['x']
        df = _fallback_create_df(arrays, columns)
        assert list(df.columns) == ['x']
        assert len(df) == 2


class TestCreateDfFast:
    def test_basic(self):
        arrays = [np.array([1, 2, 3]), np.array([4.0, 5.0, 6.0])]
        columns = ['a', 'b']
        df = create_df_fast(arrays=arrays, columns=columns)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ['a', 'b']
        assert len(df) == 3

    def test_multiple_dtypes(self):
        arrays = [
            np.array([1, 2], dtype='int64'),
            np.array([3.0, 4.0], dtype='float64'),
            np.array(['a', 'b'], dtype='object'),
        ]
        columns = ['int_col', 'float_col', 'str_col']
        df = create_df_fast(arrays=arrays, columns=columns)
        assert len(df) == 2
        assert df['int_col'].dtype == np.int64
        assert df['float_col'].dtype == np.float64

    def test_empty_arrays(self):
        arrays = [np.array([], dtype='float64')]
        columns = ['empty']
        df = create_df_fast(arrays=arrays, columns=columns)
        assert len(df) == 0

    def test_fallback_on_error(self):
        # Force an error in the fast path by passing something that
        # will fail in the fast creation but succeed in fallback
        arrays = [np.array([1, 2, 3])]
        columns = ['col']
        df = create_df_fast(arrays=arrays, columns=columns, fallback=True)
        assert len(df) == 3
