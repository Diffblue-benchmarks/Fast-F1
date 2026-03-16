"""Tests for Telemetry.calculate_differential_distance method"""
import pytest
import pandas as pd
import numpy as np
from datetime import timedelta

from fastf1 import core


class TestTelemetryCalculateDifferentialDistance:
    """Tests for Telemetry.calculate_differential_distance method"""

    def test_calculate_differential_distance_missing_speed_column(self):
        """Test that ValueError is raised when Speed column is missing"""
        # Create telemetry with Time but no Speed
        data = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=s) for s in [0, 1, 2, 3, 4]]
        })
        tel = core.Telemetry(data, session=None, driver='1')

        with pytest.raises(ValueError, match="Telemetry does not contain required channels 'Time' and 'Speed'."):
            tel.calculate_differential_distance()

    def test_calculate_differential_distance_missing_time_column(self):
        """Test that ValueError is raised when Time column is missing"""
        # Create telemetry with Speed but no Time
        data = pd.DataFrame({
            'Speed': [100, 120, 140, 160, 180]
        })
        tel = core.Telemetry(data, session=None, driver='1')

        with pytest.raises(ValueError, match="Telemetry does not contain required channels 'Time' and 'Speed'."):
            tel.calculate_differential_distance()

    def test_calculate_differential_distance_missing_both_columns(self):
        """Test that ValueError is raised when both Speed and Time columns are missing"""
        # Create telemetry with neither Speed nor Time
        data = pd.DataFrame({
            'X': [1, 2, 3, 4, 5],
            'Y': [10, 20, 30, 40, 50]
        })
        tel = core.Telemetry(data, session=None, driver='1')

        with pytest.raises(ValueError, match="Telemetry does not contain required channels 'Time' and 'Speed'."):
            tel.calculate_differential_distance()

    def test_calculate_differential_distance_empty_telemetry(self):
        """Test that empty Series is returned for empty telemetry"""
        # Create empty telemetry with correct columns
        data = pd.DataFrame({
            'Time': pd.Series([], dtype='timedelta64[ns]'),
            'Speed': pd.Series([], dtype='float64')
        })
        tel = core.Telemetry(data, session=None, driver='1')

        result = tel.calculate_differential_distance()

        assert isinstance(result, pd.Series)
        assert len(result) == 0

    def test_calculate_differential_distance_single_sample(self):
        """Test differential distance calculation with a single sample"""
        # Create telemetry with one sample
        data = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=5)],
            'Speed': [100.0]  # 100 km/h
        })
        tel = core.Telemetry(data, session=None, driver='1')

        result = tel.calculate_differential_distance()

        # First sample: dt = Time[0].total_seconds() = 5.0
        # ds = Speed / 3.6 * dt = 100 / 3.6 * 5.0 = 138.888...
        expected_distance = 100.0 / 3.6 * 5.0
        assert len(result) == 1
        assert np.isclose(result.iloc[0], expected_distance)

    def test_calculate_differential_distance_multiple_samples(self):
        """Test differential distance calculation with multiple samples"""
        # Create telemetry with multiple samples at 1-second intervals
        data = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=s) for s in [0, 1, 2, 3, 4]],
            'Speed': [100.0, 120.0, 140.0, 160.0, 180.0]  # km/h
        })
        tel = core.Telemetry(data, session=None, driver='1')

        result = tel.calculate_differential_distance()

        # First sample: dt = 0 seconds, ds = 100 / 3.6 * 0 = 0
        # Second sample: dt = 1 second, ds = 120 / 3.6 * 1 = 33.333...
        # Third sample: dt = 1 second, ds = 140 / 3.6 * 1 = 38.888...
        # Fourth sample: dt = 1 second, ds = 160 / 3.6 * 1 = 44.444...
        # Fifth sample: dt = 1 second, ds = 180 / 3.6 * 1 = 50.0

        assert len(result) == 5
        assert np.isclose(result.iloc[0], 100.0 / 3.6 * 0.0)
        assert np.isclose(result.iloc[1], 120.0 / 3.6 * 1.0)
        assert np.isclose(result.iloc[2], 140.0 / 3.6 * 1.0)
        assert np.isclose(result.iloc[3], 160.0 / 3.6 * 1.0)
        assert np.isclose(result.iloc[4], 180.0 / 3.6 * 1.0)

    def test_calculate_differential_distance_variable_time_intervals(self):
        """Test differential distance calculation with variable time intervals"""
        # Create telemetry with varying time intervals
        data = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=s) for s in [2, 3, 5, 8, 13]],
            'Speed': [100.0, 100.0, 100.0, 100.0, 100.0]  # constant speed
        })
        tel = core.Telemetry(data, session=None, driver='1')

        result = tel.calculate_differential_distance()

        # Speed is constant at 100 km/h = 100/3.6 m/s = 27.777... m/s
        # First sample: dt = 2 seconds, ds = 27.777... * 2 = 55.555...
        # Second sample: dt = 1 second, ds = 27.777... * 1 = 27.777...
        # Third sample: dt = 2 seconds, ds = 27.777... * 2 = 55.555...
        # Fourth sample: dt = 3 seconds, ds = 27.777... * 3 = 83.333...
        # Fifth sample: dt = 5 seconds, ds = 27.777... * 5 = 138.888...

        speed_ms = 100.0 / 3.6
        assert len(result) == 5
        assert np.isclose(result.iloc[0], speed_ms * 2.0)
        assert np.isclose(result.iloc[1], speed_ms * 1.0)
        assert np.isclose(result.iloc[2], speed_ms * 2.0)
        assert np.isclose(result.iloc[3], speed_ms * 3.0)
        assert np.isclose(result.iloc[4], speed_ms * 5.0)

    def test_calculate_differential_distance_zero_speed(self):
        """Test differential distance calculation when speed is zero"""
        # Create telemetry with zero speed (car stopped)
        data = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=s) for s in [0, 1, 2, 3]],
            'Speed': [0.0, 0.0, 0.0, 0.0]
        })
        tel = core.Telemetry(data, session=None, driver='1')

        result = tel.calculate_differential_distance()

        # All distances should be 0 when speed is 0
        assert len(result) == 4
        assert all(result == 0.0)

    def test_calculate_differential_distance_mixed_speeds(self):
        """Test differential distance calculation with mixed speeds including zero"""
        # Create telemetry with varying speeds including zero
        data = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=s) for s in [0, 1, 2, 3, 4]],
            'Speed': [0.0, 50.0, 100.0, 50.0, 0.0]
        })
        tel = core.Telemetry(data, session=None, driver='1')

        result = tel.calculate_differential_distance()

        # First sample: dt = 0, ds = 0 / 3.6 * 0 = 0
        # Second sample: dt = 1, ds = 50 / 3.6 * 1 = 13.888...
        # Third sample: dt = 1, ds = 100 / 3.6 * 1 = 27.777...
        # Fourth sample: dt = 1, ds = 50 / 3.6 * 1 = 13.888...
        # Fifth sample: dt = 1, ds = 0 / 3.6 * 1 = 0

        assert len(result) == 5
        assert np.isclose(result.iloc[0], 0.0 / 3.6 * 0.0)
        assert np.isclose(result.iloc[1], 50.0 / 3.6 * 1.0)
        assert np.isclose(result.iloc[2], 100.0 / 3.6 * 1.0)
        assert np.isclose(result.iloc[3], 50.0 / 3.6 * 1.0)
        assert np.isclose(result.iloc[4], 0.0 / 3.6 * 1.0)
