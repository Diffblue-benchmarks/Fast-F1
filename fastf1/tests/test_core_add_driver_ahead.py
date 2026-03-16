"""Tests for Telemetry.add_driver_ahead method"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

from fastf1 import core


class TestTelemetryAddDriverAhead:
    """Tests for Telemetry.add_driver_ahead method"""

    def _create_mock_telemetry_with_calculate_driver_ahead(
        self, session_times, speeds, dates, driver_ahead_result,
        distance_result, ref_tel_data
    ):
        """Helper to create telemetry with mocked calculate_driver_ahead"""
        data = pd.DataFrame({
            'SessionTime': [pd.Timedelta(seconds=s) for s in session_times],
            'Speed': speeds,
            'Date': dates,
            'Time': [pd.Timedelta(seconds=s) for s in session_times]
        })
        tel = core.Telemetry(data, session=None, driver='1')

        # Create reference telemetry
        ref_tel = core.Telemetry(ref_tel_data, session=None, driver='1')

        # Mock calculate_driver_ahead to return test data
        tel.calculate_driver_ahead = Mock(
            return_value=(driver_ahead_result, distance_result, ref_tel)
        )

        return tel

    def test_add_driver_ahead_columns_dont_exist(self):
        """Test add_driver_ahead when DriverAhead columns don't exist"""
        # Create base telemetry data
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        # Create reference telemetry data with same dates
        ref_tel_data = pd.DataFrame({
            'SessionTime': [pd.Timedelta(seconds=s) for s in session_times],
            'Date': dates,
            'Time': [pd.Timedelta(seconds=s) for s in session_times]
        })

        # Mock calculate_driver_ahead results
        driver_ahead_result = np.array(['2', '2', '2', '2', '2'])
        distance_result = np.array([10.0, 15.0, 20.0, 25.0, 30.0])

        tel = self._create_mock_telemetry_with_calculate_driver_ahead(
            session_times, speeds, dates, driver_ahead_result,
            distance_result, ref_tel_data
        )

        # Call add_driver_ahead
        result = tel.add_driver_ahead()

        # Verify calculate_driver_ahead was called with return_reference=True
        tel.calculate_driver_ahead.assert_called_once_with(return_reference=True)

        # Verify DriverAhead and DistanceToDriverAhead columns were added
        assert 'DriverAhead' in result.columns
        assert 'DistanceToDriverAhead' in result.columns
        assert len(result) == 5

    def test_add_driver_ahead_columns_exist_drop_existing_true(self):
        """Test add_driver_ahead when columns exist and drop_existing=True"""
        # Create base telemetry data with existing columns
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        # Create reference telemetry data
        ref_tel_data = pd.DataFrame({
            'SessionTime': [pd.Timedelta(seconds=s) for s in session_times],
            'Date': dates,
            'Time': [pd.Timedelta(seconds=s) for s in session_times]
        })

        # Mock calculate_driver_ahead results
        driver_ahead_result = np.array(['3', '3', '3', '3', '3'])
        distance_result = np.array([50.0, 55.0, 60.0, 65.0, 70.0])

        tel = self._create_mock_telemetry_with_calculate_driver_ahead(
            session_times, speeds, dates, driver_ahead_result,
            distance_result, ref_tel_data
        )

        # Add existing columns with old values
        tel['DriverAhead'] = ['2', '2', '2', '2', '2']
        tel['DistanceToDriverAhead'] = [10.0, 15.0, 20.0, 25.0, 30.0]

        # Call add_driver_ahead with drop_existing=True
        result = tel.add_driver_ahead(drop_existing=True)

        # Verify calculate_driver_ahead was called
        tel.calculate_driver_ahead.assert_called_once_with(return_reference=True)

        # Verify columns were recalculated
        assert 'DriverAhead' in result.columns
        assert 'DistanceToDriverAhead' in result.columns

    def test_add_driver_ahead_columns_exist_drop_existing_false(self):
        """Test add_driver_ahead when columns exist and drop_existing=False"""
        # Create base telemetry data with existing columns
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        data = pd.DataFrame({
            'SessionTime': [pd.Timedelta(seconds=s) for s in session_times],
            'Speed': speeds,
            'Date': dates,
            'Time': [pd.Timedelta(seconds=s) for s in session_times],
            'DriverAhead': ['2', '2', '2', '2', '2'],
            'DistanceToDriverAhead': [10.0, 15.0, 20.0, 25.0, 30.0]
        })
        tel = core.Telemetry(data, session=None, driver='1')

        # Call add_driver_ahead with drop_existing=False
        result = tel.add_driver_ahead(drop_existing=False)

        # Verify it returned self without recalculation
        assert result is tel
        assert list(result['DriverAhead']) == ['2', '2', '2', '2', '2']
        assert list(result['DistanceToDriverAhead']) == [10.0, 15.0, 20.0, 25.0, 30.0]

    def test_add_driver_ahead_columns_dont_exist_with_line_coverage(self):
        """Test add_driver_ahead covering the else branch when columns don't exist"""
        # Create base telemetry data without DriverAhead columns
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        # Create reference telemetry data
        ref_tel_data = pd.DataFrame({
            'SessionTime': [pd.Timedelta(seconds=s) for s in session_times],
            'Date': dates,
            'Time': [pd.Timedelta(seconds=s) for s in session_times]
        })

        # Mock calculate_driver_ahead results
        driver_ahead_result = np.array(['2', '2', '2', '2', '2'])
        distance_result = np.array([10.0, 15.0, 20.0, 25.0, 30.0])

        tel = self._create_mock_telemetry_with_calculate_driver_ahead(
            session_times, speeds, dates, driver_ahead_result,
            distance_result, ref_tel_data
        )

        # Call add_driver_ahead (columns don't exist, so line 917: d = self is executed)
        result = tel.add_driver_ahead()

        # Verify calculate_driver_ahead was called
        tel.calculate_driver_ahead.assert_called_once_with(return_reference=True)

        # Verify result has both columns added
        assert 'DriverAhead' in result.columns
        assert 'DistanceToDriverAhead' in result.columns

    def test_add_driver_ahead_requires_resampling_different_shape(self):
        """Test add_driver_ahead when Date arrays have different shapes (triggers resampling)"""
        # Create base telemetry data with 5 samples
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        # Create reference telemetry data with 3 samples (different shape)
        ref_dates = pd.date_range('2023-01-01 10:00:00', periods=3, freq='1s')
        ref_tel_data = pd.DataFrame({
            'SessionTime': [pd.Timedelta(seconds=s) for s in [0, 1, 2]],
            'Date': ref_dates,
            'Time': [pd.Timedelta(seconds=s) for s in [0, 1, 2]]
        })

        # Mock calculate_driver_ahead results (3 samples, matching ref_tel)
        driver_ahead_result = np.array(['2', '2', '2'])
        distance_result = np.array([10.0, 15.0, 20.0])

        tel = self._create_mock_telemetry_with_calculate_driver_ahead(
            session_times, speeds, dates, driver_ahead_result,
            distance_result, ref_tel_data
        )

        # We need to patch the resample_channels to avoid session dependency
        def mock_resample_channels(self, new_date_ref):
            # Return a mocked resampled telemetry that matches the target shape
            resampled_data = pd.DataFrame({
                'SessionTime': [pd.Timedelta(seconds=s) for s in session_times],
                'Date': dates.copy(),
                'Time': [pd.Timedelta(seconds=s) for s in session_times],
                'DriverAhead': ['2', '2', '2', '2', '2'],
                'DistanceToDriverAhead': [10.0, 12.5, 15.0, 17.5, 20.0]
            })
            result = core.Telemetry(resampled_data, session=None, driver='1')
            return result

        # Patch at the function level
        import unittest.mock
        with unittest.mock.patch.object(core.Telemetry, 'resample_channels', mock_resample_channels):
            # Call add_driver_ahead
            result = tel.add_driver_ahead()

            # Verify result has the columns
            assert 'DriverAhead' in result.columns
            assert 'DistanceToDriverAhead' in result.columns
            assert len(result) == 5

    def test_add_driver_ahead_integration_with_same_dates(self):
        """Test add_driver_ahead with matching Date arrays (no resampling needed)"""
        # Create base telemetry data
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        # Create reference telemetry data with SAME dates
        ref_tel_data = pd.DataFrame({
            'SessionTime': [pd.Timedelta(seconds=s) for s in session_times],
            'Date': dates.copy(),
            'Time': [pd.Timedelta(seconds=s) for s in session_times]
        })

        # Mock calculate_driver_ahead results
        driver_ahead_result = np.array(['2', '2', '2', '2', '2'])
        distance_result = np.array([10.0, 15.0, 20.0, 25.0, 30.0])

        tel = self._create_mock_telemetry_with_calculate_driver_ahead(
            session_times, speeds, dates, driver_ahead_result,
            distance_result, ref_tel_data
        )

        # Call add_driver_ahead
        result = tel.add_driver_ahead()

        # Verify calculate_driver_ahead was called
        tel.calculate_driver_ahead.assert_called_once_with(return_reference=True)

        # Verify result has the correct columns
        assert 'DriverAhead' in result.columns
        assert 'DistanceToDriverAhead' in result.columns
        assert len(result) == 5

    def test_add_driver_ahead_with_different_date_values(self):
        """Test add_driver_ahead when Date arrays have same shape but different values (triggers resampling)"""
        # Create base telemetry data
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        # Create reference telemetry data with DIFFERENT date values (offset by 0.5s)
        ref_dates = pd.date_range('2023-01-01 10:00:00.5', periods=5, freq='1s')
        ref_tel_data = pd.DataFrame({
            'SessionTime': [pd.Timedelta(seconds=s + 0.5) for s in session_times],
            'Date': ref_dates,
            'Time': [pd.Timedelta(seconds=s + 0.5) for s in session_times]
        })

        # Mock calculate_driver_ahead results
        driver_ahead_result = np.array(['2', '2', '2', '2', '2'])
        distance_result = np.array([10.0, 15.0, 20.0, 25.0, 30.0])

        tel = self._create_mock_telemetry_with_calculate_driver_ahead(
            session_times, speeds, dates, driver_ahead_result,
            distance_result, ref_tel_data
        )

        # Mock resample_channels to avoid session dependency
        def mock_resample_channels(self, new_date_ref):
            # Return a mocked resampled telemetry
            resampled_data = pd.DataFrame({
                'SessionTime': [pd.Timedelta(seconds=s) for s in session_times],
                'Date': dates.copy(),
                'Time': [pd.Timedelta(seconds=s) for s in session_times],
                'DriverAhead': ['2', '2', '2', '2', '2'],
                'DistanceToDriverAhead': [10.0, 15.0, 20.0, 25.0, 30.0]
            })
            return core.Telemetry(resampled_data, session=None, driver='1')

        # Patch at the function level
        import unittest.mock
        with unittest.mock.patch.object(core.Telemetry, 'resample_channels', mock_resample_channels):
            # Call add_driver_ahead
            result = tel.add_driver_ahead()

            # Verify result has the columns
            assert 'DriverAhead' in result.columns
            assert 'DistanceToDriverAhead' in result.columns
            assert len(result) == 5

    def test_add_driver_ahead_with_outer_join(self):
        """Test that add_driver_ahead uses outer join when merging data"""
        # Create base telemetry data
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        # Create reference telemetry data
        ref_tel_data = pd.DataFrame({
            'SessionTime': [pd.Timedelta(seconds=s) for s in session_times],
            'Date': dates,
            'Time': [pd.Timedelta(seconds=s) for s in session_times]
        })

        # Mock calculate_driver_ahead results
        driver_ahead_result = np.array(['2', '2', '2', '2', '2'])
        distance_result = np.array([10.0, 15.0, 20.0, 25.0, 30.0])

        tel = self._create_mock_telemetry_with_calculate_driver_ahead(
            session_times, speeds, dates, driver_ahead_result,
            distance_result, ref_tel_data
        )

        # Mock the join method to verify it's called with how='outer'
        original_join = tel.join
        join_calls = []

        def mock_join(other, **kwargs):
            join_calls.append(kwargs)
            return original_join(other, **kwargs)

        tel.join = mock_join

        # Call add_driver_ahead
        result = tel.add_driver_ahead()

        # Verify join was called with how='outer'
        assert len(join_calls) > 0
        assert join_calls[-1].get('how') == 'outer'
