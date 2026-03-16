"""Tests for Telemetry.add_differential_distance method"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock

from fastf1 import core


class TestTelemetryAddDifferentialDistance:
    """Tests for Telemetry.add_differential_distance method"""

    def _create_mock_telemetry_with_calculate_differential_distance(
        self, session_times, speeds, dates, differential_distance_result
    ):
        """Helper to create telemetry with mocked calculate_differential_distance"""
        data = pd.DataFrame({
            'SessionTime': [pd.Timedelta(seconds=s) for s in session_times],
            'Speed': speeds,
            'Date': dates,
            'Time': [pd.Timedelta(seconds=s) for s in session_times]
        })
        tel = core.Telemetry(data, session=None, driver='1')

        # Mock calculate_differential_distance to return test data
        tel.calculate_differential_distance = Mock(return_value=differential_distance_result)

        return tel

    def test_add_differential_distance_column_doesnt_exist(self):
        """Test add_differential_distance when DifferentialDistance column doesn't exist"""
        # Create base telemetry data
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        # Mock calculate_differential_distance results
        differential_distance_result = pd.Series([0.0, 30.0, 35.0, 40.0, 45.0])

        tel = self._create_mock_telemetry_with_calculate_differential_distance(
            session_times, speeds, dates, differential_distance_result
        )

        # Call add_differential_distance
        result = tel.add_differential_distance()

        # Verify calculate_differential_distance was called
        tel.calculate_differential_distance.assert_called_once()

        # Verify DifferentialDistance column was added
        assert 'DifferentialDistance' in result.columns
        assert len(result) == 5

    def test_add_differential_distance_column_exists_drop_existing_true(self):
        """Test add_differential_distance when DifferentialDistance column exists and drop_existing=True"""
        # Create base telemetry data with existing DifferentialDistance column
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        # Mock calculate_differential_distance results (new values)
        differential_distance_result = pd.Series([0.0, 50.0, 55.0, 60.0, 65.0])

        tel = self._create_mock_telemetry_with_calculate_differential_distance(
            session_times, speeds, dates, differential_distance_result
        )

        # Add existing DifferentialDistance column with old values
        tel['DifferentialDistance'] = [0.0, 30.0, 35.0, 40.0, 45.0]

        # Call add_differential_distance with drop_existing=True (default)
        result = tel.add_differential_distance(drop_existing=True)

        # Verify calculate_differential_distance was called
        tel.calculate_differential_distance.assert_called_once()

        # Verify DifferentialDistance column was recalculated
        assert 'DifferentialDistance' in result.columns

    def test_add_differential_distance_column_exists_drop_existing_false(self):
        """Test add_differential_distance when DifferentialDistance column exists and drop_existing=False"""
        # Create base telemetry data with existing DifferentialDistance column
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        data = pd.DataFrame({
            'SessionTime': [pd.Timedelta(seconds=s) for s in session_times],
            'Speed': speeds,
            'Date': dates,
            'Time': [pd.Timedelta(seconds=s) for s in session_times],
            'DifferentialDistance': [0.0, 30.0, 35.0, 40.0, 45.0]
        })
        tel = core.Telemetry(data, session=None, driver='1')

        # Call add_differential_distance with drop_existing=False
        result = tel.add_differential_distance(drop_existing=False)

        # Verify it returned self without recalculation
        assert result is tel
        assert list(result['DifferentialDistance']) == [0.0, 30.0, 35.0, 40.0, 45.0]

    def test_add_differential_distance_uses_outer_join(self):
        """Test that add_differential_distance uses outer join when merging data"""
        # Create base telemetry data
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        # Mock calculate_differential_distance results
        differential_distance_result = pd.Series([0.0, 30.0, 35.0, 40.0, 45.0])

        tel = self._create_mock_telemetry_with_calculate_differential_distance(
            session_times, speeds, dates, differential_distance_result
        )

        # Mock the join method to verify it's called with how='outer'
        original_join = tel.join
        join_calls = []

        def mock_join(other, **kwargs):
            join_calls.append(kwargs)
            return original_join(other, **kwargs)

        tel.join = mock_join

        # Call add_differential_distance
        result = tel.add_differential_distance()

        # Verify join was called with how='outer'
        assert len(join_calls) > 0
        assert join_calls[-1].get('how') == 'outer'
