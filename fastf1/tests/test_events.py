import datetime

import pandas as pd
import pytest

from fastf1.events import (
    Event,
    EventSchedule,
    _SESSION_TYPE_ABBREVIATIONS,
)


def _make_schedule(events_data=None, year=2023):
    """Helper to create a minimal EventSchedule."""
    if events_data is None:
        events_data = {
            'RoundNumber': [1, 2],
            'Country': ['Bahrain', 'Saudi Arabia'],
            'Location': ['Sakhir', 'Jeddah'],
            'OfficialEventName': ['Bahrain GP 2023', 'Saudi Arabian GP 2023'],
            'EventDate': [pd.Timestamp('2023-03-05'),
                          pd.Timestamp('2023-03-19')],
            'EventName': ['Bahrain Grand Prix', 'Saudi Arabian Grand Prix'],
            'EventFormat': ['conventional', 'conventional'],
            'Session1': ['Practice 1', 'Practice 1'],
            'Session1Date': [None, None],
            'Session1DateUtc': [pd.Timestamp('2023-03-03'),
                                pd.Timestamp('2023-03-17')],
            'Session2': ['Practice 2', 'Practice 2'],
            'Session2Date': [None, None],
            'Session2DateUtc': [pd.Timestamp('2023-03-03'),
                                pd.Timestamp('2023-03-17')],
            'Session3': ['Practice 3', 'Practice 3'],
            'Session3Date': [None, None],
            'Session3DateUtc': [pd.Timestamp('2023-03-04'),
                                pd.Timestamp('2023-03-18')],
            'Session4': ['Qualifying', 'Qualifying'],
            'Session4Date': [None, None],
            'Session4DateUtc': [pd.Timestamp('2023-03-04'),
                                pd.Timestamp('2023-03-18')],
            'Session5': ['Race', 'Race'],
            'Session5Date': [None, None],
            'Session5DateUtc': [pd.Timestamp('2023-03-05'),
                                pd.Timestamp('2023-03-19')],
            'F1ApiSupport': [True, True],
        }
    return EventSchedule(events_data, year=year)


def _make_testing_schedule(year=2023):
    """Helper for a schedule with a testing event."""
    data = {
        'RoundNumber': [0],
        'Country': ['Bahrain'],
        'Location': ['Sakhir'],
        'OfficialEventName': ['Pre-Season Testing 2023'],
        'EventDate': [pd.Timestamp('2023-02-25')],
        'EventName': ['Pre-Season Testing'],
        'EventFormat': ['testing'],
        'Session1': ['Practice 1', ],
        'Session1Date': [None],
        'Session1DateUtc': [pd.Timestamp('2023-02-23')],
        'Session2': ['Practice 2'],
        'Session2Date': [None],
        'Session2DateUtc': [pd.Timestamp('2023-02-24')],
        'Session3': ['Practice 3'],
        'Session3Date': [None],
        'Session3DateUtc': [pd.Timestamp('2023-02-25')],
        'Session4': [None],
        'Session4Date': [None],
        'Session4DateUtc': [pd.NaT],
        'Session5': [None],
        'Session5Date': [None],
        'Session5DateUtc': [pd.NaT],
        'F1ApiSupport': [True],
    }
    return EventSchedule(data, year=year)


class TestSessionTypeAbbreviations:
    def test_race(self):
        assert _SESSION_TYPE_ABBREVIATIONS['R'] == 'Race'

    def test_qualifying(self):
        assert _SESSION_TYPE_ABBREVIATIONS['Q'] == 'Qualifying'

    def test_sprint(self):
        assert _SESSION_TYPE_ABBREVIATIONS['S'] == 'Sprint'

    def test_fp1(self):
        assert _SESSION_TYPE_ABBREVIATIONS['FP1'] == 'Practice 1'


class TestEventSchedule:
    def test_year_attribute(self):
        schedule = _make_schedule(year=2023)
        assert schedule.year == 2023

    def test_is_testing_false_for_conventional(self):
        schedule = _make_schedule()
        result = schedule.is_testing()
        assert not result.any()

    def test_is_testing_true_for_testing(self):
        schedule = _make_testing_schedule()
        result = schedule.is_testing()
        assert result.all()

    def test_get_event_by_round(self):
        schedule = _make_schedule()
        event = schedule.get_event_by_round(1)
        assert event['EventName'] == 'Bahrain Grand Prix'

    def test_get_event_by_round_invalid(self):
        schedule = _make_schedule()
        with pytest.raises(ValueError, match="Invalid round"):
            schedule.get_event_by_round(99)

    def test_get_event_by_round_zero_raises(self):
        schedule = _make_schedule()
        with pytest.raises(ValueError, match="Cannot get testing"):
            schedule.get_event_by_round(0)

    def test_strict_event_search(self):
        schedule = _make_schedule()
        event = schedule._strict_event_search('Bahrain Grand Prix')
        assert event['Country'] == 'Bahrain'

    def test_strict_event_search_case_insensitive(self):
        schedule = _make_schedule()
        event = schedule._strict_event_search('bahrain grand prix')
        assert event['Country'] == 'Bahrain'

    def test_strict_event_search_not_found(self):
        schedule = _make_schedule()
        with pytest.raises(KeyError, match="No exact event name"):
            schedule._strict_event_search('Nonexistent GP')

    def test_get_event_by_name_exact(self):
        schedule = _make_schedule()
        event = schedule.get_event_by_name(
            'Bahrain Grand Prix', exact_match=True
        )
        assert event['Country'] == 'Bahrain'

    def test_get_event_by_name_exact_not_found(self):
        schedule = _make_schedule()
        with pytest.raises(KeyError):
            schedule.get_event_by_name('Nope', exact_match=True)


class TestEvent:
    def _get_event(self):
        schedule = _make_schedule(year=2023)
        return schedule.iloc[0]

    def test_is_testing_false(self):
        event = self._get_event()
        assert event.is_testing() is False

    def test_is_testing_true(self):
        schedule = _make_testing_schedule()
        event = schedule.iloc[0]
        assert event.is_testing() is True

    def test_get_session_name_by_number(self):
        event = self._get_event()
        assert event.get_session_name(1) == 'Practice 1'
        assert event.get_session_name(5) == 'Race'

    def test_get_session_name_by_abbreviation(self):
        event = self._get_event()
        assert event.get_session_name('Q') == 'Qualifying'
        assert event.get_session_name('R') == 'Race'
        assert event.get_session_name('FP1') == 'Practice 1'

    def test_get_session_name_by_full_name(self):
        event = self._get_event()
        assert event.get_session_name('Qualifying') == 'Qualifying'
        assert event.get_session_name('Race') == 'Race'

    def test_get_session_name_case_insensitive(self):
        event = self._get_event()
        assert event.get_session_name('qualifying') == 'Qualifying'
        assert event.get_session_name('RACE') == 'Race'

    def test_get_session_name_invalid_string(self):
        event = self._get_event()
        with pytest.raises(ValueError, match="Invalid session type"):
            event.get_session_name('xyz')

    def test_get_session_name_invalid_number(self):
        event = self._get_event()
        with pytest.raises(ValueError, match="Invalid session type"):
            event.get_session_name(0)

    def test_get_session_name_invalid_number_6(self):
        event = self._get_event()
        with pytest.raises(ValueError, match="Invalid session type"):
            event.get_session_name(6)

    def test_get_session_date_utc(self):
        event = self._get_event()
        date = event.get_session_date('Race', utc=True)
        assert isinstance(date, pd.Timestamp)

    def test_get_session_date_nonexistent(self):
        event = self._get_event()
        with pytest.raises(ValueError):
            event.get_session_date('Sprint')
