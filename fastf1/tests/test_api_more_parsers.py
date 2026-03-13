"""Tests for remaining _api.py parser functions: weather_data, driver_info
(full parsing), season_schedule, and livedata branch coverage."""
import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from fastf1._api import SessionNotAvailableError


class TestWeatherData:
    def test_basic_parsing(self):
        response = [
            ['0:05:00.000', {
                'AirTemp': '25.3', 'Humidity': '51.0',
                'Pressure': '1013.0', 'Rainfall': '0',
                'TrackTemp': '38.5', 'WindDirection': '180',
                'WindSpeed': '2.1',
            }],
        ]
        from fastf1._api import weather_data
        result = weather_data.__wrapped__('/test/', response=response)
        assert len(result['Time']) == 1
        assert result['AirTemp'] == [25.3]
        assert result['Rainfall'] == [False]
        assert result['WindDirection'] == [180]

    def test_rainfall_true(self):
        response = [
            ['0:05:00.000', {
                'AirTemp': '20.0', 'Humidity': '80.0',
                'Pressure': '1000.0', 'Rainfall': '1',
                'TrackTemp': '25.0', 'WindDirection': '0',
                'WindSpeed': '0.0',
            }],
        ]
        from fastf1._api import weather_data
        result = weather_data.__wrapped__('/test/', response=response)
        assert result['Rainfall'] == [True]

    def test_missing_key_defaults(self):
        response = [
            ['0:05:00.000', {'AirTemp': '25.0'}],
        ]
        from fastf1._api import weather_data
        result = weather_data.__wrapped__('/test/', response=response)
        assert len(result['Time']) == 1
        assert result['Humidity'] == [0.0]

    def test_skips_non_dict_rows(self):
        response = [
            ['0:05:00.000', 'bad'],
            ['0:06:00.000', {'AirTemp': '25.0', 'Humidity': '50.0',
                             'Pressure': '1013.0', 'Rainfall': '0',
                             'TrackTemp': '38.0', 'WindDirection': '0',
                             'WindSpeed': '0.0'}],
        ]
        from fastf1._api import weather_data
        result = weather_data.__wrapped__('/test/', response=response)
        assert len(result['Time']) == 1

    def test_livedata_branch(self):
        livedata = MagicMock()
        livedata.has.return_value = True
        livedata.get.return_value = [
            ['0:01:00.000', {'AirTemp': '20.0', 'Humidity': '50.0',
                             'Pressure': '1013.0', 'Rainfall': '0',
                             'TrackTemp': '30.0', 'WindDirection': '90',
                             'WindSpeed': '1.0'}],
        ]
        from fastf1._api import weather_data
        result = weather_data.__wrapped__('/test/', livedata=livedata)
        assert len(result['Time']) == 1
        livedata.has.assert_called_with('WeatherData')

    @patch('fastf1._api.fetch_page', return_value=None)
    def test_no_data_raises(self, mock_fetch):
        from fastf1._api import weather_data
        with pytest.raises(SessionNotAvailableError):
            weather_data.__wrapped__('/test/')


class TestSeasonSchedule:
    def test_basic(self):
        response = {'Meetings': [{'Name': 'Bahrain GP'}]}
        from fastf1._api import season_schedule
        result = season_schedule.__wrapped__('/test/', response=response)
        assert result == [{'Name': 'Bahrain GP'}]

    @patch('fastf1._api.fetch_page', return_value=None)
    def test_no_data_raises(self, mock_fetch):
        from fastf1._api import season_schedule
        with pytest.raises(SessionNotAvailableError):
            season_schedule.__wrapped__('/test/')

    @patch('fastf1._api.fetch_page')
    def test_fetches_when_no_response(self, mock_fetch):
        mock_fetch.return_value = {'Meetings': []}
        from fastf1._api import season_schedule
        result = season_schedule.__wrapped__('/test/')
        assert result == []
        mock_fetch.assert_called_once()


class TestDriverInfoFull:
    def test_multiple_drivers(self):
        response = [
            ['0:00:00.000', {
                '1': {
                    'RacingNumber': '1', 'Tla': 'VER',
                    'TeamName': 'Red Bull Racing', 'TeamColour': '3671C6',
                    'FirstName': 'Max', 'LastName': 'Verstappen',
                    'BroadcastName': 'M VERSTAPPEN',
                },
                '44': {
                    'RacingNumber': '44', 'Tla': 'HAM',
                    'TeamName': 'Mercedes', 'TeamColour': '27F4D2',
                    'FirstName': 'Lewis', 'LastName': 'Hamilton',
                    'BroadcastName': 'L HAMILTON',
                },
            }],
        ]
        from fastf1._api import driver_info
        result = driver_info.__wrapped__('/test/', response=response)
        assert '1' in result
        assert '44' in result
        assert result['44']['Tla'] == 'HAM'

    def test_incremental_updates(self):
        response = [
            ['0:00:00.000', {
                '1': {'RacingNumber': '1', 'Tla': 'VER'},
            }],
            ['0:00:01.000', {
                '1': {'TeamName': 'Red Bull Racing'},
            }],
        ]
        from fastf1._api import driver_info
        result = driver_info.__wrapped__('/test/', response=response)
        assert result['1']['Tla'] == 'VER'
        assert result['1']['TeamName'] == 'Red Bull Racing'

    def test_delayed_driver_skipped(self):
        response = [
            ['0:00:00.000', {'1': {'RacingNumber': '1', 'Tla': 'VER'}}],
            ['2:00:00.000', {'99': {'RacingNumber': '99', 'Tla': 'NEW'}}],
        ]
        from fastf1._api import driver_info
        result = driver_info.__wrapped__('/test/', response=response)
        assert '1' in result
        assert '99' not in result

    def test_livedata_branch(self):
        livedata = MagicMock()
        livedata.has.return_value = True
        livedata.get.return_value = [
            ['0:00:00.000', {'1': {'RacingNumber': '1', 'Tla': 'VER'}}],
        ]
        from fastf1._api import driver_info
        result = driver_info.__wrapped__('/test/', livedata=livedata)
        assert '1' in result

    def test_ignores_unknown_keys(self):
        response = [
            ['0:00:00.000', {
                '1': {'RacingNumber': '1', 'UnknownKey': 'value'},
            }],
        ]
        from fastf1._api import driver_info
        result = driver_info.__wrapped__('/test/', response=response)
        assert 'UnknownKey' not in result['1']


class TestLivedataBranches:
    """Test the livedata code paths in parsers that we haven't covered yet."""

    def test_track_status_livedata(self):
        livedata = MagicMock()
        livedata.has.return_value = True
        livedata.get.return_value = [
            ['0:01:00.000', {'Status': '1', 'Message': 'AllClear'}],
        ]
        from fastf1._api import track_status_data
        result = track_status_data.__wrapped__('/test/', livedata=livedata)
        assert result['Status'] == ['1']

    def test_session_status_livedata(self):
        livedata = MagicMock()
        livedata.has.return_value = True
        livedata.get.return_value = [
            ['0:00:00.000', {'Status': 'Started'}],
        ]
        from fastf1._api import session_status_data
        result = session_status_data.__wrapped__('/test/', livedata=livedata)
        assert result['Status'] == ['Started']

    def test_race_control_messages_livedata(self):
        livedata = MagicMock()
        livedata.has.return_value = True
        livedata.get.return_value = [
            ['0:01:00.000', {
                'Messages': [{'Utc': '2023-03-05T15:01:00Z',
                              'Category': 'Flag', 'Message': 'GREEN'}]
            }],
        ]
        from fastf1._api import race_control_messages
        result = race_control_messages.__wrapped__('/test/', livedata=livedata)
        assert result['Category'] == ['Flag']

    def test_lap_count_livedata(self):
        livedata = MagicMock()
        livedata.has.return_value = True
        livedata.get.return_value = [
            ['0:01:00.000', {'TotalLaps': 57, 'CurrentLap': 1}],
        ]
        from fastf1._api import lap_count
        result = lap_count.__wrapped__('/test/', livedata=livedata)
        assert result['TotalLaps'] == [57]

    def test_session_info_livedata(self):
        livedata = MagicMock()
        livedata.has.return_value = True
        livedata.get.return_value = [
            ('0:00:00.000', {
                'StartDate': '2023-03-05T15:00:00Z',
                'EndDate': '2023-03-05T17:00:00Z',
                'GmtOffset': '3:00:00',
            }),
        ]
        from fastf1._api import session_info
        result = session_info.__wrapped__('/test/', livedata=livedata)
        assert isinstance(result['StartDate'], datetime.datetime)

    @patch('fastf1._api.fetch_page', return_value=None)
    def test_track_status_no_data_raises(self, _):
        from fastf1._api import track_status_data
        with pytest.raises(SessionNotAvailableError):
            track_status_data.__wrapped__('/test/')

    @patch('fastf1._api.fetch_page', return_value=None)
    def test_session_status_no_data_raises(self, _):
        from fastf1._api import session_status_data
        with pytest.raises(SessionNotAvailableError):
            session_status_data.__wrapped__('/test/')

    @patch('fastf1._api.fetch_page', return_value=None)
    def test_race_control_no_data_raises(self, _):
        from fastf1._api import race_control_messages
        with pytest.raises(SessionNotAvailableError):
            race_control_messages.__wrapped__('/test/')

    @patch('fastf1._api.fetch_page', return_value=None)
    def test_lap_count_no_data_raises(self, _):
        from fastf1._api import lap_count
        with pytest.raises(SessionNotAvailableError):
            lap_count.__wrapped__('/test/')

    @patch('fastf1._api.fetch_page', return_value=None)
    def test_session_info_no_data_raises(self, _):
        from fastf1._api import session_info
        with pytest.raises(SessionNotAvailableError):
            session_info.__wrapped__('/test/')

    @patch('fastf1._api.fetch_page', return_value=None)
    def test_driver_info_no_data_raises(self, _):
        from fastf1._api import driver_info
        with pytest.raises(SessionNotAvailableError):
            driver_info.__wrapped__('/test/')
