"""Tests for Session._set_laps_deleted_from_rcm method"""
import pytest
import pandas as pd
from unittest.mock import Mock
from datetime import datetime

from fastf1 import core


class TestSessionSetLapsDeletedFromRcm:
    """Tests for Session._set_laps_deleted_from_rcm method"""

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

    def test_set_laps_deleted_from_rcm_without_laps_attribute(self):
        """Test _set_laps_deleted_from_rcm returns early when _laps attribute is missing (line 1825)"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Create race control messages but no _laps attribute
        rcm_data = pd.DataFrame({
            'Message': ['CAR 44 LAP TIME 1:30.123 DELETED - TRACK LIMITS']
        })
        session._race_control_messages = rcm_data

        # Should return early without error
        session._set_laps_deleted_from_rcm()

        # Verify method completed without setting any attributes
        assert not hasattr(session, '_laps') or session._laps is None

    def test_set_laps_deleted_from_rcm_without_rcm_attribute(self):
        """Test _set_laps_deleted_from_rcm returns early when _race_control_messages is missing (line 1825)"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Create laps but no race control messages
        laps_data = pd.DataFrame({
            'DriverNumber': ['44'],
            'LapTime': [pd.Timedelta(seconds=90)],
            'Deleted': [False],
            'IsPersonalBest': [False],
            'DeletedReason': [None]
        })
        session._laps = core.Laps(laps_data, session=session)

        # Should return early without error
        session._set_laps_deleted_from_rcm()

        # Verify laps were not modified
        assert session._laps['Deleted'].iloc[0] == False

    def test_set_laps_deleted_from_rcm_with_reinstated_lap(self):
        """Test _set_laps_deleted_from_rcm handles reinstated laps (lines 1846-1848, 1858)"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Create laps data
        laps_data = pd.DataFrame({
            'DriverNumber': ['44', '44'],
            'LapTime': [pd.Timedelta(minutes=1, seconds=30, milliseconds=123),
                        pd.Timedelta(minutes=1, seconds=31, milliseconds=456)],
            'Deleted': [False, False],
            'IsPersonalBest': [True, False],
            'DeletedReason': [None, None]
        })
        session._laps = core.Laps(laps_data, session=session)

        # Create race control messages: deletion followed by reinstatement
        rcm_data = pd.DataFrame({
            'Message': [
                'CAR 44 LAP TIME 1:30.123 DELETED - TRACK LIMITS AT TURN 1',
                'CAR 44 LAP TIME 1:30.123 REINSTATED - DECISION OVERTURNED'
            ]
        })
        session._race_control_messages = rcm_data

        session._set_laps_deleted_from_rcm()

        # Verify lap was NOT marked as deleted (because it was reinstated)
        assert session._laps['Deleted'].iloc[0] == False
        # Verify IsPersonalBest was NOT changed (lap not deleted)
        assert session._laps['IsPersonalBest'].iloc[0] == True
        # Verify DeletedReason is None
        assert pd.isna(session._laps['DeletedReason'].iloc[0]) or session._laps['DeletedReason'].iloc[0] is None

    def test_set_laps_deleted_from_rcm_with_deleted_lap_not_reinstated(self):
        """Test _set_laps_deleted_from_rcm marks lap as deleted when not reinstated"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Create laps data
        laps_data = pd.DataFrame({
            'DriverNumber': ['44', '77'],
            'LapTime': [pd.Timedelta(minutes=1, seconds=30, milliseconds=123),
                        pd.Timedelta(minutes=1, seconds=31, milliseconds=456)],
            'Deleted': [False, False],
            'IsPersonalBest': [True, False],
            'DeletedReason': [None, None]
        })
        session._laps = core.Laps(laps_data, session=session)

        # Create race control messages with deletion only (no reinstatement)
        rcm_data = pd.DataFrame({
            'Message': [
                'CAR 44 LAP TIME 1:30.123 DELETED - TRACK LIMITS AT TURN 1'
            ]
        })
        session._race_control_messages = rcm_data

        session._set_laps_deleted_from_rcm()

        # Verify lap was marked as deleted
        assert session._laps['Deleted'].iloc[0] == True
        # Verify IsPersonalBest was set to False
        assert session._laps['IsPersonalBest'].iloc[0] == False
        # Verify DeletedReason contains text (timestamp removed)
        assert 'TRACK LIMITS AT TURN 1' in session._laps['DeletedReason'].iloc[0]

    def test_set_laps_deleted_from_rcm_multiple_reinstated_laps(self):
        """Test _set_laps_deleted_from_rcm with multiple reinstated laps (lines 1846-1848)"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Create laps data for two drivers
        laps_data = pd.DataFrame({
            'DriverNumber': ['44', '77', '33'],
            'LapTime': [pd.Timedelta(minutes=1, seconds=30, milliseconds=123),
                        pd.Timedelta(minutes=1, seconds=31, milliseconds=456),
                        pd.Timedelta(minutes=1, seconds=32, milliseconds=789)],
            'Deleted': [False, False, False],
            'IsPersonalBest': [True, True, True],
            'DeletedReason': [None, None, None]
        })
        session._laps = core.Laps(laps_data, session=session)

        # Create race control messages with multiple deletions and reinstatements
        rcm_data = pd.DataFrame({
            'Message': [
                'CAR 44 LAP TIME 1:30.123 DELETED - TRACK LIMITS',
                'CAR 77 LAP TIME 1:31.456 DELETED - TRACK LIMITS',
                'CAR 33 LAP TIME 1:32.789 DELETED - TRACK LIMITS',
                'CAR 44 LAP TIME 1:30.123 REINSTATED - DECISION OVERTURNED',
                'CAR 77 LAP TIME 1:31.456 REINSTATED - DECISION OVERTURNED'
            ]
        })
        session._race_control_messages = rcm_data

        session._set_laps_deleted_from_rcm()

        # Verify cars 44 and 77 were NOT deleted (reinstated)
        assert session._laps[session._laps['DriverNumber'] == '44']['Deleted'].iloc[0] == False
        assert session._laps[session._laps['DriverNumber'] == '77']['Deleted'].iloc[0] == False
        # Verify car 33 WAS deleted (not reinstated)
        assert session._laps[session._laps['DriverNumber'] == '33']['Deleted'].iloc[0] == True
        # Verify IsPersonalBest maintained for reinstated laps
        assert session._laps[session._laps['DriverNumber'] == '44']['IsPersonalBest'].iloc[0] == True
        assert session._laps[session._laps['DriverNumber'] == '77']['IsPersonalBest'].iloc[0] == True
        # Verify IsPersonalBest cleared for deleted lap
        assert session._laps[session._laps['DriverNumber'] == '33']['IsPersonalBest'].iloc[0] == False

    def test_set_laps_deleted_from_rcm_with_no_matching_messages(self):
        """Test _set_laps_deleted_from_rcm when no RCM messages match deletion pattern"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        # Create laps data
        laps_data = pd.DataFrame({
            'DriverNumber': ['44'],
            'LapTime': [pd.Timedelta(minutes=1, seconds=30, milliseconds=123)],
            'Deleted': [False],
            'IsPersonalBest': [True],
            'DeletedReason': [None]
        })
        session._laps = core.Laps(laps_data, session=session)

        # Create race control messages that don't match the deletion pattern
        rcm_data = pd.DataFrame({
            'Message': [
                'SAFETY CAR DEPLOYED',
                'RACE SUSPENDED'
            ]
        })
        session._race_control_messages = rcm_data

        session._set_laps_deleted_from_rcm()

        # Verify all laps remain with Deleted = False (default set by method)
        assert session._laps['Deleted'].iloc[0] == False
        assert session._laps['IsPersonalBest'].iloc[0] == True
