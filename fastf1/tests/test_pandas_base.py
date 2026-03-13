import pandas as pd
import pytest

from fastf1.internals.pandas_base import (
    BaseDataFrame,
    BaseSeries,
)


class TestBaseDataFrame:
    def test_constructor_returns_same_type(self):
        class MyDF(BaseDataFrame):
            pass

        df = MyDF({'a': [1, 2], 'b': [3, 4]})
        sliced = df[['a']]
        assert type(sliced) is MyDF

    def test_base_class_view(self):
        df = BaseDataFrame({'a': [1, 2], 'b': [3, 4]})
        view = df.base_class_view
        assert type(view) is pd.DataFrame

    def test_force_default_cols(self):
        class MyDF(BaseDataFrame):
            _COLUMNS = {
                'Col1': int,
                'Col2': str,
            }

        df = MyDF({'Col1': [1, 2], 'Col2': ['a', 'b']},
                  _force_default_cols=True)
        assert list(df.columns) == ['Col1', 'Col2']

    def test_force_default_cols_drops_unknown(self):
        class MyDF(BaseDataFrame):
            _COLUMNS = {
                'Col1': int,
            }

        df = MyDF({'Col1': [1, 2], 'Extra': ['x', 'y']},
                  _force_default_cols=True)
        assert 'Extra' not in df.columns

    def test_cast_default_cols(self):
        class MyDF(BaseDataFrame):
            _COLUMNS = {
                'Col1': int,
            }

        df = MyDF({'Col1': [1.0, 2.0]}, _cast_default_cols=True)
        assert df['Col1'].dtype == int

    def test_repr(self):
        df = BaseDataFrame({'a': [1]})
        r = repr(df)
        assert 'a' in r


class TestBaseSeries:
    def test_constructor_returns_same_type(self):
        class MySeries(BaseSeries):
            pass

        s = MySeries([1, 2, 3])
        sliced = s[:2]
        assert type(sliced) is MySeries

    def test_basic_operations(self):
        s = BaseSeries([10, 20, 30])
        assert len(s) == 3
        assert s.iloc[0] == 10
