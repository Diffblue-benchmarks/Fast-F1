"""Tests for Session.__fix_tyre_info method"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock

from fastf1.core import Session


class TestSessionFixTyreInfo:
    """Tests for Session.__fix_tyre_info method"""

    def test_fix_tyre_info_with_stint_errors(self, caplog):
        """Test __fix_tyre_info when stint counter is incorrectly incremented"""
        # Create a minimal session object
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)

        # Create test data with incorrect stint numbering
        # Stint 0 should be first, but we'll have some entries incorrectly marked as stint 2
        df = pd.DataFrame({
            'Time': [
                pd.Timedelta(seconds=10),
                pd.Timedelta(seconds=20),
                pd.Timedelta(seconds=30),  # This one incorrectly has Stint=2
                pd.Timedelta(seconds=40),  # This one incorrectly has Stint=2
                pd.Timedelta(seconds=100),
            ],
            'Stint': [0, 0, 2, 2, 1],  # Stint 2 appears before Stint 1 (error)
            'Driver': ['HAM', 'HAM', 'HAM', 'HAM', 'HAM'],
            'Compound': ['SOFT', 'SOFT', 'SOFT', 'SOFT', 'MEDIUM'],
            'New': [True, True, True, True, True],
        })

        pit_in_times = [
            pd.Timedelta(seconds=50),
        ]

        # Call the method (accessing name-mangled private method)
        result = session._Session__fix_tyre_info(df, pit_in_times)

        # Verify that the warning was logged
        assert any("Fixed incorrect tyre stint information" in record.message
                   for record in caplog.records)
        assert any("HAM" in record.message for record in caplog.records)

        # Verify that the result has corrected stint numbers
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_fix_tyre_info_with_stint_errors_unknown_driver(self, caplog):
        """Test __fix_tyre_info when stint errors exist but driver cannot be determined"""
        # Create a minimal session object
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)

        # Create test data with incorrect stint numbering but no driver information
        df = pd.DataFrame({
            'Time': [
                pd.Timedelta(seconds=10),
                pd.Timedelta(seconds=20),
                pd.Timedelta(seconds=30),
            ],
            'Stint': [0, 2, 2],  # Stint 2 appears incorrectly
            'Driver': [np.nan, np.nan, np.nan],  # All drivers are NaN
            'Compound': ['SOFT', 'SOFT', 'SOFT'],
            'New': [True, True, True],
        })

        pit_in_times = []

        # Call the method
        result = session._Session__fix_tyre_info(df, pit_in_times)

        # Verify that the warning was logged with 'unknown' driver
        assert any("Fixed incorrect tyre stint information" in record.message
                   for record in caplog.records)
        assert any("unknown" in record.message for record in caplog.records)

        # Verify that the result is valid
        assert isinstance(result, pd.DataFrame)

    def test_fix_tyre_info_without_errors(self):
        """Test __fix_tyre_info when there are no stint errors"""
        # Create a minimal session object
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)

        # Create test data with correct stint numbering
        df = pd.DataFrame({
            'Time': [
                pd.Timedelta(seconds=10),
                pd.Timedelta(seconds=20),
                pd.Timedelta(seconds=30),
                pd.Timedelta(seconds=100),
            ],
            'Stint': [0, 0, 0, 1],  # Correct progression
            'Driver': ['VER', 'VER', 'VER', 'VER'],
            'Compound': ['SOFT', 'SOFT', 'SOFT', 'MEDIUM'],
            'New': [True, True, True, True],
        })

        pit_in_times = [
            pd.Timedelta(seconds=50),
        ]

        # Call the method
        result = session._Session__fix_tyre_info(df, pit_in_times)

        # Verify that the result is valid
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(df['Stint'].unique())

    def test_fix_tyre_info_with_corrections(self):
        """Test __fix_tyre_info with delayed tyre data corrections"""
        # Create a minimal session object
        event_mock = Mock()
        event_mock.get_session_date.return_value = pd.Timestamp('2024-01-01', tz='UTC')
        event_mock.__getitem__ = Mock(side_effect=lambda x: {
            'EventName': 'Test GP',
            'EventDate': pd.Timestamp('2024-01-01')
        }[x])

        session = Session(event_mock, 'Race', f1_api_support=True)

        # Create test data with multiple messages for the same stint (corrections)
        df = pd.DataFrame({
            'Time': [
                pd.Timedelta(seconds=10),
                pd.Timedelta(seconds=15),  # Correction for stint 0
                pd.Timedelta(seconds=100),
            ],
            'Stint': [0, 0, 1],
            'Driver': ['LEC', 'LEC', 'LEC'],
            'Compound': ['SOFT', np.nan, 'MEDIUM'],  # Second message has NaN (correction)
            'New': [True, True, True],
        })

        pit_in_times = [
            pd.Timedelta(seconds=50),
        ]

        # Call the method
        result = session._Session__fix_tyre_info(df, pit_in_times)

        # Verify that corrections were applied
        assert isinstance(result, pd.DataFrame)
        # Should have 2 stints (0 and 1)
        assert len(result) == 2
        # First stint should keep the compound from the first message
        assert result.iloc[0]['Compound'] == 'SOFT'
