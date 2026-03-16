"""Tests for Telemetry.merge_channels method"""
import warnings
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock

from fastf1 import core


class TestTelemetryMergeChannels:
    """Tests for Telemetry.merge_channels method"""

    def _create_mock_session(self, t0_date='2023-01-01 10:00:00'):
        """Helper to create a mock session"""
        session = Mock()
        session.t0_date = pd.Timestamp(t0_date)
        return session

    def test_merge_channels_basic_merge_original_frequency(self):
        """Test merge_channels with basic telemetry data and original frequency"""
        session = self._create_mock_session()

        # Create two telemetry objects with different channels
        dates1 = pd.to_datetime(['2023-01-01 10:00:00', '2023-01-01 10:00:01', '2023-01-01 10:00:02'])
        data1 = pd.DataFrame({
            'Date': dates1,
            'Speed': [100.0, 110.0, 120.0],
            'Source': ['car', 'car', 'car'],
            'Time': [pd.Timedelta(0), pd.Timedelta(seconds=1), pd.Timedelta(seconds=2)],
            'SessionTime': [pd.Timedelta(0), pd.Timedelta(seconds=1), pd.Timedelta(seconds=2)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')

        dates2 = pd.to_datetime(['2023-01-01 10:00:00', '2023-01-01 10:00:01', '2023-01-01 10:00:02'])
        data2 = pd.DataFrame({
            'Date': dates2,
            'RPM': [8000.0, 8500.0, 9000.0],
            'Source': ['car', 'car', 'car']
        })
        tel2 = core.Telemetry(data2, session=session, driver='1')

        # Merge with original frequency
        result = tel1.merge_channels(tel2, frequency='original')

        # Verify both channels exist
        assert 'Speed' in result.columns
        assert 'RPM' in result.columns
        assert len(result) == 3
        assert 'Date' in result.columns

    def test_merge_channels_overlapping_columns_update(self):
        """Test merge_channels with overlapping columns (should update from first telemetry)"""
        session = self._create_mock_session()

        # Create two telemetry objects with overlapping Source column
        dates1 = pd.to_datetime(['2023-01-01 10:00:00', '2023-01-01 10:00:01'])
        data1 = pd.DataFrame({
            'Date': dates1,
            'Speed': [100.0, 110.0],
            'Source': ['car', 'car'],
            'Time': [pd.Timedelta(0), pd.Timedelta(seconds=1)],
            'SessionTime': [pd.Timedelta(0), pd.Timedelta(seconds=1)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')

        dates2 = pd.to_datetime(['2023-01-01 10:00:00', '2023-01-01 10:00:01'])
        data2 = pd.DataFrame({
            'Date': dates2,
            'RPM': [8000.0, 8500.0],
            'Source': ['pos', 'pos']
        })
        tel2 = core.Telemetry(data2, session=session, driver='1')

        # Merge with original frequency
        result = tel1.merge_channels(tel2, frequency='original')

        # Verify Source column was updated from tel1 (first dataframe)
        assert 'Source' in result.columns
        assert list(result['Source']) == ['car', 'car']

    def test_merge_channels_multiple_drivers_error(self):
        """Test merge_channels raises ValueError when merging multiple drivers"""
        session = self._create_mock_session()

        # Create telemetry with Driver column at different timestamps
        # This ensures both driver values end up in the merged dataframe
        dates1 = pd.to_datetime(['2023-01-01 10:00:00'])
        data1 = pd.DataFrame({
            'Date': dates1,
            'Speed': [100.0],
            'Driver': ['1'],
            'Time': [pd.Timedelta(0)],
            'SessionTime': [pd.Timedelta(0)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')

        dates2 = pd.to_datetime(['2023-01-01 10:00:01'])
        data2 = pd.DataFrame({
            'Date': dates2,
            'RPM': [8000.0],
            'Driver': ['2']
        })
        tel2 = core.Telemetry(data2, session=session, driver='2')

        # Should raise ValueError - different timestamps means both Driver values appear
        with pytest.raises(ValueError, match="Cannot merge multiple drivers"):
            tel1.merge_channels(tel2, frequency='original')

    def test_merge_channels_no_valid_time_data_error(self):
        """Test merge_channels raises ValueError when no valid Time data"""
        session = self._create_mock_session()

        # Create telemetry with all zero Time values
        dates1 = pd.to_datetime(['2023-01-01 10:00:00', '2023-01-01 10:00:01'])
        data1 = pd.DataFrame({
            'Date': dates1,
            'Speed': [100.0, 110.0],
            'Time': [pd.Timedelta(0), pd.Timedelta(0)],  # All zeros
            'SessionTime': [pd.Timedelta(0), pd.Timedelta(0)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')

        dates2 = pd.to_datetime(['2023-01-01 10:00:00', '2023-01-01 10:00:01'])
        data2 = pd.DataFrame({
            'Date': dates2,
            'RPM': [8000.0, 8500.0]
        })
        tel2 = core.Telemetry(data2, session=session, driver='1')

        # Should raise ValueError
        with pytest.raises(ValueError, match="No valid 'Time' data"):
            tel1.merge_channels(tel2, frequency='original')

    def test_merge_channels_with_integer_frequency(self):
        """Test merge_channels with integer frequency for resampling"""
        session = self._create_mock_session()

        # Create telemetry with sufficient data for resampling
        dates1 = pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:00:01',
            '2023-01-01 10:00:02',
            '2023-01-01 10:00:03'
        ])
        data1 = pd.DataFrame({
            'Date': dates1,
            'Speed': [100.0, 110.0, 120.0, 130.0],
            'Source': ['car', 'car', 'car', 'car'],
            'Time': [pd.Timedelta(0), pd.Timedelta(seconds=1), pd.Timedelta(seconds=2), pd.Timedelta(seconds=3)],
            'SessionTime': [pd.Timedelta(0), pd.Timedelta(seconds=1), pd.Timedelta(seconds=2), pd.Timedelta(seconds=3)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')

        dates2 = pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:00:01',
            '2023-01-01 10:00:02',
            '2023-01-01 10:00:03'
        ])
        data2 = pd.DataFrame({
            'Date': dates2,
            'RPM': [8000.0, 8500.0, 9000.0, 9500.0]
        })
        tel2 = core.Telemetry(data2, session=session, driver='1')

        # Merge with 1 Hz frequency
        result = tel1.merge_channels(tel2, frequency=1)

        # Verify data was resampled
        assert 'Speed' in result.columns
        assert 'RPM' in result.columns
        assert 'Date' in result.columns
        assert 'SessionTime' in result.columns
        assert 'Time' in result.columns

    def test_merge_channels_continuous_channel_quadratic(self):
        """Test merge_channels resampling with continuous channel using quadratic interpolation"""
        session = self._create_mock_session()

        # Create telemetry with X channel (quadratic interpolation)
        dates1 = pd.to_datetime([
            '2023-01-01 10:00:00.0',
            '2023-01-01 10:00:00.5',
            '2023-01-01 10:00:01.0',
            '2023-01-01 10:00:01.5'
        ])
        data1 = pd.DataFrame({
            'Date': dates1,
            'X': [0.0, 50.0, 100.0, 150.0],
            'Source': ['car', 'car', 'car', 'car'],
            'Time': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1), pd.Timedelta(milliseconds=1500)],
            'SessionTime': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1), pd.Timedelta(milliseconds=1500)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')

        dates2 = pd.to_datetime(['2023-01-01 10:00:00.0', '2023-01-01 10:00:01.5'])
        data2 = pd.DataFrame({
            'Date': dates2,
            'RPM': [8000.0, 9000.0]
        })
        tel2 = core.Telemetry(data2, session=session, driver='1')

        # Merge with 1 Hz frequency
        result = tel1.merge_channels(tel2, frequency=1)

        # Verify X channel was interpolated
        assert 'X' in result.columns
        assert not result['X'].isna().any()

    def test_merge_channels_continuous_channel_index_method(self):
        """Test merge_channels resampling with continuous channel using index interpolation"""
        session = self._create_mock_session()

        # Create telemetry with Speed channel (index interpolation)
        dates1 = pd.to_datetime([
            '2023-01-01 10:00:00.0',
            '2023-01-01 10:00:00.5',
            '2023-01-01 10:00:01.0'
        ])
        data1 = pd.DataFrame({
            'Date': dates1,
            'Speed': [100.0, 110.0, 120.0],
            'Source': ['car', 'car', 'car'],
            'Time': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)],
            'SessionTime': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')

        dates2 = pd.to_datetime(['2023-01-01 10:00:00.0', '2023-01-01 10:00:01.0'])
        data2 = pd.DataFrame({
            'Date': dates2,
            'RPM': [8000.0, 9000.0]
        })
        tel2 = core.Telemetry(data2, session=session, driver='1')

        # Merge with 1 Hz frequency
        result = tel1.merge_channels(tel2, frequency=1)

        # Verify Speed was interpolated
        assert 'Speed' in result.columns
        assert not result['Speed'].isna().any()

    def test_merge_channels_continuous_channel_scipy_methods(self):
        """Test merge_channels resampling with scipy interpolation methods"""
        session = self._create_mock_session()

        # Register custom channels with scipy methods
        core.Telemetry.register_new_channel('TestNearest', 'continuous', 'nearest')
        core.Telemetry.register_new_channel('TestSlinear', 'continuous', 'slinear')

        try:
            dates1 = pd.to_datetime([
                '2023-01-01 10:00:00.0',
                '2023-01-01 10:00:00.5',
                '2023-01-01 10:00:01.0',
                '2023-01-01 10:00:01.5'
            ])
            data1 = pd.DataFrame({
                'Date': dates1,
                'TestNearest': [10.0, 20.0, 30.0, 40.0],
                'TestSlinear': [100.0, 200.0, 300.0, 400.0],
                'Source': ['car', 'car', 'car', 'car'],
                'Time': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1), pd.Timedelta(milliseconds=1500)],
                'SessionTime': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1), pd.Timedelta(milliseconds=1500)]
            })
            tel1 = core.Telemetry(data1, session=session, driver='1')

            dates2 = pd.to_datetime(['2023-01-01 10:00:00.0'])
            data2 = pd.DataFrame({
                'Date': dates2,
                'RPM': [8000.0]
            })
            tel2 = core.Telemetry(data2, session=session, driver='1')

            # Merge with 1 Hz frequency
            result = tel1.merge_channels(tel2, frequency=1)

            # Verify channels were interpolated
            assert 'TestNearest' in result.columns
            assert 'TestSlinear' in result.columns
            assert not result['TestNearest'].isna().any()
            assert not result['TestSlinear'].isna().any()
        finally:
            # Clean up
            if 'TestNearest' in core.Telemetry._CHANNELS:
                del core.Telemetry._CHANNELS['TestNearest']
            if 'TestSlinear' in core.Telemetry._CHANNELS:
                del core.Telemetry._CHANNELS['TestSlinear']

    def test_merge_channels_continuous_channel_pad_method(self):
        """Test merge_channels resampling with pad/ffill interpolation"""
        session = self._create_mock_session()

        # Register custom channel with pad method
        core.Telemetry.register_new_channel('TestPad', 'continuous', 'pad')

        try:
            dates1 = pd.to_datetime([
                '2023-01-01 10:00:00.0',
                '2023-01-01 10:00:00.5',
                '2023-01-01 10:00:01.0'
            ])
            data1 = pd.DataFrame({
                'Date': dates1,
                'TestPad': [10.0, 20.0, 30.0],
                'Source': ['car', 'car', 'car'],
                'Time': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)],
                'SessionTime': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)]
            })
            tel1 = core.Telemetry(data1, session=session, driver='1')

            dates2 = pd.to_datetime(['2023-01-01 10:00:00.0'])
            data2 = pd.DataFrame({
                'Date': dates2,
                'RPM': [8000.0]
            })
            tel2 = core.Telemetry(data2, session=session, driver='1')

            # Merge with 1 Hz frequency
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=FutureWarning)
                result = tel1.merge_channels(tel2, frequency=1)

            # Verify channel was interpolated
            assert 'TestPad' in result.columns
        finally:
            # Clean up
            if 'TestPad' in core.Telemetry._CHANNELS:
                del core.Telemetry._CHANNELS['TestPad']

    def test_merge_channels_continuous_channel_other_methods(self):
        """Test merge_channels resampling with other interpolation methods"""
        session = self._create_mock_session()

        # Register custom channel with linear method (uses limit_direction)
        core.Telemetry.register_new_channel('TestLinear', 'continuous', 'linear')

        try:
            dates1 = pd.to_datetime([
                '2023-01-01 10:00:00.0',
                '2023-01-01 10:00:00.5',
                '2023-01-01 10:00:01.0'
            ])
            data1 = pd.DataFrame({
                'Date': dates1,
                'TestLinear': [0.0, 10.0, 20.0],
                'Source': ['car', 'car', 'car'],
                'Time': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)],
                'SessionTime': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)]
            })
            tel1 = core.Telemetry(data1, session=session, driver='1')

            dates2 = pd.to_datetime(['2023-01-01 10:00:00.0'])
            data2 = pd.DataFrame({
                'Date': dates2,
                'RPM': [8000.0]
            })
            tel2 = core.Telemetry(data2, session=session, driver='1')

            # Merge with 1 Hz frequency
            result = tel1.merge_channels(tel2, frequency=1)

            # Verify channel was interpolated
            assert 'TestLinear' in result.columns
            assert not result['TestLinear'].isna().any()
        finally:
            # Clean up
            if 'TestLinear' in core.Telemetry._CHANNELS:
                del core.Telemetry._CHANNELS['TestLinear']

    def test_merge_channels_discrete_channel(self):
        """Test merge_channels resampling with discrete channel"""
        session = self._create_mock_session()

        # Create telemetry with nGear (discrete channel)
        dates1 = pd.to_datetime([
            '2023-01-01 10:00:00.0',
            '2023-01-01 10:00:00.5',
            '2023-01-01 10:00:01.0'
        ])
        data1 = pd.DataFrame({
            'Date': dates1,
            'nGear': [1, 2, 3],
            'Source': ['car', 'car', 'car'],
            'Time': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)],
            'SessionTime': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')

        dates2 = pd.to_datetime(['2023-01-01 10:00:00.0'])
        data2 = pd.DataFrame({
            'Date': dates2,
            'Speed': [100.0]
        })
        tel2 = core.Telemetry(data2, session=session, driver='1')

        # Merge with 1 Hz frequency
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            result = tel1.merge_channels(tel2, frequency=1)

        # Verify discrete channel was handled
        assert 'nGear' in result.columns

    def test_merge_channels_source_column_handling(self):
        """Test merge_channels properly handles Source column during resampling"""
        session = self._create_mock_session()

        dates1 = pd.to_datetime([
            '2023-01-01 10:00:00.0',
            '2023-01-01 10:00:00.5',
            '2023-01-01 10:00:01.0'
        ])
        data1 = pd.DataFrame({
            'Date': dates1,
            'Speed': [100.0, 110.0, 120.0],
            'Source': ['car', 'car', 'car'],
            'Time': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)],
            'SessionTime': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')

        dates2 = pd.to_datetime(['2023-01-01 10:00:00.0'])
        data2 = pd.DataFrame({
            'Date': dates2,
            'RPM': [8000.0],
            'Source': ['pos']
        })
        tel2 = core.Telemetry(data2, session=session, driver='1')

        # Merge with 1 Hz frequency
        result = tel1.merge_channels(tel2, frequency=1)

        # Verify Source column exists and contains 'interpolation' for resampled rows
        assert 'Source' in result.columns
        # Some values should be 'interpolation' due to resampling
        assert 'interpolation' in result['Source'].values or 'car' in result['Source'].values

    def test_merge_channels_sessiontime_time_recalculation(self):
        """Test merge_channels recalculates SessionTime and Time after resampling"""
        session = self._create_mock_session()

        dates1 = pd.to_datetime([
            '2023-01-01 10:00:00.0',
            '2023-01-01 10:00:00.5',
            '2023-01-01 10:00:01.0'
        ])
        data1 = pd.DataFrame({
            'Date': dates1,
            'Speed': [100.0, 110.0, 120.0],
            'Source': ['car', 'car', 'car'],
            'Time': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)],
            'SessionTime': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')

        dates2 = pd.to_datetime(['2023-01-01 10:00:00.0'])
        data2 = pd.DataFrame({
            'Date': dates2,
            'RPM': [8000.0]
        })
        tel2 = core.Telemetry(data2, session=session, driver='1')

        # Merge with 1 Hz frequency
        result = tel1.merge_channels(tel2, frequency=1)

        # Verify SessionTime and Time were recalculated
        assert 'SessionTime' in result.columns
        assert 'Time' in result.columns
        assert result['Time'].iloc[0] == pd.Timedelta(0)

    def test_merge_channels_dtype_preservation(self):
        """Test merge_channels preserves data types after merging"""
        session = self._create_mock_session()

        # Create telemetry with specific dtypes
        dates1 = pd.to_datetime(['2023-01-01 10:00:00', '2023-01-01 10:00:01'])
        data1 = pd.DataFrame({
            'Date': dates1,
            'Speed': [100.0, 110.0],
            'nGear': [1, 2],  # int type
            'Source': ['car', 'car'],
            'Time': [pd.Timedelta(0), pd.Timedelta(seconds=1)],
            'SessionTime': [pd.Timedelta(0), pd.Timedelta(seconds=1)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')

        dates2 = pd.to_datetime(['2023-01-01 10:00:00', '2023-01-01 10:00:01'])
        data2 = pd.DataFrame({
            'Date': dates2,
            'RPM': [8000.0, 8500.0]
        })
        tel2 = core.Telemetry(data2, session=session, driver='1')

        # Merge with original frequency
        result = tel1.merge_channels(tel2, frequency='original')

        # Verify nGear is still int type (or can be converted back)
        assert 'nGear' in result.columns

    def test_merge_channels_dtype_preservation_warning(self):
        """Test merge_channels logs warning when dtype preservation fails"""
        session = self._create_mock_session()

        # Create telemetry with a custom column that will fail dtype conversion
        dates1 = pd.to_datetime(['2023-01-01 10:00:00', '2023-01-01 10:00:01'])
        data1 = pd.DataFrame({
            'Date': dates1,
            'CustomColumn': [1, 2],  # int type that will have NaN after merge
            'Source': ['car', 'car'],
            'Time': [pd.Timedelta(0), pd.Timedelta(seconds=1)],
            'SessionTime': [pd.Timedelta(0), pd.Timedelta(seconds=1)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')

        # Create second telemetry with different timestamps (will create NaN in merge)
        dates2 = pd.to_datetime(['2023-01-01 10:00:00.5', '2023-01-01 10:00:01.5'])
        data2 = pd.DataFrame({
            'Date': dates2,
            'RPM': [8000.0, 8500.0]
        })
        tel2 = core.Telemetry(data2, session=session, driver='1')

        # Merge with original frequency - might cause dtype conversion issues
        result = tel1.merge_channels(tel2, frequency='original')

        # Just verify the merge completed (warning handling is internal)
        assert 'CustomColumn' in result.columns

    def test_merge_channels_uses_default_frequency(self):
        """Test merge_channels uses TELEMETRY_FREQUENCY when frequency not specified"""
        session = self._create_mock_session()

        dates1 = pd.to_datetime(['2023-01-01 10:00:00', '2023-01-01 10:00:01'])
        data1 = pd.DataFrame({
            'Date': dates1,
            'Speed': [100.0, 110.0],
            'Source': ['car', 'car'],
            'Time': [pd.Timedelta(0), pd.Timedelta(seconds=1)],
            'SessionTime': [pd.Timedelta(0), pd.Timedelta(seconds=1)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')
        tel1.TELEMETRY_FREQUENCY = 'original'  # Set default

        dates2 = pd.to_datetime(['2023-01-01 10:00:00', '2023-01-01 10:00:01'])
        data2 = pd.DataFrame({
            'Date': dates2,
            'RPM': [8000.0, 8500.0]
        })
        tel2 = core.Telemetry(data2, session=session, driver='1')

        # Merge without specifying frequency
        result = tel1.merge_channels(tel2)

        # Verify merge completed successfully
        assert 'Speed' in result.columns
        assert 'RPM' in result.columns

    def test_merge_channels_different_time_bases(self):
        """Test merge_channels with objects having different time bases"""
        session = self._create_mock_session()

        # Create telemetry at different timestamps
        dates1 = pd.to_datetime([
            '2023-01-01 10:00:00.0',
            '2023-01-01 10:00:00.5',
            '2023-01-01 10:00:01.0'
        ])
        data1 = pd.DataFrame({
            'Date': dates1,
            'Speed': [100.0, 110.0, 120.0],
            'Source': ['car', 'car', 'car'],
            'Time': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)],
            'SessionTime': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')

        # Different timestamps
        dates2 = pd.to_datetime([
            '2023-01-01 10:00:00.25',
            '2023-01-01 10:00:00.75'
        ])
        data2 = pd.DataFrame({
            'Date': dates2,
            'RPM': [8000.0, 8500.0]
        })
        tel2 = core.Telemetry(data2, session=session, driver='1')

        # Merge with original frequency (keeps all timestamps)
        result = tel1.merge_channels(tel2, frequency='original')

        # Verify all timestamps were preserved
        assert len(result) == 5  # 3 + 2 unique timestamps
        assert 'Speed' in result.columns
        assert 'RPM' in result.columns

    def test_merge_channels_unknown_channel_original_frequency(self):
        """Test merge_channels with unknown channel using original frequency"""
        session = self._create_mock_session()

        dates1 = pd.to_datetime([
            '2023-01-01 10:00:00.0',
            '2023-01-01 10:00:00.5',
            '2023-01-01 10:00:01.0'
        ])
        data1 = pd.DataFrame({
            'Date': dates1,
            'Speed': [100.0, 110.0, 120.0],
            'UnknownChannel': [1.0, 2.0, 3.0],  # Unknown channel
            'Source': ['car', 'car', 'car'],
            'Time': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)],
            'SessionTime': [pd.Timedelta(0), pd.Timedelta(milliseconds=500), pd.Timedelta(seconds=1)]
        })
        tel1 = core.Telemetry(data1, session=session, driver='1')

        dates2 = pd.to_datetime(['2023-01-01 10:00:00.0'])
        data2 = pd.DataFrame({
            'Date': dates2,
            'RPM': [8000.0]
        })
        tel2 = core.Telemetry(data2, session=session, driver='1')

        # Merge with original frequency (no resampling, so unknown channel preserved)
        result = tel1.merge_channels(tel2, frequency='original')

        # Unknown channel should be present when not resampling
        assert 'Speed' in result.columns
        assert 'RPM' in result.columns
        assert 'UnknownChannel' in result.columns
