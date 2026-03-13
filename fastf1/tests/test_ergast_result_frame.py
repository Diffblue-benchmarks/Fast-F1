"""Tests for ergast/interface.py ErgastResultFrame and related."""
import copy
from unittest.mock import MagicMock

import pytest

from fastf1.ergast.interface import (
    ErgastResultFrame,
    ErgastResultSeries,
)
from fastf1.ergast.structure import (
    Driver as DriverCategory,
    _flatten_by_rename,
)


class TestErgastResultFrame:
    def test_create_from_data(self):
        data = [{'driverId': 'hamilton', 'code': 'HAM'}]
        df = ErgastResultFrame(data)
        assert len(df) == 1

    def test_create_from_response(self):
        response = [
            {'driverId': 'hamilton', 'code': 'HAM',
             'permanentNumber': '44', 'url': '', 'givenName': 'Lewis',
             'familyName': 'Hamilton', 'dateOfBirth': '1985-01-07',
             'nationality': 'British'},
        ]
        df = ErgastResultFrame(
            response=response, category=DriverCategory
        )
        assert len(df) == 1
        assert 'driverId' in df.columns

    def test_cannot_provide_both_data_and_response(self):
        with pytest.raises(ValueError, match="Cannot initialize"):
            ErgastResultFrame(
                data=[{}],
                response=[{}],
                category=DriverCategory,
            )

    def test_horizontal_slice_returns_series(self):
        data = [
            {'driverId': 'hamilton', 'code': 'HAM',
             'permanentNumber': '44', 'url': '', 'givenName': 'Lewis',
             'familyName': 'Hamilton', 'dateOfBirth': '1985-01-07',
             'nationality': 'British'},
        ]
        df = ErgastResultFrame(response=data, category=DriverCategory)
        row = df.iloc[0]
        assert isinstance(row, ErgastResultSeries)

    def test_auto_cast(self):
        response = [
            {'driverId': 'hamilton', 'permanentNumber': '44',
             'code': 'HAM', 'url': '', 'givenName': 'Lewis',
             'familyName': 'Hamilton', 'dateOfBirth': '1985-01-07',
             'nationality': 'British'},
        ]
        df = ErgastResultFrame(
            response=response, category=DriverCategory, auto_cast=True
        )
        # permanentNumber should be cast to int via save_int
        assert df.iloc[0]['driverNumber'] == 44

    def test_no_cast(self):
        response = [
            {'driverId': 'hamilton', 'permanentNumber': '44',
             'code': 'HAM', 'url': '', 'givenName': 'Lewis',
             'familyName': 'Hamilton', 'dateOfBirth': '1985-01-07',
             'nationality': 'British'},
        ]
        df = ErgastResultFrame(
            response=response, category=DriverCategory, auto_cast=False
        )
        assert df.iloc[0]['driverNumber'] == '44'
