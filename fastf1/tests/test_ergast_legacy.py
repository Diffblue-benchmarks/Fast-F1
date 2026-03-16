import json
import warnings
from unittest import mock

import pytest

from fastf1.ergast import legacy


class MockResponse:
    """Mock response object for requests."""
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content


def test_fetch_results_race():
    """Test fetch_results with Race session."""
    mock_data = {
        'MRData': {
            'RaceTable': {
                'Races': [{
                    'Results': [{'position': '1', 'Driver': {'driverId': 'hamilton'}}]
                }]
            }
        }
    }
    mock_response = MockResponse(200, json.dumps(mock_data).encode('utf-8'))

    with mock.patch('fastf1.req.Cache.requests_get', return_value=mock_response):
        result = legacy.fetch_results(2023, 1, 'Race')
        assert result == [{'position': '1', 'Driver': {'driverId': 'hamilton'}}]


def test_fetch_results_qualifying():
    """Test fetch_results with Qualifying session."""
    mock_data = {
        'MRData': {
            'RaceTable': {
                'Races': [{
                    'QualifyingResults': [{'position': '1', 'Driver': {'driverId': 'verstappen'}}]
                }]
            }
        }
    }
    mock_response = MockResponse(200, json.dumps(mock_data).encode('utf-8'))

    with mock.patch('fastf1.req.Cache.requests_get', return_value=mock_response):
        result = legacy.fetch_results(2023, 1, 'Qualifying')
        assert result == [{'position': '1', 'Driver': {'driverId': 'verstappen'}}]


def test_fetch_results_sprint_qualifying():
    """Test fetch_results with Sprint Qualifying session."""
    mock_data = {
        'MRData': {
            'RaceTable': {
                'Races': [{
                    'SprintResults': [{'position': '1', 'Driver': {'driverId': 'leclerc'}}]
                }]
            }
        }
    }
    mock_response = MockResponse(200, json.dumps(mock_data).encode('utf-8'))

    with mock.patch('fastf1.req.Cache.requests_get', return_value=mock_response):
        result = legacy.fetch_results(2023, 1, 'Sprint Qualifying')
        assert result == [{'position': '1', 'Driver': {'driverId': 'leclerc'}}]


def test_fetch_results_sprint():
    """Test fetch_results with Sprint session."""
    mock_data = {
        'MRData': {
            'RaceTable': {
                'Races': [{
                    'SprintResults': [{'position': '1', 'Driver': {'driverId': 'sainz'}}]
                }]
            }
        }
    }
    mock_response = MockResponse(200, json.dumps(mock_data).encode('utf-8'))

    with mock.patch('fastf1.req.Cache.requests_get', return_value=mock_response):
        result = legacy.fetch_results(2023, 1, 'Sprint')
        assert result == [{'position': '1', 'Driver': {'driverId': 'sainz'}}]


def test_fetch_season():
    """Test fetch_season with successful response."""
    mock_data = {
        'MRData': {
            'RaceTable': {
                'Races': [
                    {'raceName': 'Bahrain Grand Prix', 'round': '1'},
                    {'raceName': 'Saudi Arabian Grand Prix', 'round': '2'}
                ]
            }
        }
    }
    mock_response = MockResponse(200, json.dumps(mock_data).encode('utf-8'))

    with mock.patch('fastf1.req.Cache.requests_get', return_value=mock_response):
        result = legacy.fetch_season(2023)
        assert len(result) == 2
        assert result[0]['raceName'] == 'Bahrain Grand Prix'
        assert result[1]['raceName'] == 'Saudi Arabian Grand Prix'


def test_fetch_day():
    """Test fetch_day with successful response."""
    mock_data = {
        'MRData': {
            'RaceTable': {
                'Races': [{'raceName': 'Test Race'}]
            }
        }
    }
    mock_response = MockResponse(200, json.dumps(mock_data).encode('utf-8'))

    with mock.patch('fastf1.req.Cache.requests_get', return_value=mock_response):
        result = legacy.fetch_day(2023, 1, 'results')
        assert 'MRData' in result
        assert result['MRData']['RaceTable']['Races'][0]['raceName'] == 'Test Race'


def test_parse_json_response_success():
    """Test _parse_json_response with status code 200."""
    test_data = {'key': 'value', 'nested': {'data': 'test'}}
    mock_response = MockResponse(200, json.dumps(test_data).encode('utf-8'))

    result = legacy._parse_json_response(mock_response)
    assert result == test_data


def test_parse_json_response_error():
    """Test _parse_json_response with non-200 status code."""
    mock_response = MockResponse(404, b'Not Found')

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = legacy._parse_json_response(mock_response)

        assert result is None
        assert len(w) == 1
        assert "Request returned: 404" in str(w[0].message)


def test_parse_ergast():
    """Test _parse_ergast with valid data structure."""
    test_data = {
        'MRData': {
            'RaceTable': {
                'Races': [
                    {'raceName': 'Race 1'},
                    {'raceName': 'Race 2'}
                ]
            }
        }
    }

    result = legacy._parse_ergast(test_data)
    assert len(result) == 2
    assert result[0]['raceName'] == 'Race 1'
    assert result[1]['raceName'] == 'Race 2'
