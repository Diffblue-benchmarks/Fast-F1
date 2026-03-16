"""Tests for Session._load_total_lap_count method"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime

from fastf1 import core


class TestSessionLoadTotalLapCount:
    """Tests for Session._load_total_lap_count method"""

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

    @patch('fastf1._api.lap_count')
    def test_load_total_lap_count_success_with_valid_data(self, mock_lap_count):
        """Test _load_total_lap_count successfully loads lap count (lines 2108-2115)"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Mock lap_count to return valid data
        mock_lap_count.return_value = {
            'TotalLaps': [50, 50, 50]
        }

        session._load_total_lap_count()

        # Verify api.lap_count was called (line 2109)
        mock_lap_count.assert_called_once_with(session.api_path, livedata=None)
        # Verify _total_laps was set to the last non-None value (line 2115)
        assert session._total_laps == 50

    @patch('fastf1._api.lap_count')
    def test_load_total_lap_count_with_none_values(self, mock_lap_count):
        """Test _load_total_lap_count handles None values in lap count (lines 2113-2115)"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Mock lap_count with None values mixed in
        mock_lap_count.return_value = {
            'TotalLaps': [None, 50, None, 52, None]
        }

        session._load_total_lap_count()

        # Verify _total_laps was set to last non-None value (line 2115)
        # The iteration should set it to 50, then to 52
        assert session._total_laps == 52

    @patch('fastf1._api.lap_count')
    def test_load_total_lap_count_with_all_none_values(self, mock_lap_count):
        """Test _load_total_lap_count when all lap counts are None (line 2113-2114)"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Set initial value to verify it doesn't get overwritten
        session._total_laps = 100

        # Mock lap_count with all None values
        mock_lap_count.return_value = {
            'TotalLaps': [None, None, None]
        }

        session._load_total_lap_count()

        # Verify _total_laps was not modified (line 2114 condition never True)
        assert session._total_laps == 100

    @patch('fastf1._api.lap_count')
    def test_load_total_lap_count_with_index_error(self, mock_lap_count, caplog):
        """Test _load_total_lap_count handles IndexError (lines 2116-2118)"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Mock lap_count to raise IndexError
        mock_lap_count.side_effect = IndexError("List index out of range")

        session._load_total_lap_count()

        # Verify _total_laps is set to None (line 2117)
        assert session._total_laps is None
        # Verify warning was logged (line 2118)
        assert any("No lap count data for this session" in record.message
                   for record in caplog.records)

    @patch('fastf1._api.lap_count')
    def test_load_total_lap_count_with_empty_total_laps(self, mock_lap_count):
        """Test _load_total_lap_count when TotalLaps is empty (line 2113)"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Set initial value
        session._total_laps = 100

        # Mock lap_count with empty TotalLaps list
        mock_lap_count.return_value = {
            'TotalLaps': []
        }

        session._load_total_lap_count()

        # Verify _total_laps was not modified (loop never executes)
        assert session._total_laps == 100

    @patch('fastf1._api.lap_count')
    def test_load_total_lap_count_non_race_like_session(self, mock_lap_count):
        """Test _load_total_lap_count for non-race-like sessions (line 2120)"""
        mock_event = self._create_mock_event()
        # 'Practice 1' is not in _RACE_LIKE_SESSIONS
        session = core.Session(event=mock_event, session_name='Practice 1')

        session._load_total_lap_count()

        # Verify api.lap_count was not called
        mock_lap_count.assert_not_called()
        # Verify _total_laps is set to None (line 2120)
        assert session._total_laps is None

    @patch('fastf1._api.lap_count')
    def test_load_total_lap_count_with_livedata_parameter(self, mock_lap_count):
        """Test _load_total_lap_count passes livedata parameter (line 2109)"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        mock_lap_count.return_value = {
            'TotalLaps': [50]
        }

        # Create mock livedata
        mock_livedata = Mock()

        session._load_total_lap_count(livedata=mock_livedata)

        # Verify api.lap_count was called with livedata parameter
        mock_lap_count.assert_called_once_with(session.api_path, livedata=mock_livedata)
        assert session._total_laps == 50

    @patch('fastf1._api.lap_count')
    def test_load_total_lap_count_sprint_session(self, mock_lap_count):
        """Test _load_total_lap_count for Sprint sessions (line 2107)"""
        mock_event = self._create_mock_event()
        # 'Sprint' is in _RACE_LIKE_SESSIONS
        session = core.Session(event=mock_event, session_name='Sprint')

        mock_lap_count.return_value = {
            'TotalLaps': [25]
        }

        session._load_total_lap_count()

        # Verify lap count was loaded for Sprint session
        mock_lap_count.assert_called_once()
        assert session._total_laps == 25

    @patch('fastf1._api.lap_count')
    def test_load_total_lap_count_sprint_qualifying_session(self, mock_lap_count):
        """Test _load_total_lap_count for Sprint Qualifying sessions (line 2107)"""
        mock_event = self._create_mock_event(year=2023)  # Sprint Qualifying exists in 2023+
        # 'Sprint Qualifying' is in _RACE_LIKE_SESSIONS for 2023+
        session = core.Session(event=mock_event, session_name='Sprint Qualifying')

        mock_lap_count.return_value = {
            'TotalLaps': [12]
        }

        session._load_total_lap_count()

        # Verify lap count was loaded for Sprint Qualifying session
        mock_lap_count.assert_called_once()
        assert session._total_laps == 12
