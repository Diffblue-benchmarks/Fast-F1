"""Tests for core.py Telemetry and Laps classes."""
import numpy as np
import pandas as pd
import pytest

from fastf1.core import Telemetry, Laps


class TestTelemetryCreation:
    def test_basic_creation(self):
        data = {
            'Speed': [200.0, 210.0, 220.0],
            'RPM': [10000.0, 10500.0, 11000.0],
        }
        tel = Telemetry(data)
        assert len(tel) == 3
        assert 'Speed' in tel.columns

    def test_metadata_driver(self):
        tel = Telemetry({'Speed': [200.0]}, driver='44')
        assert tel.driver == '44'

    def test_metadata_session(self):
        mock_session = object()
        tel = Telemetry({'Speed': [200.0]}, session=mock_session)
        assert tel.session is mock_session

    def test_drop_unknown_channels(self):
        data = {
            'Speed': [200.0],
            'UnknownChannel': [42.0],
        }
        tel = Telemetry(data, drop_unknown_channels=True)
        assert 'UnknownChannel' not in tel.columns
        assert 'Speed' in tel.columns

    def test_constructor_returns_telemetry(self):
        tel = Telemetry({'Speed': [200.0, 210.0]})
        sliced = tel[['Speed']]
        assert type(sliced) is Telemetry

    def test_base_class_view(self):
        tel = Telemetry({'Speed': [200.0]})
        view = tel.base_class_view
        assert type(view) is pd.DataFrame


class TestTelemetryJoinMerge:
    def test_join_propagates_metadata(self):
        tel1 = Telemetry({'Speed': [200.0, 210.0]}, driver='44')
        tel2 = pd.DataFrame({'RPM': [10000.0, 10500.0]})
        result = tel1.join(tel2)
        assert result.driver == '44'
        assert 'RPM' in result.columns

    def test_merge_propagates_metadata(self):
        tel1 = Telemetry({'key': [1, 2], 'Speed': [200.0, 210.0]},
                         driver='44')
        tel2 = pd.DataFrame({'key': [1, 2], 'RPM': [10000.0, 10500.0]})
        result = tel1.merge(tel2, on='key')
        assert result.driver == '44'
        assert 'Speed' in result.columns
        assert 'RPM' in result.columns


class TestTelemetrySliceByMask:
    def test_basic_slice(self):
        tel = Telemetry({
            'Speed': [100.0, 200.0, 300.0, 400.0, 500.0]
        })
        mask = pd.Series([False, True, True, False, False])
        result = tel.slice_by_mask(mask)
        assert len(result) == 2

    def test_slice_with_pad_both(self):
        tel = Telemetry({
            'Speed': [100.0, 200.0, 300.0, 400.0, 500.0]
        })
        mask = pd.Series([False, False, True, False, False])
        result = tel.slice_by_mask(mask, pad=1, pad_side='both')
        assert len(result) == 3  # idx 1, 2, 3

    def test_slice_with_pad_before(self):
        tel = Telemetry({
            'Speed': [100.0, 200.0, 300.0, 400.0, 500.0]
        })
        mask = pd.Series([False, False, True, False, False])
        result = tel.slice_by_mask(mask, pad=1, pad_side='before')
        assert len(result) == 2  # idx 1, 2

    def test_slice_with_pad_after(self):
        tel = Telemetry({
            'Speed': [100.0, 200.0, 300.0, 400.0, 500.0]
        })
        mask = pd.Series([False, False, True, False, False])
        result = tel.slice_by_mask(mask, pad=1, pad_side='after')
        assert len(result) == 2  # idx 2, 3


class TestLapsCreation:
    def test_basic_creation(self):
        data = {
            'LapNumber': [1, 2],
            'Driver': ['HAM', 'HAM'],
            'LapTime': [pd.Timedelta(seconds=90), pd.Timedelta(seconds=89)],
        }
        laps = Laps(data)
        assert len(laps) == 2

    def test_metadata_propagation(self):
        mock_session = object()
        laps = Laps({'LapNumber': [1]}, session=mock_session)
        assert laps.session is mock_session

    def test_join_propagates_metadata(self):
        mock_session = object()
        laps = Laps({'LapNumber': [1, 2]}, session=mock_session)
        other = pd.DataFrame({'Extra': [10, 20]})
        result = laps.join(other)
        assert result.session is mock_session

    def test_merge_propagates_metadata(self):
        mock_session = object()
        laps = Laps({'key': [1, 2], 'LapNumber': [1, 2]},
                    session=mock_session)
        other = pd.DataFrame({'key': [1, 2], 'Extra': [10, 20]})
        result = laps.merge(other, on='key')
        assert result.session is mock_session

    def test_constructor_returns_laps(self):
        laps = Laps({'LapNumber': [1, 2], 'Driver': ['A', 'B']})
        sliced = laps[['LapNumber']]
        assert type(sliced) is Laps
