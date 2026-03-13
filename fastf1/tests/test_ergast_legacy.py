"""Tests for ergast/legacy.py with mocked HTTP."""
import json
import warnings
from unittest.mock import MagicMock, patch

import pytest

from fastf1.ergast.legacy import (
    _parse_ergast,
    _parse_json_response,
    fetch_day,
    fetch_season,
)


class TestParseJsonResponse:
    def test_success(self):
        resp = MagicMock()
        resp.status_code = 200
        resp.content = json.dumps({'data': 'value'}).encode('utf-8')
        result = _parse_json_response(resp)
        assert result == {'data': 'value'}

    def test_failure_warns(self):
        resp = MagicMock()
        resp.status_code = 404
        with pytest.warns(match="404"):
            result = _parse_json_response(resp)
        assert result is None


class TestParseErgast:
    def test_extracts_races(self):
        data = {'MRData': {'RaceTable': {'Races': [{'raceName': 'Test'}]}}}
        result = _parse_ergast(data)
        assert result == [{'raceName': 'Test'}]


class TestFetchDay:
    @patch('fastf1.ergast.legacy.Cache')
    def test_fetch_day(self, mock_cache):
        resp = MagicMock()
        resp.status_code = 200
        resp.content = json.dumps({
            'MRData': {'RaceTable': {'Races': []}}
        }).encode('utf-8')
        mock_cache.requests_get.return_value = resp

        result = fetch_day(2023, 1, 'results')
        assert result is not None
        mock_cache.requests_get.assert_called_once()


class TestFetchSeason:
    @patch('fastf1.ergast.legacy.Cache')
    def test_fetch_season(self, mock_cache):
        resp = MagicMock()
        resp.status_code = 200
        resp.content = json.dumps({
            'MRData': {'RaceTable': {'Races': [{'round': '1'}]}}
        }).encode('utf-8')
        mock_cache.requests_get.return_value = resp

        result = fetch_season(2023)
        assert len(result) == 1
        assert result[0]['round'] == '1'
