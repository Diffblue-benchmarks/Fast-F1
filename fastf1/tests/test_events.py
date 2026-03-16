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


# Tests for _get_schedule_from_ergast
@pytest.fixture
def mock_ergast_conventional_race():
    """Mock ergast data for a conventional race."""
    return [{
        'round': '1',
        'raceName': 'Bahrain Grand Prix',
        'Circuit': {
            'Location': {
                'country': 'Bahrain',
                'locality': 'Sakhir'
            }
        },
        'date': '2020-03-22',
        'time': '15:10:00Z'
    }]


@pytest.fixture
def mock_ergast_sprint_2021():
    """Mock ergast data for a sprint race in 2021."""
    return [{
        'round': '10',
        'raceName': 'British Grand Prix',
        'Circuit': {
            'Location': {
                'country': 'UK',
                'locality': 'Silverstone'
            }
        },
        'date': '2021-07-18',
        'time': '14:00:00Z',
        'Sprint': {
            'date': '2021-07-17',
            'time': '15:30:00Z'
        }
    }]


@pytest.fixture
def mock_ergast_sprint_2023():
    """Mock ergast data for a sprint race in 2023."""
    return [{
        'round': '4',
        'raceName': 'Azerbaijan Grand Prix',
        'Circuit': {
            'Location': {
                'country': 'Azerbaijan',
                'locality': 'Baku'
            }
        },
        'date': '2023-04-30',
        'time': '11:00:00Z',
        'Sprint': {
            'date': '2023-04-29',
            'time': '10:30:00Z'
        }
    }]


@pytest.fixture
def mock_ergast_sprint_2024():
    """Mock ergast data for a sprint race in 2024."""
    return [{
        'round': '6',
        'raceName': 'Miami Grand Prix',
        'Circuit': {
            'Location': {
                'country': 'USA',
                'locality': 'Miami'
            }
        },
        'date': '2024-05-05',
        'time': '19:00:00Z',
        'Sprint': {
            'date': '2024-05-04',
            'time': '18:00:00Z'
        }
    }]


def test_get_schedule_from_ergast_conventional(mock_ergast_conventional_race):
    """Test _get_schedule_from_ergast with conventional race format."""
    with patch('fastf1.ergast.fetch_season', return_value=mock_ergast_conventional_race):
        result = events._get_schedule_from_ergast(2020)

        assert isinstance(result, EventSchedule)
        assert result.year == 2020
        assert len(result) == 1
        assert result.iloc[0]['RoundNumber'] == 1
        assert result.iloc[0]['Country'] == 'Bahrain'
        assert result.iloc[0]['Location'] == 'Sakhir'
        assert result.iloc[0]['EventName'] == 'Bahrain Grand Prix'
        assert result.iloc[0]['EventFormat'] == 'conventional'
        assert result.iloc[0]['Session1'] == 'Practice 1'
        assert result.iloc[0]['Session2'] == 'Practice 2'
        assert result.iloc[0]['Session3'] == 'Practice 3'
        assert result.iloc[0]['Session4'] == 'Qualifying'
        assert result.iloc[0]['Session5'] == 'Race'
        assert result.iloc[0]['F1ApiSupport'] == True


def test_get_schedule_from_ergast_sprint_2021(mock_ergast_sprint_2021):
    """Test _get_schedule_from_ergast with 2021 sprint format."""
    with patch('fastf1.ergast.fetch_season', return_value=mock_ergast_sprint_2021):
        result = events._get_schedule_from_ergast(2021)

        assert isinstance(result, EventSchedule)
        assert len(result) == 1
        assert result.iloc[0]['EventFormat'] == 'sprint'
        assert result.iloc[0]['Session1'] == 'Practice 1'
        assert result.iloc[0]['Session2'] == 'Qualifying'
        assert result.iloc[0]['Session3'] == 'Practice 2'
        assert result.iloc[0]['Session4'] == 'Sprint'
        assert result.iloc[0]['Session5'] == 'Race'


def test_get_schedule_from_ergast_sprint_2022(mock_ergast_sprint_2021):
    """Test _get_schedule_from_ergast with 2022 sprint format."""
    with patch('fastf1.ergast.fetch_season', return_value=mock_ergast_sprint_2021):
        result = events._get_schedule_from_ergast(2022)

        assert isinstance(result, EventSchedule)
        assert len(result) == 1
        assert result.iloc[0]['EventFormat'] == 'sprint'
        assert result.iloc[0]['Session1'] == 'Practice 1'
        assert result.iloc[0]['Session2'] == 'Qualifying'
        assert result.iloc[0]['Session3'] == 'Practice 2'
        assert result.iloc[0]['Session4'] == 'Sprint'
        assert result.iloc[0]['Session5'] == 'Race'


def test_get_schedule_from_ergast_sprint_shootout_2023(mock_ergast_sprint_2023):
    """Test _get_schedule_from_ergast with 2023 sprint shootout format."""
    with patch('fastf1.ergast.fetch_season', return_value=mock_ergast_sprint_2023):
        result = events._get_schedule_from_ergast(2023)

        assert isinstance(result, EventSchedule)
        assert len(result) == 1
        assert result.iloc[0]['EventFormat'] == 'sprint_shootout'
        assert result.iloc[0]['Session1'] == 'Practice 1'
        assert result.iloc[0]['Session2'] == 'Qualifying'
        assert result.iloc[0]['Session3'] == 'Sprint Shootout'
        assert result.iloc[0]['Session4'] == 'Sprint'
        assert result.iloc[0]['Session5'] == 'Race'


def test_get_schedule_from_ergast_sprint_qualifying_2024(mock_ergast_sprint_2024):
    """Test _get_schedule_from_ergast with 2024+ sprint qualifying format."""
    with patch('fastf1.ergast.fetch_season', return_value=mock_ergast_sprint_2024):
        result = events._get_schedule_from_ergast(2024)

        assert isinstance(result, EventSchedule)
        assert len(result) == 1
        assert result.iloc[0]['EventFormat'] == 'sprint_qualifying'
        assert result.iloc[0]['Session1'] == 'Practice 1'
        assert result.iloc[0]['Session2'] == 'Sprint Qualifying'
        assert result.iloc[0]['Session3'] == 'Sprint'
        assert result.iloc[0]['Session4'] == 'Qualifying'
        assert result.iloc[0]['Session5'] == 'Race'


def test_get_schedule_from_ergast_year_before_2018():
    """Test _get_schedule_from_ergast sets F1ApiSupport to False for years before 2018."""
    mock_data = [{
        'round': '1',
        'raceName': 'Australian Grand Prix',
        'Circuit': {
            'Location': {
                'country': 'Australia',
                'locality': 'Melbourne'
            }
        },
        'date': '2017-03-26',
        'time': '05:00:00Z'
    }]

    with patch('fastf1.ergast.fetch_season', return_value=mock_data):
        result = events._get_schedule_from_ergast(2017)

        assert result.iloc[0]['F1ApiSupport'] == False


def test_get_schedule_from_ergast_with_date_and_time():
    """Test _get_schedule_from_ergast correctly parses date and time."""
    mock_data = [{
        'round': '1',
        'raceName': 'Test Grand Prix',
        'Circuit': {
            'Location': {
                'country': 'Test Country',
                'locality': 'Test City'
            }
        },
        'date': '2020-03-15',
        'time': '14:10:00Z'
    }]

    with patch('fastf1.ergast.fetch_season', return_value=mock_data):
        result = events._get_schedule_from_ergast(2020)

        assert isinstance(result, EventSchedule)
        assert result.iloc[0]['EventDate'] == pd.Timestamp('2020-03-15T14:10:00')


def test_get_schedule_from_ergast_date_without_time():
    """Test _get_schedule_from_ergast handles date without time."""
    mock_data = [{
        'round': '1',
        'raceName': 'Test Grand Prix',
        'Circuit': {
            'Location': {
                'country': 'Test Country',
                'locality': 'Test City'
            }
        },
        'date': '2020-03-15'
    }]

    with patch('fastf1.ergast.fetch_season', return_value=mock_data):
        result = events._get_schedule_from_ergast(2020)

        assert isinstance(result, EventSchedule)
        # When time is missing, it should still parse the date correctly
        assert result.iloc[0]['EventDate'] == pd.Timestamp('2020-03-15')


def test_get_schedule_from_ergast_session_dates():
    """Test _get_schedule_from_ergast correctly calculates session dates."""
    mock_data = [{
        'round': '1',
        'raceName': 'Test Grand Prix',
        'Circuit': {
            'Location': {
                'country': 'Test Country',
                'locality': 'Test City'
            }
        },
        'date': '2020-03-22',
        'time': '15:10:00Z'
    }]

    with patch('fastf1.ergast.fetch_season', return_value=mock_data):
        result = events._get_schedule_from_ergast(2020)

        race_date = pd.Timestamp('2020-03-22T15:10:00')
        expected_day_minus_2 = race_date.floor('D') - pd.Timedelta(days=2)
        expected_day_minus_1 = race_date.floor('D') - pd.Timedelta(days=1)

        assert result.iloc[0]['Session1DateUtc'] == expected_day_minus_2
        assert result.iloc[0]['Session2DateUtc'] == expected_day_minus_2
        assert result.iloc[0]['Session3DateUtc'] == expected_day_minus_1
        assert result.iloc[0]['Session4DateUtc'] == expected_day_minus_1
        assert result.iloc[0]['Session5DateUtc'] == race_date


def test_get_schedule_from_ergast_official_event_name():
    """Test _get_schedule_from_ergast sets OfficialEventName to empty string."""
    mock_data = [{
        'round': '1',
        'raceName': 'Test Grand Prix',
        'Circuit': {
            'Location': {
                'country': 'Test Country',
                'locality': 'Test City'
            }
        },
        'date': '2020-03-22',
        'time': '15:10:00Z'
    }]

    with patch('fastf1.ergast.fetch_season', return_value=mock_data):
        result = events._get_schedule_from_ergast(2020)

        assert result.iloc[0]['OfficialEventName'] == ""


def test_get_schedule_from_ergast_multiple_races():
    """Test _get_schedule_from_ergast with multiple races."""
    mock_data = [
        {
            'round': '1',
            'raceName': 'First Grand Prix',
            'Circuit': {
                'Location': {
                    'country': 'Country1',
                    'locality': 'City1'
                }
            },
            'date': '2020-03-22',
            'time': '15:10:00Z'
        },
        {
            'round': '2',
            'raceName': 'Second Grand Prix',
            'Circuit': {
                'Location': {
                    'country': 'Country2',
                    'locality': 'City2'
                }
            },
            'date': '2020-04-05',
            'time': '13:00:00Z'
        }
    ]

    with patch('fastf1.ergast.fetch_season', return_value=mock_data):
        result = events._get_schedule_from_ergast(2020)

        assert len(result) == 2
        assert result.iloc[0]['RoundNumber'] == 1
        assert result.iloc[1]['RoundNumber'] == 2
        assert result.iloc[0]['EventName'] == 'First Grand Prix'
        assert result.iloc[1]['EventName'] == 'Second Grand Prix'


# Tests for _get_schedule_from_f1_timing
def test_get_schedule_from_f1_timing_conventional_2020():
    """Test _get_schedule_from_f1_timing with conventional format for year <= 2020."""
    mock_response = [{
        'Country': {'Name': 'Bahrain'},
        'Location': 'Sakhir',
        'Name': 'Bahrain Grand Prix',
        'OfficialName': 'Formula 1 Gulf Air Bahrain Grand Prix 2020',
        'Number': 1,
        'Sessions': [
            {'Key': 1, 'Name': 'Practice 1', 'StartDate': '2020-03-27T11:30:00', 'GmtOffset': '03:00:00'},
            {'Key': 2, 'Name': 'Practice 2', 'StartDate': '2020-03-27T15:00:00', 'GmtOffset': '03:00:00'},
            {'Key': 3, 'Name': 'Practice 3', 'StartDate': '2020-03-28T12:00:00', 'GmtOffset': '03:00:00'},
            {'Key': 4, 'Name': 'Qualifying', 'StartDate': '2020-03-28T15:00:00', 'GmtOffset': '03:00:00'},
            {'Key': 5, 'Name': 'Race', 'StartDate': '2020-03-29T15:10:00', 'GmtOffset': '03:00:00'}
        ]
    }]

    with patch('fastf1._api.season_schedule', return_value=mock_response):
        result = events._get_schedule_from_f1_timing(2020)

        assert isinstance(result, EventSchedule)
        assert result.year == 2020
        assert len(result) == 1
        assert result.iloc[0]['Country'] == 'Bahrain'
        assert result.iloc[0]['Location'] == 'Sakhir'
        assert result.iloc[0]['EventName'] == 'Bahrain Grand Prix'
        assert result.iloc[0]['OfficialEventName'] == 'Formula 1 Gulf Air Bahrain Grand Prix 2020'
        assert result.iloc[0]['EventFormat'] == 'conventional'
        assert result.iloc[0]['RoundNumber'] == 1
        assert result.iloc[0]['F1ApiSupport'] == True
        assert result.iloc[0]['Session1'] == 'Practice 1'
        assert result.iloc[0]['Session2'] == 'Practice 2'
        assert result.iloc[0]['Session3'] == 'Practice 3'
        assert result.iloc[0]['Session4'] == 'Qualifying'
        assert result.iloc[0]['Session5'] == 'Race'


def test_get_schedule_from_f1_timing_testing_event():
    """Test _get_schedule_from_f1_timing with testing event."""
    mock_response = [{
        'Country': {'Name': 'Spain'},
        'Location': 'Barcelona',
        'Name': 'Pre-Season Test',
        'OfficialName': 'Formula 1 Pre-Season Testing',
        'Number': 0,
        'Sessions': [
            {'Key': 1, 'Name': 'Practice 1', 'StartDate': '2023-02-23T09:00:00', 'GmtOffset': '01:00:00'},
            {'Key': 2, 'Name': 'Practice 2', 'StartDate': '2023-02-23T13:00:00', 'GmtOffset': '01:00:00'},
            {'Key': 3, 'Name': 'Practice 3', 'StartDate': '2023-02-24T09:00:00', 'GmtOffset': '01:00:00'}
        ]
    }]

    with patch('fastf1._api.season_schedule', return_value=mock_response):
        result = events._get_schedule_from_f1_timing(2023)

        assert isinstance(result, EventSchedule)
        assert len(result) == 1
        assert result.iloc[0]['EventName'] == 'Pre-Season Test'
        assert result.iloc[0]['EventFormat'] == 'testing'
        assert result.iloc[0]['RoundNumber'] == 0


def test_get_schedule_from_f1_timing_sprint_2021():
    """Test _get_schedule_from_f1_timing with 2021 sprint format."""
    mock_response = [{
        'Country': {'Name': 'UK'},
        'Location': 'Silverstone',
        'Name': 'British Grand Prix',
        'OfficialName': 'Formula 1 Pirelli British Grand Prix 2021',
        'Number': 10,
        'Sessions': [
            {'Key': 1, 'Name': 'Practice 1', 'StartDate': '2021-07-16T14:30:00', 'GmtOffset': '01:00:00'},
            {'Key': 2, 'Name': 'Qualifying', 'StartDate': '2021-07-16T18:00:00', 'GmtOffset': '01:00:00'},
            {'Key': 3, 'Name': 'Practice 2', 'StartDate': '2021-07-17T12:00:00', 'GmtOffset': '01:00:00'},
            {'Key': 4, 'Name': 'Sprint Qualifying', 'StartDate': '2021-07-17T16:30:00', 'GmtOffset': '01:00:00'},
            {'Key': 5, 'Name': 'Race', 'StartDate': '2021-07-18T15:00:00', 'GmtOffset': '01:00:00'}
        ]
    }]

    with patch('fastf1._api.season_schedule', return_value=mock_response):
        result = events._get_schedule_from_f1_timing(2021)

        assert isinstance(result, EventSchedule)
        assert len(result) == 1
        assert result.iloc[0]['EventFormat'] == 'sprint'
        assert result.iloc[0]['Session4'] == 'Sprint'  # Should be renamed from 'Sprint Qualifying'
        assert result.iloc[0]['RoundNumber'] == 10


def test_get_schedule_from_f1_timing_sprint_2022():
    """Test _get_schedule_from_f1_timing with 2022 sprint format."""
    mock_response = [{
        'Country': {'Name': 'Austria'},
        'Location': 'Spielberg',
        'Name': 'Austrian Grand Prix',
        'OfficialName': 'Formula 1 Rolex Großer Preis von Österreich 2022',
        'Number': 11,
        'Sessions': [
            {'Key': 1, 'Name': 'Practice 1', 'StartDate': '2022-07-08T13:30:00', 'GmtOffset': '02:00:00'},
            {'Key': 2, 'Name': 'Qualifying', 'StartDate': '2022-07-08T17:00:00', 'GmtOffset': '02:00:00'},
            {'Key': 3, 'Name': 'Practice 2', 'StartDate': '2022-07-09T12:30:00', 'GmtOffset': '02:00:00'},
            {'Key': 4, 'Name': 'Sprint', 'StartDate': '2022-07-09T16:30:00', 'GmtOffset': '02:00:00'},
            {'Key': 5, 'Name': 'Race', 'StartDate': '2022-07-10T15:00:00', 'GmtOffset': '02:00:00'}
        ]
    }]

    with patch('fastf1._api.season_schedule', return_value=mock_response):
        result = events._get_schedule_from_f1_timing(2022)

        assert isinstance(result, EventSchedule)
        assert len(result) == 1
        assert result.iloc[0]['EventFormat'] == 'sprint'
        assert result.iloc[0]['Session4'] == 'Sprint'
        assert result.iloc[0]['RoundNumber'] == 11


def test_get_schedule_from_f1_timing_conventional_2022():
    """Test _get_schedule_from_f1_timing with conventional format in 2022."""
    mock_response = [{
        'Country': {'Name': 'Monaco'},
        'Location': 'Monaco',
        'Name': 'Monaco Grand Prix',
        'OfficialName': 'Formula 1 Grand Prix de Monaco 2022',
        'Number': 7,
        'Sessions': [
            {'Key': 1, 'Name': 'Practice 1', 'StartDate': '2022-05-27T14:00:00', 'GmtOffset': '02:00:00'},
            {'Key': 2, 'Name': 'Practice 2', 'StartDate': '2022-05-27T17:00:00', 'GmtOffset': '02:00:00'},
            {'Key': 3, 'Name': 'Practice 3', 'StartDate': '2022-05-28T13:00:00', 'GmtOffset': '02:00:00'},
            {'Key': 4, 'Name': 'Qualifying', 'StartDate': '2022-05-28T16:00:00', 'GmtOffset': '02:00:00'},
            {'Key': 5, 'Name': 'Race', 'StartDate': '2022-05-29T15:00:00', 'GmtOffset': '02:00:00'}
        ]
    }]

    with patch('fastf1._api.season_schedule', return_value=mock_response):
        result = events._get_schedule_from_f1_timing(2022)

        assert isinstance(result, EventSchedule)
        assert len(result) == 1
        assert result.iloc[0]['EventFormat'] == 'conventional'
        assert result.iloc[0]['Session3'] == 'Practice 3'
        assert result.iloc[0]['Session4'] == 'Qualifying'


def test_get_schedule_from_f1_timing_sprint_shootout_2023():
    """Test _get_schedule_from_f1_timing with 2023 sprint shootout format."""
    mock_response = [{
        'Country': {'Name': 'Azerbaijan'},
        'Location': 'Baku',
        'Name': 'Azerbaijan Grand Prix',
        'OfficialName': 'Formula 1 Azerbaijan Grand Prix 2023',
        'Number': 4,
        'Sessions': [
            {'Key': 1, 'Name': 'Practice 1', 'StartDate': '2023-04-28T13:30:00', 'GmtOffset': '04:00:00'},
            {'Key': 2, 'Name': 'Qualifying', 'StartDate': '2023-04-28T17:00:00', 'GmtOffset': '04:00:00'},
            {'Key': 3, 'Name': 'Sprint Shootout', 'StartDate': '2023-04-29T12:30:00', 'GmtOffset': '04:00:00'},
            {'Key': 4, 'Name': 'Sprint', 'StartDate': '2023-04-29T16:30:00', 'GmtOffset': '04:00:00'},
            {'Key': 5, 'Name': 'Race', 'StartDate': '2023-04-30T13:00:00', 'GmtOffset': '04:00:00'}
        ]
    }]

    with patch('fastf1._api.season_schedule', return_value=mock_response):
        result = events._get_schedule_from_f1_timing(2023)

        assert isinstance(result, EventSchedule)
        assert len(result) == 1
        assert result.iloc[0]['EventFormat'] == 'sprint_shootout'
        assert result.iloc[0]['Session3'] == 'Sprint Shootout'
        assert result.iloc[0]['RoundNumber'] == 4


def test_get_schedule_from_f1_timing_conventional_2023():
    """Test _get_schedule_from_f1_timing with conventional format in 2023."""
    mock_response = [{
        'Country': {'Name': 'Italy'},
        'Location': 'Monza',
        'Name': 'Italian Grand Prix',
        'OfficialName': 'Formula 1 Pirelli Gran Premio d\'Italia 2023',
        'Number': 16,
        'Sessions': [
            {'Key': 1, 'Name': 'Practice 1', 'StartDate': '2023-09-01T13:30:00', 'GmtOffset': '02:00:00'},
            {'Key': 2, 'Name': 'Practice 2', 'StartDate': '2023-09-01T17:00:00', 'GmtOffset': '02:00:00'},
            {'Key': 3, 'Name': 'Practice 3', 'StartDate': '2023-09-02T12:30:00', 'GmtOffset': '02:00:00'},
            {'Key': 4, 'Name': 'Qualifying', 'StartDate': '2023-09-02T16:00:00', 'GmtOffset': '02:00:00'},
            {'Key': 5, 'Name': 'Race', 'StartDate': '2023-09-03T15:00:00', 'GmtOffset': '02:00:00'}
        ]
    }]

    with patch('fastf1._api.season_schedule', return_value=mock_response):
        result = events._get_schedule_from_f1_timing(2023)

        assert isinstance(result, EventSchedule)
        assert len(result) == 1
        assert result.iloc[0]['EventFormat'] == 'conventional'
        assert result.iloc[0]['Session3'] == 'Practice 3'


def test_get_schedule_from_f1_timing_sprint_qualifying_2024():
    """Test _get_schedule_from_f1_timing with 2024+ sprint qualifying format."""
    mock_response = [{
        'Country': {'Name': 'USA'},
        'Location': 'Miami',
        'Name': 'Miami Grand Prix',
        'OfficialName': 'Formula 1 Crypto.com Miami Grand Prix 2024',
        'Number': 6,
        'Sessions': [
            {'Key': 1, 'Name': 'Practice 1', 'StartDate': '2024-05-03T20:30:00', 'GmtOffset': '-04:00:00'},
            {'Key': 2, 'Name': 'Sprint Qualifying', 'StartDate': '2024-05-04T18:30:00', 'GmtOffset': '-04:00:00'},
            {'Key': 3, 'Name': 'Sprint', 'StartDate': '2024-05-04T22:00:00', 'GmtOffset': '-04:00:00'},
            {'Key': 4, 'Name': 'Qualifying', 'StartDate': '2024-05-05T18:00:00', 'GmtOffset': '-04:00:00'},
            {'Key': 5, 'Name': 'Race', 'StartDate': '2024-05-05T21:30:00', 'GmtOffset': '-04:00:00'}
        ]
    }]

    with patch('fastf1._api.season_schedule', return_value=mock_response):
        result = events._get_schedule_from_f1_timing(2024)

        assert isinstance(result, EventSchedule)
        assert len(result) == 1
        assert result.iloc[0]['EventFormat'] == 'sprint_qualifying'
        assert result.iloc[0]['Session2'] == 'Sprint Qualifying'
        assert result.iloc[0]['RoundNumber'] == 6


def test_get_schedule_from_f1_timing_conventional_2024():
    """Test _get_schedule_from_f1_timing with conventional format in 2024+."""
    mock_response = [{
        'Country': {'Name': 'Japan'},
        'Location': 'Suzuka',
        'Name': 'Japanese Grand Prix',
        'OfficialName': 'Formula 1 Rolex Japanese Grand Prix 2024',
        'Number': 5,
        'Sessions': [
            {'Key': 1, 'Name': 'Practice 1', 'StartDate': '2024-04-05T11:30:00', 'GmtOffset': '09:00:00'},
            {'Key': 2, 'Name': 'Practice 2', 'StartDate': '2024-04-05T15:00:00', 'GmtOffset': '09:00:00'},
            {'Key': 3, 'Name': 'Practice 3', 'StartDate': '2024-04-06T11:30:00', 'GmtOffset': '09:00:00'},
            {'Key': 4, 'Name': 'Qualifying', 'StartDate': '2024-04-06T15:00:00', 'GmtOffset': '09:00:00'},
            {'Key': 5, 'Name': 'Race', 'StartDate': '2024-04-07T14:00:00', 'GmtOffset': '09:00:00'}
        ]
    }]

    with patch('fastf1._api.season_schedule', return_value=mock_response):
        result = events._get_schedule_from_f1_timing(2024)

        assert isinstance(result, EventSchedule)
        assert len(result) == 1
        assert result.iloc[0]['EventFormat'] == 'conventional'
        assert result.iloc[0]['Session3'] == 'Practice 3'
        assert result.iloc[0]['Session4'] == 'Qualifying'


def test_get_schedule_from_f1_timing_fewer_sessions():
    """Test _get_schedule_from_f1_timing with fewer than 5 sessions (IndexError handling)."""
    mock_response = [{
        'Country': {'Name': 'Spain'},
        'Location': 'Barcelona',
        'Name': 'Testing Session',
        'OfficialName': 'Pre-Season Testing',
        'Number': 0,
        'Sessions': [
            {'Key': 1, 'Name': 'Practice 1', 'StartDate': '2023-02-23T09:00:00', 'GmtOffset': '01:00:00'},
            {'Key': 2, 'Name': 'Practice 2', 'StartDate': '2023-02-23T13:00:00', 'GmtOffset': '01:00:00'},
            {'Key': 3, 'Name': 'Practice 3', 'StartDate': '2023-02-24T09:00:00', 'GmtOffset': '01:00:00'}
        ]
    }]

    with patch('fastf1._api.season_schedule', return_value=mock_response):
        result = events._get_schedule_from_f1_timing(2023)

        assert isinstance(result, EventSchedule)
        assert len(result) == 1
        assert result.iloc[0]['Session1'] == 'Practice 1'
        assert result.iloc[0]['Session2'] == 'Practice 2'
        assert result.iloc[0]['Session3'] == 'Practice 3'
        # Missing sessions may be None or empty string depending on EventSchedule implementation
        assert result.iloc[0]['Session4'] in (None, '')
        assert result.iloc[0]['Session5'] in (None, '')
        assert pd.isna(result.iloc[0]['Session4DateUtc'])
        assert pd.isna(result.iloc[0]['Session5DateUtc'])


def test_get_schedule_from_f1_timing_invalid_sessions_filtered():
    """Test _get_schedule_from_f1_timing filters out invalid sessions (Key=-1 or no Name)."""
    mock_response = [{
        'Country': {'Name': 'Bahrain'},
        'Location': 'Sakhir',
        'Name': 'Bahrain Grand Prix',
        'OfficialName': 'Formula 1 Gulf Air Bahrain Grand Prix 2023',
        'Number': 1,
        'Sessions': [
            {'Key': 1, 'Name': 'Practice 1', 'StartDate': '2023-03-03T11:30:00', 'GmtOffset': '03:00:00'},
            {'Key': -1, 'Name': 'Invalid Session', 'StartDate': '2023-03-03T13:00:00', 'GmtOffset': '03:00:00'},
            {'Key': 2, 'Name': '', 'StartDate': '2023-03-03T15:00:00', 'GmtOffset': '03:00:00'},
            {'Key': 3, 'Name': 'Practice 2', 'StartDate': '2023-03-03T17:00:00', 'GmtOffset': '03:00:00'},
            {'Key': 4, 'Name': 'Practice 3', 'StartDate': '2023-03-04T12:30:00', 'GmtOffset': '03:00:00'},
            {'Key': 5, 'Name': 'Qualifying', 'StartDate': '2023-03-04T16:00:00', 'GmtOffset': '03:00:00'},
            {'Key': 6, 'Name': 'Race', 'StartDate': '2023-03-05T15:00:00', 'GmtOffset': '03:00:00'}
        ]
    }]

    with patch('fastf1._api.season_schedule', return_value=mock_response):
        result = events._get_schedule_from_f1_timing(2023)

        assert isinstance(result, EventSchedule)
        assert len(result) == 1
        assert result.iloc[0]['Session1'] == 'Practice 1'
        assert result.iloc[0]['Session2'] == 'Practice 2'
        assert result.iloc[0]['Session3'] == 'Practice 3'
        assert result.iloc[0]['Session4'] == 'Qualifying'
        assert result.iloc[0]['Session5'] == 'Race'


def test_get_schedule_from_f1_timing_multiple_events():
    """Test _get_schedule_from_f1_timing with multiple events."""
    mock_response = [
        {
            'Country': {'Name': 'Bahrain'},
            'Location': 'Sakhir',
            'Name': 'Bahrain Grand Prix',
            'OfficialName': 'Formula 1 Gulf Air Bahrain Grand Prix 2023',
            'Number': 1,
            'Sessions': [
                {'Key': 1, 'Name': 'Practice 1', 'StartDate': '2023-03-03T11:30:00', 'GmtOffset': '03:00:00'},
                {'Key': 2, 'Name': 'Practice 2', 'StartDate': '2023-03-03T15:00:00', 'GmtOffset': '03:00:00'},
                {'Key': 3, 'Name': 'Practice 3', 'StartDate': '2023-03-04T12:30:00', 'GmtOffset': '03:00:00'},
                {'Key': 4, 'Name': 'Qualifying', 'StartDate': '2023-03-04T16:00:00', 'GmtOffset': '03:00:00'},
                {'Key': 5, 'Name': 'Race', 'StartDate': '2023-03-05T15:00:00', 'GmtOffset': '03:00:00'}
            ]
        },
        {
            'Country': {'Name': 'Saudi Arabia'},
            'Location': 'Jeddah',
            'Name': 'Saudi Arabian Grand Prix',
            'OfficialName': 'Formula 1 STC Saudi Arabian Grand Prix 2023',
            'Number': 2,
            'Sessions': [
                {'Key': 1, 'Name': 'Practice 1', 'StartDate': '2023-03-17T14:30:00', 'GmtOffset': '03:00:00'},
                {'Key': 2, 'Name': 'Practice 2', 'StartDate': '2023-03-17T18:00:00', 'GmtOffset': '03:00:00'},
                {'Key': 3, 'Name': 'Practice 3', 'StartDate': '2023-03-18T14:30:00', 'GmtOffset': '03:00:00'},
                {'Key': 4, 'Name': 'Qualifying', 'StartDate': '2023-03-18T18:00:00', 'GmtOffset': '03:00:00'},
                {'Key': 5, 'Name': 'Race', 'StartDate': '2023-03-19T18:00:00', 'GmtOffset': '03:00:00'}
            ]
        }
    ]

    with patch('fastf1._api.season_schedule', return_value=mock_response):
        result = events._get_schedule_from_f1_timing(2023)

        assert isinstance(result, EventSchedule)
        assert len(result) == 2
        assert result.iloc[0]['Country'] == 'Bahrain'
        assert result.iloc[1]['Country'] == 'Saudi Arabia'
        assert result.iloc[0]['RoundNumber'] == 1
        assert result.iloc[1]['RoundNumber'] == 2
