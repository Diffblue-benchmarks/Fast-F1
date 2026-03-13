import datetime
import math

import pytest

from fastf1.ergast.structure import (
    _flatten_by_rename,
    _flatten_inline_list_of_dicts,
    _merge_dicts_of_lists,
    date_from_ergast,
    save_float,
    save_int,
    time_from_ergast,
    timedelta_from_ergast,
)


class TestDateFromErgast:
    def test_valid_date(self):
        result = date_from_ergast('2021-03-28')
        assert result == datetime.datetime(2021, 3, 28)

    def test_invalid_format(self):
        assert date_from_ergast('not-a-date') is None

    def test_empty_string(self):
        assert date_from_ergast('') is None

    def test_non_string_input(self):
        assert date_from_ergast(42) is None

    def test_none_input(self):
        assert date_from_ergast(None) is None


class TestTimeFromErgast:
    def test_hh_mm_ss(self):
        result = time_from_ergast('12:34:56')
        assert result == datetime.time(12, 34, 56)

    def test_mm_ss(self):
        result = time_from_ergast('34:56')
        assert result == datetime.time(0, 34, 56)

    def test_ss_only(self):
        result = time_from_ergast('56')
        assert result == datetime.time(0, 0, 56)

    def test_with_microseconds(self):
        result = time_from_ergast('1:23:45.678')
        assert result == datetime.time(1, 23, 45, 678000)

    def test_single_microsecond_digit(self):
        result = time_from_ergast('1:23:45.6')
        assert result == datetime.time(1, 23, 45, 600000)

    def test_with_utc_z(self):
        result = time_from_ergast('12:00:00Z')
        assert result.tzinfo == datetime.timezone.utc

    def test_with_tz_offset(self):
        result = time_from_ergast('12:00:00+05:30')
        assert result is not None
        assert result.hour == 12

    def test_empty_string(self):
        assert time_from_ergast('') is None

    def test_non_string(self):
        assert time_from_ergast(123) is None

    def test_none(self):
        assert time_from_ergast(None) is None


class TestTimedeltaFromErgast:
    def test_positive_timedelta(self):
        result = timedelta_from_ergast('1:23:45.678')
        expected = datetime.timedelta(hours=1, minutes=23, seconds=45,
                                      microseconds=678000)
        assert result == expected

    def test_negative_timedelta(self):
        result = timedelta_from_ergast('-0:01:30')
        expected = -datetime.timedelta(minutes=1, seconds=30)
        assert result == expected

    def test_positive_prefix(self):
        result = timedelta_from_ergast('+0:01:30')
        expected = datetime.timedelta(minutes=1, seconds=30)
        assert result == expected

    def test_seconds_only(self):
        result = timedelta_from_ergast('45')
        assert result == datetime.timedelta(seconds=45)

    def test_empty_string(self):
        assert timedelta_from_ergast('') is None

    def test_non_string(self):
        assert timedelta_from_ergast(42) is None

    def test_none(self):
        assert timedelta_from_ergast(None) is None


class TestSaveInt:
    def test_valid_int(self):
        assert save_int('1234') == 1234

    def test_negative_int(self):
        assert save_int('-5') == -5

    def test_positive_prefix(self):
        assert save_int('+10') == 10

    def test_empty_string(self):
        assert save_int('') == -1

    def test_float_string(self):
        assert save_int('12.34') == -1

    def test_non_numeric(self):
        assert save_int('abc') == -1

    def test_none_input(self):
        assert save_int(None) == -1


class TestSaveFloat:
    def test_valid_float(self):
        assert save_float('1234.5678') == 1234.5678

    def test_integer_string(self):
        assert save_float('42') == 42.0

    def test_negative_float(self):
        assert save_float('-3.14') == -3.14

    def test_empty_string(self):
        assert math.isnan(save_float(''))

    def test_non_numeric(self):
        assert math.isnan(save_float('abc'))

    def test_none_input(self):
        assert math.isnan(save_float(None))

    def test_dot_prefix(self):
        assert save_float('.5') == 0.5


class TestFlattenByRename:
    def test_basic_rename(self):
        nested = {'driverId': 'hamilton', 'code': 'HAM'}
        category = {
            'map': {
                'driverId': {'name': 'driver_id', 'type': str},
                'code': {'name': 'driver_code', 'type': str},
            }
        }
        flat = {}
        _flatten_by_rename(nested, category, flat)
        assert flat == {'driver_id': 'hamilton', 'driver_code': 'HAM'}

    def test_with_cast(self):
        nested = {'position': '1'}
        category = {
            'map': {'position': {'name': 'pos', 'type': int}}
        }
        flat = {}
        _flatten_by_rename(nested, category, flat)
        assert flat == {'pos': 1}

    def test_missing_key_skipped(self):
        nested = {'driverId': 'hamilton'}
        category = {
            'map': {
                'driverId': {'name': 'driver_id', 'type': str},
                'code': {'name': 'driver_code', 'type': str},
            }
        }
        flat = {}
        _flatten_by_rename(nested, category, flat)
        assert flat == {'driver_id': 'hamilton'}
        assert 'driver_code' not in flat

    def test_no_rename(self):
        nested = {'driverId': 'hamilton'}
        category = {
            'map': {'driverId': {'name': 'driver_id', 'type': str}}
        }
        flat = {}
        _flatten_by_rename(nested, category, flat, rename=False)
        assert flat == {'driverId': 'hamilton'}

    def test_no_cast(self):
        nested = {'position': '1'}
        category = {
            'map': {'position': {'name': 'pos', 'type': int}}
        }
        flat = {}
        _flatten_by_rename(nested, category, flat, cast=False)
        assert flat == {'pos': '1'}


class TestFlattenInlineListOfDicts:
    def test_basic(self):
        nested = [
            {'constructorId': 'mclaren', 'name': 'McLaren'},
            {'constructorId': 'mercedes', 'name': 'Mercedes'},
        ]
        category = {
            'map': {
                'constructorId': {'name': 'constructorIds', 'type': str},
                'name': {'name': 'constructorNames', 'type': str},
            }
        }
        flat = {}
        _flatten_inline_list_of_dicts(nested, category, flat)
        assert flat == {
            'constructorIds': ['mclaren', 'mercedes'],
            'constructorNames': ['McLaren', 'Mercedes'],
        }

    def test_missing_keys(self):
        nested = [
            {'constructorId': 'mclaren'},
            {'constructorId': 'mercedes'},
        ]
        category = {
            'map': {
                'constructorId': {'name': 'ids', 'type': str},
                'name': {'name': 'names', 'type': str},
            }
        }
        flat = {}
        _flatten_inline_list_of_dicts(nested, category, flat)
        assert flat == {'ids': ['mclaren', 'mercedes']}
        assert 'names' not in flat

    def test_no_rename(self):
        nested = [{'id': 'a'}, {'id': 'b'}]
        category = {
            'map': {'id': {'name': 'ids', 'type': str}}
        }
        flat = {}
        _flatten_inline_list_of_dicts(nested, category, flat, rename=False)
        assert flat == {'id': ['a', 'b']}


class TestMergeDictsOfLists:
    def test_single_dict(self):
        data = [{'a': [1, 2], 'b': [3, 4]}]
        result = _merge_dicts_of_lists(data)
        assert result == {'a': [1, 2], 'b': [3, 4]}

    def test_two_dicts(self):
        data = [{'a': [1, 2], 'b': [3, 4]},
                {'a': [5, 6], 'b': [7, 8]}]
        result = _merge_dicts_of_lists(data)
        assert result == {'a': [1, 2, 5, 6], 'b': [3, 4, 7, 8]}

    def test_three_dicts(self):
        data = [{'x': [1]}, {'x': [2]}, {'x': [3]}]
        result = _merge_dicts_of_lists(data)
        assert result == {'x': [1, 2, 3]}
