"""Tests for mvapi with mocked HTTP responses."""
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from fastf1.mvapi.api import get_circuit
from fastf1.mvapi.data import CircuitInfo, get_circuit_info


class TestGetCircuit:
    @patch('fastf1.mvapi.api.Cache')
    def test_success(self, mock_cache):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'corners': [],
            'marshalLights': [],
            'marshalSectors': [],
            'rotation': 45.0,
        }
        mock_cache.requests_get.return_value = mock_resp

        result = get_circuit(year=2023, circuit_key=1)
        assert result is not None
        assert result['rotation'] == 45.0

    @patch('fastf1.mvapi.api.Cache')
    def test_not_found_returns_none(self, mock_cache):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.content = b'Not Found'
        mock_cache.requests_get.return_value = mock_resp

        result = get_circuit(year=2023, circuit_key=999)
        assert result is None

    @patch('fastf1.mvapi.api.Cache')
    def test_json_decode_error_returns_none(self, mock_cache):
        import requests.exceptions
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = requests.exceptions.JSONDecodeError(
            'err', 'doc', 0
        )
        mock_cache.requests_get.return_value = mock_resp

        result = get_circuit(year=2023, circuit_key=1)
        assert result is None


class TestGetCircuitInfo:
    @patch('fastf1.mvapi.data.get_circuit')
    def test_full_data(self, mock_get_circuit):
        mock_get_circuit.return_value = {
            'corners': [
                {'trackPosition': {'x': 1.0, 'y': 2.0},
                 'number': 1, 'letter': 'A', 'angle': 90.0},
                {'trackPosition': {'x': 3.0, 'y': 4.0},
                 'number': 2, 'letter': '', 'angle': 45.0},
            ],
            'marshalLights': [
                {'trackPosition': {'x': 5.0, 'y': 6.0},
                 'number': 1, 'letter': '', 'angle': 0.0},
            ],
            'marshalSectors': [
                {'trackPosition': {'x': 7.0, 'y': 8.0},
                 'number': 1, 'letter': '', 'angle': 0.0},
            ],
            'rotation': 123.4,
        }

        result = get_circuit_info(year=2023, circuit_key=1)
        assert isinstance(result, CircuitInfo)
        assert result.rotation == 123.4
        assert len(result.corners) == 2
        assert result.corners.iloc[0]['X'] == 1.0
        assert result.corners.iloc[0]['Number'] == 1
        assert result.corners.iloc[0]['Letter'] == 'A'
        assert len(result.marshal_lights) == 1
        assert len(result.marshal_sectors) == 1

    @patch('fastf1.mvapi.data.get_circuit')
    def test_empty_data_returns_none(self, mock_get_circuit):
        mock_get_circuit.return_value = {}

        result = get_circuit_info(year=2023, circuit_key=1)
        assert result is None

    @patch('fastf1.mvapi.data.get_circuit')
    def test_none_data_returns_none(self, mock_get_circuit):
        mock_get_circuit.return_value = None

        result = get_circuit_info(year=2023, circuit_key=1)
        assert result is None

    @patch('fastf1.mvapi.data.get_circuit')
    def test_missing_categories_handled(self, mock_get_circuit):
        mock_get_circuit.return_value = {
            'corners': [
                {'trackPosition': {'x': 1.0, 'y': 2.0},
                 'number': 1, 'letter': '', 'angle': 0.0},
            ],
            # marshalLights and marshalSectors missing
            'rotation': 0.0,
        }

        result = get_circuit_info(year=2023, circuit_key=1)
        assert isinstance(result, CircuitInfo)
        assert len(result.corners) == 1
        assert len(result.marshal_lights) == 0
        assert len(result.marshal_sectors) == 0

    @patch('fastf1.mvapi.data.get_circuit')
    def test_missing_track_position_defaults(self, mock_get_circuit):
        mock_get_circuit.return_value = {
            'corners': [
                {'number': 1, 'letter': '', 'angle': 0.0},
            ],
            'marshalLights': [],
            'marshalSectors': [],
            'rotation': 0.0,
        }

        result = get_circuit_info(year=2023, circuit_key=1)
        assert result.corners.iloc[0]['X'] == 0.0
        assert result.corners.iloc[0]['Y'] == 0.0
