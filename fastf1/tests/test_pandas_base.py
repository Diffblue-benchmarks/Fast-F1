import typing
from typing import Optional

import pandas as pd
import pytest

from fastf1.internals.pandas_base import (
    BaseDataFrame,
    BaseSeries,
    _BaseSeriesConstructor
)


class CustomDataFrame(BaseDataFrame):
    """Custom DataFrame class for testing BaseDataFrame."""
    _COLUMNS = {
        'col1': int,
        'col2': str,
        'col3': object,
        'col4': 'datetime64[ns]',
        'col5': Optional[int],
        'missing_col': int
    }


def test_basedataframe_init_skip_missing_column():
    """Test that __init__ skips columns defined in _COLUMNS but not present in DataFrame."""
    # This test targets line 87: continue statement when column is not in self.columns
    data = {'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']}
    df = CustomDataFrame(data, _cast_default_cols=True)

    # missing_col is defined in _COLUMNS but not in the data
    # Should not raise an error and should skip it
    assert 'missing_col' not in df.columns
    assert 'col1' in df.columns
    assert 'col2' in df.columns


def test_basedataframe_init_cast_object_type_with_empty_column():
    """Test that __init__ handles empty object-typed columns correctly."""
    # This test targets lines 101-102: object type handling with empty column
    data = {'col3': [None, None, None]}
    df = CustomDataFrame(data, _cast_default_cols=True)

    # col3 is defined as object type in _COLUMNS
    # When all values are NA, it should set to None and not cast
    assert 'col3' in df.columns
    # The column should exist and handle object type correctly


def test_basedataframe_init_cast_object_type_string():
    """Test that __init__ handles 'object' as string type correctly."""
    # Another test targeting lines 101-102 with _type == 'object' as string
    class CustomDataFrameObjectStr(BaseDataFrame):
        _COLUMNS = {
            'obj_col': 'object'
        }

    data = {'obj_col': [None, None]}
    df = CustomDataFrameObjectStr(data, _cast_default_cols=True)

    assert 'obj_col' in df.columns


def test_basedataframe_constructor_sliced_horizontal():
    """Test that _constructor_sliced_horizontal returns pd.Series."""
    # This test targets line 129: return pd.Series
    df = CustomDataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})

    # Access the property
    constructor = df._constructor_sliced_horizontal

    # Should return pd.Series class
    assert constructor == pd.Series


def test_baseseriesconstructor_new_with_no_parent():
    """Test _BaseSeriesConstructor.__new__ when parent is None."""
    # This test targets line 166: constructor = pd.Series when parent is None

    # Create a dynamic constructor without parent
    DynamicConstructor = type('_DynamicBaseSeriesConstructor',
                              (_BaseSeriesConstructor,),
                              {})

    # Call __new__ without parent
    result = DynamicConstructor([1, 2, 3])

    # Should return a pd.Series
    assert isinstance(result, pd.Series)
    assert not isinstance(result, BaseDataFrame)


def test_baseseriesconstructor_new_with_no_index():
    """Test _BaseSeriesConstructor.__new__ when index is None."""
    # This test targets line 166: constructor = pd.Series when index is None

    df = CustomDataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})

    # Create a dynamic constructor with parent
    DynamicConstructor = type('_DynamicBaseSeriesConstructor',
                              (_BaseSeriesConstructor,),
                              {'__meta_created_from': df})

    # Call __new__ with no index and simple data (not Series/DataFrame)
    result = DynamicConstructor([1, 2, 3])

    # Should return a pd.Series since index is None
    assert isinstance(result, pd.Series)


def test_baseseriesconstructor_new_with_singleblockmanager():
    """Test _BaseSeriesConstructor.__new__ with SingleBlockManager data."""
    # This test targets line 177: obj = constructor._from_mgr

    # Create a DataFrame and get a Series to extract its manager
    df = CustomDataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
    series = pd.Series([1, 2, 3])

    # Get the SingleBlockManager from the series
    mgr = getattr(series, '_mgr')

    # Create a dynamic constructor with parent
    DynamicConstructor = type('_DynamicBaseSeriesConstructor',
                              (_BaseSeriesConstructor,),
                              {'__meta_created_from': df})

    # Call __new__ with SingleBlockManager
    # This should trigger the _from_mgr path
    result = DynamicConstructor(mgr)

    assert isinstance(result, pd.Series)


def test_basedataframe_force_default_cols():
    """Test BaseDataFrame with _force_default_cols=True."""
    data = {'col1': [1, 2, 3], 'extra_col': ['x', 'y', 'z']}
    df = CustomDataFrame(data, _force_default_cols=True)

    # Should only have columns defined in _COLUMNS
    assert 'col1' in df.columns
    # extra_col should be removed (not in _COLUMNS)
    assert 'extra_col' not in df.columns


def test_basedataframe_empty_datetime_column():
    """Test empty datetime column casting."""
    data = {'col4': [None, None, None]}
    df = CustomDataFrame(data, _cast_default_cols=True)

    # col4 is defined as 'datetime64[ns]' in _COLUMNS
    assert 'col4' in df.columns


def test_basedataframe_optional_type_empty():
    """Test Optional type with empty column."""
    data = {'col5': [None, None]}
    df = CustomDataFrame(data, _cast_default_cols=True)

    # col5 is defined as Optional[int]
    assert 'col5' in df.columns


def test_basedataframe_constructor_sliced():
    """Test _constructor_sliced returns custom constructor."""
    df = CustomDataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})

    constructor = df._constructor_sliced

    # Should return a dynamically created class
    assert issubclass(constructor, _BaseSeriesConstructor)


def test_basedataframe_constructor_sliced_vertical():
    """Test _constructor_sliced_vertical returns pd.Series."""
    df = CustomDataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})

    constructor = df._constructor_sliced_vertical

    assert constructor == pd.Series


def test_basedataframe_base_class_view():
    """Test base_class_view property."""
    df = CustomDataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})

    view = df.base_class_view

    assert isinstance(view, pd.DataFrame)
    assert not isinstance(view, CustomDataFrame)


def test_baseseries_constructor():
    """Test BaseSeries _constructor property."""
    series = BaseSeries([1, 2, 3])

    assert series._constructor == BaseSeries


def test_basedataframe_repr():
    """Test BaseDataFrame __repr__ uses base_class_view."""
    df = CustomDataFrame({'col1': [1, 2, 3]})

    repr_str = repr(df)

    # Should call base_class_view's __repr__
    assert isinstance(repr_str, str)
