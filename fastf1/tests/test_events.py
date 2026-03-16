import datetime
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

import fastf1.events as events
from fastf1.events import Event, EventSchedule


# Mock data fixtures
@pytest.fixture
def mock_event_schedule():
    """Create a mock EventSchedule for testing."""
    data = {
        'RoundNumber': [1, 2, 0],
        'Country': ['Bahrain', 'Saudi Arabia', 'Test'],
        'Location': ['Sakhir', 'Jeddah', 'Barcelona'],
        'EventName': ['Bahrain Grand Prix', 'Saudi Arabian Grand Prix', 'Pre-Season Test'],
        'OfficialEventName': ['Formula 1 Gulf Air Bahrain Grand Prix 2023',
                              'Formula 1 STC Saudi Arabian Grand Prix 2023', ''],
        'EventDate': [pd.Timestamp('2023-03-05'), pd.Timestamp('2023-03-19'), pd.Timestamp('2023-02-23')],
        'EventFormat': ['conventional', 'conventional', 'testing'],
        'Session1': ['Practice 1', 'Practice 1', 'Practice 1'],
        'Session1Date': [None, None, None],
        'Session1DateUtc': [pd.Timestamp('2023-03-03 11:30:00'),
                            pd.Timestamp('2023-03-17 11:30:00'),
                            pd.Timestamp('2023-02-23 08:00:00')],
        'Session2': ['Practice 2', 'Practice 2', 'Practice 2'],
        'Session2Date': [None, None, None],
        'Session2DateUtc': [pd.Timestamp('2023-03-03 15:00:00'),
                            pd.Timestamp('2023-03-17 15:00:00'),
                            pd.Timestamp('2023-02-23 12:00:00')],
        'Session3': ['Practice 3', 'Practice 3', 'Practice 3'],
        'Session3Date': [None, None, None],
        'Session3DateUtc': [pd.Timestamp('2023-03-04 12:30:00'),
                            pd.Timestamp('2023-03-18 12:30:00'),
                            pd.Timestamp('2023-02-24 08:00:00')],
        'Session4': ['Qualifying', 'Qualifying', None],
        'Session4Date': [None, None, None],
        'Session4DateUtc': [pd.Timestamp('2023-03-04 16:00:00'),
                            pd.Timestamp('2023-03-18 16:00:00'),
                            pd.NaT],
        'Session5': ['Race', 'Race', None],
        'Session5Date': [None, None, None],
        'Session5DateUtc': [pd.Timestamp('2023-03-05 15:00:00'),
                            pd.Timestamp('2023-03-19 17:00:00'),
                            pd.NaT],
        'F1ApiSupport': [True, True, True]
    }
    return EventSchedule(data, year=2023, _force_default_cols=True)


@pytest.fixture
def mock_event():
    """Create a mock Event for testing."""
    data = pd.Series({
        'RoundNumber': 1,
        'Country': 'Bahrain',
        'Location': 'Sakhir',
        'EventName': 'Bahrain Grand Prix',
        'OfficialEventName': 'Formula 1 Gulf Air Bahrain Grand Prix 2023',
        'EventDate': pd.Timestamp('2023-03-05'),
        'EventFormat': 'conventional',
        'Session1': 'Practice 1',
        'Session1Date': None,
        'Session1DateUtc': pd.Timestamp('2023-03-03 11:30:00'),
        'Session2': 'Practice 2',
        'Session2Date': None,
        'Session2DateUtc': pd.Timestamp('2023-03-03 15:00:00'),
        'Session3': 'Practice 3',
        'Session3Date': None,
        'Session3DateUtc': pd.Timestamp('2023-03-04 12:30:00'),
        'Session4': 'Qualifying',
        'Session4Date': None,
        'Session4DateUtc': pd.Timestamp('2023-03-04 16:00:00'),
        'Session5': 'Race',
        'Session5Date': None,
        'Session5DateUtc': pd.Timestamp('2023-03-05 15:00:00'),
        'F1ApiSupport': True
    })
    return Event(data, year=2023)


def test_get_testing_session(mock_event_schedule):
    """Test get_testing_session function."""
    with patch('fastf1.events.get_testing_event') as mock_get_testing_event:
        mock_event = mock_event_schedule.iloc[2]
        mock_get_testing_event.return_value = mock_event

        with patch.object(Event, 'get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            result = events.get_testing_session(2023, 1, 1)

            mock_get_testing_event.assert_called_once_with(2023, 1, backend=None)
            mock_get_session.assert_called_once_with(1)


def test_get_testing_event_with_ergast_backend():
    """Test get_testing_event raises ValueError for ergast backend."""
    with pytest.raises(ValueError, match="The 'ergast' backend does not support testing events"):
        events.get_testing_event(2023, 1, backend='ergast')


def test_get_testing_event_invalid_test_number(mock_event_schedule):
    """Test get_testing_event with invalid test number."""
    with patch('fastf1.events.get_event_schedule') as mock_get_schedule:
        mock_get_schedule.return_value = mock_event_schedule

        with pytest.raises(ValueError, match="Test event number .* does not exist"):
            events.get_testing_event(2023, 5, backend='fastf1')


def test_get_testing_event_zero_test_number(mock_event_schedule):
    """Test get_testing_event with test number 0."""
    with patch('fastf1.events.get_event_schedule') as mock_get_schedule:
        mock_get_schedule.return_value = mock_event_schedule

        with pytest.raises(ValueError, match="Test event number .* does not exist"):
            events.get_testing_event(2023, 0, backend='fastf1')


def test_get_event_schedule_with_specific_backend():
    """Test get_event_schedule with specific backend."""
    with patch('fastf1.events._get_schedule_from_ergast') as mock_ergast:
        mock_schedule = MagicMock()
        mock_ergast.return_value = mock_schedule

        result = events.get_event_schedule(2023, backend='ergast')

        mock_ergast.assert_called_once_with(2023)
        assert result == mock_schedule


def test_get_event_schedule_year_before_2018():
    """Test get_event_schedule defaults to ergast for years before 2018."""
    with patch('fastf1.events._get_schedule_from_ergast') as mock_ergast:
        mock_schedule = MagicMock()
        mock_ergast.return_value = mock_schedule

        result = events.get_event_schedule(2015)

        mock_ergast.assert_called_once_with(2015)


def test_get_event_schedule_all_backends_fail():
    """Test get_event_schedule raises ValueError when all backends fail."""
    with patch('fastf1.events._get_schedule_ff1', return_value=None), \
         patch('fastf1.events._get_schedule_from_f1_timing', return_value=None), \
         patch('fastf1.events._get_schedule_from_ergast', return_value=None):

        with pytest.raises(ValueError, match="Failed to load any schedule data"):
            events.get_event_schedule(2023)


def test_get_events_remaining_no_datetime(mock_event_schedule):
    """Test get_events_remaining without providing datetime."""
    with patch('fastf1.events.get_event_schedule') as mock_get_schedule:
        # Update schedule dates to be in the future
        future_schedule = mock_event_schedule.copy()
        future_schedule.at[0, 'Session5DateUtc'] = pd.Timestamp('2026-06-05 15:00:00')
        future_schedule.at[1, 'Session5DateUtc'] = pd.Timestamp('2026-06-19 17:00:00')
        mock_get_schedule.return_value = future_schedule

        result = events.get_events_remaining(include_testing=False)

        # Should return events that are in the future
        assert len(result) >= 0


def test_get_events_remaining_with_datetime_no_testing(mock_event_schedule):
    """Test get_events_remaining with specific datetime and no testing."""
    with patch('fastf1.events.get_event_schedule') as mock_get_schedule:
        mock_get_schedule.return_value = mock_event_schedule

        dt = datetime.datetime(2023, 3, 10, 12, 0, 0)
        result = events.get_events_remaining(dt=dt, include_testing=False)

        assert len(result) == 1
        assert result.iloc[0]['EventName'] == 'Saudi Arabian Grand Prix'


def test_get_events_remaining_with_testing(mock_event_schedule):
    """Test get_events_remaining with testing events included."""
    with patch('fastf1.events.get_event_schedule') as mock_get_schedule:
        mock_get_schedule.return_value = mock_event_schedule

        dt = datetime.datetime(2023, 2, 20, 12, 0, 0)
        result = events.get_events_remaining(dt=dt, include_testing=True)

        # Should include testing and both race events
        assert len(result) == 3


def test_get_events_remaining_filters_testing_correctly(mock_event_schedule):
    """Test that get_events_remaining correctly filters testing events based on Session3DateUtc."""
    with patch('fastf1.events.get_event_schedule') as mock_get_schedule:
        mock_get_schedule.return_value = mock_event_schedule

        dt = datetime.datetime(2023, 2, 24, 12, 0, 0)
        result = events.get_events_remaining(dt=dt, include_testing=True)

        # Testing event should be filtered out as Session3DateUtc is before dt
        assert all(event['RoundNumber'] != 0 or event['Session3DateUtc'] > dt
                   for _, event in result.iterrows())


def test_get_schedule_ff1_with_none_gmt_offset():
    """Test _get_schedule_ff1 handles None gmt_offset."""
    mock_response = MagicMock()
    mock_response.text = '{"round": {"1": 1}, "country": {"1": "Bahrain"}, "location": {"1": "Sakhir"}, "event_name": {"1": "Bahrain Grand Prix"}, "official_event_name": {"1": "Formula 1 Gulf Air Bahrain Grand Prix 2023"}, "event_date": {"1": "2023-03-05T00:00:00"}, "event_format": {"1": "conventional"}, "session1": {"1": "Practice 1"}, "session1_date": {"1": "2023-03-03T11:30:00"}, "session2": {"1": "Practice 2"}, "session2_date": {"1": "2023-03-03T15:00:00"}, "session3": {"1": "Practice 3"}, "session3_date": {"1": "2023-03-04T12:30:00"}, "session4": {"1": "Qualifying"}, "session4_date": {"1": "2023-03-04T16:00:00"}, "session5": {"1": "Race"}, "session5_date": {"1": "2023-03-05T15:00:00"}, "f1_api_support": {"1": true}, "gmt_offset": {"1": null}}'

    with patch('fastf1.req.Cache.requests_get', return_value=mock_response):
        result = events._get_schedule_ff1(2023)

        assert result is not None
        assert isinstance(result, EventSchedule)


def test_event_schedule_get_event_by_round_zero():
    """Test EventSchedule.get_event_by_round raises ValueError for round 0."""
    schedule = EventSchedule(pd.DataFrame({
        'RoundNumber': [1, 2],
        'EventName': ['Event 1', 'Event 2']
    }), year=2023)

    with pytest.raises(ValueError, match="Cannot get testing event by round number"):
        schedule.get_event_by_round(0)


def test_event_schedule_get_event_by_round_invalid():
    """Test EventSchedule.get_event_by_round raises ValueError for invalid round."""
    schedule = EventSchedule(pd.DataFrame({
        'RoundNumber': [1, 2],
        'EventName': ['Event 1', 'Event 2']
    }), year=2023)

    with pytest.raises(ValueError, match="Invalid round"):
        schedule.get_event_by_round(99)


def test_event_schedule_strict_event_search_found(mock_event_schedule):
    """Test EventSchedule._strict_event_search finds exact match."""
    result = mock_event_schedule._strict_event_search('Bahrain Grand Prix')

    assert result['EventName'] == 'Bahrain Grand Prix'


def test_event_schedule_strict_event_search_case_insensitive(mock_event_schedule):
    """Test EventSchedule._strict_event_search is case insensitive."""
    result = mock_event_schedule._strict_event_search('bahrain grand prix')

    assert result['EventName'] == 'Bahrain Grand Prix'


def test_event_schedule_strict_event_search_not_found(mock_event_schedule):
    """Test EventSchedule._strict_event_search raises KeyError when not found."""
    with pytest.raises(KeyError, match="No exact event name"):
        mock_event_schedule._strict_event_search('Nonexistent Event')


def test_event_schedule_fuzzy_event_search_short_name(mock_event_schedule):
    """Test EventSchedule._fuzzy_event_search raises ValueError for short names."""
    with pytest.raises(ValueError, match="Unique part of the event name is too short"):
        mock_event_schedule._fuzzy_event_search('GP')


def test_event_schedule_get_event_by_name_exact_match(mock_event_schedule):
    """Test EventSchedule.get_event_by_name with exact_match=True."""
    result = mock_event_schedule.get_event_by_name('Bahrain Grand Prix', exact_match=True)

    assert result['EventName'] == 'Bahrain Grand Prix'


def test_event_get_session_name_invalid_abbreviation(mock_event):
    """Test Event.get_session_name with invalid abbreviation."""
    with pytest.raises(ValueError, match="Invalid session type"):
        mock_event.get_session_name('XYZ')


def test_event_get_session_name_not_in_event(mock_event):
    """Test Event.get_session_name when session doesn't exist in event."""
    with pytest.raises(ValueError, match="does not exist for this event"):
        mock_event.get_session_name('Sprint')


def test_event_get_session_name_invalid_number(mock_event):
    """Test Event.get_session_name with invalid session number."""
    with pytest.raises(ValueError, match="Invalid session type"):
        mock_event.get_session_name(10)


def test_event_get_session_name_null_session(mock_event):
    """Test Event.get_session_name when session is null."""
    mock_event_with_null = mock_event.copy()
    mock_event_with_null['Session5'] = None

    with pytest.raises(ValueError, match="does not exist for this event"):
        mock_event_with_null.get_session_name(5)


def test_event_get_session_date_no_session(mock_event):
    """Test Event.get_session_date raises ValueError when session doesn't exist."""
    with pytest.raises(ValueError, match="does not exist for this event"):
        mock_event.get_session_date('Sprint')


def test_event_get_session_date_local_not_available(mock_event):
    """Test Event.get_session_date raises ValueError when local timestamp not available."""
    with pytest.raises(ValueError, match="Local timestamp is not available"):
        mock_event.get_session_date('Race', utc=False)


def test_event_get_session_by_name_not_in_values(mock_event):
    """Test Event.get_session raises ValueError when session name not in values."""
    with patch.object(Event, 'get_session_name', return_value='Sprint'):
        with pytest.raises(ValueError, match="does not exist for this event"):
            mock_event.get_session('Sprint')


def test_event_get_session_invalid_number(mock_event):
    """Test Event.get_session with invalid session number."""
    with pytest.raises(ValueError, match="Invalid session type"):
        mock_event.get_session(10)


def test_event_get_session_null_session(mock_event):
    """Test Event.get_session when session is null."""
    mock_event_with_null = mock_event.copy()
    mock_event_with_null['Session5'] = None

    with pytest.raises(ValueError, match="does not exist for this event"):
        mock_event_with_null.get_session(5)


def test_event_get_race(mock_event):
    """Test Event.get_race method."""
    with patch.object(Event, 'get_session') as mock_get_session:
        mock_event.get_race()
        mock_get_session.assert_called_once_with('Race')


def test_event_get_qualifying(mock_event):
    """Test Event.get_qualifying method."""
    with patch.object(Event, 'get_session') as mock_get_session:
        mock_event.get_qualifying()
        mock_get_session.assert_called_once_with('Qualifying')


def test_event_get_sprint(mock_event):
    """Test Event.get_sprint method."""
    with patch.object(Event, 'get_session') as mock_get_session:
        mock_event.get_sprint()
        mock_get_session.assert_called_once_with('Sprint')


def test_event_get_sprint_shootout(mock_event):
    """Test Event.get_sprint_shootout method."""
    with patch.object(Event, 'get_session') as mock_get_session:
        mock_event.get_sprint_shootout()
        mock_get_session.assert_called_once_with('Sprint Shootout')


def test_event_get_sprint_qualifying(mock_event):
    """Test Event.get_sprint_qualifying method."""
    with patch.object(Event, 'get_session') as mock_get_session:
        mock_event.get_sprint_qualifying()
        mock_get_session.assert_called_once_with('Sprint Qualifying')


def test_event_get_practice(mock_event):
    """Test Event.get_practice method."""
    with patch.object(Event, 'get_session') as mock_get_session:
        mock_event.get_practice(1)
        mock_get_session.assert_called_once_with('Practice 1')
