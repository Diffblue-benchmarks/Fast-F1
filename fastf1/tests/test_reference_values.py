import pandas as pd
import pytest

from fastf1.testing.reference_values import ensure_data_type


def test_ensure_data_type_matching_dtypes():
    """Test that ensure_data_type passes when all dtypes match."""
    # Create a DataFrame with specific dtypes
    df = pd.DataFrame({
        'col_int': [1, 2, 3],
        'col_float': [1.0, 2.0, 3.0],
        'col_str': ['a', 'b', 'c']
    })

    # Define expected dtypes
    column_dtypes = {
        'col_int': 'int64',
        'col_float': 'float64',
        'col_str': 'O'
    }

    # Should not raise any exception
    ensure_data_type(column_dtypes, df)


def test_ensure_data_type_mismatched_dtype():
    """Test that ensure_data_type raises TypeError when dtype doesn't match."""
    # Create a DataFrame
    df = pd.DataFrame({
        'col_int': [1, 2, 3],
        'col_float': [1.0, 2.0, 3.0]
    })

    # Define expected dtypes with intentional mismatch
    column_dtypes = {
        'col_int': 'float64',  # Expected float64 but actual is int64
        'col_float': 'float64'
    }

    # Should raise TypeError
    with pytest.raises(TypeError, match=r"Dtype .* not equivalent to target dtype"):
        ensure_data_type(column_dtypes, df)


def test_ensure_data_type_missing_column():
    """Test that ensure_data_type skips columns not present in DataFrame."""
    # Create a DataFrame with only some columns
    df = pd.DataFrame({
        'col_int': [1, 2, 3],
        'col_float': [1.0, 2.0, 3.0]
    })

    # Define expected dtypes including columns not in df
    column_dtypes = {
        'col_int': 'int64',
        'col_float': 'float64',
        'col_missing': 'O'  # This column is not in df
    }

    # Should not raise any exception (missing column is skipped)
    ensure_data_type(column_dtypes, df)


def test_ensure_data_type_partial_check():
    """Test that ensure_data_type checks only specified columns."""
    # Create a DataFrame with multiple columns
    df = pd.DataFrame({
        'col_int': [1, 2, 3],
        'col_float': [1.0, 2.0, 3.0],
        'col_str': ['a', 'b', 'c']
    })

    # Define expected dtypes for only a subset of columns
    column_dtypes = {
        'col_int': 'int64',
        'col_float': 'float64'
        # col_str is not checked
    }

    # Should not raise any exception
    ensure_data_type(column_dtypes, df)
