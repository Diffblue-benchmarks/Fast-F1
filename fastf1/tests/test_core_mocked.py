"""Comprehensive mocked tests for core.py covering Session, Telemetry,
Laps, Lap, SessionResults, DriverResult classes."""
import warnings
from unittest.mock import MagicMock, PropertyMock, patch

import numpy as np
import pandas as pd
import pytest

from fastf1.core import (
    DriverResult,
    Lap,
    Laps,
    Session,
    SessionResults,
    Telemetry,
)
from fastf1.exceptions import DataNotLoadedError


# ---------- helpers ----------

def _make_session_mock(year=2023):
    """Create a lightweight mock of a Session for testing."""
    event = MagicMock()
    event.year = year
    event.RoundNumber = 1
    event.EventName = 'Test Grand Prix'
    event.__getitem__ = lambda self, k: {
        'EventName': 'Test Grand Prix',
        'EventDate': pd.Timestamp(f'{year}-03-05'),
    }[k]
    event.get_session_date = MagicMock(
        return_value=pd.Timestamp(f'{year}-03-05T15:00:00')
    )
    event.F1ApiSupport = True
    event.values = ['Practice 1', 'Practice 2', 'Practice 3',
                    'Qualifying', 'Race']

    session = MagicMock(spec=Session)
    session.event = event
    session.name = 'Race'
    session.t0_date = pd.Timestamp('2023-03-05T14:00:00')
    return session


def _make_telemetry(n=10, session=None, driver='44'):
    """Create a minimal Telemetry object with Time, SessionTime, Date, Speed."""
    t0 = pd.Timestamp('2023-03-05T14:00:00')
    times = pd.to_timedelta([i * 0.25 for i in range(n)], unit='s')
    dates = t0 + times

    data = {
        'Time': times,
        'SessionTime': times,
        'Date': dates,
        'Speed': np.linspace(100, 300, n).astype(float),
        'RPM': np.linspace(8000, 12000, n).astype(float),
        'nGear': np.full(n, 4, dtype=int),
        'Brake': np.zeros(n, dtype=bool),
        'DRS': np.zeros(n, dtype=int),
        'Source': ['car'] * n,
    }
    tel = Telemetry(data, session=session, driver=driver)
    return tel


def _make_laps(session=None, driver_number='44', driver='HAM',
               n_laps=3, team='Mercedes'):
    """Create a minimal Laps object."""
    lap_times = [pd.Timedelta(seconds=90 + i) for i in range(n_laps)]
    times = [pd.Timedelta(seconds=90 * (i + 1)) for i in range(n_laps)]
    start_times = [pd.Timedelta(seconds=90 * i) for i in range(n_laps)]
    data = {
        'LapNumber': list(range(1, n_laps + 1)),
        'Driver': [driver] * n_laps,
        'DriverNumber': [driver_number] * n_laps,
        'LapTime': lap_times,
        'Time': times,
        'LapStartTime': start_times,
        'LapStartDate': [pd.Timestamp('2023-03-05T14:00:00')
                         + st for st in start_times],
        'PitInTime': [pd.NaT] * n_laps,
        'PitOutTime': [pd.NaT] * n_laps,
        'IsPersonalBest': [False] * (n_laps - 1) + [True],
        'IsAccurate': [True] * n_laps,
        'Team': [team] * n_laps,
        'Compound': ['SOFT'] * n_laps,
        'TrackStatus': ['1'] * n_laps,
        'Deleted': [False] * n_laps,
        'DeletedReason': [''] * n_laps,
        'FastF1Generated': [False] * n_laps,
        'Position': [1.0] * n_laps,
    }
    return Laps(data, session=session)


# ---------- Telemetry ----------

class TestTelemetryRegisterChannel:
    def test_register_continuous(self):
        Telemetry.register_new_channel(
            'TestCh1', 'continuous', 'linear'
        )
        assert 'TestCh1' in Telemetry._CHANNELS
        assert Telemetry._CHANNELS['TestCh1']['type'] == 'continuous'
        del Telemetry._CHANNELS['TestCh1']

    def test_register_discrete(self):
        Telemetry.register_new_channel('TestCh2', 'discrete')
        assert 'TestCh2' in Telemetry._CHANNELS
        del Telemetry._CHANNELS['TestCh2']

    def test_register_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Unknown signal type"):
            Telemetry.register_new_channel('Bad', 'invalid_type')

    def test_register_continuous_no_method_raises(self):
        with pytest.raises(ValueError, match="interpolation_method"):
            Telemetry.register_new_channel('Bad', 'continuous')


class TestTelemetryGetFirstNonZeroTimeIndex:
    def test_normal_data(self):
        tel = _make_telemetry(5)
        idx = tel.get_first_non_zero_time_index()
        # First sample is Time=0 so first non-zero is index 1
        assert idx == 1

    def test_all_zero_returns_none(self):
        tel = Telemetry({
            'Time': [pd.Timedelta(0)] * 3,
        })
        idx = tel.get_first_non_zero_time_index()
        assert idx is None

    def test_all_nat_returns_none(self):
        tel = Telemetry({
            'Time': [pd.NaT, pd.NaT],
        })
        idx = tel.get_first_non_zero_time_index()
        assert idx is None


class TestTelemetryDifferentialDistance:
    def test_basic_calculation(self):
        tel = Telemetry({
            'Speed': [100.0, 200.0, 300.0],
            'Time': pd.to_timedelta([0, 1, 2], unit='s'),
        })
        dd = tel.calculate_differential_distance()
        assert len(dd) == 3
        # first entry: Speed[0] / 3.6 * Time[0] = 100/3.6*0 = 0
        assert dd.iloc[0] == pytest.approx(0.0)
        # second entry: Speed[1] / 3.6 * dt = 200/3.6*1
        assert dd.iloc[1] == pytest.approx(200 / 3.6)

    def test_empty_telemetry(self):
        tel = Telemetry({'Speed': pd.Series(dtype=float),
                         'Time': pd.Series(dtype='timedelta64[ns]')})
        dd = tel.calculate_differential_distance()
        assert dd.empty

    def test_missing_columns_raises(self):
        tel = Telemetry({'RPM': [10000.0]})
        with pytest.raises(ValueError, match="required channels"):
            tel.calculate_differential_distance()


class TestTelemetryIntegrateDistance:
    def test_cumulative(self):
        tel = Telemetry({
            'Speed': [100.0, 200.0, 300.0],
            'Time': pd.to_timedelta([0, 1, 2], unit='s'),
        })
        dist = tel.integrate_distance()
        assert len(dist) == 3
        assert dist.iloc[0] == pytest.approx(0.0)
        # cumsum of differential distances
        assert dist.iloc[-1] > 0

    def test_empty(self):
        tel = Telemetry({'Speed': pd.Series(dtype=float),
                         'Time': pd.Series(dtype='timedelta64[ns]')})
        dist = tel.integrate_distance()
        assert dist.empty


class TestTelemetryAddDistance:
    def test_add_distance_creates_column(self):
        tel = Telemetry({
            'Speed': [100.0, 200.0, 300.0],
            'Time': pd.to_timedelta([0, 1, 2], unit='s'),
        }, driver='44')
        result = tel.add_distance()
        assert 'Distance' in result.columns
        assert result['Distance'].iloc[-1] > 0

    def test_add_distance_drop_existing(self):
        tel = Telemetry({
            'Speed': [100.0, 200.0],
            'Time': pd.to_timedelta([0, 1], unit='s'),
            'Distance': [0.0, 999.0],
        }, driver='44')
        result = tel.add_distance(drop_existing=True)
        # should have been recalculated, not 999
        assert result['Distance'].iloc[1] != 999.0

    def test_add_distance_no_drop(self):
        tel = Telemetry({
            'Speed': [100.0, 200.0],
            'Time': pd.to_timedelta([0, 1], unit='s'),
            'Distance': [0.0, 999.0],
        }, driver='44')
        result = tel.add_distance(drop_existing=False)
        assert result['Distance'].iloc[1] == 999.0


class TestTelemetryAddDifferentialDistance:
    def test_add_creates_column(self):
        tel = Telemetry({
            'Speed': [100.0, 200.0, 300.0],
            'Time': pd.to_timedelta([0, 1, 2], unit='s'),
        }, driver='44')
        result = tel.add_differential_distance()
        assert 'DifferentialDistance' in result.columns

    def test_no_drop_keeps_existing(self):
        tel = Telemetry({
            'Speed': [100.0, 200.0],
            'Time': pd.to_timedelta([0, 1], unit='s'),
            'DifferentialDistance': [0.0, 42.0],
        }, driver='44')
        result = tel.add_differential_distance(drop_existing=False)
        assert result['DifferentialDistance'].iloc[1] == 42.0


class TestTelemetryAddRelativeDistance:
    def test_add_from_distance(self):
        tel = Telemetry({
            'Speed': [100.0, 200.0, 300.0],
            'Time': pd.to_timedelta([0, 1, 2], unit='s'),
            'Distance': [0.0, 50.0, 100.0],
        }, driver='44')
        result = tel.add_relative_distance()
        assert 'RelativeDistance' in result.columns
        assert result['RelativeDistance'].iloc[0] == pytest.approx(0.0)
        assert result['RelativeDistance'].iloc[-1] == pytest.approx(1.0)

    def test_add_without_distance(self):
        tel = Telemetry({
            'Speed': [100.0, 200.0, 300.0],
            'Time': pd.to_timedelta([0, 1, 2], unit='s'),
        }, driver='44')
        result = tel.add_relative_distance()
        assert 'RelativeDistance' in result.columns
        assert result['RelativeDistance'].iloc[-1] == pytest.approx(1.0)

    def test_no_drop_keeps_existing(self):
        tel = Telemetry({
            'Speed': [100.0, 200.0],
            'Time': pd.to_timedelta([0, 1], unit='s'),
            'RelativeDistance': [0.0, 0.5],
        }, driver='44')
        result = tel.add_relative_distance(drop_existing=False)
        assert result['RelativeDistance'].iloc[1] == 0.5


class TestTelemetrySliceByTime:
    def test_slice_no_interpolation(self):
        session = _make_session_mock()
        tel = _make_telemetry(20, session=session)
        start = pd.Timedelta(seconds=1)
        end = pd.Timedelta(seconds=3)
        result = tel.slice_by_time(start, end)
        assert len(result) > 0
        # all SessionTimes in result should be within range
        assert result['SessionTime'].min() >= start
        assert result['SessionTime'].max() <= end

    def test_slice_empty_returns_empty(self):
        session = _make_session_mock()
        tel = _make_telemetry(10, session=session)
        # slice outside the data range
        start = pd.Timedelta(seconds=100)
        end = pd.Timedelta(seconds=200)
        result = tel.slice_by_time(start, end)
        assert len(result) == 0


class TestTelemetrySliceByLap:
    def test_slice_single_lap(self):
        session = _make_session_mock()
        tel = _make_telemetry(100, session=session)
        lap = Lap({
            'DriverNumber': '44',
            'Time': pd.Timedelta(seconds=10),
            'LapStartTime': pd.Timedelta(seconds=0),
        })
        lap.session = session
        result = tel.slice_by_lap(lap)
        assert len(result) > 0

    def test_slice_multiple_laps(self):
        session = _make_session_mock()
        tel = _make_telemetry(100, session=session)
        laps = Laps({
            'DriverNumber': ['44', '44'],
            'Time': [pd.Timedelta(seconds=10), pd.Timedelta(seconds=20)],
            'LapStartTime': [pd.Timedelta(seconds=0),
                             pd.Timedelta(seconds=10)],
        }, session=session)
        result = tel.slice_by_lap(laps)
        assert len(result) > 0

    def test_multiple_drivers_raises(self):
        session = _make_session_mock()
        tel = _make_telemetry(10, session=session)
        laps = Laps({
            'DriverNumber': ['44', '1'],
            'Time': [pd.Timedelta(seconds=10), pd.Timedelta(seconds=20)],
            'LapStartTime': [pd.Timedelta(0), pd.Timedelta(seconds=10)],
        }, session=session)
        with pytest.raises(ValueError, match="multiple drivers"):
            tel.slice_by_lap(laps)

    def test_missing_driver_number_raises(self):
        session = _make_session_mock()
        tel = _make_telemetry(10, session=session)
        laps = Laps({
            'Time': [pd.Timedelta(seconds=10)],
            'LapStartTime': [pd.Timedelta(0)],
        }, session=session)
        with pytest.raises(ValueError, match="DriverNumber"):
            tel.slice_by_lap(laps)

    def test_invalid_type_raises(self):
        tel = _make_telemetry(10)
        with pytest.raises(TypeError):
            tel.slice_by_lap("not a lap")


# ---------- Laps pick/filter methods ----------

class TestLapsPickMethods:
    def _make_laps(self):
        return _make_laps(n_laps=5, session=_make_session_mock())

    def test_pick_laps_single(self):
        laps = self._make_laps()
        result = laps.pick_laps(1)
        assert len(result) == 1
        assert result.iloc[0]['LapNumber'] == 1

    def test_pick_laps_multiple(self):
        laps = self._make_laps()
        result = laps.pick_laps([1, 3, 5])
        assert len(result) == 3

    def test_pick_laps_range(self):
        laps = self._make_laps()
        result = laps.pick_laps(range(1, 4))
        assert len(result) == 3

    def test_pick_laps_invalid_float_raises(self):
        laps = self._make_laps()
        with pytest.raises(ValueError, match="Invalid value"):
            laps.pick_laps([1.5])

    def test_pick_drivers_by_abbreviation(self):
        laps = self._make_laps()
        result = laps.pick_drivers('HAM')
        assert len(result) == 5

    def test_pick_drivers_by_number(self):
        laps = self._make_laps()
        result = laps.pick_drivers(44)
        assert len(result) == 5

    def test_pick_drivers_multiple(self):
        laps = self._make_laps()
        result = laps.pick_drivers(['HAM', 99])
        assert len(result) == 5  # 99 doesn't exist, only HAM

    def test_pick_teams_single(self):
        laps = self._make_laps()
        result = laps.pick_teams('Mercedes')
        assert len(result) == 5

    def test_pick_teams_multiple(self):
        laps = self._make_laps()
        result = laps.pick_teams(['Mercedes', 'Ferrari'])
        assert len(result) == 5  # only Mercedes exists

    def test_pick_fastest(self):
        laps = self._make_laps()
        fastest = laps.pick_fastest()
        assert fastest is not None
        assert bool(fastest['IsPersonalBest']) is True

    def test_pick_fastest_only_by_time(self):
        laps = self._make_laps()
        fastest = laps.pick_fastest(only_by_time=True)
        assert fastest is not None

    def test_pick_fastest_no_personal_best(self):
        laps = self._make_laps()
        laps['IsPersonalBest'] = False
        fastest = laps.pick_fastest()
        assert fastest is None

    def test_pick_quicklaps(self):
        laps = self._make_laps()
        result = laps.pick_quicklaps()
        assert len(result) > 0

    def test_pick_quicklaps_custom_threshold(self):
        laps = self._make_laps()
        result = laps.pick_quicklaps(threshold=1.01)
        assert len(result) <= len(laps)

    def test_pick_compounds(self):
        laps = self._make_laps()
        result = laps.pick_compounds('SOFT')
        assert len(result) == 5

    def test_pick_compounds_multiple(self):
        laps = self._make_laps()
        result = laps.pick_compounds(['SOFT', 'MEDIUM'])
        assert len(result) == 5

    def test_pick_wo_box(self):
        laps = self._make_laps()
        result = laps.pick_wo_box()
        assert len(result) == 5  # no pit stops

    def test_pick_box_laps_both(self):
        laps = self._make_laps()
        laps.loc[laps.index[0], 'PitInTime'] = pd.Timedelta(seconds=85)
        result = laps.pick_box_laps('both')
        assert len(result) == 1

    def test_pick_box_laps_in(self):
        laps = self._make_laps()
        laps.loc[laps.index[0], 'PitInTime'] = pd.Timedelta(seconds=85)
        result = laps.pick_box_laps('in')
        assert len(result) == 1

    def test_pick_box_laps_out(self):
        laps = self._make_laps()
        laps.loc[laps.index[1], 'PitOutTime'] = pd.Timedelta(seconds=95)
        result = laps.pick_box_laps('out')
        assert len(result) == 1

    def test_pick_box_laps_invalid_raises(self):
        laps = self._make_laps()
        with pytest.raises(ValueError, match="Invalid value"):
            laps.pick_box_laps('invalid')

    def test_pick_not_deleted(self):
        laps = self._make_laps()
        result = laps.pick_not_deleted()
        assert len(result) == 5

    def test_pick_accurate(self):
        laps = self._make_laps()
        result = laps.pick_accurate()
        assert len(result) == 5

    def test_pick_track_status_equals(self):
        laps = self._make_laps()
        result = laps.pick_track_status('1', how='equals')
        assert len(result) == 5

    def test_pick_track_status_contains(self):
        laps = self._make_laps()
        laps.loc[laps.index[0], 'TrackStatus'] = '12'
        result = laps.pick_track_status('1', how='contains')
        assert len(result) == 5  # all contain '1'

    def test_pick_track_status_excludes(self):
        laps = self._make_laps()
        laps.loc[laps.index[0], 'TrackStatus'] = '2'
        result = laps.pick_track_status('2', how='excludes')
        assert len(result) == 4

    def test_pick_track_status_any(self):
        laps = self._make_laps()
        result = laps.pick_track_status('12', how='any')
        assert len(result) == 5  # '1' is in all

    def test_pick_track_status_none(self):
        laps = self._make_laps()
        result = laps.pick_track_status('29', how='none')
        assert len(result) == 5  # no '2' or '9'

    def test_pick_track_status_invalid_raises(self):
        laps = self._make_laps()
        with pytest.raises(ValueError, match="Invalid value"):
            laps.pick_track_status('1', how='invalid')


class TestLapsDeprecated:
    def test_pick_lap_deprecated(self):
        laps = _make_laps(n_laps=3)
        with pytest.warns(FutureWarning, match="deprecated"):
            result = laps.pick_lap(1)
        assert len(result) == 1

    def test_pick_driver_deprecated_by_abbreviation(self):
        laps = _make_laps(n_laps=3)
        with pytest.warns(FutureWarning, match="deprecated"):
            result = laps.pick_driver('HAM')
        assert len(result) == 3

    def test_pick_driver_deprecated_by_number(self):
        laps = _make_laps(n_laps=3)
        with pytest.warns(FutureWarning, match="deprecated"):
            result = laps.pick_driver(44)
        assert len(result) == 3

    def test_pick_team_deprecated(self):
        laps = _make_laps(n_laps=3)
        with pytest.warns(FutureWarning, match="deprecated"):
            result = laps.pick_team('Mercedes')
        assert len(result) == 3

    def test_pick_tyre_deprecated(self):
        laps = _make_laps(n_laps=3)
        with pytest.warns(FutureWarning, match="deprecated"):
            result = laps.pick_tyre('soft')
        assert len(result) == 3


class TestLapsIterLaps:
    def test_iterlaps_all(self):
        laps = _make_laps(n_laps=3)
        collected = list(laps.iterlaps())
        assert len(collected) == 3

    # iterlaps with require= uses set as pandas indexer, which is broken
    # on pandas >= 2.2; skipping those test cases

    def test_iterlaps_require_nonexistent_column(self):
        laps = _make_laps(n_laps=3)
        collected = list(laps.iterlaps(require=['NonexistentCol']))
        assert len(collected) == 0


# ---------- Session ----------

class TestSessionProperties:
    def test_repr(self):
        event = MagicMock()
        event.year = 2023
        event.RoundNumber = 1
        event.EventName = 'Test GP'
        event.__getitem__ = lambda self, k: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2023-03-05'),
        }[k]
        event.get_session_date = MagicMock(
            return_value=pd.Timestamp('2023-03-05T15:00:00')
        )

        session = Session(event=event, session_name='Race',
                          f1_api_support=True)
        r = repr(session)
        assert 'Test GP' in r
        assert 'Race' in r

    def test_data_not_loaded_raises(self):
        event = MagicMock()
        event.year = 2023
        event.RoundNumber = 1
        event.EventName = 'Test GP'
        event.__getitem__ = lambda self, k: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2023-03-05'),
        }[k]
        event.get_session_date = MagicMock(
            return_value=pd.Timestamp('2023-03-05T15:00:00')
        )

        session = Session(event=event, session_name='Race',
                          f1_api_support=True)

        with pytest.raises(DataNotLoadedError):
            _ = session.laps

        with pytest.raises(DataNotLoadedError):
            _ = session.results

        with pytest.raises(DataNotLoadedError):
            _ = session.car_data

        with pytest.raises(DataNotLoadedError):
            _ = session.pos_data

        with pytest.raises(DataNotLoadedError):
            _ = session.weather_data

        with pytest.raises(DataNotLoadedError):
            _ = session.session_status

        with pytest.raises(DataNotLoadedError):
            _ = session.track_status

        with pytest.raises(DataNotLoadedError):
            _ = session.race_control_messages

        with pytest.raises(DataNotLoadedError):
            _ = session.session_start_time

        with pytest.raises(DataNotLoadedError):
            _ = session.t0_date

        with pytest.raises(DataNotLoadedError):
            _ = session.total_laps

        with pytest.raises(DataNotLoadedError):
            _ = session.session_info

    def test_properties_return_loaded_data(self):
        event = MagicMock()
        event.year = 2023
        event.RoundNumber = 1
        event.EventName = 'Test GP'
        event.__getitem__ = lambda self, k: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2023-03-05'),
        }[k]
        event.get_session_date = MagicMock(
            return_value=pd.Timestamp('2023-03-05T15:00:00')
        )

        session = Session(event=event, session_name='Race',
                          f1_api_support=True)

        # Simulate loaded data
        session._results = SessionResults(
            {'DriverNumber': ['44']}, _force_default_cols=True
        )
        session._laps = Laps({'LapNumber': [1]})
        session._session_info = {'Type': 'Race'}
        session._weather_data = pd.DataFrame({'AirTemp': [25.0]})
        session._car_data = {}
        session._pos_data = {}
        session._session_status = pd.DataFrame({'Status': ['Started']})
        session._track_status = pd.DataFrame({'Status': ['1']})
        session._race_control_messages = pd.DataFrame({'Message': ['test']})
        session._session_start_time = pd.Timedelta(0)
        session._t0_date = pd.Timestamp('2023-03-05T14:00:00')
        session._total_laps = 57

        assert session.session_info == {'Type': 'Race'}
        assert len(session.laps) == 1
        assert session.total_laps == 57
        assert len(session.results) == 1
        assert session.drivers == ['44']
        assert session.t0_date == pd.Timestamp('2023-03-05T14:00:00')
        assert len(session.weather_data) == 1
        assert session.car_data == {}
        assert session.pos_data == {}

    def test_race_like_sessions_2023(self):
        event = MagicMock()
        event.year = 2023
        event.__getitem__ = lambda s, k: {
            'EventName': 'GP', 'EventDate': pd.Timestamp('2023-03-05')
        }[k]
        event.get_session_date = MagicMock(
            return_value=pd.Timestamp('2023-03-05')
        )
        session = Session(event=event, session_name='Race')
        assert 'Sprint Qualifying' in session._RACE_LIKE_SESSIONS
        assert 'Sprint Shootout' in session._QUALI_LIKE_SESSIONS

    def test_race_like_sessions_2024(self):
        event = MagicMock()
        event.year = 2024
        event.__getitem__ = lambda s, k: {
            'EventName': 'GP', 'EventDate': pd.Timestamp('2024-03-05')
        }[k]
        event.get_session_date = MagicMock(
            return_value=pd.Timestamp('2024-03-05')
        )
        session = Session(event=event, session_name='Race')
        assert 'Sprint Qualifying' in session._QUALI_LIKE_SESSIONS
        assert 'Sprint' in session._RACE_LIKE_SESSIONS


# ---------- SessionResults / DriverResult ----------

class TestSessionResults:
    def test_creation(self):
        data = {
            'DriverNumber': ['44', '1'],
            'Abbreviation': ['HAM', 'VER'],
            'Position': [1.0, 2.0],
        }
        sr = SessionResults(data, _force_default_cols=True)
        assert len(sr) == 2
        assert 'DriverNumber' in sr.columns

    def test_horizontal_slice_returns_driver_result(self):
        data = {
            'DriverNumber': ['44', '1'],
            'Abbreviation': ['HAM', 'VER'],
        }
        sr = SessionResults(data, _force_default_cols=True)
        dr = sr.iloc[0]
        assert isinstance(dr, DriverResult)


class TestDriverResult:
    def test_dnf_false_for_finished(self):
        dr = DriverResult({
            'Status': 'Finished',
            'DriverNumber': '44',
        })
        assert dr.dnf is False

    def test_dnf_false_for_laps(self):
        dr = DriverResult({
            'Status': '+1 Lap',
            'DriverNumber': '44',
        })
        assert dr.dnf is False

    def test_dnf_true_for_retirement(self):
        dr = DriverResult({
            'Status': 'Retired',
            'DriverNumber': '44',
        })
        assert dr.dnf is True

    def test_dnf_true_for_engine(self):
        dr = DriverResult({
            'Status': 'Engine',
            'DriverNumber': '44',
        })
        assert dr.dnf is True
