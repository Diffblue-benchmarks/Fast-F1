"""Tests for plotting/_backend.py with mocked API calls."""
from unittest.mock import patch

import pytest

from fastf1.plotting._backend import (
    Constants,
    _generate_team,
    _load_drivers_from_f1_livetiming,
)


class TestConstants:
    def test_constants_loaded(self):
        assert isinstance(Constants, dict)
        assert len(Constants) > 0

    def test_constants_have_teams(self):
        # check any available year
        year = next(iter(Constants.keys()))
        assert hasattr(Constants[year], 'teams')
        assert len(Constants[year].teams) > 0

    def test_constants_have_compound_colors(self):
        year = next(iter(Constants.keys()))
        assert hasattr(Constants[year], 'compound_colors')
        assert len(Constants[year].compound_colors) > 0


class TestGenerateTeam:
    def test_basic(self):
        team = _generate_team('Red Bull Racing', '#3671c6')
        assert team.name == 'Red Bull Racing'
        assert team.colors.official == '#3671c6'
        assert team.colors.fastf1 == '#3671c6'

    def test_removes_common_words(self):
        team = _generate_team('Haas F1 Team', '#b6babd')
        assert 'F1' not in team.short_name
        assert 'Team' not in team.short_name

    def test_keeps_racing_prefix(self):
        team = _generate_team('Racing Bulls', '#6692ff')
        assert 'Racing' in team.short_name

    def test_removes_racing_not_at_start(self):
        team = _generate_team('Alpine F1 Racing Team', '#0093cc')
        assert team.short_name.strip()  # should still have something


class TestLoadDriversFromF1Livetiming:
    @patch('fastf1.plotting._backend.fastf1._api.driver_info')
    def test_loads_drivers(self, mock_driver_info):
        mock_driver_info.return_value = {
            '1': {
                'RacingNumber': '1',
                'BroadcastName': 'M VERSTAPPEN',
                'FullName': 'Max VERSTAPPEN',
                'Tla': 'VER',
                'TeamName': 'Red Bull Racing',
                'TeamColour': '3671C6',
                'FirstName': 'Max',
                'LastName': 'Verstappen',
            },
            '11': {
                'RacingNumber': '11',
                'BroadcastName': 'S PEREZ',
                'FullName': 'Sergio PEREZ',
                'Tla': 'PER',
                'TeamName': 'Red Bull Racing',
                'TeamColour': '3671C6',
                'FirstName': 'Sergio',
                'LastName': 'Perez',
            },
        }

        year = next(iter(Constants.keys()))
        teams = _load_drivers_from_f1_livetiming(
            api_path='/static/test/', year=year
        )

        # should have at least the team from the mock data
        team_names = [t.name for t in teams]
        assert 'Red Bull Racing' in team_names

        rb_team = [t for t in teams if t.name == 'Red Bull Racing'][0]
        assert len(rb_team.drivers) == 2
        driver_abbs = [d.abbreviation for d in rb_team.drivers]
        assert 'VER' in driver_abbs
        assert 'PER' in driver_abbs

    @patch('fastf1.plotting._backend.fastf1._api.driver_info')
    def test_skips_incomplete_driver_data(self, mock_driver_info):
        mock_driver_info.return_value = {
            '1': {
                'RacingNumber': '1',
                'Tla': '',  # empty abbreviation
                'TeamName': 'Some Team',
                'TeamColour': 'FFFFFF',
                'FirstName': '',
                'LastName': '',
            },
        }
        year = next(iter(Constants.keys()))
        teams = _load_drivers_from_f1_livetiming(
            api_path='/static/test/', year=year
        )
        # no drivers should be loaded due to empty names
        driver_count = sum(len(t.drivers) for t in teams)
        assert driver_count == 0

    @patch('fastf1.plotting._backend.fastf1._api.driver_info')
    def test_unknown_year_generates_teams(self, mock_driver_info):
        mock_driver_info.return_value = {
            '1': {
                'RacingNumber': '1',
                'Tla': 'VER',
                'TeamName': 'Future Racing Team',
                'TeamColour': 'AABBCC',
                'FirstName': 'Max',
                'LastName': 'Verstappen',
            },
        }

        with pytest.warns(match="No built-in"):
            teams = _load_drivers_from_f1_livetiming(
                api_path='/static/test/', year='2099'
            )

        assert len(teams) >= 1
        assert any(t.name == 'Future Racing Team' for t in teams)
