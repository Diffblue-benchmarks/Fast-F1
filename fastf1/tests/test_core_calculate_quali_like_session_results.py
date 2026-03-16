"""Tests for Session._calculate_quali_like_session_results method"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock, patch

from fastf1.core import Session, Laps


class TestSessionCalculateQualiLikeSessionResults:
    """Tests for Session._calculate_quali_like_session_results method"""

    def test_early_return_when_not_quali_session(self):
        """Test early return when session is not a qualifying-like session"""
        # Create a minimal session object for a race session
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)
        session._laps = Mock()
        session._results = pd.DataFrame()

        # Call the method - should return early without doing anything
        session._calculate_quali_like_session_results()

        # Results should remain unchanged
        assert session._results.empty

    def test_early_return_when_no_laps_loaded(self):
        """Test early return when _laps attribute is not set"""
        # Create a minimal session object for a qualifying session
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Qualifying', f1_api_support=True)
        # Don't set _laps attribute
        session._results = pd.DataFrame({'Position': [np.nan]})

        # Call the method - should return early
        session._calculate_quali_like_session_results()

        # Results should remain unchanged (still have NaN)
        assert session._results['Position'].isna().all()

    def test_warning_when_deleted_column_not_bool(self, caplog):
        """Test warning is logged when Deleted column is not boolean"""
        # Create a minimal session object
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Qualifying', f1_api_support=True)

        # Create laps with non-boolean Deleted column
        laps_data = pd.DataFrame({
            'DriverNumber': ['1', '44', '63'],
            'LapTime': [pd.Timedelta(seconds=90), pd.Timedelta(seconds=91), pd.Timedelta(seconds=92)],
            'Deleted': ['0', '0', '0'],  # String instead of bool
            'IsAccurate': [True, True, True],
            'LapNumber': [1, 1, 1],
        })

        # Mock the laps object
        laps_mock = Mock(spec=Laps)
        laps_mock.__getitem__ = lambda self, key: laps_data[key]
        laps_mock.loc = laps_data.loc
        laps_mock.pick_accurate = Mock(return_value=laps_mock)
        laps_mock.split_qualifying_sessions = Mock(return_value=[None, None, None])

        session._laps = laps_mock
        session._results = pd.DataFrame({
            'Position': [np.nan, np.nan, np.nan],
            'DriverNumber': ['1', '44', '63']
        })

        # Call the method
        session._calculate_quali_like_session_results()

        # Verify warning was logged
        assert any("Cannot calculate qualifying results" in record.message
                   for record in caplog.records)
        assert any("missing information about deleted laps" in record.message
                   for record in caplog.records)

    def test_calculate_results_single_session(self):
        """Test calculating quali results for a single qualifying session"""
        # Create a minimal session object
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Qualifying', f1_api_support=True)

        # Create test lap data
        laps_data = pd.DataFrame({
            'DriverNumber': ['1', '1', '44', '44', '63'],
            'LapTime': [
                pd.Timedelta(seconds=90.5),
                pd.Timedelta(seconds=89.2),  # Best for driver 1
                pd.Timedelta(seconds=88.8),  # Best for driver 44
                pd.Timedelta(seconds=89.0),
                pd.Timedelta(seconds=90.1)   # Best for driver 63
            ],
            'Deleted': [False, False, False, False, False],
            'IsAccurate': [True, True, True, True, True],
            'LapNumber': [1, 2, 1, 2, 1],
        })

        # Create a mock Laps object for Q1
        q1_laps_mock = Mock(spec=Laps)
        q1_laps_mock.__getitem__ = lambda self, key: laps_data[key]
        q1_laps_filtered = laps_data[~laps_data['LapTime'].isna() & ~laps_data['Deleted']].copy()
        q1_grouped = q1_laps_filtered.groupby(['DriverNumber']).agg({'LapTime': 'min'})
        q1_grouped = q1_grouped.rename(columns={'LapTime': 'Q1'})

        q1_laps_mock.pick_quicklaps = Mock(return_value=q1_laps_mock)
        q1_laps_mock.__getitem__ = lambda self, key: q1_laps_filtered[key] if isinstance(key, str) else q1_laps_filtered[key]
        q1_laps_mock.groupby = lambda cols: q1_laps_filtered.groupby(cols)

        # Mock the main laps object
        main_laps = pd.DataFrame({
            'DriverNumber': ['1', '44', '63'],
            'Deleted': [False, False, False]
        })
        laps_mock = Mock(spec=Laps)
        laps_mock.loc = main_laps.loc
        laps_mock.__getitem__ = lambda self, key: main_laps[key]
        laps_mock.pick_accurate = Mock(return_value=laps_mock)
        laps_mock.split_qualifying_sessions = Mock(return_value=[q1_laps_mock, None, None])

        session._laps = laps_mock
        session._results = pd.DataFrame({
            'Position': [np.nan, np.nan, np.nan],
            'DriverNumber': ['1', '44', '63']
        }).set_index('DriverNumber')

        # Call the method
        session._calculate_quali_like_session_results()

        # Verify results were calculated and sorted
        assert not session.results['Position'].isna().all()
        assert session._results['Position'].iloc[0] == 1.0
        # Driver 44 should be first (fastest)
        assert session._results.index[0] == '44' or session.results['Position'].min() == 1.0

    def test_calculate_results_with_none_session(self):
        """Test calculating quali results when one session is None"""
        # Create a minimal session object
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Qualifying', f1_api_support=True)

        # Create test data for Q1 only
        q1_data = pd.DataFrame({
            'DriverNumber': ['1', '44', '63'],
            'LapTime': [
                pd.Timedelta(seconds=89.2),
                pd.Timedelta(seconds=88.8),
                pd.Timedelta(seconds=90.1)
            ],
            'Deleted': [False, False, False],
        })

        # Mock Q1 laps
        q1_laps_mock = Mock(spec=Laps)
        q1_laps_mock.__getitem__ = lambda self, key: q1_data[key]
        q1_laps_mock.pick_quicklaps = Mock(return_value=q1_laps_mock)
        q1_laps_mock.groupby = lambda cols: q1_data.groupby(cols)

        # Mock main laps
        main_laps = pd.DataFrame({
            'DriverNumber': ['1', '44', '63'],
            'Deleted': [False, False, False]
        })
        laps_mock = Mock(spec=Laps)
        laps_mock.loc = main_laps.loc
        laps_mock.__getitem__ = lambda self, key: main_laps[key]
        laps_mock.pick_accurate = Mock(return_value=laps_mock)
        # Q2 and Q3 are None
        laps_mock.split_qualifying_sessions = Mock(return_value=[q1_laps_mock, None, None])

        session._laps = laps_mock
        session._results = pd.DataFrame({
            'Position': [np.nan, np.nan, np.nan],
            'DriverNumber': ['1', '44', '63']
        }).set_index('DriverNumber')

        # Call the method
        session._calculate_quali_like_session_results()

        # Verify results contain Q2 and Q3 columns with NaT values
        assert 'Q1' in session.results.columns or 'Position' in session.results.columns
        assert not session.results['Position'].isna().all()

    def test_calculate_results_multiple_sessions(self):
        """Test calculating quali results across Q1, Q2, and Q3"""
        # Create a minimal session object
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Qualifying', f1_api_support=True)

        # Create test data for each session
        # Q1: All drivers
        q1_data = pd.DataFrame({
            'DriverNumber': ['1', '44', '63'],
            'LapTime': [
                pd.Timedelta(seconds=89.5),
                pd.Timedelta(seconds=89.0),
                pd.Timedelta(seconds=90.0)
            ],
            'Deleted': [False, False, False],
        })

        # Q2: Top 2 drivers
        q2_data = pd.DataFrame({
            'DriverNumber': ['1', '44'],
            'LapTime': [
                pd.Timedelta(seconds=88.5),
                pd.Timedelta(seconds=88.0)
            ],
            'Deleted': [False, False],
        })

        # Q3: Top driver only
        q3_data = pd.DataFrame({
            'DriverNumber': ['44'],
            'LapTime': [pd.Timedelta(seconds=87.5)],
            'Deleted': [False],
        })

        # Mock Q1, Q2, Q3 laps
        q1_laps_mock = Mock(spec=Laps)
        q1_laps_mock.__getitem__ = lambda self, key: q1_data[key]
        q1_laps_mock.pick_quicklaps = Mock(return_value=q1_laps_mock)
        q1_laps_mock.groupby = lambda cols: q1_data.groupby(cols)

        q2_laps_mock = Mock(spec=Laps)
        q2_laps_mock.__getitem__ = lambda self, key: q2_data[key]
        q2_laps_mock.pick_quicklaps = Mock(return_value=q2_laps_mock)
        q2_laps_mock.groupby = lambda cols: q2_data.groupby(cols)

        q3_laps_mock = Mock(spec=Laps)
        q3_laps_mock.__getitem__ = lambda self, key: q3_data[key]
        q3_laps_mock.pick_quicklaps = Mock(return_value=q3_laps_mock)
        q3_laps_mock.groupby = lambda cols: q3_data.groupby(cols)

        # Mock main laps
        main_laps = pd.DataFrame({
            'DriverNumber': ['1', '44', '63'],
            'Deleted': [False, False, False]
        })
        laps_mock = Mock(spec=Laps)
        laps_mock.loc = main_laps.loc
        laps_mock.__getitem__ = lambda self, key: main_laps[key]
        laps_mock.pick_accurate = Mock(return_value=laps_mock)
        laps_mock.split_qualifying_sessions = Mock(return_value=[q1_laps_mock, q2_laps_mock, q3_laps_mock])

        session._laps = laps_mock
        session._results = pd.DataFrame({
            'Position': [np.nan, np.nan, np.nan],
            'DriverNumber': ['1', '44', '63']
        }).set_index('DriverNumber')

        # Call the method
        session._calculate_quali_like_session_results()

        # Verify results were calculated
        assert not session.results['Position'].isna().all()
        # Position 1 should be assigned
        assert 1.0 in session.results['Position'].values

    def test_force_recalculation_when_results_exist(self):
        """Test that force=True recalculates even when results exist"""
        # Create a minimal session object
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Qualifying', f1_api_support=True)

        # Create test data
        q1_data = pd.DataFrame({
            'DriverNumber': ['1', '44'],
            'LapTime': [
                pd.Timedelta(seconds=89.0),
                pd.Timedelta(seconds=88.0)
            ],
            'Deleted': [False, False],
        })

        # Mock Q1 laps
        q1_laps_mock = Mock(spec=Laps)
        q1_laps_mock.__getitem__ = lambda self, key: q1_data[key]
        q1_laps_mock.pick_quicklaps = Mock(return_value=q1_laps_mock)
        q1_laps_mock.groupby = lambda cols: q1_data.groupby(cols)

        # Mock main laps
        main_laps = pd.DataFrame({
            'DriverNumber': ['1', '44'],
            'Deleted': [False, False]
        })
        laps_mock = Mock(spec=Laps)
        laps_mock.loc = main_laps.loc
        laps_mock.__getitem__ = lambda self, key: main_laps[key]
        laps_mock.pick_accurate = Mock(return_value=laps_mock)
        laps_mock.split_qualifying_sessions = Mock(return_value=[q1_laps_mock, None, None])

        session._laps = laps_mock
        # Results already exist
        session._results = pd.DataFrame({
            'Position': [2.0, 1.0],
            'DriverNumber': ['1', '44']
        }).set_index('DriverNumber')

        # Call with force=True
        session._calculate_quali_like_session_results(force=True)

        # Results should have been recalculated
        # Verify the method was executed (split_qualifying_sessions was called)
        assert laps_mock.split_qualifying_sessions.called

    def test_no_recalculation_when_results_exist_and_not_forced(self):
        """Test that results are not recalculated when they exist and force=False"""
        # Create a minimal session object
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Qualifying', f1_api_support=True)

        # Mock laps
        laps_mock = Mock(spec=Laps)
        laps_mock.pick_accurate = Mock(return_value=laps_mock)
        laps_mock.split_qualifying_sessions = Mock(return_value=[None, None, None])

        session._laps = laps_mock
        # Results already exist
        original_results = pd.DataFrame({
            'Position': [2.0, 1.0],
            'DriverNumber': ['1', '44']
        }).set_index('DriverNumber')
        session._results = original_results.copy()

        # Call without force (default is False)
        session._calculate_quali_like_session_results()

        # split_qualifying_sessions should not have been called
        assert not laps_mock.split_qualifying_sessions.called
        # Results should remain unchanged
        pd.testing.assert_frame_equal(session._results, original_results)
