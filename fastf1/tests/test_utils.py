import datetime

import pytest

from fastf1.utils import (
    recursive_dict_get,
    to_datetime,
    to_timedelta,
)


class TestRecursiveDictGet:
    def test_single_key(self):
        d = {'a': 1}
        assert recursive_dict_get(d, 'a') == 1

    def test_nested_keys(self):
        d = {'a': {'b': {'c': 42}}}
        assert recursive_dict_get(d, 'a', 'b', 'c') == 42

    def test_missing_key_returns_empty_dict(self):
        d = {'a': 1}
        assert recursive_dict_get(d, 'x') == {}

    def test_missing_nested_key_returns_empty_dict(self):
        d = {'a': {'b': 1}}
        assert recursive_dict_get(d, 'a', 'z') == {}

    def test_default_none_true_missing_key(self):
        d = {'a': 1}
        assert recursive_dict_get(d, 'x', default_none=True) is None

    def test_default_none_false_missing_key(self):
        d = {'a': 1}
        assert recursive_dict_get(d, 'x', default_none=False) == {}

    def test_default_none_true_existing_key(self):
        d = {'a': {'b': 42}}
        assert recursive_dict_get(d, 'a', 'b', default_none=True) == 42

    def test_empty_dict(self):
        d = {}
        assert recursive_dict_get(d, 'a') == {}

    def test_deeply_nested(self):
        d = {'a': {'b': {'c': {'d': {'e': 'deep'}}}}}
        assert recursive_dict_get(d, 'a', 'b', 'c', 'd', 'e') == 'deep'


class TestToTimedelta:
    def test_seconds_only(self):
        result = to_timedelta('46')
        assert result == datetime.timedelta(seconds=46)

    def test_seconds_with_milliseconds(self):
        result = to_timedelta('24.356')
        assert result == datetime.timedelta(seconds=24, microseconds=356000)

    def test_seconds_with_microseconds(self):
        result = to_timedelta('24.356412')
        assert result == datetime.timedelta(seconds=24, microseconds=356412)

    def test_minutes_and_seconds(self):
        result = to_timedelta('36:54')
        assert result == datetime.timedelta(minutes=36, seconds=54)

    def test_hours_minutes_seconds(self):
        result = to_timedelta('8:45:46')
        assert result == datetime.timedelta(hours=8, minutes=45, seconds=46)

    def test_full_format_with_microseconds(self):
        result = to_timedelta('13:24:46.320215')
        expected = datetime.timedelta(
            hours=13, minutes=24, seconds=46, microseconds=320215
        )
        assert result == expected

    def test_short_microseconds_padded(self):
        result = to_timedelta('1:23.4')
        expected = datetime.timedelta(minutes=1, seconds=23, microseconds=400000)
        assert result == expected

    def test_long_microseconds_truncated(self):
        result = to_timedelta('1:23.1234567')
        expected = datetime.timedelta(minutes=1, seconds=23, microseconds=123456)
        assert result == expected

    def test_passthrough_timedelta(self):
        td = datetime.timedelta(seconds=10)
        assert to_timedelta(td) is td

    def test_empty_string_returns_none(self):
        assert to_timedelta('') is None

    def test_none_returns_none(self):
        assert to_timedelta(None) is None

    def test_invalid_string_returns_none(self):
        assert to_timedelta('not_a_time') is None

    def test_integer_returns_none(self):
        assert to_timedelta(42) is None


class TestToDatetime:
    def test_full_format(self):
        result = to_datetime('2020-12-13T13:27:15.320000')
        expected = datetime.datetime(2020, 12, 13, 13, 27, 15, 320000)
        assert result == expected

    def test_with_trailing_z(self):
        result = to_datetime('2020-12-13T13:27:15.320000Z')
        expected = datetime.datetime(2020, 12, 13, 13, 27, 15, 320000)
        assert result == expected

    def test_short_microseconds(self):
        result = to_datetime('2020-12-13T13:27:15.32Z')
        expected = datetime.datetime(2020, 12, 13, 13, 27, 15, 320000)
        assert result == expected

    def test_no_microseconds(self):
        result = to_datetime('2020-12-13T13:27:15')
        expected = datetime.datetime(2020, 12, 13, 13, 27, 15)
        assert result == expected

    def test_long_microseconds_truncated(self):
        result = to_datetime('2020-12-13T13:27:15.1234567')
        expected = datetime.datetime(2020, 12, 13, 13, 27, 15, 123456)
        assert result == expected

    def test_passthrough_datetime(self):
        dt = datetime.datetime(2021, 1, 1)
        assert to_datetime(dt) is dt

    def test_empty_string_returns_none(self):
        assert to_datetime('') is None

    def test_none_returns_none(self):
        assert to_datetime(None) is None

    def test_invalid_string_returns_none(self):
        assert to_datetime('not_a_datetime') is None

    def test_integer_returns_none(self):
        assert to_datetime(42) is None
