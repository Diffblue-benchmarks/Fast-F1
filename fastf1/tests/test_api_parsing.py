"""Tests for _api.py parsing functions using mocked network calls."""
import base64
import datetime
import json
import zlib
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from fastf1._api import (
    SessionNotAvailableError,
    _stream_data_driver,
    fetch_page,
    parse,
    EMPTY_STREAM,
)


class TestParse:
    def test_parse_json_dict(self):
        result = parse('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_plain_string(self):
        result = parse('hello world')
        assert result == 'hello world'

    def test_parse_quoted_string(self):
        result = parse('"some text"')
        assert result == 'some text'

    def test_parse_zipped_data(self):
        inner = '{"data": 42}'
        compressed = zlib.compress(inner.encode('utf-8-sig'), level=6)
        # strip the zlib header (first 2 bytes) and checksum (last 4 bytes)
        raw_deflate = compressed[2:-4]
        encoded = base64.b64encode(raw_deflate).decode('ascii')
        result = parse(f'"{encoded}"', zipped=True)
        assert result == {"data": 42}

    def test_parse_nested_json(self):
        data = '{"a": {"b": [1, 2, 3]}}'
        result = parse(data)
        assert result['a']['b'] == [1, 2, 3]


class TestFetchPage:
    @patch('fastf1._api.Cache')
    def test_fetch_page_success_json(self, mock_cache):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'{"MeetingKey": 1234}'
        mock_cache.requests_get.return_value = mock_resp

        result = fetch_page('/static/2023/', 'index')
        assert result == {"MeetingKey": 1234}

    @patch('fastf1._api.Cache')
    def test_fetch_page_success_json_stream(self, mock_cache):
        record1 = '00:01:00.000{"Status": "1", "Message": "AllClear"}'
        record2 = '00:02:00.000{"Status": "2", "Message": "Yellow"}'
        raw = f'{record1}\r\n{record2}\r\n'

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = raw.encode('utf-8-sig')
        mock_cache.requests_get.return_value = mock_resp

        result = fetch_page('/static/2023/', 'track_status')
        assert len(result) == 2
        assert result[0][0] == '00:01:00.000'
        assert result[0][1] == {"Status": "1", "Message": "AllClear"}

    @patch('fastf1._api.Cache')
    def test_fetch_page_fallback_to_mirror(self, mock_cache):
        fail_resp = MagicMock()
        fail_resp.status_code = 404

        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.content = b'{"ok": true}'

        mock_cache.requests_get.side_effect = [fail_resp, ok_resp]

        result = fetch_page('/static/2023/', 'index')
        assert result == {"ok": True}
        assert mock_cache.requests_get.call_count == 2

    @patch('fastf1._api.Cache')
    def test_fetch_page_both_fail_returns_none(self, mock_cache):
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        mock_cache.requests_get.return_value = fail_resp

        result = fetch_page('/static/2023/', 'index')
        assert result is None

    @patch('fastf1._api.Cache')
    def test_fetch_page_car_data_returns_raw_records(self, mock_cache):
        raw = '00:00:00.000somedata\r\n00:00:00.240otherdata\r\n'
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = raw.encode('utf-8-sig')
        mock_cache.requests_get.return_value = mock_resp

        result = fetch_page('/static/2023/', 'car_data')
        assert isinstance(result, list)
        assert len(result) == 2
        # car_data returns raw strings, not parsed
        assert isinstance(result[0], str)


class TestTrackStatusData:
    @patch('fastf1._api.fetch_page')
    def test_track_status_parsing(self, mock_fetch):
        mock_fetch.return_value = [
            ['0:01:00.000', {'Status': '1', 'Message': 'AllClear'}],
            ['0:02:00.000', {'Status': '2', 'Message': 'Yellow'}],
        ]

        from fastf1._api import track_status_data
        # bypass the cache wrapper
        result = track_status_data.__wrapped__(
            '/test/', response=mock_fetch.return_value
        )

        assert len(result['Time']) == 2
        assert result['Status'] == ['1', '2']
        assert result['Message'] == ['AllClear', 'Yellow']

    def test_track_status_skips_short_entries(self):
        response = [
            ['0:01:00.000', {'Status': '1', 'Message': 'AllClear'}],
            ['short'],  # should be skipped
        ]

        from fastf1._api import track_status_data
        result = track_status_data.__wrapped__('/test/', response=response)
        assert len(result['Time']) == 1

    def test_track_status_skips_non_dict_rows(self):
        response = [
            ['0:01:00.000', {'Status': '1', 'Message': 'AllClear'}],
            ['0:02:00.000', 'not a dict'],
        ]

        from fastf1._api import track_status_data
        result = track_status_data.__wrapped__('/test/', response=response)
        assert len(result['Time']) == 1


class TestSessionStatusData:
    def test_session_status_parsing(self):
        response = [
            ['0:00:00.000', {'Status': 'Started'}],
            ['1:30:00.000', {'Status': 'Finished'}],
        ]

        from fastf1._api import session_status_data
        result = session_status_data.__wrapped__('/test/', response=response)
        assert result['Status'] == ['Started', 'Finished']
        assert len(result['Time']) == 2

    def test_session_status_skips_non_dict(self):
        response = [
            ['0:00:00.000', {'Status': 'Started'}],
            ['0:01:00.000', 'invalid'],
        ]
        from fastf1._api import session_status_data
        result = session_status_data.__wrapped__('/test/', response=response)
        assert len(result['Status']) == 1

    def test_session_status_skips_missing_status_key(self):
        response = [
            ['0:00:00.000', {'Status': 'Started'}],
            ['0:01:00.000', {'NoStatus': 'here'}],
        ]
        from fastf1._api import session_status_data
        result = session_status_data.__wrapped__('/test/', response=response)
        assert len(result['Status']) == 1


class TestRaceControlMessages:
    def test_basic_parsing(self):
        response = [
            ['0:01:00.000', {
                'Messages': [
                    {
                        'Utc': '2023-03-05T15:01:00.000Z',
                        'Category': 'Flag',
                        'Message': 'GREEN FLAG',
                        'Flag': 'GREEN',
                        'Scope': 'Track',
                    }
                ]
            }],
        ]

        from fastf1._api import race_control_messages
        result = race_control_messages.__wrapped__('/test/', response=response)
        assert len(result['Time']) == 1
        assert result['Category'] == ['Flag']
        assert result['Message'] == ['GREEN FLAG']
        assert result['Flag'] == ['GREEN']

    def test_messages_as_dict(self):
        response = [
            ['0:01:00.000', {
                'Messages': {
                    '0': {
                        'Utc': '2023-03-05T15:01:00.000Z',
                        'Category': 'Other',
                        'Message': 'DRS ENABLED',
                    }
                }
            }],
        ]

        from fastf1._api import race_control_messages
        result = race_control_messages.__wrapped__('/test/', response=response)
        assert len(result['Time']) == 1
        assert result['Category'] == ['Other']

    def test_missing_optional_keys(self):
        response = [
            ['0:01:00.000', {
                'Messages': [{
                    'Utc': '2023-03-05T15:01:00.000Z',
                    'Category': 'Other',
                    'Message': 'Test',
                }]
            }],
        ]

        from fastf1._api import race_control_messages
        result = race_control_messages.__wrapped__('/test/', response=response)
        assert result['Flag'] == [None]
        assert result['Scope'] == [None]
        assert result['Sector'] == [None]


class TestLapCount:
    def test_basic_parsing(self):
        response = [
            ['0:01:00.000', {'TotalLaps': 57, 'CurrentLap': 1}],
            ['0:02:30.000', {'CurrentLap': 2}],
        ]

        from fastf1._api import lap_count
        result = lap_count.__wrapped__('/test/', response=response)
        assert result['TotalLaps'] == [57, None]
        assert result['CurrentLap'] == [1, 2]
        assert len(result['Time']) == 2


class TestStreamDataDriver:
    def test_basic_stream(self):
        driver_raw = [
            ('0:01:00.000', {'Position': '1'}),
            ('0:01:01.000', {'Position': '1',
                             'GapToLeader': 'LAP',
                             'IntervalToPositionAhead': {'Value': '0.5'}}),
        ]
        result = _stream_data_driver(driver_raw, EMPTY_STREAM, '44')
        assert len(result['Time']) == 2
        assert result['Driver'] == ['44', '44']
        assert result['Position'] == [1, 1]

    def test_no_new_entries(self):
        driver_raw = [
            ('0:01:00.000', {'SomeOtherKey': 'value'}),
        ]
        result = _stream_data_driver(driver_raw, EMPTY_STREAM, '44')
        # no new_entry triggers, so we get zero rows (initial row minus 1)
        assert len(result['Time']) == 0


class TestDriverInfo:
    def test_basic_parsing(self):
        response = [
            ['0:00:00.000', {
                '1': {
                    'RacingNumber': '1',
                    'BroadcastName': 'M VERSTAPPEN',
                    'FullName': 'Max VERSTAPPEN',
                    'Tla': 'VER',
                    'TeamName': 'Red Bull Racing',
                    'TeamColour': '3671C6',
                    'FirstName': 'Max',
                    'LastName': 'Verstappen',
                }
            }],
        ]

        from fastf1._api import driver_info
        result = driver_info.__wrapped__('/test/', response=response)
        assert '1' in result
        assert result['1']['Tla'] == 'VER'
        assert result['1']['TeamName'] == 'Red Bull Racing'


class TestSessionInfo:
    def test_basic_parsing(self):
        response = [
            ('0:00:00.000', {
                'Meeting': {'Name': 'Bahrain Grand Prix'},
                'StartDate': '2023-03-05T15:00:00.000Z',
                'EndDate': '2023-03-05T17:00:00.000Z',
                'GmtOffset': '3:00:00',
                'Type': 'Race',
            }),
        ]

        from fastf1._api import session_info
        result = session_info.__wrapped__('/test/', response=response)
        assert isinstance(result['StartDate'], datetime.datetime)
        assert isinstance(result['EndDate'], datetime.datetime)
        assert isinstance(result['GmtOffset'], datetime.timedelta)
        assert result['Type'] == 'Race'


class TestTimingAppData:
    def test_basic_parsing(self):
        response = [
            ['0:05:00.000', {
                'Lines': {
                    '44': {
                        'Stints': {
                            '0': {
                                'Compound': 'SOFT',
                                'New': 'true',
                                'TotalLaps': 5,
                            }
                        }
                    }
                }
            }],
        ]

        from fastf1._api import timing_app_data
        result = timing_app_data.__wrapped__('/test/', response=response)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]['Compound'] == 'SOFT'
        assert result.iloc[0]['Driver'] == '44'

    def test_skips_entries_without_lines(self):
        response = [
            ['0:05:00.000', {'NoLines': 'here'}],
        ]
        from fastf1._api import timing_app_data
        result = timing_app_data.__wrapped__('/test/', response=response)
        assert len(result) == 0

    def test_stints_as_list(self):
        response = [
            ['0:05:00.000', {
                'Lines': {
                    '1': {
                        'Stints': [
                            {
                                'Compound': 'MEDIUM',
                                'New': 'false',
                                'TotalLaps': 10,
                            }
                        ]
                    }
                }
            }],
        ]
        from fastf1._api import timing_app_data
        result = timing_app_data.__wrapped__('/test/', response=response)
        assert len(result) == 1
        assert result.iloc[0]['Compound'] == 'MEDIUM'
