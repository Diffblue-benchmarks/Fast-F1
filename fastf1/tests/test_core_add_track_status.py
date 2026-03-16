"""Tests for Telemetry.add_track_status method"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

from fastf1 import core


class TestTelemetryAddTrackStatus:
    """Tests for Telemetry.add_track_status method"""

    def _create_mock_session_with_track_status(self, track_status_times, track_status_values):
        """Helper to create a mock session with track status data"""
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')
        session.track_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=t) for t in track_status_times],
            'Status': track_status_values
        })
        return session

    def _create_telemetry_with_dates(self, session, dates, session_times):
        """Helper to create telemetry with dates"""
        data = pd.DataFrame({
            'SessionTime': [pd.Timedelta(seconds=s) for s in session_times],
            'Date': dates,
            'Time': [pd.Timedelta(seconds=s) for s in session_times]
        })
        return core.Telemetry(data, session=session, driver='1')

    def test_add_track_status_column_doesnt_exist(self):
        """Test add_track_status when TrackStatus column doesn't exist"""
        # Create mock session with track status data
        # First event at t=-0.5 to ensure all telemetry is covered
        track_status_times = [-0.5, 10.5, 20.5]
        track_status_values = ['1', '2', '4']
        session = self._create_mock_session_with_track_status(
            track_status_times, track_status_values
        )

        # Create telemetry data with dates spanning the track status events
        # Starting at t=0, samples at 0,1,2,...,24 seconds
        dates = pd.date_range('2023-01-01 10:00:00', periods=25, freq='1s')
        session_times = list(range(25))

        tel = self._create_telemetry_with_dates(session, dates, session_times)

        # Call add_track_status
        result = tel.add_track_status()

        # Verify TrackStatus column was added
        assert 'TrackStatus' in result.columns
        assert len(result) == 25

        # Verify track status values are correctly assigned
        # Event times are at -0.5, 10.5, 20.5 seconds
        # Samples 0-10 should have status '1' (t=-0.5 <= 0-10 < 10.5)
        assert all(result['TrackStatus'].iloc[0:11] == '1')
        # Samples 11-20 should have status '2' (t=10.5 <= 11-20 < 20.5)
        assert all(result['TrackStatus'].iloc[11:21] == '2')
        # Samples 21-24 should have status '4' (t > 20.5)
        assert all(result['TrackStatus'].iloc[21:25] == '4')

    def test_add_track_status_column_exists_drop_existing_true(self):
        """Test add_track_status when TrackStatus exists and drop_existing=True"""
        # Create mock session with track status data
        # First event at t=-0.5 to ensure all telemetry is covered
        track_status_times = [-0.5, 15.5]
        track_status_values = ['1', '2']
        session = self._create_mock_session_with_track_status(
            track_status_times, track_status_values
        )

        # Create telemetry data with existing TrackStatus column
        dates = pd.date_range('2023-01-01 10:00:00', periods=20, freq='1s')
        session_times = list(range(20))

        tel = self._create_telemetry_with_dates(session, dates, session_times)

        # Add existing TrackStatus column with old values
        tel['TrackStatus'] = ['0'] * 20

        # Call add_track_status with drop_existing=True
        result = tel.add_track_status(drop_existing=True)

        # Verify TrackStatus column was recalculated
        assert 'TrackStatus' in result.columns
        assert len(result) == 20

        # Verify old values were replaced
        # Event times are at -0.5, 15.5 seconds
        assert all(result['TrackStatus'].iloc[0:16] == '1')
        assert all(result['TrackStatus'].iloc[16:20] == '2')

    def test_add_track_status_column_exists_drop_existing_false(self):
        """Test add_track_status when TrackStatus exists and drop_existing=False"""
        # Create mock session
        track_status_times = [0, 10]
        track_status_values = ['1', '2']
        session = self._create_mock_session_with_track_status(
            track_status_times, track_status_values
        )

        # Create telemetry data with existing TrackStatus column
        dates = pd.date_range('2023-01-01 10:00:00', periods=15, freq='1s')
        session_times = list(range(15))

        tel = self._create_telemetry_with_dates(session, dates, session_times)

        # Add existing TrackStatus column with values
        original_values = ['9'] * 15
        tel['TrackStatus'] = original_values

        # Call add_track_status with drop_existing=False
        result = tel.add_track_status(drop_existing=False)

        # Verify it returned self without recalculation
        assert result is tel
        assert all(result['TrackStatus'] == '9')

    def test_add_track_status_with_multiple_track_status_events(self):
        """Test add_track_status with multiple track status transitions"""
        # Create mock session with multiple track status changes
        # First event at t=-0.5 to ensure all telemetry is covered
        track_status_times = [-0.5, 5.5, 10.5, 15.5, 20.5]
        track_status_values = ['1', '2', '4', '5', '1']
        session = self._create_mock_session_with_track_status(
            track_status_times, track_status_values
        )

        # Create telemetry data spanning all events
        dates = pd.date_range('2023-01-01 10:00:00', periods=25, freq='1s')
        session_times = list(range(25))

        tel = self._create_telemetry_with_dates(session, dates, session_times)

        # Call add_track_status
        result = tel.add_track_status()

        # Verify TrackStatus column was added
        assert 'TrackStatus' in result.columns
        assert len(result) == 25

        # Verify track status values for each period
        # Event times are at -0.5, 5.5, 10.5, 15.5, 20.5 seconds
        assert all(result['TrackStatus'].iloc[0:6] == '1')
        assert all(result['TrackStatus'].iloc[6:11] == '2')
        assert all(result['TrackStatus'].iloc[11:16] == '4')
        assert all(result['TrackStatus'].iloc[16:21] == '5')
        assert all(result['TrackStatus'].iloc[21:25] == '1')

    def test_add_track_status_with_sparse_telemetry(self):
        """Test add_track_status when telemetry has gaps between track status events"""
        # Create mock session
        # First event at t=-1 to ensure all telemetry is covered
        track_status_times = [-1, 21, 41]
        track_status_values = ['1', '2', '4']
        session = self._create_mock_session_with_track_status(
            track_status_times, track_status_values
        )

        # Create sparse telemetry data (every 5 seconds)
        dates = pd.date_range('2023-01-01 10:00:00', periods=10, freq='5s')
        session_times = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45]

        tel = self._create_telemetry_with_dates(session, dates, session_times)

        # Call add_track_status
        result = tel.add_track_status()

        # Verify TrackStatus column was added
        assert 'TrackStatus' in result.columns
        assert len(result) == 10

        # Verify track status values based on event boundaries
        # Event times are at -1, 21, 41 seconds
        # Samples at t=0,5,10,15,20 should have status '1' (-1 <= t < 21)
        assert all(result['TrackStatus'].iloc[0:5] == '1')
        # Samples at t=25,30,35,40 should have status '2' (21 <= t < 41)
        assert all(result['TrackStatus'].iloc[5:9] == '2')
        # Samples at t=45 should have status '4' (t > 41)
        assert all(result['TrackStatus'].iloc[9:10] == '4')

    def test_add_track_status_with_two_events(self):
        """Test add_track_status with minimal track status events (2 events)"""
        # Create mock session with just two track status events
        # First event at t=-0.5 to ensure all telemetry is covered
        track_status_times = [-0.5, 30.5]
        track_status_values = ['1', '4']
        session = self._create_mock_session_with_track_status(
            track_status_times, track_status_values
        )

        # Create telemetry data
        dates = pd.date_range('2023-01-01 10:00:00', periods=40, freq='1s')
        session_times = list(range(40))

        tel = self._create_telemetry_with_dates(session, dates, session_times)

        # Call add_track_status
        result = tel.add_track_status()

        # Verify TrackStatus column was added
        assert 'TrackStatus' in result.columns
        assert len(result) == 40

        # Verify track status values
        # Event times are at -0.5, 30.5 seconds
        assert all(result['TrackStatus'].iloc[0:31] == '1')
        assert all(result['TrackStatus'].iloc[31:40] == '4')

    def test_add_track_status_all_telemetry_after_last_event(self):
        """Test add_track_status when all telemetry comes after the last track status event"""
        # Create mock session
        track_status_times = [0, 10]
        track_status_values = ['1', '2']
        session = self._create_mock_session_with_track_status(
            track_status_times, track_status_values
        )

        # Create telemetry data starting after all track status events
        dates = pd.date_range('2023-01-01 10:00:15', periods=10, freq='1s')
        session_times = list(range(15, 25))

        tel = self._create_telemetry_with_dates(session, dates, session_times)

        # Call add_track_status
        result = tel.add_track_status()

        # Verify TrackStatus column was added
        assert 'TrackStatus' in result.columns
        assert len(result) == 10

        # All samples should have the last track status value
        assert all(result['TrackStatus'] == '2')
