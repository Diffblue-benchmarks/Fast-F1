import datetime
import warnings
from unittest.mock import MagicMock, Mock

import numpy as np
import pandas as pd
import pytest

from fastf1.utils import delta_time, recursive_dict_get, to_timedelta, to_datetime


class TestDeltaTime:
    """Tests for delta_time function"""

    def test_delta_time_deprecation_warning(self):
        """Test that delta_time raises FutureWarning (lines 85-88)"""
        # Create mock laps with necessary methods
        ref_lap = Mock()
        comp_lap = Mock()

        # Create mock telemetry data with required fields
        ref_telemetry = pd.DataFrame({
            'Time': pd.to_timedelta([0, 1, 2], unit='s'),
            'Distance': [0.0, 100.0, 200.0],
            'Speed': [0, 100, 200]
        })

        comp_telemetry = pd.DataFrame({
            'Time': pd.to_timedelta([0, 1.1, 2.2], unit='s'),
            'Distance': [0.0, 95.0, 190.0],
            'Speed': [0, 95, 190]
        })

        # Make add_distance() return self
        ref_telemetry.add_distance = Mock(return_value=ref_telemetry)
        comp_telemetry.add_distance = Mock(return_value=comp_telemetry)

        # Configure mocks to return telemetry
        ref_lap.get_car_data = Mock(return_value=ref_telemetry)
        comp_lap.get_car_data = Mock(return_value=comp_telemetry)

        # Test that FutureWarning is raised
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = delta_time(ref_lap, comp_lap)

            assert len(w) == 1
            assert issubclass(w[0].category, FutureWarning)
            assert "deprecated" in str(w[0].message)

    def test_delta_time_basic_computation(self):
        """Test basic delta time computation (lines 90-108)"""
        # Create mock laps
        ref_lap = Mock()
        comp_lap = Mock()

        # Create telemetry with more data points for mini_pro
        ref_telemetry = pd.DataFrame({
            'Time': pd.to_timedelta([0, 1, 2, 3, 4], unit='s'),
            'Distance': [0.0, 50.0, 100.0, 150.0, 200.0],
            'Speed': [0, 50, 100, 150, 200]
        })

        comp_telemetry = pd.DataFrame({
            'Time': pd.to_timedelta([0, 1.2, 2.4, 3.6, 4.8], unit='s'),
            'Distance': [0.0, 45.0, 90.0, 135.0, 180.0],
            'Speed': [0, 45, 90, 135, 180]
        })

        ref_telemetry.add_distance = Mock(return_value=ref_telemetry)
        comp_telemetry.add_distance = Mock(return_value=comp_telemetry)

        ref_lap.get_car_data = Mock(return_value=ref_telemetry)
        comp_lap.get_car_data = Mock(return_value=comp_telemetry)

        # Suppress the deprecation warning for this test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            delta, ref_tel, comp_tel = delta_time(ref_lap, comp_lap)

        # Verify results
        assert isinstance(delta, (pd.Series, np.ndarray))
        assert len(delta) == len(ref_telemetry)
        assert ref_tel is ref_telemetry
        assert comp_tel is comp_telemetry

        # Verify get_car_data was called with correct parameters
        ref_lap.get_car_data.assert_called_once_with(interpolate_edges=True)
        comp_lap.get_car_data.assert_called_once_with(interpolate_edges=True)


class TestRecursiveDictGet:
    """Tests for recursive_dict_get function"""

    def test_default_none_returns_none_for_empty_dict(self):
        """Test that default_none=True returns None for empty result (line 117)"""
        d = {'a': {'b': 'value'}}

        # Try to get a non-existent key with default_none=True
        result = recursive_dict_get(d, 'x', 'y', default_none=True)

        assert result is None

    def test_default_none_false_returns_empty_dict(self):
        """Test that default_none=False returns empty dict"""
        d = {'a': {'b': 'value'}}

        result = recursive_dict_get(d, 'x', 'y', default_none=False)

        assert result == {}

    def test_successful_nested_retrieval(self):
        """Test successful retrieval of nested value"""
        d = {'a': {'b': {'c': 'value'}}}

        result = recursive_dict_get(d, 'a', 'b', 'c')

        assert result == 'value'

    def test_partial_path_exists(self):
        """Test when partial path exists but not complete"""
        d = {'a': {'b': {'d': 'value'}}}

        result = recursive_dict_get(d, 'a', 'b', 'c')

        assert result == {}


class TestToTimedelta:
    """Tests for to_timedelta function"""

    def test_microseconds_more_than_6_digits(self):
        """Test truncating microseconds longer than 6 digits (lines 158-159)"""
        # String with 9 digits after decimal (nanoseconds precision)
        result = to_timedelta("12.123456789")

        expected = datetime.timedelta(seconds=12, microseconds=123456)
        assert result == expected

    def test_microseconds_less_than_6_digits(self):
        """Test padding microseconds shorter than 6 digits (line 157)"""
        result = to_timedelta("12.123")

        expected = datetime.timedelta(seconds=12, microseconds=123000)
        assert result == expected

    def test_invalid_string_returns_none(self):
        """Test that invalid string returns None (lines 168-171)"""
        result = to_timedelta("invalid:time:format:extra")

        assert result is None

    def test_malformed_time_string(self):
        """Test that malformed time returns None"""
        result = to_timedelta("abc:def:ghi")

        assert result is None

    def test_timedelta_input_returns_same(self):
        """Test that timedelta input is returned unchanged (line 174)"""
        td = datetime.timedelta(hours=1, minutes=30, seconds=45)

        result = to_timedelta(td)

        assert result is td

    def test_empty_string_returns_none(self):
        """Test that empty string returns None (line 177)"""
        result = to_timedelta("")

        assert result is None

    def test_none_input_returns_none(self):
        """Test that None input returns None"""
        result = to_timedelta(None)

        assert result is None

    def test_valid_hhmmss_format(self):
        """Test valid HH:MM:SS format"""
        result = to_timedelta("1:30:45")

        expected = datetime.timedelta(hours=1, minutes=30, seconds=45)
        assert result == expected

    def test_valid_mmss_format(self):
        """Test valid MM:SS format"""
        result = to_timedelta("30:45")

        expected = datetime.timedelta(minutes=30, seconds=45)
        assert result == expected

    def test_valid_seconds_only(self):
        """Test valid seconds only format"""
        result = to_timedelta("45.5")

        expected = datetime.timedelta(seconds=45, microseconds=500000)
        assert result == expected


class TestToDatetime:
    """Tests for to_datetime function"""

    def test_datetime_with_microseconds_short(self):
        """Test datetime with microseconds less than 6 digits (lines 208-209)"""
        result = to_datetime("2021-05-23T13:27:15.32")

        expected = datetime.datetime(2021, 5, 23, 13, 27, 15, 320000)
        assert result == expected

    def test_datetime_with_microseconds_long(self):
        """Test datetime with microseconds more than 6 digits (lines 210-211)"""
        result = to_datetime("2021-05-23T13:27:15.123456789")

        expected = datetime.datetime(2021, 5, 23, 13, 27, 15, 123456)
        assert result == expected

    def test_datetime_without_microseconds(self):
        """Test datetime without microseconds (line 213)"""
        result = to_datetime("2021-05-23T13:27:15")

        expected = datetime.datetime(2021, 5, 23, 13, 27, 15, 0)
        assert result == expected

    def test_datetime_with_trailing_z(self):
        """Test datetime with trailing Z"""
        result = to_datetime("2021-05-23T13:27:15.320000Z")

        expected = datetime.datetime(2021, 5, 23, 13, 27, 15, 320000)
        assert result == expected

    def test_invalid_datetime_string_returns_none(self):
        """Test that invalid datetime string returns None (lines 220-223)"""
        result = to_datetime("not-a-valid-datetime")

        assert result is None

    def test_malformed_datetime_string(self):
        """Test that malformed datetime returns None"""
        result = to_datetime("2021-13-45T25:70:99")

        assert result is None

    def test_datetime_input_returns_same(self):
        """Test that datetime input is returned unchanged (line 226)"""
        dt = datetime.datetime(2021, 5, 23, 13, 27, 15)

        result = to_datetime(dt)

        assert result is dt

    def test_empty_string_returns_none(self):
        """Test that empty string returns None (line 229)"""
        result = to_datetime("")

        assert result is None

    def test_none_input_returns_none(self):
        """Test that None input returns None"""
        result = to_datetime(None)

        assert result is None

    def test_datetime_with_exact_6_microseconds(self):
        """Test datetime with exactly 6 digit microseconds"""
        result = to_datetime("2021-05-23T13:27:15.123456")

        expected = datetime.datetime(2021, 5, 23, 13, 27, 15, 123456)
        assert result == expected
