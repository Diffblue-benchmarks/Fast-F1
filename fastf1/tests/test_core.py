"""Tests for fastf1.core module"""
import warnings
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock

import fastf1
from fastf1 import core
from fastf1 import exceptions


class TestModuleGetattr:
    """Tests for module-level __getattr__ function"""

    def test_getattr_no_lap_data_error_deprecation(self):
        """Test deprecated access to NoLapDataError"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = core.__getattr__("NoLapDataError")
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            assert "fastf1.exceptions" in str(w[0].message)
            assert result is exceptions.NoLapDataError

    def test_getattr_data_not_loaded_error_deprecation(self):
        """Test deprecated access to DataNotLoadedError"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = core.__getattr__("DataNotLoadedError")
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            assert result is exceptions.DataNotLoadedError

    def test_getattr_invalid_session_error_deprecation(self):
        """Test deprecated access to InvalidSessionError"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = core.__getattr__("InvalidSessionError")
            assert len(w) >= 1
            assert any("deprecated" in str(warning.message).lower() for warning in w)
            assert result is exceptions.InvalidSessionError

    def test_getattr_unknown_attribute_raises(self):
        """Test that unknown attributes raise AttributeError"""
        with pytest.raises(AttributeError) as excinfo:
            core.__getattr__("UnknownAttribute")
        assert "UnknownAttribute" in str(excinfo.value)
        assert "fastf1.core" in str(excinfo.value)


class TestTelemetry:
    """Tests for Telemetry class"""

    def test_init_with_drop_unknown_channels(self, caplog):
        """Test Telemetry initialization with drop_unknown_channels=True"""
        data = pd.DataFrame({
            'Time': [0, 1, 2],
            'Speed': [100, 110, 120],
            'UnknownChannel': [1, 2, 3]
        })

        telemetry = core.Telemetry(
            data,
            session=None,
            driver='HAM',
            drop_unknown_channels=True
        )
        assert 'UnknownChannel' not in telemetry.columns
        assert any("unknown telemetry channels" in record.message.lower()
                   for record in caplog.records)

    def test_init_without_drop_unknown_channels(self):
        """Test Telemetry initialization with drop_unknown_channels=False"""
        data = pd.DataFrame({
            'Time': [0, 1, 2],
            'Speed': [100, 110, 120],
            'UnknownChannel': [1, 2, 3]
        })

        telemetry = core.Telemetry(
            data,
            session=None,
            driver='HAM',
            drop_unknown_channels=False
        )
        assert 'UnknownChannel' in telemetry.columns

    def test_constructor_property(self):
        """Test _constructor property returns Telemetry"""
        data = pd.DataFrame({'Time': [0, 1, 2]})
        telemetry = core.Telemetry(data)
        assert telemetry._constructor is core.Telemetry

    def test_base_class_view(self):
        """Test base_class_view property"""
        data = pd.DataFrame({'Time': [0, 1, 2], 'Speed': [100, 110, 120]})
        telemetry = core.Telemetry(data)
        view = telemetry.base_class_view
        assert isinstance(view, pd.DataFrame)
        assert not isinstance(view, core.Telemetry)

    def test_join_propagates_metadata(self):
        """Test that join propagates metadata"""
        data1 = pd.DataFrame({'Time': [0, 1, 2], 'Speed': [100, 110, 120]})
        data2 = pd.DataFrame({'RPM': [8000, 8500, 9000]}, index=[0, 1, 2])

        telemetry = core.Telemetry(data1, session=Mock(), driver='HAM')
        result = telemetry.join(data2)

        assert result.session is telemetry.session
        assert result.driver == 'HAM'
        assert 'RPM' in result.columns

    def test_merge_propagates_metadata(self):
        """Test that merge propagates metadata"""
        data1 = pd.DataFrame({'Time': [0, 1, 2], 'Speed': [100, 110, 120]})
        data2 = pd.DataFrame({'Time': [0, 1, 2], 'RPM': [8000, 8500, 9000]})

        telemetry = core.Telemetry(data1, session=Mock(), driver='HAM')
        result = telemetry.merge(data2, on='Time')

        assert result.session is telemetry.session
        assert result.driver == 'HAM'
        assert 'RPM' in result.columns

    def test_slice_by_mask_with_padding_both(self):
        """Test slice_by_mask with padding on both sides"""
        data = pd.DataFrame({'Time': range(10), 'Speed': range(100, 110)})
        telemetry = core.Telemetry(data)

        mask = np.array([False] * 10)
        mask[5] = True

        result = telemetry.slice_by_mask(mask, pad=2, pad_side='both')
        assert len(result) == 5  # indices 3-7
        assert result.iloc[0]['Time'] == 3

    def test_slice_by_mask_with_padding_before(self):
        """Test slice_by_mask with padding before only"""
        data = pd.DataFrame({'Time': range(10), 'Speed': range(100, 110)})
        telemetry = core.Telemetry(data)

        mask = np.array([False] * 10)
        mask[5] = True

        result = telemetry.slice_by_mask(mask, pad=2, pad_side='before')
        assert len(result) == 3  # indices 3-5
        assert result.iloc[0]['Time'] == 3

    def test_slice_by_mask_with_padding_after(self):
        """Test slice_by_mask with padding after only"""
        data = pd.DataFrame({'Time': range(10), 'Speed': range(100, 110)})
        telemetry = core.Telemetry(data)

        mask = np.array([False] * 10)
        mask[5] = True

        result = telemetry.slice_by_mask(mask, pad=2, pad_side='after')
        assert len(result) == 3  # indices 5-7
        assert result.iloc[0]['Time'] == 5

    def test_slice_by_mask_no_padding(self):
        """Test slice_by_mask without padding"""
        data = pd.DataFrame({'Time': range(10), 'Speed': range(100, 110)})
        telemetry = core.Telemetry(data)

        mask = np.array([False] * 10)
        mask[5] = True

        result = telemetry.slice_by_mask(mask, pad=0)
        assert len(result) == 1
        assert result.iloc[0]['Time'] == 5


class TestSession:
    """Tests for Session class"""

    def _create_mock_event(self, year=2023, round_number=5, event_name='Monaco Grand Prix'):
        """Helper to create a mock event"""
        from datetime import datetime
        mock_event = Mock()
        mock_event.year = year
        mock_event.RoundNumber = round_number
        mock_event.EventName = event_name
        mock_event.__getitem__ = Mock(side_effect=lambda key: {
            'EventName': event_name,
            'EventDate': pd.Timestamp(datetime(year, 5, 20))
        }[key])
        mock_event.get_session_date = Mock(return_value=pd.Timestamp(datetime(year, 5, 20)))
        return mock_event

    def test_repr(self):
        """Test Session __repr__ method"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')
        repr_str = repr(session)
        assert '2023' in repr_str
        assert '5' in repr_str
        assert 'Monaco Grand Prix' in repr_str
        assert 'Race' in repr_str

    def test_get_property_warn_not_loaded_raises_exception(self):
        """Test _get_property_warn_not_loaded raises exception when property not loaded"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        with pytest.raises(exceptions.DataNotLoadedError) as excinfo:
            session._get_property_warn_not_loaded('_non_existent_property')
        assert "not been loaded" in str(excinfo.value)

    def test_session_info_not_loaded(self):
        """Test session_info property when data not loaded"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        with pytest.raises(exceptions.DataNotLoadedError):
            _ = session.session_info

    def test_car_data_not_loaded(self):
        """Test car_data property when data not loaded"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        with pytest.raises(exceptions.DataNotLoadedError):
            _ = session.car_data

    def test_pos_data_not_loaded(self):
        """Test pos_data property when data not loaded"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        with pytest.raises(exceptions.DataNotLoadedError):
            _ = session.pos_data

    def test_track_status_not_loaded(self):
        """Test track_status property when data not loaded"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        with pytest.raises(exceptions.DataNotLoadedError):
            _ = session.track_status

    def test_race_control_messages_not_loaded(self):
        """Test race_control_messages property when data not loaded"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        with pytest.raises(exceptions.DataNotLoadedError):
            _ = session.race_control_messages

    def test_t0_date_not_loaded(self):
        """Test t0_date property when data not loaded"""
        mock_event = self._create_mock_event()
        session = core.Session(event=mock_event, session_name='Race')

        with pytest.raises(exceptions.DataNotLoadedError):
            _ = session.t0_date


class TestLaps:
    """Tests for Laps class"""

    @pytest.mark.skip(reason="Requires complex session setup with telemetry data")
    def test_telemetry_not_loaded(self):
        """Test telemetry property when data not loaded"""
        laps_data = pd.DataFrame({'LapNumber': [1, 2], 'Driver': ['HAM', 'HAM']})
        laps = core.Laps(laps_data, session=None)

        with pytest.raises((exceptions.DataNotLoadedError, KeyError, AttributeError)):
            _ = laps.telemetry

    def test_pick_lap_returns_laps(self):
        """Test pick_lap returns Laps object"""
        laps_data = pd.DataFrame({'LapNumber': [1.0, 2.0, 3.0]})
        laps = core.Laps(laps_data)

        # Pick existing lap (suppressing deprecation warning)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            result = laps.pick_lap(2)
            assert isinstance(result, core.Laps)
            assert len(result) == 1
            assert result.iloc[0]['LapNumber'] == 2.0

    def test_pick_wo_box(self):
        """Test pick_wo_box filters out pit stop laps"""
        laps_data = pd.DataFrame({
            'LapNumber': [1, 2, 3, 4],
            'PitOutTime': [pd.NaT, pd.NaT, pd.Timedelta('0 days 00:00:10'), pd.NaT],
            'PitInTime': [pd.NaT, pd.Timedelta('0 days 00:00:05'), pd.NaT, pd.NaT]
        })
        laps = core.Laps(laps_data)

        result = laps.pick_wo_box()
        assert len(result) == 2  # Only laps 1 and 4 should remain

    def test_pick_accurate(self):
        """Test pick_accurate filters laps by accuracy"""
        laps_data = pd.DataFrame({
            'LapNumber': [1, 2, 3],
            'IsAccurate': [True, False, True]
        })
        laps = core.Laps(laps_data)

        result = laps.pick_accurate()
        assert len(result) == 2
        assert all(result['IsAccurate'])


class TestLap:
    """Tests for Lap class"""

    @pytest.mark.skip(reason="Requires complex session setup with telemetry data")
    def test_telemetry_not_loaded(self):
        """Test telemetry property when data not loaded"""
        lap_data = pd.Series({'LapNumber': 1, 'Time': pd.Timedelta('0 days 00:01:30')})
        lap = core.Lap(lap_data)

        with pytest.raises((exceptions.DataNotLoadedError, AttributeError)):
            _ = lap.telemetry

    def test_get_weather_data_fallback_before_lap_end(self):
        """Test get_weather_data returns last value before lap end when no data within lap"""
        # Create mock session with weather data that only exists before the lap
        mock_session = Mock()
        weather_data = pd.DataFrame({
            'Time': [
                pd.Timedelta('0 days 00:00:50'),
                pd.Timedelta('0 days 00:01:00')
            ],
            'AirTemp': [22.0, 23.0],
            'TrackTemp': [35.0, 36.0]
        })
        mock_session.weather_data = weather_data

        # Create lap that starts after all weather data
        lap_data = pd.Series({
            'LapStartTime': pd.Timedelta('0 days 00:01:20'),
            'Time': pd.Timedelta('0 days 00:02:00')
        })
        lap = core.Lap(lap_data)
        lap.session = mock_session

        result = lap.get_weather_data()

        # Should return the last weather data point before lap end (second row)
        assert result['Time'] == pd.Timedelta('0 days 00:01:00')
        assert result['AirTemp'] == 23.0
        assert result['TrackTemp'] == 36.0

    def test_get_weather_data_no_data_available(self):
        """Test get_weather_data returns Series with NaN values when no weather data available"""
        # Create mock session with weather data that only exists after the lap
        mock_session = Mock()
        weather_data = pd.DataFrame({
            'Time': [
                pd.Timedelta('0 days 00:03:00'),
                pd.Timedelta('0 days 00:04:00')
            ],
            'AirTemp': [22.0, 23.0],
            'TrackTemp': [35.0, 36.0]
        })
        mock_session.weather_data = weather_data

        # Create lap that ends before any weather data
        lap_data = pd.Series({
            'LapStartTime': pd.Timedelta('0 days 00:01:00'),
            'Time': pd.Timedelta('0 days 00:02:00')
        })
        lap = core.Lap(lap_data)
        lap.session = mock_session

        result = lap.get_weather_data()

        # Should return Series with correct column names but NaN values
        assert isinstance(result, pd.Series)
        assert list(result.index) == list(weather_data.columns)
        assert pd.isna(result['Time'])
        assert pd.isna(result['AirTemp'])
        assert pd.isna(result['TrackTemp'])


class TestDriverResult:
    """Tests for DriverResult class"""

    def test_dnf_finished(self):
        """Test dnf property for finished driver"""
        driver_data = pd.Series({'Status': 'Finished'})
        driver_result = core.DriverResult(driver_data)
        assert driver_result.dnf is False

    def test_dnf_lapped(self):
        """Test dnf property for lapped driver"""
        driver_data = pd.Series({'Status': '+1 Lap'})
        driver_result = core.DriverResult(driver_data)
        assert driver_result.dnf is False

    def test_dnf_retired(self):
        """Test dnf property for retired driver"""
        driver_data = pd.Series({'Status': 'Retired'})
        driver_result = core.DriverResult(driver_data)
        assert driver_result.dnf is True

    def test_dnf_accident(self):
        """Test dnf property for accident"""
        driver_data = pd.Series({'Status': 'Accident'})
        driver_result = core.DriverResult(driver_data)
        assert driver_result.dnf is True
