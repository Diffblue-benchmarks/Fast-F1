"""Tests for Telemetry.slice_by_lap method"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from fastf1 import core


class TestTelemetrySliceByLap:
    """Tests for Telemetry.slice_by_lap method"""

    def _create_mock_session(self, t0_date='2023-01-01 10:00:00'):
        """Helper to create a mock session"""
        session = Mock()
        session.t0_date = pd.Timestamp(t0_date)
        return session

    def _create_telemetry(self, session):
        """Helper to create test telemetry data"""
        dates = pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:00:01',
            '2023-01-01 10:00:02',
            '2023-01-01 10:00:03',
            '2023-01-01 10:00:04',
            '2023-01-01 10:00:05',
            '2023-01-01 10:00:06',
            '2023-01-01 10:00:07',
            '2023-01-01 10:00:08',
            '2023-01-01 10:00:09'
        ])
        data = pd.DataFrame({
            'Date': dates,
            'SessionTime': [
                pd.Timedelta(seconds=0),
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=3),
                pd.Timedelta(seconds=4),
                pd.Timedelta(seconds=5),
                pd.Timedelta(seconds=6),
                pd.Timedelta(seconds=7),
                pd.Timedelta(seconds=8),
                pd.Timedelta(seconds=9)
            ],
            'Speed': [100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 190.0]
        })
        return core.Telemetry(data, session=session)

    def test_slice_by_lap_with_single_lap(self):
        """Test slice_by_lap with a single Lap object"""
        session = self._create_mock_session()
        telemetry = self._create_telemetry(session)

        # Create a single Lap with required fields
        lap_data = pd.Series({
            'DriverNumber': '44',
            'LapStartTime': pd.Timedelta(seconds=2),
            'Time': pd.Timedelta(seconds=5)
        })
        lap = core.Lap(lap_data)
        lap.session = session

        # Mock slice_by_time to verify it's called correctly
        with patch.object(telemetry, 'slice_by_time') as mock_slice:
            mock_slice.return_value = core.Telemetry(pd.DataFrame(), session=session)
            result = telemetry.slice_by_lap(lap)

            # Verify slice_by_time was called with correct parameters
            mock_slice.assert_called_once_with(
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=5),
                0,
                'both',
                False
            )

    def test_slice_by_lap_with_multiple_laps_same_driver(self):
        """Test slice_by_lap with multiple laps from same driver"""
        session = self._create_mock_session()
        telemetry = self._create_telemetry(session)

        # Create multiple laps with same driver
        laps_data = pd.DataFrame({
            'DriverNumber': ['44', '44', '44'],
            'LapStartTime': [
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=4),
                pd.Timedelta(seconds=7)
            ],
            'Time': [
                pd.Timedelta(seconds=3),
                pd.Timedelta(seconds=6),
                pd.Timedelta(seconds=9)
            ]
        })
        laps = core.Laps(laps_data, session=session)

        # Mock slice_by_time to verify it's called correctly
        with patch.object(telemetry, 'slice_by_time') as mock_slice:
            mock_slice.return_value = core.Telemetry(pd.DataFrame(), session=session)
            result = telemetry.slice_by_lap(laps)

            # Verify slice_by_time was called with min/max times
            mock_slice.assert_called_once_with(
                pd.Timedelta(seconds=1),  # min LapStartTime
                pd.Timedelta(seconds=9),  # max Time
                0,
                'both',
                False
            )

    def test_slice_by_lap_multiple_laps_missing_driver_number(self):
        """Test slice_by_lap raises ValueError when Laps missing DriverNumber"""
        session = self._create_mock_session()
        telemetry = self._create_telemetry(session)

        # Create multiple laps without DriverNumber column
        laps_data = pd.DataFrame({
            'LapStartTime': [
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=4)
            ],
            'Time': [
                pd.Timedelta(seconds=3),
                pd.Timedelta(seconds=6)
            ]
        })
        laps = core.Laps(laps_data, session=session)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Laps is missing 'DriverNumber'"):
            telemetry.slice_by_lap(laps)

    def test_slice_by_lap_multiple_laps_multiple_drivers(self):
        """Test slice_by_lap raises ValueError with laps from multiple drivers"""
        session = self._create_mock_session()
        telemetry = self._create_telemetry(session)

        # Create multiple laps with different drivers
        laps_data = pd.DataFrame({
            'DriverNumber': ['44', '77', '44'],
            'LapStartTime': [
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=4),
                pd.Timedelta(seconds=7)
            ],
            'Time': [
                pd.Timedelta(seconds=3),
                pd.Timedelta(seconds=6),
                pd.Timedelta(seconds=9)
            ]
        })
        laps = core.Laps(laps_data, session=session)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Cannot create telemetry for multiple drivers"):
            telemetry.slice_by_lap(laps)

    def test_slice_by_lap_single_lap_in_laps_object(self):
        """Test slice_by_lap with Laps object containing single lap"""
        session = self._create_mock_session()
        telemetry = self._create_telemetry(session)

        # Create Laps with only one lap
        laps_data = pd.DataFrame({
            'DriverNumber': ['44'],
            'LapStartTime': [pd.Timedelta(seconds=2)],
            'Time': [pd.Timedelta(seconds=5)]
        })
        laps = core.Laps(laps_data, session=session)

        # Mock slice_by_time to verify it's called correctly
        with patch.object(telemetry, 'slice_by_time') as mock_slice:
            mock_slice.return_value = core.Telemetry(pd.DataFrame(), session=session)
            result = telemetry.slice_by_lap(laps)

            # Should handle as single lap
            mock_slice.assert_called_once_with(
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=5),
                0,
                'both',
                False
            )

    def test_slice_by_lap_single_lap_missing_driver_number(self):
        """Test slice_by_lap raises ValueError when single Lap missing DriverNumber"""
        session = self._create_mock_session()
        telemetry = self._create_telemetry(session)

        # Create a single Lap without DriverNumber
        lap_data = pd.Series({
            'LapStartTime': pd.Timedelta(seconds=2),
            'Time': pd.Timedelta(seconds=5)
        })
        lap = core.Lap(lap_data)
        lap.session = session

        # Should raise ValueError
        with pytest.raises(ValueError, match="Lap is missing 'DriverNumber'"):
            telemetry.slice_by_lap(lap)

    def test_slice_by_lap_invalid_type(self):
        """Test slice_by_lap raises TypeError for invalid ref_laps type"""
        session = self._create_mock_session()
        telemetry = self._create_telemetry(session)

        # Pass invalid type (not Lap or Laps)
        with pytest.raises(TypeError, match="Attribute 'ref_laps' needs to be an instance"):
            telemetry.slice_by_lap("invalid")

        with pytest.raises(TypeError, match="Attribute 'ref_laps' needs to be an instance"):
            telemetry.slice_by_lap(123)

        with pytest.raises(TypeError, match="Attribute 'ref_laps' needs to be an instance"):
            telemetry.slice_by_lap(pd.DataFrame())

    def test_slice_by_lap_with_padding_parameters(self):
        """Test slice_by_lap passes padding parameters correctly"""
        session = self._create_mock_session()
        telemetry = self._create_telemetry(session)

        # Create a single Lap
        lap_data = pd.Series({
            'DriverNumber': '44',
            'LapStartTime': pd.Timedelta(seconds=2),
            'Time': pd.Timedelta(seconds=5)
        })
        lap = core.Lap(lap_data)
        lap.session = session

        # Test with padding parameters
        with patch.object(telemetry, 'slice_by_time') as mock_slice:
            mock_slice.return_value = core.Telemetry(pd.DataFrame(), session=session)
            result = telemetry.slice_by_lap(
                lap,
                pad=2,
                pad_side='before',
                interpolate_edges=True
            )

            # Verify parameters are passed through
            mock_slice.assert_called_once_with(
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=5),
                2,
                'before',
                True
            )

    def test_slice_by_lap_returns_telemetry(self):
        """Test slice_by_lap returns Telemetry object"""
        session = self._create_mock_session()
        telemetry = self._create_telemetry(session)

        # Create a single Lap
        lap_data = pd.Series({
            'DriverNumber': '44',
            'LapStartTime': pd.Timedelta(seconds=2),
            'Time': pd.Timedelta(seconds=5)
        })
        lap = core.Lap(lap_data)
        lap.session = session

        # Mock slice_by_time to return a real Telemetry object
        expected_result = core.Telemetry(pd.DataFrame({'Speed': [120.0]}), session=session)
        with patch.object(telemetry, 'slice_by_time', return_value=expected_result):
            result = telemetry.slice_by_lap(lap)

            # Verify result is Telemetry
            assert isinstance(result, core.Telemetry)
            assert result is expected_result
