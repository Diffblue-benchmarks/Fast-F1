import datetime
import pytest

from fastf1.ergast.structure import (
    date_from_ergast,
    time_from_ergast,
    timedelta_from_ergast,
    save_int,
    save_float,
    _flatten_by_rename,
    _flatten_inline_list_of_dicts,
    _lap_timings_flatten_by_rename,
    _merge_dicts_of_lists
)


class TestDateFromErgast:
    """Tests for date_from_ergast function"""

    def test_non_string_input(self):
        """Test with non-string input returns None"""
        assert date_from_ergast(123) is None
        assert date_from_ergast(None) is None
        assert date_from_ergast([]) is None

    def test_empty_string(self):
        """Test with empty string returns None"""
        assert date_from_ergast("") is None

    def test_invalid_date_format(self):
        """Test with invalid date format returns None"""
        assert date_from_ergast("invalid-date") is None
        assert date_from_ergast("2023-13-45") is None
        assert date_from_ergast("not-a-date") is None


class TestTimeFromErgast:
    """Tests for time_from_ergast function"""

    def test_non_string_input(self):
        """Test with non-string input returns None"""
        assert time_from_ergast(123) is None
        assert time_from_ergast(None) is None
        assert time_from_ergast({}) is None

    def test_empty_string(self):
        """Test with empty string returns None"""
        assert time_from_ergast("") is None

    def test_invalid_format(self):
        """Test with invalid time format returns None"""
        assert time_from_ergast("not-a-time") is None
        assert time_from_ergast("xyz:abc") is None

    def test_timezone_offset(self):
        """Test parsing time with timezone offset"""
        result = time_from_ergast("12:34:56+05:30")
        assert result is not None
        assert result.hour == 12
        assert result.minute == 34
        assert result.second == 56
        assert result.tzinfo is not None

    def test_invalid_time_values(self):
        """Test with time values that are out of range"""
        assert time_from_ergast("25:00:00") is None
        assert time_from_ergast("12:60:00") is None
        assert time_from_ergast("12:00:60") is None


class TestTimedeltaFromErgast:
    """Tests for timedelta_from_ergast function"""

    def test_non_string_input(self):
        """Test with non-string input returns None"""
        assert timedelta_from_ergast(123) is None
        assert timedelta_from_ergast(None) is None
        assert timedelta_from_ergast([]) is None

    def test_negative_timedelta(self):
        """Test parsing negative timedelta"""
        result = timedelta_from_ergast("-1:30.5")
        assert result is not None
        assert result.total_seconds() < 0

    def test_invalid_time_returns_none(self):
        """Test that invalid time strings return None"""
        result = timedelta_from_ergast("invalid")
        assert result is None


class TestSaveInt:
    """Tests for save_int function"""

    def test_non_string_input(self):
        """Test with non-string input returns -1"""
        assert save_int(None) == -1
        assert save_int([]) == -1
        assert save_int({}) == -1

    def test_invalid_string(self):
        """Test with invalid string returns -1"""
        assert save_int("") == -1
        assert save_int("abc") == -1
        assert save_int("12.34") == -1
        assert save_int("12abc") == -1


class TestSaveFloat:
    """Tests for save_float function"""

    def test_non_string_input(self):
        """Test with non-string input returns nan"""
        result = save_float(None)
        assert result != result  # nan != nan
        result = save_float([])
        assert result != result

    def test_invalid_string(self):
        """Test with invalid string returns nan"""
        result = save_float("")
        assert result != result
        result = save_float("abc")
        assert result != result
        result = save_float("12abc")
        assert result != result


class TestFlattenByRename:
    """Tests for _flatten_by_rename function"""

    def test_flatten_without_rename(self):
        """Test flattening without renaming keys"""
        nested = {'testKey': 'testValue'}
        category = {
            'map': {
                'testKey': {
                    'name': 'renamedKey',
                    'type': str
                }
            }
        }
        flat = {}

        _flatten_by_rename(nested, category, flat, cast=True, rename=False)

        assert 'testKey' in flat
        assert flat['testKey'] == 'testValue'
        assert 'renamedKey' not in flat


class TestFlattenInlineListOfDicts:
    """Tests for _flatten_inline_list_of_dicts function"""

    def test_flatten_list_with_cast(self):
        """Test flattening list of dicts with type casting"""
        nested = [
            {'id': '1', 'name': 'first'},
            {'id': '2', 'name': 'second'}
        ]
        category = {
            'map': {
                'id': {'name': 'ids', 'type': int},
                'name': {'name': 'names', 'type': str}
            }
        }
        flat = {}

        _flatten_inline_list_of_dicts(nested, category, flat, cast=True, rename=True)

        assert flat['ids'] == [1, 2]
        assert flat['names'] == ['first', 'second']

    def test_flatten_list_without_rename(self):
        """Test flattening list of dicts without renaming"""
        nested = [
            {'id': '1'},
            {'id': '2'}
        ]
        category = {
            'map': {
                'id': {'name': 'ids', 'type': int}
            }
        }
        flat = {}

        _flatten_inline_list_of_dicts(nested, category, flat, cast=True, rename=False)

        assert 'id' in flat
        assert flat['id'] == [1, 2]

    def test_flatten_list_with_missing_keys(self):
        """Test flattening list where some dicts lack keys"""
        nested = [
            {'id': '1', 'name': 'first'},
            {'id': '2'},
            {'id': '3', 'name': 'third'}
        ]
        category = {
            'map': {
                'id': {'name': 'ids', 'type': int},
                'name': {'name': 'names', 'type': str}
            }
        }
        flat = {}

        _flatten_inline_list_of_dicts(nested, category, flat, cast=True, rename=True)

        assert flat['ids'] == [1, 2, 3]
        assert flat['names'] == ['first', 'third']

    def test_flatten_empty_list(self):
        """Test flattening empty list produces no entries"""
        nested = []
        category = {
            'map': {
                'id': {'name': 'ids', 'type': int}
            }
        }
        flat = {}

        _flatten_inline_list_of_dicts(nested, category, flat, cast=True, rename=True)

        assert 'ids' not in flat


class TestLapTimingsFlattenByRename:
    """Tests for _lap_timings_flatten_by_rename function"""

    def test_lap_timings_flatten(self):
        """Test flattening lap timings with Timings subcategory"""
        nested = {
            'number': '5',
            'Timings': [
                {'driverId': 'ham', 'position': '1', 'time': '1:30.5'},
                {'driverId': 'ver', 'position': '2', 'time': '1:31.0'}
            ]
        }

        # Define the category structures
        timings_category = {
            'name': 'Timings',
            'type': list,
            'method': _flatten_inline_list_of_dicts,
            'map': {
                'driverId': {'name': 'driverId', 'type': str},
                'position': {'name': 'position', 'type': int},
                'time': {'name': 'time', 'type': str}
            }
        }

        category = {
            'map': {
                'number': {'name': 'number', 'type': int}
            }
        }
        flat = {}

        # Manually set up Timings reference for the function
        import fastf1.ergast.structure as structure_module
        original_timings = structure_module.Timings if hasattr(structure_module, 'Timings') else None
        structure_module.Timings = timings_category

        try:
            _lap_timings_flatten_by_rename(nested, category, flat, cast=True, rename=True)

            assert 'number' in flat
            assert isinstance(flat['number'], list)
            assert len(flat['number']) == len(flat['driverId'])
            assert all(n == 5 for n in flat['number'])
        finally:
            if original_timings is not None:
                structure_module.Timings = original_timings


class TestMergeDictsOfLists:
    """Tests for _merge_dicts_of_lists function"""

    def test_merge_single_dict(self):
        """Test merging a single dict returns it unchanged"""
        data = [{'value': [1, 2, 3], 'name': ['a', 'b', 'c']}]
        result = _merge_dicts_of_lists(data)

        assert result == {'value': [1, 2, 3], 'name': ['a', 'b', 'c']}

    def test_merge_multiple_dicts(self):
        """Test merging multiple dicts combines their lists"""
        data = [
            {'value': [1, 2, 3], 'name': ['a', 'b', 'c']},
            {'value': [4, 5, 6], 'name': ['d', 'e', 'f']},
            {'value': [7, 8], 'name': ['g', 'h']}
        ]
        result = _merge_dicts_of_lists(data)

        assert result['value'] == [1, 2, 3, 4, 5, 6, 7, 8]
        assert result['name'] == ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

    def test_merge_two_dicts(self):
        """Test merging exactly two dicts"""
        data = [
            {'value': [1, 2], 'name': ['a', 'b']},
            {'value': [3, 4], 'name': ['c', 'd']}
        ]
        result = _merge_dicts_of_lists(data)

        assert result['value'] == [1, 2, 3, 4]
        assert result['name'] == ['a', 'b', 'c', 'd']
