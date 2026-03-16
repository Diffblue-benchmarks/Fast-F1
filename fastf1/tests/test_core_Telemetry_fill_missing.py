"""Tests for Telemetry.fill_missing method"""
import warnings
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock

from fastf1 import core


class TestTelemetryFillMissing:
    """Tests for Telemetry.fill_missing method"""

    def test_fill_missing_continuous_quadratic(self):
        """Test fill_missing with continuous channel using quadratic interpolation"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')

        # Create telemetry data with missing values in a continuous channel
        data = pd.DataFrame({
            'Date': pd.to_datetime([
                '2023-01-01 10:00:00',
                '2023-01-01 10:00:01',
                '2023-01-01 10:00:02',
                '2023-01-01 10:00:03',
                '2023-01-01 10:00:04'
            ]),
            'X': [1.0, np.nan, 3.0, np.nan, 5.0]
        })

        telemetry = core.Telemetry(data, session=session)
        result = telemetry.fill_missing()

        # Verify continuous channel was interpolated
        assert not result['X'].isna().any()
        assert len(result) == len(telemetry)
        # Verify SessionTime and Time were calculated
        assert 'SessionTime' in result.columns
        assert 'Time' in result.columns

    def test_fill_missing_continuous_index_method(self):
        """Test fill_missing with continuous channel using index interpolation"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')

        # Create telemetry data with missing values in Speed (uses 'index' method)
        data = pd.DataFrame({
            'Date': pd.to_datetime([
                '2023-01-01 10:00:00',
                '2023-01-01 10:00:01',
                '2023-01-01 10:00:02',
                '2023-01-01 10:00:03'
            ]),
            'Speed': [100.0, np.nan, 120.0, np.nan]
        })

        telemetry = core.Telemetry(data, session=session)
        result = telemetry.fill_missing()

        # Verify Speed was interpolated
        assert not result['Speed'].isna().any()
        assert result['Speed'].iloc[1] > 100.0
        assert result['Speed'].iloc[1] < 120.0

    def test_fill_missing_continuous_with_scipy_methods(self):
        """Test fill_missing with continuous channel using scipy interpolation methods"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')

        # Register a custom channel with cubic interpolation
        channel_name = 'TestCubicChannel'
        core.Telemetry.register_new_channel(channel_name, 'continuous', 'cubic')

        try:
            # Create telemetry data with missing values
            # Need more data points for cubic interpolation to work properly
            data = pd.DataFrame({
                'Date': pd.to_datetime([
                    '2023-01-01 10:00:00',
                    '2023-01-01 10:00:01',
                    '2023-01-01 10:00:02',
                    '2023-01-01 10:00:03',
                    '2023-01-01 10:00:04',
                    '2023-01-01 10:00:05',
                    '2023-01-01 10:00:06',
                    '2023-01-01 10:00:07'
                ]),
                channel_name: [1.0, 2.0, np.nan, 4.0, np.nan, 6.0, 7.0, 8.0]
            })

            telemetry = core.Telemetry(data, session=session)
            result = telemetry.fill_missing()

            # Verify channel was interpolated
            assert not result[channel_name].isna().any()
        finally:
            # Clean up
            del core.Telemetry._CHANNELS[channel_name]

    def test_fill_missing_continuous_with_pad_method(self):
        """Test fill_missing with continuous channel using pad/ffill method"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')

        # Register a custom channel with pad interpolation
        channel_name = 'TestPadChannel'
        core.Telemetry.register_new_channel(channel_name, 'continuous', 'pad')

        try:
            # Create telemetry data with missing values
            data = pd.DataFrame({
                'Date': pd.to_datetime([
                    '2023-01-01 10:00:00',
                    '2023-01-01 10:00:01',
                    '2023-01-01 10:00:02',
                    '2023-01-01 10:00:03'
                ]),
                channel_name: [1.0, np.nan, np.nan, 4.0]
            })

            telemetry = core.Telemetry(data, session=session)

            # Suppress pandas FutureWarning about deprecated pad/backfill methods
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=FutureWarning)
                result = telemetry.fill_missing()

            # Verify channel was forward-filled
            assert not result[channel_name].isna().any()
            assert result[channel_name].iloc[1] == 1.0  # forward fill
            assert result[channel_name].iloc[2] == 1.0  # forward fill
        finally:
            # Clean up
            del core.Telemetry._CHANNELS[channel_name]

    def test_fill_missing_continuous_with_other_methods(self):
        """Test fill_missing with continuous channel using other interpolation methods"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')

        # Register a custom channel with linear interpolation
        channel_name = 'TestLinearChannel'
        core.Telemetry.register_new_channel(channel_name, 'continuous', 'linear')

        try:
            # Create telemetry data with missing values
            data = pd.DataFrame({
                'Date': pd.to_datetime([
                    '2023-01-01 10:00:00',
                    '2023-01-01 10:00:01',
                    '2023-01-01 10:00:02',
                    '2023-01-01 10:00:03'
                ]),
                channel_name: [0.0, np.nan, np.nan, 3.0]
            })

            telemetry = core.Telemetry(data, session=session)
            result = telemetry.fill_missing()

            # Verify channel was linearly interpolated
            assert not result[channel_name].isna().any()
            assert result[channel_name].iloc[1] == 1.0  # linear interpolation
            assert result[channel_name].iloc[2] == 2.0  # linear interpolation
        finally:
            # Clean up
            del core.Telemetry._CHANNELS[channel_name]

    def test_fill_missing_continuous_object_dtype_warning(self):
        """Test fill_missing warns when continuous channel has object dtype"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')

        # Register a custom channel
        channel_name = 'TestObjectChannel'
        core.Telemetry.register_new_channel(channel_name, 'continuous', 'linear')

        try:
            # Create telemetry data with object dtype
            data = pd.DataFrame({
                'Date': pd.to_datetime([
                    '2023-01-01 10:00:00',
                    '2023-01-01 10:00:01',
                    '2023-01-01 10:00:02'
                ]),
                channel_name: ['a', 'b', 'c']  # object dtype
            })

            telemetry = core.Telemetry(data, session=session)

            # Capture warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = telemetry.fill_missing()

                # Verify warning was raised
                assert len(w) >= 1
                assert any("Interpolation not possible" in str(warning.message) for warning in w)
        finally:
            # Clean up
            del core.Telemetry._CHANNELS[channel_name]

    def test_fill_missing_discrete_channel(self):
        """Test fill_missing with discrete channel using ffill/bfill"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')

        # Create telemetry data with missing values in discrete channels
        data = pd.DataFrame({
            'Date': pd.to_datetime([
                '2023-01-01 10:00:00',
                '2023-01-01 10:00:01',
                '2023-01-01 10:00:02',
                '2023-01-01 10:00:03',
                '2023-01-01 10:00:04'
            ]),
            'nGear': [1, np.nan, 3, np.nan, 5],
            'DRS': [0, np.nan, 1, np.nan, 1]
        })

        telemetry = core.Telemetry(data, session=session)
        result = telemetry.fill_missing()

        # Verify discrete channels were filled
        assert not result['nGear'].isna().any()
        assert not result['DRS'].isna().any()
        # Forward fill should be applied
        assert result['nGear'].iloc[1] == 1  # forward filled
        assert result['DRS'].iloc[1] == 0  # forward filled

    def test_fill_missing_discrete_channel_first_row_nan(self):
        """Test fill_missing with discrete channel having NaN in first row (bfill needed)"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')

        # Create telemetry data with NaN in first row
        data = pd.DataFrame({
            'Date': pd.to_datetime([
                '2023-01-01 10:00:00',
                '2023-01-01 10:00:01',
                '2023-01-01 10:00:02'
            ]),
            'nGear': [np.nan, 2, 3]
        })

        telemetry = core.Telemetry(data, session=session)
        result = telemetry.fill_missing()

        # Verify first row was back-filled
        assert not result['nGear'].isna().any()
        assert result['nGear'].iloc[0] == 2  # back filled

    def test_fill_missing_source_column(self):
        """Test fill_missing fills Source column with 'interpolation'"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')

        # Create telemetry data with Source column having NaN
        data = pd.DataFrame({
            'Date': pd.to_datetime([
                '2023-01-01 10:00:00',
                '2023-01-01 10:00:01',
                '2023-01-01 10:00:02'
            ]),
            'Source': ['car', np.nan, 'car']
        })

        telemetry = core.Telemetry(data, session=session)
        result = telemetry.fill_missing()

        # Verify Source was filled with 'interpolation'
        assert not result['Source'].isna().any()
        assert result['Source'].iloc[1] == 'interpolation'

    def test_fill_missing_sessiontime_with_date_column(self):
        """Test fill_missing calculates SessionTime when Date column exists"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')

        # Create telemetry data with Date column
        data = pd.DataFrame({
            'Date': pd.to_datetime([
                '2023-01-01 10:00:00',
                '2023-01-01 10:00:01',
                '2023-01-01 10:00:02'
            ]),
            'Speed': [100.0, 110.0, 120.0]
        })

        telemetry = core.Telemetry(data, session=session)
        result = telemetry.fill_missing()

        # Verify SessionTime was calculated
        assert 'SessionTime' in result.columns
        assert result['SessionTime'].iloc[0] == pd.Timedelta(0)
        assert result['SessionTime'].iloc[1] == pd.Timedelta(seconds=1)
        assert result['SessionTime'].iloc[2] == pd.Timedelta(seconds=2)

    def test_fill_missing_sessiontime_with_datetimeindex(self):
        """Test fill_missing calculates SessionTime when index is DatetimeIndex"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')

        # Create telemetry data with DatetimeIndex but no Date column
        dates = pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:00:01',
            '2023-01-01 10:00:02'
        ])
        data = pd.DataFrame({
            'Speed': [100.0, 110.0, 120.0]
        }, index=dates)

        telemetry = core.Telemetry(data, session=session)
        result = telemetry.fill_missing()

        # Verify SessionTime was calculated from index
        assert 'SessionTime' in result.columns
        assert result['SessionTime'].iloc[0] == pd.Timedelta(0)
        assert result['SessionTime'].iloc[1] == pd.Timedelta(seconds=1)
        assert result['SessionTime'].iloc[2] == pd.Timedelta(seconds=2)

    def test_fill_missing_time_calculation(self):
        """Test fill_missing calculates Time relative to first SessionTime"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 09:59:50')  # 10 seconds before first data point

        # Create telemetry data
        data = pd.DataFrame({
            'Date': pd.to_datetime([
                '2023-01-01 10:00:00',
                '2023-01-01 10:00:01',
                '2023-01-01 10:00:02'
            ]),
            'Speed': [100.0, 110.0, 120.0]
        })

        telemetry = core.Telemetry(data, session=session)
        result = telemetry.fill_missing()

        # Verify Time was calculated relative to first SessionTime
        assert 'Time' in result.columns
        assert result['Time'].iloc[0] == pd.Timedelta(0)
        assert result['Time'].iloc[1] == pd.Timedelta(seconds=1)
        assert result['Time'].iloc[2] == pd.Timedelta(seconds=2)

    def test_fill_missing_returns_copy(self):
        """Test fill_missing returns a copy and doesn't modify original"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')

        # Create telemetry data with missing values
        data = pd.DataFrame({
            'Date': pd.to_datetime([
                '2023-01-01 10:00:00',
                '2023-01-01 10:00:01',
                '2023-01-01 10:00:02'
            ]),
            'Speed': [100.0, np.nan, 120.0]
        })

        telemetry = core.Telemetry(data, session=session)
        original_has_nan = telemetry['Speed'].isna().any()

        result = telemetry.fill_missing()

        # Verify original still has NaN but result doesn't
        assert original_has_nan
        assert telemetry['Speed'].isna().any()
        assert not result['Speed'].isna().any()

    def test_fill_missing_with_no_channels_in_columns(self):
        """Test fill_missing when telemetry has no known channels"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')

        # Create telemetry data with only Date column (no known telemetry channels)
        data = pd.DataFrame({
            'Date': pd.to_datetime([
                '2023-01-01 10:00:00',
                '2023-01-01 10:00:01',
                '2023-01-01 10:00:02'
            ])
        })

        telemetry = core.Telemetry(data, session=session)
        result = telemetry.fill_missing()

        # Should still calculate SessionTime and Time
        assert 'SessionTime' in result.columns
        assert 'Time' in result.columns
        assert len(result) == len(telemetry)

    def test_fill_missing_multiple_channel_types(self):
        """Test fill_missing with mix of continuous and discrete channels"""
        # Create mock session with t0_date
        session = Mock()
        session.t0_date = pd.Timestamp('2023-01-01 10:00:00')

        # Create telemetry data with both continuous and discrete channels
        data = pd.DataFrame({
            'Date': pd.to_datetime([
                '2023-01-01 10:00:00',
                '2023-01-01 10:00:01',
                '2023-01-01 10:00:02',
                '2023-01-01 10:00:03',
                '2023-01-01 10:00:04'
            ]),
            'Speed': [100.0, np.nan, 120.0, np.nan, 140.0],  # continuous
            'nGear': [1, np.nan, 3, np.nan, 5],  # discrete
            'Source': ['car', np.nan, 'car', np.nan, 'car']
        })

        telemetry = core.Telemetry(data, session=session)
        result = telemetry.fill_missing()

        # Verify all channels were filled appropriately
        assert not result['Speed'].isna().any()
        assert not result['nGear'].isna().any()
        assert not result['Source'].isna().any()
        assert result['Source'].iloc[1] == 'interpolation'
        assert result['Source'].iloc[3] == 'interpolation'
        assert 'SessionTime' in result.columns
        assert 'Time' in result.columns
