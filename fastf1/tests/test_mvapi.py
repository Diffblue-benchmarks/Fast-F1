import numpy as np
import pandas as pd
import pytest

from fastf1.mvapi.api import _make_url
from fastf1.mvapi.data import CircuitInfo, get_circuit_info


class TestMakeUrl:
    def test_basic(self):
        result = _make_url('/api/v1/circuits/1/2023')
        assert result == 'https://api.multiviewer.app/api/v1/circuits/1/2023'

    def test_path_preserved(self):
        result = _make_url('/test/path')
        assert result.endswith('/test/path')


class TestCircuitInfo:
    def test_creation(self):
        corners = pd.DataFrame({
            'X': [1.0, 2.0], 'Y': [3.0, 4.0],
            'Number': [1, 2], 'Letter': ['', ''],
            'Angle': [0.0, 90.0], 'Distance': [np.nan, np.nan]
        })
        marshal_lights = pd.DataFrame({
            'X': [5.0], 'Y': [6.0],
            'Number': [1], 'Letter': [''],
            'Angle': [45.0], 'Distance': [np.nan]
        })
        marshal_sectors = pd.DataFrame({
            'X': [7.0], 'Y': [8.0],
            'Number': [1], 'Letter': [''],
            'Angle': [0.0], 'Distance': [np.nan]
        })

        info = CircuitInfo(
            corners=corners,
            marshal_lights=marshal_lights,
            marshal_sectors=marshal_sectors,
            rotation=90.0
        )

        assert info.rotation == 90.0
        assert len(info.corners) == 2
        assert len(info.marshal_lights) == 1
        assert len(info.marshal_sectors) == 1
