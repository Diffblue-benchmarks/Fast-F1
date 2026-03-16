"""Tests for Telemetry.slice_by_time method"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock

from fastf1 import core


class TestTelemetrySliceByTime:
    """Tests for Telemetry.slice_by_time method"""

    def _create_mock_session(self, t0_date='2023-01-01 10:00:00'):
        """Helper to create a mock session"""
        session = Mock()
        session.t0_date = pd.Timestamp(t0_date)
        return session

    def test_slice_by_time_basic_slice_no_interpolation(self):
        """Test slice_by_time with basic time range and no edge interpolation"""
        session = self._create_mock_session()

        # Create telemetry with SessionTime and Speed
        dates = pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:00:01',
            '2023-01-01 10:00:02',
            '2023-01-01 10:00:03',
            '2023-01-01 10:00:04'
        ])
        data = pd.DataFrame({
            'Date': dates,
            'SessionTime': [
                pd.Timedelta(seconds=0),
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=3),
                pd.Timedelta(seconds=4)
            ],
            'Speed': [100.0, 110.0, 120.0, 130.0, 140.0]
        })
        telemetry = core.Telemetry(data, session=session)

        # Slice between 1 and 3 seconds
        result = telemetry.slice_by_time(
            pd.Timedelta(seconds=1),
            pd.Timedelta(seconds=3),
            interpolate_edges=False
        )

        # Verify the slice contains only data within the range
        assert len(result) == 3
        assert result['Speed'].iloc[0] == 110.0
        assert result['Speed'].iloc[1] == 120.0
        assert result['Speed'].iloc[2] == 130.0

    def test_slice_by_time_with_time_column_adjustment(self):
        """Test slice_by_time adjusts Time column relative to start_time"""
        session = self._create_mock_session()

        # Create telemetry with SessionTime and Time columns
        dates = pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:00:01',
            '2023-01-01 10:00:02',
            '2023-01-01 10:00:03',
            '2023-01-01 10:00:04'
        ])
        data = pd.DataFrame({
            'Date': dates,
            'SessionTime': [
                pd.Timedelta(seconds=0),
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=3),
                pd.Timedelta(seconds=4)
            ],
            'Time': [
                pd.Timedelta(seconds=10),
                pd.Timedelta(seconds=11),
                pd.Timedelta(seconds=12),
                pd.Timedelta(seconds=13),
                pd.Timedelta(seconds=14)
            ],
            'Speed': [100.0, 110.0, 120.0, 130.0, 140.0]
        })
        telemetry = core.Telemetry(data, session=session)

        # Slice between 1 and 3 seconds
        result = telemetry.slice_by_time(
            pd.Timedelta(seconds=1),
            pd.Timedelta(seconds=3),
            interpolate_edges=False
        )

        # Verify Time column is adjusted to start at 0
        assert 'Time' in result.columns
        assert result['Time'].iloc[0] == pd.Timedelta(seconds=0)
        assert result['Time'].iloc[1] == pd.Timedelta(seconds=1)
        assert result['Time'].iloc[2] == pd.Timedelta(seconds=2)

    def test_slice_by_time_with_pad(self):
        """Test slice_by_time with padding"""
        session = self._create_mock_session()

        # Create telemetry with SessionTime
        dates = pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:00:01',
            '2023-01-01 10:00:02',
            '2023-01-01 10:00:03',
            '2023-01-01 10:00:04'
        ])
        data = pd.DataFrame({
            'Date': dates,
            'SessionTime': [
                pd.Timedelta(seconds=0),
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=3),
                pd.Timedelta(seconds=4)
            ],
            'Speed': [100.0, 110.0, 120.0, 130.0, 140.0]
        })
        telemetry = core.Telemetry(data, session=session)

        # Slice between 2 and 2 seconds with 1 sample padding on both sides
        result = telemetry.slice_by_time(
            pd.Timedelta(seconds=2),
            pd.Timedelta(seconds=2),
            pad=1,
            pad_side='both',
            interpolate_edges=False
        )

        # Verify padding includes adjacent samples
        assert len(result) == 3  # 1 before + 1 match + 1 after
        assert result['Speed'].iloc[0] == 110.0  # padded before
        assert result['Speed'].iloc[1] == 120.0  # matched
        assert result['Speed'].iloc[2] == 130.0  # padded after

    def test_slice_by_time_with_interpolate_edges(self):
        """Test slice_by_time with edge interpolation"""
        session = self._create_mock_session()

        # Create telemetry with SessionTime and Time columns (required for merge_channels)
        dates = pd.to_datetime([
            '2023-01-01 10:00:00.0',
            '2023-01-01 10:00:01.0',
            '2023-01-01 10:00:02.0',
            '2023-01-01 10:00:03.0'
        ])
        data = pd.DataFrame({
            'Date': dates,
            'SessionTime': [
                pd.Timedelta(seconds=0),
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=3)
            ],
            'Time': [
                pd.Timedelta(seconds=0),
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=3)
            ],
            'Speed': [100.0, 110.0, 120.0, 130.0],
            'Source': ['car', 'car', 'car', 'car']
        })
        telemetry = core.Telemetry(data, session=session)

        # Slice between 0.5 and 2.5 seconds with interpolation
        result = telemetry.slice_by_time(
            pd.Timedelta(milliseconds=500),
            pd.Timedelta(milliseconds=2500),
            interpolate_edges=True
        )

        # Verify edges are interpolated - should have more samples than without
        assert len(result) >= 2
        # The exact start and end times should be included via interpolation
        assert result['SessionTime'].min() == pd.Timedelta(milliseconds=500)
        assert result['SessionTime'].max() == pd.Timedelta(milliseconds=2500)

    def test_slice_by_time_no_matching_data_returns_empty(self):
        """Test slice_by_time returns empty Telemetry when no data in range"""
        session = self._create_mock_session()

        # Create telemetry with SessionTime
        dates = pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:00:01',
            '2023-01-01 10:00:02'
        ])
        data = pd.DataFrame({
            'Date': dates,
            'SessionTime': [
                pd.Timedelta(seconds=0),
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=2)
            ],
            'Speed': [100.0, 110.0, 120.0]
        })
        telemetry = core.Telemetry(data, session=session)

        # Slice with a time range that has no data
        result = telemetry.slice_by_time(
            pd.Timedelta(seconds=10),
            pd.Timedelta(seconds=20),
            interpolate_edges=False
        )

        # Verify an empty Telemetry is returned
        assert len(result) == 0
        assert isinstance(result, core.Telemetry)

    def test_slice_by_time_without_time_column(self):
        """Test slice_by_time when Time column is not present"""
        session = self._create_mock_session()

        # Create telemetry without Time column
        dates = pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:00:01',
            '2023-01-01 10:00:02',
            '2023-01-01 10:00:03'
        ])
        data = pd.DataFrame({
            'Date': dates,
            'SessionTime': [
                pd.Timedelta(seconds=0),
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=3)
            ],
            'Speed': [100.0, 110.0, 120.0, 130.0]
        })
        telemetry = core.Telemetry(data, session=session)

        # Slice between 1 and 2 seconds
        result = telemetry.slice_by_time(
            pd.Timedelta(seconds=1),
            pd.Timedelta(seconds=2),
            interpolate_edges=False
        )

        # Verify slice works without Time column
        assert len(result) == 2
        assert 'Time' not in result.columns
        assert result['Speed'].iloc[0] == 110.0
        assert result['Speed'].iloc[1] == 120.0

    def test_slice_by_time_edge_case_single_sample(self):
        """Test slice_by_time with single sample in range"""
        session = self._create_mock_session()

        # Create telemetry with SessionTime
        dates = pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:00:01',
            '2023-01-01 10:00:02',
            '2023-01-01 10:00:03'
        ])
        data = pd.DataFrame({
            'Date': dates,
            'SessionTime': [
                pd.Timedelta(seconds=0),
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=3)
            ],
            'Speed': [100.0, 110.0, 120.0, 130.0]
        })
        telemetry = core.Telemetry(data, session=session)

        # Slice to get exactly one sample
        result = telemetry.slice_by_time(
            pd.Timedelta(seconds=1),
            pd.Timedelta(seconds=1),
            interpolate_edges=False
        )

        # Verify single sample is returned
        assert len(result) == 1
        assert result['Speed'].iloc[0] == 110.0

    def test_slice_by_time_pad_before(self):
        """Test slice_by_time with padding only before"""
        session = self._create_mock_session()

        # Create telemetry with SessionTime
        dates = pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:00:01',
            '2023-01-01 10:00:02',
            '2023-01-01 10:00:03',
            '2023-01-01 10:00:04'
        ])
        data = pd.DataFrame({
            'Date': dates,
            'SessionTime': [
                pd.Timedelta(seconds=0),
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=3),
                pd.Timedelta(seconds=4)
            ],
            'Speed': [100.0, 110.0, 120.0, 130.0, 140.0]
        })
        telemetry = core.Telemetry(data, session=session)

        # Slice between 2 and 2 seconds with 1 sample padding before
        result = telemetry.slice_by_time(
            pd.Timedelta(seconds=2),
            pd.Timedelta(seconds=2),
            pad=1,
            pad_side='before',
            interpolate_edges=False
        )

        # Verify padding only includes sample before
        assert len(result) == 2  # 1 before + 1 match
        assert result['Speed'].iloc[0] == 110.0  # padded before
        assert result['Speed'].iloc[1] == 120.0  # matched

    def test_slice_by_time_pad_after(self):
        """Test slice_by_time with padding only after"""
        session = self._create_mock_session()

        # Create telemetry with SessionTime
        dates = pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:00:01',
            '2023-01-01 10:00:02',
            '2023-01-01 10:00:03',
            '2023-01-01 10:00:04'
        ])
        data = pd.DataFrame({
            'Date': dates,
            'SessionTime': [
                pd.Timedelta(seconds=0),
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=3),
                pd.Timedelta(seconds=4)
            ],
            'Speed': [100.0, 110.0, 120.0, 130.0, 140.0]
        })
        telemetry = core.Telemetry(data, session=session)

        # Slice between 2 and 2 seconds with 1 sample padding after
        result = telemetry.slice_by_time(
            pd.Timedelta(seconds=2),
            pd.Timedelta(seconds=2),
            pad=1,
            pad_side='after',
            interpolate_edges=False
        )

        # Verify padding only includes sample after
        assert len(result) == 2  # 1 match + 1 after
        assert result['Speed'].iloc[0] == 120.0  # matched
        assert result['Speed'].iloc[1] == 130.0  # padded after

    def test_slice_by_time_inclusive_boundary(self):
        """Test slice_by_time includes samples at exact start and end times"""
        session = self._create_mock_session()

        # Create telemetry with SessionTime
        dates = pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:00:01',
            '2023-01-01 10:00:02',
            '2023-01-01 10:00:03'
        ])
        data = pd.DataFrame({
            'Date': dates,
            'SessionTime': [
                pd.Timedelta(seconds=0),
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=3)
            ],
            'Speed': [100.0, 110.0, 120.0, 130.0]
        })
        telemetry = core.Telemetry(data, session=session)

        # Slice with boundaries exactly on data points
        result = telemetry.slice_by_time(
            pd.Timedelta(seconds=1),
            pd.Timedelta(seconds=2),
            interpolate_edges=False
        )

        # Verify boundaries are included
        assert len(result) == 2
        assert result['Speed'].iloc[0] == 110.0
        assert result['Speed'].iloc[1] == 120.0

    def test_slice_by_time_all_data_in_range(self):
        """Test slice_by_time when entire dataset is within range"""
        session = self._create_mock_session()

        # Create telemetry with SessionTime
        dates = pd.to_datetime([
            '2023-01-01 10:00:01',
            '2023-01-01 10:00:02',
            '2023-01-01 10:00:03'
        ])
        data = pd.DataFrame({
            'Date': dates,
            'SessionTime': [
                pd.Timedelta(seconds=1),
                pd.Timedelta(seconds=2),
                pd.Timedelta(seconds=3)
            ],
            'Speed': [110.0, 120.0, 130.0]
        })
        telemetry = core.Telemetry(data, session=session)

        # Slice with range that includes all data
        result = telemetry.slice_by_time(
            pd.Timedelta(seconds=0),
            pd.Timedelta(seconds=10),
            interpolate_edges=False
        )

        # Verify all data is returned
        assert len(result) == 3
        assert result['Speed'].iloc[0] == 110.0
        assert result['Speed'].iloc[1] == 120.0
        assert result['Speed'].iloc[2] == 130.0
