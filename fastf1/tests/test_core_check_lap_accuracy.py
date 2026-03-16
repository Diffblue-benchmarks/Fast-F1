"""Tests for Session._check_lap_accuracy method"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock
from datetime import datetime

from fastf1 import core


class TestSessionCheckLapAccuracy:
    """Tests for Session._check_lap_accuracy method"""

    def _create_mock_event(self, year=2023):
        """Create a mock Event object for testing"""
        mock_event = Mock()
        mock_event.year = year
        mock_event.RoundNumber = 5
        mock_event.EventName = 'Monaco Grand Prix'
        mock_event.__getitem__ = Mock(side_effect=lambda key: {
            'EventName': 'Monaco Grand Prix',
            'EventDate': pd.Timestamp(datetime(year, 5, 20))
        }[key])
        mock_event.get_session_date = Mock(return_value=pd.Timestamp(datetime(year, 5, 20)))
        return mock_event

    def test_check_lap_accuracy_with_sector_time_mismatch(self, caplog):
        """Test _check_lap_accuracy when sector times don't sum to lap time (line 2268)"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Create lap data where sector times don't sum to lap time
        laps_data = pd.DataFrame({
            'DriverNumber': ['44'],
            'PitInTime': [pd.NaT],
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [False],
            'TrackStatus': ['1'],
            'LapTime': [pd.Timedelta(seconds=90)],
            'Sector1Time': [pd.Timedelta(seconds=30)],
            'Sector2Time': [pd.Timedelta(seconds=30)],
            'Sector3Time': [pd.Timedelta(seconds=25)],  # Sum is 85, not 90
            'Time': [pd.Timedelta(seconds=90)],
            'IsAccurate': [False],
        })
        session._laps = core.Laps(laps_data, session=session)

        # Create results data with driver number
        results_data = pd.DataFrame({'DriverNumber': ['44']})
        session._results = core.SessionResults(results_data)

        session._check_lap_accuracy()

        # Verify lap is marked as inaccurate
        assert session._laps['IsAccurate'].iloc[0] == False
        # Verify warning was logged for integrity error (line 2323)
        assert any("integrity check failed" in record.message.lower()
                   for record in caplog.records)

    def test_check_lap_accuracy_with_time_difference_mismatch(self, caplog):
        """Test _check_lap_accuracy when time difference doesn't match lap time (line 2295)"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Create two laps where second lap's time difference doesn't match lap time
        laps_data = pd.DataFrame({
            'DriverNumber': ['44', '44'],
            'PitInTime': [pd.NaT, pd.NaT],
            'PitOutTime': [pd.NaT, pd.NaT],
            'FastF1Generated': [False, False],
            'TrackStatus': ['1', '1'],
            'LapTime': [pd.Timedelta(seconds=90), pd.Timedelta(seconds=100)],
            'Sector1Time': [pd.Timedelta(seconds=30), pd.Timedelta(seconds=33)],
            'Sector2Time': [pd.Timedelta(seconds=30), pd.Timedelta(seconds=33)],
            'Sector3Time': [pd.Timedelta(seconds=30), pd.Timedelta(seconds=34)],
            'Time': [pd.Timedelta(seconds=90), pd.Timedelta(seconds=180)],  # Diff is 90, not 100
            'IsAccurate': [False, False],
        })
        session._laps = core.Laps(laps_data, session=session)

        # Create results data with driver number
        results_data = pd.DataFrame({'DriverNumber': ['44']})
        session._results = core.SessionResults(results_data)

        session._check_lap_accuracy()

        # Second lap should be marked as inaccurate
        assert session._laps['IsAccurate'].iloc[1] == False
        # Verify warning was logged for integrity error
        assert any("integrity check failed" in record.message.lower()
                   for record in caplog.records)

    def test_check_lap_accuracy_with_no_laps_for_driver(self, caplog):
        """Test _check_lap_accuracy when a driver has no laps (lines 2312-2314)"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Create empty laps dataframe
        laps_data = pd.DataFrame({
            'DriverNumber': pd.Series([], dtype=str),
            'PitInTime': pd.Series([], dtype='datetime64[ns]'),
            'PitOutTime': pd.Series([], dtype='datetime64[ns]'),
            'FastF1Generated': pd.Series([], dtype=bool),
            'TrackStatus': pd.Series([], dtype=str),
            'LapTime': pd.Series([], dtype='timedelta64[ns]'),
            'Sector1Time': pd.Series([], dtype='timedelta64[ns]'),
            'Sector2Time': pd.Series([], dtype='timedelta64[ns]'),
            'Sector3Time': pd.Series([], dtype='timedelta64[ns]'),
            'Time': pd.Series([], dtype='timedelta64[ns]'),
            'IsAccurate': pd.Series([], dtype=bool),
        })
        session._laps = core.Laps(laps_data, session=session)

        # Create results data with driver who has no laps
        results_data = pd.DataFrame({'DriverNumber': ['44']})
        session._results = core.SessionResults(results_data)

        session._check_lap_accuracy()

        # Verify warning was logged about all laps marked as inaccurate
        assert any("all laps marked as inaccurate" in record.message.lower()
                   for record in caplog.records)

    def test_check_lap_accuracy_integrity_error_increments(self, caplog):
        """Test _check_lap_accuracy increments integrity_errors (line 2301)"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Create multiple laps with integrity issues
        laps_data = pd.DataFrame({
            'DriverNumber': ['44', '44', '44'],
            'PitInTime': [pd.NaT, pd.NaT, pd.NaT],
            'PitOutTime': [pd.NaT, pd.NaT, pd.NaT],
            'FastF1Generated': [False, False, False],
            'TrackStatus': ['1', '1', '1'],
            'LapTime': [pd.Timedelta(seconds=90), pd.Timedelta(seconds=90), pd.Timedelta(seconds=90)],
            'Sector1Time': [pd.Timedelta(seconds=30), pd.Timedelta(seconds=30), pd.Timedelta(seconds=30)],
            'Sector2Time': [pd.Timedelta(seconds=30), pd.Timedelta(seconds=30), pd.Timedelta(seconds=30)],
            'Sector3Time': [pd.Timedelta(seconds=25), pd.Timedelta(seconds=25), pd.Timedelta(seconds=25)],  # All incorrect
            'Time': [pd.Timedelta(seconds=90), pd.Timedelta(seconds=180), pd.Timedelta(seconds=270)],
            'IsAccurate': [False, False, False],
        })
        session._laps = core.Laps(laps_data, session=session)

        # Create results data with driver number
        results_data = pd.DataFrame({'DriverNumber': ['44']})
        session._results = core.SessionResults(results_data)

        session._check_lap_accuracy()

        # Verify all laps are marked as inaccurate
        assert all(session._laps['IsAccurate'] == False)
        # Verify warning mentions 3 laps failed (line 2323)
        assert any("3 lap(s)" in record.message for record in caplog.records)

    def test_check_lap_accuracy_accurate_lap(self):
        """Test _check_lap_accuracy with accurate lap data"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Create lap data that passes all checks
        laps_data = pd.DataFrame({
            'DriverNumber': ['44'],
            'PitInTime': [pd.NaT],
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [False],
            'TrackStatus': ['1'],
            'LapTime': [pd.Timedelta(seconds=90)],
            'Sector1Time': [pd.Timedelta(seconds=30)],
            'Sector2Time': [pd.Timedelta(seconds=30)],
            'Sector3Time': [pd.Timedelta(seconds=30)],
            'Time': [pd.Timedelta(seconds=90)],
            'IsAccurate': [False],
        })
        session._laps = core.Laps(laps_data, session=session)

        # Create results data with driver number
        results_data = pd.DataFrame({'DriverNumber': ['44']})
        session._results = core.SessionResults(results_data)

        session._check_lap_accuracy()

        # Verify lap is marked as accurate
        assert session._laps['IsAccurate'].iloc[0] == True

    def test_check_lap_accuracy_two_accurate_laps(self):
        """Test _check_lap_accuracy with two consecutive accurate laps"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Create two laps that pass all checks
        laps_data = pd.DataFrame({
            'DriverNumber': ['44', '44'],
            'PitInTime': [pd.NaT, pd.NaT],
            'PitOutTime': [pd.NaT, pd.NaT],
            'FastF1Generated': [False, False],
            'TrackStatus': ['1', '1'],
            'LapTime': [pd.Timedelta(seconds=90), pd.Timedelta(seconds=91)],
            'Sector1Time': [pd.Timedelta(seconds=30), pd.Timedelta(seconds=30)],
            'Sector2Time': [pd.Timedelta(seconds=30), pd.Timedelta(seconds=30.5)],
            'Sector3Time': [pd.Timedelta(seconds=30), pd.Timedelta(seconds=30.5)],
            'Time': [pd.Timedelta(seconds=90), pd.Timedelta(seconds=181)],
            'IsAccurate': [False, False],
        })
        session._laps = core.Laps(laps_data, session=session)

        # Create results data with driver number
        results_data = pd.DataFrame({'DriverNumber': ['44']})
        session._results = core.SessionResults(results_data)

        session._check_lap_accuracy()

        # Verify both laps are marked as accurate
        assert all(session._laps['IsAccurate'] == True)

    def test_check_lap_accuracy_multiple_drivers(self, caplog):
        """Test _check_lap_accuracy with multiple drivers"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Create laps for two drivers - one accurate, one with error
        laps_data = pd.DataFrame({
            'DriverNumber': ['44', '77'],
            'PitInTime': [pd.NaT, pd.NaT],
            'PitOutTime': [pd.NaT, pd.NaT],
            'FastF1Generated': [False, False],
            'TrackStatus': ['1', '1'],
            'LapTime': [pd.Timedelta(seconds=90), pd.Timedelta(seconds=90)],
            'Sector1Time': [pd.Timedelta(seconds=30), pd.Timedelta(seconds=30)],
            'Sector2Time': [pd.Timedelta(seconds=30), pd.Timedelta(seconds=30)],
            'Sector3Time': [pd.Timedelta(seconds=30), pd.Timedelta(seconds=25)],  # Driver 77 has error
            'Time': [pd.Timedelta(seconds=90), pd.Timedelta(seconds=90)],
            'IsAccurate': [False, False],
        })
        session._laps = core.Laps(laps_data, session=session)

        # Create results data with both drivers
        results_data = pd.DataFrame({'DriverNumber': ['44', '77']})
        session._results = core.SessionResults(results_data)

        session._check_lap_accuracy()

        # Verify driver 44 is accurate, driver 77 is not
        assert session._laps[session._laps['DriverNumber'] == '44']['IsAccurate'].iloc[0] == True
        assert session._laps[session._laps['DriverNumber'] == '77']['IsAccurate'].iloc[0] == False
        # Verify warning logged for driver 77
        assert any("77" in record.message and "integrity check failed" in record.message.lower()
                   for record in caplog.records)
