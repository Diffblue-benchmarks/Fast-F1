"""Tests for Session._fix_missing_laps_retired_on_track method"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock

from fastf1.core import Session


class TestSessionFixMissingLapsRetiredOnTrack:
    """Tests for Session._fix_missing_laps_retired_on_track method"""

    def test_no_laps_attribute(self):
        """Test when session has no _laps attribute"""
        # Create a minimal session object
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)
        # Ensure _laps attribute doesn't exist
        if hasattr(session, '_laps'):
            delattr(session, '_laps')

        # Should return early without error
        session._fix_missing_laps_retired_on_track()
        assert not hasattr(session, '_laps')

    def test_single_fastf1_generated_lap(self):
        """Test when driver has only one FastF1-generated lap"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)

        # Create laps data with a single FastF1Generated lap
        session._laps = pd.DataFrame({
            'DriverNumber': ['44'],
            'Driver': ['HAM'],
            'Team': ['Mercedes'],
            'LapNumber': [1],
            'Time': [pd.Timedelta(seconds=90)],
            'LapStartTime': [pd.Timedelta(seconds=0)],
            'Stint': [1],
            'Compound': ['SOFT'],
            'TyreLife': [1],
            'FreshTyre': [True],
            'PitInTime': [pd.NaT],
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [True],
            'Position': [1.0]
        })

        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=100)],
            'Status': ['Finished']
        })

        initial_len = len(session._laps)
        session._fix_missing_laps_retired_on_track()
        # Should not add a lap
        assert len(session._laps) == initial_len

    def test_ref_time_fallback_to_lap_start_time(self):
        """Test when Time is NaT, fallback to LapStartTime"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)
        session._add_track_status_to_laps = Mock()

        # Create laps data where Time is NaT
        session._laps = pd.DataFrame({
            'DriverNumber': ['44'],
            'Driver': ['HAM'],
            'Team': ['Mercedes'],
            'LapNumber': [1],
            'Time': [pd.NaT],
            'LapStartTime': [pd.Timedelta(seconds=0)],
            'Stint': [1],
            'Compound': ['SOFT'],
            'TyreLife': [1],
            'FreshTyre': [True],
            'PitInTime': [pd.NaT],
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [False],
            'Position': [1.0]
        })

        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=100)],
            'Status': ['Finished']
        })
        session._total_laps = 10

        session._fix_missing_laps_retired_on_track()
        # Should add a lap
        assert len(session._laps) == 2

    def test_driver_completed_race_distance_early(self, caplog):
        """Test warning when driver completed total laps before race finished"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)

        # Create laps where driver completed total laps
        session._laps = pd.DataFrame({
            'DriverNumber': ['44'],
            'Driver': ['HAM'],
            'Team': ['Mercedes'],
            'LapNumber': [50],
            'Time': [pd.Timedelta(seconds=5000)],
            'LapStartTime': [pd.Timedelta(seconds=4910)],
            'Stint': [1],
            'Compound': ['SOFT'],
            'TyreLife': [50],
            'FreshTyre': [False],
            'PitInTime': [pd.NaT],
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [False],
            'Position': [1.0]
        })

        session._session_status = pd.DataFrame({
            'Time': [
                pd.Timedelta(seconds=4000),
                pd.Timedelta(seconds=5200)
            ],
            'Status': ['', 'Finished']
        })
        session._total_laps = 50

        initial_len = len(session._laps)
        session._fix_missing_laps_retired_on_track()

        # Should not add a lap
        assert len(session._laps) == initial_len
        # Should log warning
        assert any("completed the race distance" in record.message for record in caplog.records)

    def test_driver_finished_session_correctly(self):
        """Test when driver finished session correctly (Finished status before last lap)"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)

        session._laps = pd.DataFrame({
            'DriverNumber': ['44'],
            'Driver': ['HAM'],
            'Team': ['Mercedes'],
            'LapNumber': [45],
            'Time': [pd.Timedelta(seconds=5000)],
            'LapStartTime': [pd.Timedelta(seconds=4910)],
            'Stint': [1],
            'Compound': ['SOFT'],
            'TyreLife': [45],
            'FreshTyre': [False],
            'PitInTime': [pd.NaT],
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [False],
            'Position': [1.0]
        })

        # Finished status exists before driver's last lap time
        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=4900), pd.Timedelta(seconds=5200)],
            'Status': ['Finished', 'Other']
        })
        session._total_laps = 50

        initial_len = len(session._laps)
        session._fix_missing_laps_retired_on_track()
        # Should not add a lap
        assert len(session._laps) == initial_len

    def test_inconclusive_data_no_next_statuses(self):
        """Test when data is inconclusive (no next statuses)"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)

        session._laps = pd.DataFrame({
            'DriverNumber': ['44'],
            'Driver': ['HAM'],
            'Team': ['Mercedes'],
            'LapNumber': [45],
            'Time': [pd.Timedelta(seconds=5000)],
            'LapStartTime': [pd.Timedelta(seconds=4910)],
            'Stint': [1],
            'Compound': ['SOFT'],
            'TyreLife': [45],
            'FreshTyre': [False],
            'PitInTime': [pd.NaT],
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [False],
            'Position': [1.0]
        })

        # All statuses are before the driver's lap
        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=100)],
            'Status': ['Started']
        })
        session._total_laps = 50

        initial_len = len(session._laps)
        session._fix_missing_laps_retired_on_track()
        # Should not add a lap
        assert len(session._laps) == initial_len

    def test_inconclusive_data_no_finished_status(self):
        """Test when data is inconclusive (no Finished status in next statuses)"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)

        session._laps = pd.DataFrame({
            'DriverNumber': ['44'],
            'Driver': ['HAM'],
            'Team': ['Mercedes'],
            'LapNumber': [45],
            'Time': [pd.Timedelta(seconds=5000)],
            'LapStartTime': [pd.Timedelta(seconds=4910)],
            'Stint': [1],
            'Compound': ['SOFT'],
            'TyreLife': [45],
            'FreshTyre': [False],
            'PitInTime': [pd.NaT],
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [False],
            'Position': [1.0]
        })

        # Next status exists but is not Finished
        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=5100)],
            'Status': ['SomeOtherStatus']
        })
        session._total_laps = 50

        initial_len = len(session._laps)
        session._fix_missing_laps_retired_on_track()
        # Should not add a lap
        assert len(session._laps) == initial_len

    def test_last_lap_was_inlap(self):
        """Test when last lap was an inlap"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)

        session._laps = pd.DataFrame({
            'DriverNumber': ['44'],
            'Driver': ['HAM'],
            'Team': ['Mercedes'],
            'LapNumber': [45],
            'Time': [pd.Timedelta(seconds=5000)],
            'LapStartTime': [pd.Timedelta(seconds=4910)],
            'Stint': [1],
            'Compound': ['SOFT'],
            'TyreLife': [45],
            'FreshTyre': [False],
            'PitInTime': [pd.Timedelta(seconds=5000)],  # Last lap was an inlap
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [False],
            'Position': [1.0]
        })

        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=5100)],
            'Status': ['Finished']
        })
        session._total_laps = 50

        initial_len = len(session._laps)
        session._fix_missing_laps_retired_on_track()
        # Should not add a lap
        assert len(session._laps) == initial_len

    def test_driver_completed_full_race_distance(self):
        """Test when driver has already completed full race distance"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)
        session._total_laps = 50

        # Create 50 laps (full race distance)
        lap_data = []
        for i in range(50):
            lap_data.append({
                'DriverNumber': '44',
                'Driver': 'HAM',
                'Team': 'Mercedes',
                'LapNumber': i + 1,
                'Time': pd.Timedelta(seconds=90 * (i + 1)),
                'LapStartTime': pd.Timedelta(seconds=90 * i),
                'Stint': 1,
                'Compound': 'SOFT',
                'TyreLife': i + 1,
                'FreshTyre': i == 0,
                'PitInTime': pd.NaT,
                'PitOutTime': pd.NaT,
                'FastF1Generated': False,
                'Position': 1.0
            })

        session._laps = pd.DataFrame(lap_data)

        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=5000)],
            'Status': ['Finished']
        })
        session._total_laps = 48  # Total laps is less than actual laps

        initial_len = len(session._laps)
        session._fix_missing_laps_retired_on_track()
        # Should not add a lap
        assert len(session._laps) == initial_len

    def test_new_lap_started_in_pit_lane(self):
        """Test when last lap was inlap and new lap started in pit lane"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)

        # Two laps: first is inlap, second started in pit with no PitOutTime
        session._laps = pd.DataFrame({
            'DriverNumber': ['44', '44'],
            'Driver': ['HAM', 'HAM'],
            'Team': ['Mercedes', 'Mercedes'],
            'LapNumber': [44, 45],
            'Time': [pd.Timedelta(seconds=4900), pd.Timedelta(seconds=5000)],
            'LapStartTime': [pd.Timedelta(seconds=4810), pd.Timedelta(seconds=4910)],
            'Stint': [1, 1],
            'Compound': ['SOFT', 'SOFT'],
            'TyreLife': [44, 45],
            'FreshTyre': [False, False],
            'PitInTime': [pd.Timedelta(seconds=4900), pd.NaT],
            'PitOutTime': [pd.NaT, pd.NaT],
            'FastF1Generated': [False, False],
            'Position': [1.0, 1.0]
        })

        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=5100)],
            'Status': ['Finished']
        })
        session._total_laps = 50

        initial_len = len(session._laps)
        session._fix_missing_laps_retired_on_track()
        # Should not add a lap
        assert len(session._laps) == initial_len

    def test_session_aborted(self):
        """Test when session was aborted"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)
        session._add_track_status_to_laps = Mock()

        session._laps = pd.DataFrame({
            'DriverNumber': ['44'],
            'Driver': ['HAM'],
            'Team': ['Mercedes'],
            'LapNumber': [45],
            'Time': [pd.Timedelta(seconds=5000)],
            'LapStartTime': [pd.Timedelta(seconds=4910)],
            'Stint': [1],
            'Compound': ['SOFT'],
            'TyreLife': [45],
            'FreshTyre': [False],
            'PitInTime': [pd.NaT],
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [False],
            'Position': [1.0]
        })

        # Session was aborted then finished
        # Need both Aborted and Finished statuses:
        # - Finished is needed to pass the check at line 1732
        # - Aborted (first) triggers the specific handling at line 1759
        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=5100), pd.Timedelta(seconds=5200)],
            'Status': ['Aborted', 'Finished']
        })
        session._total_laps = 50

        session._fix_missing_laps_retired_on_track()
        # Should add a lap with assumed end time = abort time
        assert len(session._laps) == 2
        new_lap = session._laps.iloc[-1]
        assert new_lap['Time'] == pd.Timedelta(seconds=5100)

    def test_with_car_data_speed_zero(self):
        """Test when car_data is available and speed becomes zero"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)
        session._add_track_status_to_laps = Mock()

        session._laps = pd.DataFrame({
            'DriverNumber': ['44'],
            'Driver': ['HAM'],
            'Team': ['Mercedes'],
            'LapNumber': [45],
            'Time': [pd.Timedelta(seconds=5000)],
            'LapStartTime': [pd.Timedelta(seconds=4910)],
            'Stint': [1],
            'Compound': ['SOFT'],
            'TyreLife': [45],
            'FreshTyre': [False],
            'PitInTime': [pd.NaT],
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [False],
            'Position': [1.0]
        })

        # Car data with speed becoming zero
        session._car_data = {
            '44': pd.DataFrame({
                'SessionTime': [
                    pd.Timedelta(seconds=5050),
                    pd.Timedelta(seconds=5060),
                    pd.Timedelta(seconds=5070)
                ],
                'Speed': [50.0, 20.0, 0.0]
            })
        }

        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=5200)],
            'Status': ['Finished']
        })
        session._total_laps = 50

        session._fix_missing_laps_retired_on_track()
        # Should add a lap
        assert len(session._laps) == 2
        new_lap = session._laps.iloc[-1]
        # Time should be when speed became zero
        assert new_lap['Time'] == pd.Timedelta(seconds=5070)

    def test_with_car_data_no_zero_speed(self):
        """Test when car_data is available but speed never becomes zero"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)
        session._add_track_status_to_laps = Mock()

        session._laps = pd.DataFrame({
            'DriverNumber': ['44'],
            'Driver': ['HAM'],
            'Team': ['Mercedes'],
            'LapNumber': [45],
            'Time': [pd.Timedelta(seconds=5000)],
            'LapStartTime': [pd.Timedelta(seconds=4910)],
            'Stint': [1],
            'Compound': ['SOFT'],
            'TyreLife': [45],
            'FreshTyre': [False],
            'PitInTime': [pd.NaT],
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [False],
            'Position': [1.0]
        })

        # Car data with speed never becoming zero
        session._car_data = {
            '44': pd.DataFrame({
                'SessionTime': [
                    pd.Timedelta(seconds=5050),
                    pd.Timedelta(seconds=5060),
                    pd.Timedelta(seconds=5070)
                ],
                'Speed': [50.0, 40.0, 30.0]
            })
        }

        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=5200)],
            'Status': ['Finished']
        })
        session._total_laps = 50

        session._fix_missing_laps_retired_on_track()
        # Should add a lap with fallback time (150 seconds)
        assert len(session._laps) == 2
        new_lap = session._laps.iloc[-1]
        assert new_lap['Time'] == pd.Timedelta(seconds=5000 + 150)

    def test_fallback_assumed_lap_time(self):
        """Test fallback to 150 second assumed lap time"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)
        session._add_track_status_to_laps = Mock()

        session._laps = pd.DataFrame({
            'DriverNumber': ['44'],
            'Driver': ['HAM'],
            'Team': ['Mercedes'],
            'LapNumber': [45],
            'Time': [pd.Timedelta(seconds=5000)],
            'LapStartTime': [pd.Timedelta(seconds=4910)],
            'Stint': [1],
            'Compound': ['SOFT'],
            'TyreLife': [45],
            'FreshTyre': [False],
            'PitInTime': [pd.NaT],
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [False],
            'Position': [1.0]
        })

        # No car data
        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=5200)],
            'Status': ['Finished']
        })
        session._total_laps = 50

        session._fix_missing_laps_retired_on_track()
        # Should add a lap with fallback time
        assert len(session._laps) == 2
        new_lap = session._laps.iloc[-1]
        assert new_lap['Time'] == pd.Timedelta(seconds=5000 + 150)

    def test_new_lap_dataframe_fields(self):
        """Test that the new lap DataFrame has all required fields"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)
        session._add_track_status_to_laps = Mock()

        session._laps = pd.DataFrame({
            'DriverNumber': ['44'],
            'Driver': ['HAM'],
            'Team': ['Mercedes'],
            'LapNumber': [45],
            'Time': [pd.Timedelta(seconds=5000)],
            'LapStartTime': [pd.Timedelta(seconds=4910)],
            'Stint': [2],
            'Compound': ['MEDIUM'],
            'TyreLife': [15],
            'FreshTyre': [False],
            'PitInTime': [pd.NaT],
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [False],
            'Position': [3.0]
        })

        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=5200)],
            'Status': ['Finished']
        })
        session._total_laps = 50

        session._fix_missing_laps_retired_on_track()
        assert len(session._laps) == 2

        new_lap = session._laps.iloc[-1]
        # Verify all fields
        assert new_lap['LapStartTime'] == pd.Timedelta(seconds=5000)
        assert new_lap['Driver'] == 'HAM'
        assert new_lap['DriverNumber'] == '44'
        assert new_lap['Team'] == 'Mercedes'
        assert new_lap['LapNumber'] == 46
        assert new_lap['Stint'] == 2
        assert new_lap['Compound'] == 'MEDIUM'
        assert new_lap['TyreLife'] == 16
        assert new_lap['FreshTyre'] == False
        assert pd.isna(new_lap['Position'])
        assert new_lap['FastF1Generated'] == True
        assert new_lap['IsAccurate'] == False

    def test_multiple_drivers_sorting(self):
        """Test that laps are correctly sorted when multiple drivers have new laps added"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)
        session._add_track_status_to_laps = Mock()

        # Create laps for two drivers
        session._laps = pd.DataFrame({
            'DriverNumber': ['44', '77'],
            'Driver': ['HAM', 'BOT'],
            'Team': ['Mercedes', 'Mercedes'],
            'LapNumber': [45, 44],
            'Time': [pd.Timedelta(seconds=5000), pd.Timedelta(seconds=4950)],
            'LapStartTime': [pd.Timedelta(seconds=4910), pd.Timedelta(seconds=4860)],
            'Stint': [1, 1],
            'Compound': ['SOFT', 'SOFT'],
            'TyreLife': [45, 44],
            'FreshTyre': [False, False],
            'PitInTime': [pd.NaT, pd.NaT],
            'PitOutTime': [pd.NaT, pd.NaT],
            'FastF1Generated': [False, False],
            'Position': [1.0, 2.0]
        })

        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=5200)],
            'Status': ['Finished']
        })
        session._total_laps = 50

        session._fix_missing_laps_retired_on_track()
        # Should add laps for both drivers
        assert len(session._laps) == 4

        # Verify sorting by DriverNumber and LapNumber
        assert session._laps.iloc[0]['DriverNumber'] == '44'
        assert session._laps.iloc[0]['LapNumber'] == 45
        assert session._laps.iloc[1]['DriverNumber'] == '44'
        assert session._laps.iloc[1]['LapNumber'] == 46
        assert session._laps.iloc[2]['DriverNumber'] == '77'
        assert session._laps.iloc[2]['LapNumber'] == 44
        assert session._laps.iloc[3]['DriverNumber'] == '77'
        assert session._laps.iloc[3]['LapNumber'] == 45

    def test_car_data_with_missing_driver(self):
        """Test when car_data exists but doesn't have data for this driver"""
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)
        session._add_track_status_to_laps = Mock()

        session._laps = pd.DataFrame({
            'DriverNumber': ['44'],
            'Driver': ['HAM'],
            'Team': ['Mercedes'],
            'LapNumber': [45],
            'Time': [pd.Timedelta(seconds=5000)],
            'LapStartTime': [pd.Timedelta(seconds=4910)],
            'Stint': [1],
            'Compound': ['SOFT'],
            'TyreLife': [45],
            'FreshTyre': [False],
            'PitInTime': [pd.NaT],
            'PitOutTime': [pd.NaT],
            'FastF1Generated': [False],
            'Position': [1.0]
        })

        # Car data for a different driver
        session._car_data = {
            '77': pd.DataFrame({
                'SessionTime': [pd.Timedelta(seconds=5050)],
                'Speed': [0.0]
            })
        }

        session._session_status = pd.DataFrame({
            'Time': [pd.Timedelta(seconds=5200)],
            'Status': ['Finished']
        })
        session._total_laps = 50

        session._fix_missing_laps_retired_on_track()
        # Should add a lap with fallback time
        assert len(session._laps) == 2
        new_lap = session._laps.iloc[-1]
        assert new_lap['Time'] == pd.Timedelta(seconds=5000 + 150)
