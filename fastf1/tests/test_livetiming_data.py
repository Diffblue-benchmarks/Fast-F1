import json
import tempfile
import os

import pytest

from fastf1.livetiming.data import LiveTimingData, _track_status_mapping


class TestTrackStatusMapping:
    def test_all_clear(self):
        assert _track_status_mapping['AllClear'] == '1'

    def test_red(self):
        assert _track_status_mapping['Red'] == '5'

    def test_sc_deployed(self):
        assert _track_status_mapping['SCDeployed'] == '4'

    def test_vsc(self):
        assert _track_status_mapping['VSCDeployed'] == '6'


class TestLiveTimingDataFixJson:
    def test_fix_single_quotes(self):
        ltd = LiveTimingData()
        result = ltd._fix_json("{'key': 'value'}")
        assert result == '{"key": "value"}'

    def test_fix_true_false(self):
        ltd = LiveTimingData()
        result = ltd._fix_json("{'flag': True, 'other': False}")
        assert 'true' in result
        assert 'false' in result
        assert 'True' not in result
        assert 'False' not in result


class TestLiveTimingDataAddToCategory:
    def test_add_new_category(self):
        ltd = LiveTimingData()
        ltd._add_to_category('TestCat', ['data1'])
        assert 'TestCat' in ltd.data
        assert ltd.data['TestCat'] == [['data1']]

    def test_append_to_existing_category(self):
        ltd = LiveTimingData()
        ltd._add_to_category('TestCat', ['data1'])
        ltd._add_to_category('TestCat', ['data2'])
        assert ltd.data['TestCat'] == [['data1'], ['data2']]


class TestLiveTimingDataParseLine:
    def test_valid_line(self):
        ltd = LiveTimingData()
        line = json.dumps([
            'WeatherData',
            {'AirTemp': '25.0'},
            '2023-03-05T15:00:00.000Z'
        ])
        ltd._parse_line(line)
        assert 'WeatherData' in ltd.data

    def test_invalid_json(self):
        ltd = LiveTimingData()
        ltd._parse_line('not valid json at all {{{')
        assert ltd.errorcount == 1

    def test_invalid_datetime(self):
        ltd = LiveTimingData()
        line = json.dumps(['Cat', {'data': 1}, 'not_a_datetime'])
        ltd._parse_line(line)
        assert ltd.errorcount == 1


class TestLiveTimingDataFileLoading:
    def test_load_single_file(self):
        line1 = json.dumps([
            'SessionStatus',
            {'StatusSeries': [
                {'SessionStatus': 'Started', 'Utc': '2023-03-05T15:00:00.000Z'}
            ]},
            '2023-03-05T15:00:00.000Z'
        ])
        line2 = json.dumps([
            'WeatherData',
            {'AirTemp': '25.0'},
            '2023-03-05T15:00:01.000Z'
        ])

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        ) as f:
            f.write(line1 + '\n')
            f.write(line2 + '\n')
            fname = f.name

        try:
            ltd = LiveTimingData(fname)
            ltd.load()
            assert ltd.has('SessionStatus')
            assert ltd.has('WeatherData')
            cats = ltd.list_categories()
            assert 'WeatherData' in cats
        finally:
            os.unlink(fname)

    def test_has_nonexistent_category(self):
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        ) as f:
            line = json.dumps([
                'WeatherData',
                {'AirTemp': '25'},
                '2023-03-05T15:00:00.000Z'
            ])
            f.write(line + '\n')
            fname = f.name

        try:
            ltd = LiveTimingData(fname)
            assert not ltd.has('Nonexistent')
        finally:
            os.unlink(fname)
