"""Tests for Telemetry.add_distance method"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock
from datetime import datetime, timedelta

from fastf1 import core


class TestTelemetryAddDistance:
    """Tests for Telemetry.add_distance method"""

    def _create_mock_telemetry_with_integrate_distance(
        self, session_times, speeds, dates, distance_result
    ):
        """Helper to create telemetry with mocked integrate_distance"""
        data = pd.DataFrame({
            'SessionTime': [pd.Timedelta(seconds=s) for s in session_times],
            'Speed': speeds,
            'Date': dates,
            'Time': [pd.Timedelta(seconds=s) for s in session_times]
        })
        tel = core.Telemetry(data, session=None, driver='1')

        # Mock integrate_distance to return test data
        tel.integrate_distance = Mock(return_value=distance_result)

        return tel

    def test_add_distance_column_doesnt_exist(self):
        """Test add_distance when Distance column doesn't exist"""
        # Create base telemetry data
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        # Mock integrate_distance results
        distance_result = pd.Series([0.0, 30.0, 65.0, 105.0, 150.0])

        tel = self._create_mock_telemetry_with_integrate_distance(
            session_times, speeds, dates, distance_result
        )

        # Call add_distance
        result = tel.add_distance()

        # Verify integrate_distance was called
        tel.integrate_distance.assert_called_once()

        # Verify Distance column was added
        assert 'Distance' in result.columns
        assert len(result) == 5

    def test_add_distance_column_exists_drop_existing_true(self):
        """Test add_distance when Distance column exists and drop_existing=True"""
        # Create base telemetry data with existing Distance column
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        # Mock integrate_distance results (new values)
        distance_result = pd.Series([0.0, 50.0, 100.0, 150.0, 200.0])

        tel = self._create_mock_telemetry_with_integrate_distance(
            session_times, speeds, dates, distance_result
        )

        # Add existing Distance column with old values
        tel['Distance'] = [0.0, 30.0, 60.0, 90.0, 120.0]

        # Call add_distance with drop_existing=True (default)
        result = tel.add_distance(drop_existing=True)

        # Verify integrate_distance was called
        tel.integrate_distance.assert_called_once()

        # Verify Distance column was recalculated
        assert 'Distance' in result.columns

    def test_add_distance_column_exists_drop_existing_false(self):
        """Test add_distance when Distance column exists and drop_existing=False"""
        # Create base telemetry data with existing Distance column
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        data = pd.DataFrame({
            'SessionTime': [pd.Timedelta(seconds=s) for s in session_times],
            'Speed': speeds,
            'Date': dates,
            'Time': [pd.Timedelta(seconds=s) for s in session_times],
            'Distance': [0.0, 30.0, 60.0, 90.0, 120.0]
        })
        tel = core.Telemetry(data, session=None, driver='1')

        # Call add_distance with drop_existing=False
        result = tel.add_distance(drop_existing=False)

        # Verify it returned self without recalculation
        assert result is tel
        assert list(result['Distance']) == [0.0, 30.0, 60.0, 90.0, 120.0]

    def test_add_distance_uses_outer_join(self):
        """Test that add_distance uses outer join when merging data"""
        # Create base telemetry data
        dates = pd.date_range('2023-01-01 10:00:00', periods=5, freq='1s')
        session_times = [0, 1, 2, 3, 4]
        speeds = [100, 110, 120, 130, 140]

        # Mock integrate_distance results
        distance_result = pd.Series([0.0, 30.0, 65.0, 105.0, 150.0])

        tel = self._create_mock_telemetry_with_integrate_distance(
            session_times, speeds, dates, distance_result
        )

        # Mock the join method to verify it's called with how='outer'
        original_join = tel.join
        join_calls = []

        def mock_join(other, **kwargs):
            join_calls.append(kwargs)
            return original_join(other, **kwargs)

        tel.join = mock_join

        # Call add_distance
        result = tel.add_distance()

        # Verify join was called with how='outer'
        assert len(join_calls) > 0
        assert join_calls[-1].get('how') == 'outer'
