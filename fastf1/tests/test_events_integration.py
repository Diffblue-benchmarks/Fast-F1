"""Integration tests for events.py with mocked network backends."""
import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from fastf1.events import (
    Event,
    EventSchedule,
    get_event_schedule,
    get_events_remaining,
    get_testing_event,
)


def _make_full_schedule(year=2023):
    """Create a schedule with both testing and race events."""
    data = {
        'RoundNumber': [0, 1, 2],
        'Country': ['Bahrain', 'Bahrain', 'Saudi Arabia'],
        'Location': ['Sakhir', 'Sakhir', 'Jeddah'],
        'OfficialEventName': ['Pre-Season Test', 'Bahrain GP', 'Saudi GP'],
        'EventDate': [pd.Timestamp('2023-02-25'),
                      pd.Timestamp('2023-03-05'),
                      pd.Timestamp('2023-03-19')],
        'EventName': ['Pre-Season Testing', 'Bahrain Grand Prix',
                      'Saudi Arabian Grand Prix'],
        'EventFormat': ['testing', 'conventional', 'conventional'],
        'Session1': ['Practice 1', 'Practice 1', 'Practice 1'],
        'Session1Date': [None, None, None],
        'Session1DateUtc': [pd.Timestamp('2023-02-23'),
                            pd.Timestamp('2023-03-03'),
                            pd.Timestamp('2023-03-17')],
        'Session2': ['Practice 2', 'Practice 2', 'Practice 2'],
        'Session2Date': [None, None, None],
        'Session2DateUtc': [pd.Timestamp('2023-02-24'),
                            pd.Timestamp('2023-03-03'),
                            pd.Timestamp('2023-03-17')],
        'Session3': ['Practice 3', 'Practice 3', 'Practice 3'],
        'Session3Date': [None, None, None],
        'Session3DateUtc': [pd.Timestamp('2023-02-25'),
                            pd.Timestamp('2023-03-04'),
                            pd.Timestamp('2023-03-18')],
        'Session4': [None, 'Qualifying', 'Qualifying'],
        'Session4Date': [None, None, None],
        'Session4DateUtc': [pd.NaT,
                            pd.Timestamp('2023-03-04'),
                            pd.Timestamp('2023-03-18')],
        'Session5': [None, 'Race', 'Race'],
        'Session5Date': [None, None, None],
        'Session5DateUtc': [pd.NaT,
                            pd.Timestamp('2023-03-05'),
                            pd.Timestamp('2023-03-19')],
        'F1ApiSupport': [True, True, True],
    }
    return EventSchedule(data, year=year)


class TestEventScheduleFuzzySearch:
    def test_fuzzy_search_by_location(self):
        schedule = _make_full_schedule()
        # filter to non-testing
        schedule = schedule[~schedule.is_testing()]
        event = schedule._fuzzy_event_search('bahrain')
        assert event['Country'] == 'Bahrain'

    def test_fuzzy_search_by_country(self):
        schedule = _make_full_schedule()
        schedule = schedule[~schedule.is_testing()]
        event = schedule._fuzzy_event_search('saudi arabia')
        assert event['Country'] == 'Saudi Arabia'

    def test_fuzzy_search_too_short_raises(self):
        schedule = _make_full_schedule()
        schedule = schedule[~schedule.is_testing()]
        with pytest.raises(ValueError, match="too short"):
            schedule._fuzzy_event_search('GP')

    def test_get_event_by_name_fuzzy(self):
        schedule = _make_full_schedule()
        schedule = schedule[~schedule.is_testing()]
        event = schedule.get_event_by_name('bahrain')
        assert event['EventName'] == 'Bahrain Grand Prix'


class TestEventGetSession:
    def test_get_session_by_name(self):
        schedule = _make_full_schedule()
        event = schedule.iloc[1]  # Bahrain GP
        session = event.get_session('Race')
        assert session.name == 'Race'

    def test_get_session_by_number(self):
        schedule = _make_full_schedule()
        event = schedule.iloc[1]
        session = event.get_session(5)
        assert session.name == 'Race'

    def test_get_session_by_abbreviation(self):
        schedule = _make_full_schedule()
        event = schedule.iloc[1]
        session = event.get_session('Q')
        assert session.name == 'Qualifying'

    def test_get_session_invalid_raises(self):
        schedule = _make_full_schedule()
        event = schedule.iloc[1]
        with pytest.raises(ValueError):
            event.get_session('xyz')

    def test_get_race(self):
        schedule = _make_full_schedule()
        event = schedule.iloc[1]
        session = event.get_race()
        assert session.name == 'Race'

    def test_get_qualifying(self):
        schedule = _make_full_schedule()
        event = schedule.iloc[1]
        session = event.get_qualifying()
        assert session.name == 'Qualifying'

    def test_get_practice(self):
        schedule = _make_full_schedule()
        event = schedule.iloc[1]
        session = event.get_practice(1)
        assert session.name == 'Practice 1'


class TestGetEventSchedule:
    @patch('fastf1.events._get_schedule_ff1')
    def test_get_event_schedule_fastf1_backend(self, mock_ff1):
        schedule = _make_full_schedule()
        mock_ff1.return_value = schedule

        result = get_event_schedule(2023, backend='fastf1')
        assert len(result) == 3
        mock_ff1.assert_called_once_with(2023)

    @patch('fastf1.events._get_schedule_ff1')
    def test_exclude_testing(self, mock_ff1):
        schedule = _make_full_schedule()
        mock_ff1.return_value = schedule

        result = get_event_schedule(2023, include_testing=False,
                                    backend='fastf1')
        assert not result.is_testing().any()
        assert len(result) == 2

    @patch('fastf1.events._get_schedule_ff1')
    @patch('fastf1.events._get_schedule_from_f1_timing')
    @patch('fastf1.events._get_schedule_from_ergast')
    def test_fallback_on_none(self, mock_ergast, mock_f1t, mock_ff1):
        mock_ff1.return_value = None
        mock_f1t.return_value = None
        mock_ergast.return_value = _make_full_schedule()

        result = get_event_schedule(2023)
        assert result is not None
        mock_ergast.assert_called_once()

    @patch('fastf1.events._get_schedule_ff1')
    @patch('fastf1.events._get_schedule_from_f1_timing')
    @patch('fastf1.events._get_schedule_from_ergast')
    def test_all_backends_fail_raises(self, mock_ergast, mock_f1t, mock_ff1):
        mock_ff1.return_value = None
        mock_f1t.return_value = None
        mock_ergast.return_value = None

        with pytest.raises(ValueError, match="Failed to load"):
            get_event_schedule(2023)


class TestGetTestingEvent:
    @patch('fastf1.events.get_event_schedule')
    def test_get_testing_event(self, mock_schedule):
        schedule = _make_full_schedule()
        mock_schedule.return_value = schedule

        event = get_testing_event(2023, 1)
        assert event.is_testing()

    @patch('fastf1.events.get_event_schedule')
    def test_invalid_test_number_raises(self, mock_schedule):
        schedule = _make_full_schedule()
        mock_schedule.return_value = schedule

        with pytest.raises(ValueError, match="does not exist"):
            get_testing_event(2023, 99)

    def test_ergast_backend_raises(self):
        with pytest.raises(ValueError, match="ergast"):
            get_testing_event(2023, 1, backend='ergast')


class TestGetEventsRemaining:
    @patch('fastf1.events.get_event_schedule')
    def test_all_future(self, mock_schedule):
        schedule = _make_full_schedule()
        mock_schedule.return_value = schedule

        import datetime
        dt = datetime.datetime(2023, 1, 1)
        result = get_events_remaining(dt, include_testing=False)
        assert len(result) == 2  # both race events are after Jan 1

    @patch('fastf1.events.get_event_schedule')
    def test_all_past(self, mock_schedule):
        schedule = _make_full_schedule()
        mock_schedule.return_value = schedule

        import datetime
        dt = datetime.datetime(2023, 12, 31)
        result = get_events_remaining(dt, include_testing=False)
        assert len(result) == 0

    @patch('fastf1.events.get_event_schedule')
    def test_with_testing(self, mock_schedule):
        schedule = _make_full_schedule()
        mock_schedule.return_value = schedule

        import datetime
        dt = datetime.datetime(2023, 1, 1)
        result = get_events_remaining(dt, include_testing=True)
        assert len(result) == 3  # all events are future
