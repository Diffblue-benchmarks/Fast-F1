"""Tests for Telemetry.get_first_non_zero_time_index method"""
import pytest
import pandas as pd
import numpy as np

from fastf1 import core


class TestTelemetryGetFirstNonZeroTimeIndex:
    """Tests for Telemetry.get_first_non_zero_time_index method"""

    def test_get_first_non_zero_time_index_with_non_zero_values(self):
        """Test get_first_non_zero_time_index when there are non-zero time values"""
        # Create telemetry data with non-zero time values
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        data = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=1), pd.Timedelta(seconds=2),
                     pd.Timedelta(seconds=3), pd.Timedelta(seconds=4),
                     pd.Timedelta(seconds=5)],
            'Date': dates
        })
        tel = core.Telemetry(data, session=None, driver='1')

        # Call get_first_non_zero_time_index
        result = tel.get_first_non_zero_time_index()

        # Verify it returns the first index
        assert result == 0

    def test_get_first_non_zero_time_index_with_zero_at_start(self):
        """Test get_first_non_zero_time_index when first values are zero"""
        # Create telemetry data with zero at the start
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        data = pd.DataFrame({
            'Time': [pd.Timedelta(0), pd.Timedelta(0),
                     pd.Timedelta(seconds=3), pd.Timedelta(seconds=4),
                     pd.Timedelta(seconds=5)],
            'Date': dates
        })
        tel = core.Telemetry(data, session=None, driver='1')

        # Call get_first_non_zero_time_index
        result = tel.get_first_non_zero_time_index()

        # Verify it returns index 2 (first non-zero)
        assert result == 2

    def test_get_first_non_zero_time_index_all_zeros(self):
        """Test get_first_non_zero_time_index when all time values are zero"""
        # Create telemetry data with all zero times
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        data = pd.DataFrame({
            'Time': [pd.Timedelta(0), pd.Timedelta(0), pd.Timedelta(0),
                     pd.Timedelta(0), pd.Timedelta(0)],
            'Date': dates
        })
        tel = core.Telemetry(data, session=None, driver='1')

        # Call get_first_non_zero_time_index
        result = tel.get_first_non_zero_time_index()

        # Verify it returns None
        assert result is None

    def test_get_first_non_zero_time_index_with_nat_values(self):
        """Test get_first_non_zero_time_index with NaT values"""
        # Create telemetry data with NaT values
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        data = pd.DataFrame({
            'Time': [pd.NaT, pd.Timedelta(0), pd.Timedelta(seconds=3),
                     pd.Timedelta(seconds=4), pd.Timedelta(seconds=5)],
            'Date': dates
        })
        tel = core.Telemetry(data, session=None, driver='1')

        # Call get_first_non_zero_time_index
        result = tel.get_first_non_zero_time_index()

        # Verify it returns index 2 (first non-zero, non-NaT)
        assert result == 2

    def test_get_first_non_zero_time_index_all_nat(self):
        """Test get_first_non_zero_time_index when all time values are NaT"""
        # Create telemetry data with all NaT times
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        data = pd.DataFrame({
            'Time': [pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT],
            'Date': dates
        })
        tel = core.Telemetry(data, session=None, driver='1')

        # Call get_first_non_zero_time_index
        result = tel.get_first_non_zero_time_index()

        # Verify it returns None
        assert result is None

    def test_get_first_non_zero_time_index_mixed_zero_and_nat(self):
        """Test get_first_non_zero_time_index with mixed zero and NaT values"""
        # Create telemetry data with mixed zero and NaT
        dates = pd.date_range('2023-01-01 10:00:00', periods=6, freq='1s')
        data = pd.DataFrame({
            'Time': [pd.Timedelta(0), pd.NaT, pd.Timedelta(0),
                     pd.NaT, pd.Timedelta(seconds=5), pd.Timedelta(seconds=6)],
            'Date': dates
        })
        tel = core.Telemetry(data, session=None, driver='1')

        # Call get_first_non_zero_time_index
        result = tel.get_first_non_zero_time_index()

        # Verify it returns index 4 (first non-zero, non-NaT)
        assert result == 4

    def test_get_first_non_zero_time_index_empty_dataframe(self):
        """Test get_first_non_zero_time_index with empty telemetry"""
        # Create empty telemetry data
        data = pd.DataFrame({
            'Time': pd.Series([], dtype='timedelta64[ns]'),
            'Date': pd.Series([], dtype='datetime64[ns]')
        })
        tel = core.Telemetry(data, session=None, driver='1')

        # Call get_first_non_zero_time_index
        result = tel.get_first_non_zero_time_index()

        # Verify it returns None
        assert result is None
