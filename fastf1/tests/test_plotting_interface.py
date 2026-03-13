"""Tests for plotting/_interface.py with mocked driver-team mappings."""
from unittest.mock import MagicMock, patch

import pytest

from fastf1.plotting._base import (
    Driver,
    DriverTeamMapping,
    Team,
    TeamColorConstants,
)
from fastf1.plotting._interface import (
    _get_driver,
    _get_driver_color,
    _get_driver_exact,
    _get_driver_fuzzy,
    _get_team,
    _get_team_color,
    _get_team_exact,
    _get_team_fuzzy,
    _replace_magic_auto,
    get_compound_color,
    get_compound_mapping,
    get_driver_abbreviation,
    get_driver_abbreviations_by_team,
    get_driver_color,
    get_driver_color_mapping,
    get_driver_name,
    get_driver_names_by_team,
    get_team_color,
    get_team_name,
    get_team_name_by_driver,
    list_compounds,
    list_driver_abbreviations,
    list_driver_names,
    list_team_names,
    set_default_colormap,
)
from fastf1.plotting._backend import Constants


def _make_dtm():
    colors = TeamColorConstants(official='#ff0000', fastf1='#00ff00')
    team = Team(short_name='RB', colors=colors,
                name='Red Bull Racing', normalized_name='red bull')
    d1 = Driver(team=team, abbreviation='VER',
                name='Max Verstappen', normalized_name='max verstappen')
    team.add_driver(d1)
    d2 = Driver(team=team, abbreviation='PER',
                name='Sergio Perez', normalized_name='sergio perez')
    team.add_driver(d2)

    colors2 = TeamColorConstants(official='#00d2be', fastf1='#27f4d2')
    team2 = Team(short_name='Mercedes', colors=colors2,
                 name='Mercedes-AMG PETRONAS', normalized_name='mercedes')
    d3 = Driver(team=team2, abbreviation='HAM',
                name='Lewis Hamilton', normalized_name='lewis hamilton')
    team2.add_driver(d3)

    year = next(iter(Constants.keys()))
    return DriverTeamMapping(year=year, teams=[team, team2])


def _mock_session():
    session = MagicMock()
    session.api_path = '/static/test_plotting/'
    event_date = MagicMock(year=2024)
    event_mock = MagicMock()
    event_mock.__getitem__ = lambda self, k: {'EventDate': event_date}[k]
    session.event = event_mock
    return session


@pytest.fixture(autouse=True)
def _patch_dtm():
    """Patch _get_driver_team_mapping to return our mock DTM."""
    dtm = _make_dtm()
    with patch('fastf1.plotting._interface._get_driver_team_mapping',
               return_value=dtm):
        yield dtm


class TestGetDriverFuzzy:
    def test_by_abbreviation(self, _patch_dtm):
        session = _mock_session()
        driver = _get_driver_fuzzy('VER', session)
        assert driver.abbreviation == 'VER'

    def test_by_normalized_name(self, _patch_dtm):
        session = _mock_session()
        driver = _get_driver_fuzzy('max verstappen', session)
        assert driver.abbreviation == 'VER'

    def test_by_partial_name(self, _patch_dtm):
        session = _mock_session()
        driver = _get_driver_fuzzy('verstappen', session)
        assert driver.abbreviation == 'VER'

    def test_fuzzy_match(self, _patch_dtm):
        session = _mock_session()
        driver = _get_driver_fuzzy('hamilton', session)
        assert driver.abbreviation == 'HAM'


class TestGetDriverExact:
    def test_by_abbreviation(self, _patch_dtm):
        session = _mock_session()
        driver = _get_driver_exact('VER', session)
        assert driver.abbreviation == 'VER'

    def test_by_name(self, _patch_dtm):
        session = _mock_session()
        driver = _get_driver_exact('max verstappen', session)
        assert driver.abbreviation == 'VER'

    def test_not_found_raises(self, _patch_dtm):
        session = _mock_session()
        with pytest.raises(KeyError, match="exact match"):
            _get_driver_exact('nonexistent', session)


class TestGetTeamFuzzy:
    def test_by_normalized_name(self, _patch_dtm):
        session = _mock_session()
        team = _get_team_fuzzy('red bull', session)
        assert team.name == 'Red Bull Racing'

    def test_by_full_name(self, _patch_dtm):
        session = _mock_session()
        team = _get_team_fuzzy('Red Bull Racing', session)
        assert team.normalized_name == 'red bull'

    def test_by_short_name(self, _patch_dtm):
        session = _mock_session()
        team = _get_team_fuzzy('RB', session)
        assert team.normalized_name == 'red bull'

    def test_by_partial(self, _patch_dtm):
        session = _mock_session()
        team = _get_team_fuzzy('mercedes', session)
        assert team.name == 'Mercedes-AMG PETRONAS'


class TestGetTeamExact:
    def test_by_normalized(self, _patch_dtm):
        session = _mock_session()
        team = _get_team_exact('red bull', session)
        assert team.name == 'Red Bull Racing'

    def test_by_full_name(self, _patch_dtm):
        session = _mock_session()
        team = _get_team_exact('red bull racing', session)
        assert team.name == 'Red Bull Racing'

    def test_not_found_raises(self, _patch_dtm):
        session = _mock_session()
        with pytest.raises(KeyError, match="exact match"):
            _get_team_exact('nonexistent', session)


class TestColors:
    def test_get_team_color_fastf1(self, _patch_dtm):
        session = _mock_session()
        color = _get_team_color('red bull', session, colormap='fastf1',
                                exact_match=True)
        assert color == '#00ff00'

    def test_get_team_color_official(self, _patch_dtm):
        session = _mock_session()
        color = _get_team_color('red bull', session, colormap='official',
                                exact_match=True)
        assert color == '#ff0000'

    def test_get_team_color_default(self, _patch_dtm):
        session = _mock_session()
        color = _get_team_color('red bull', session, exact_match=True)
        assert isinstance(color, str)

    def test_get_team_color_invalid_colormap(self, _patch_dtm):
        session = _mock_session()
        with pytest.raises(ValueError, match="Invalid colormap"):
            _get_team_color('red bull', session, colormap='nope',
                            exact_match=True)

    def test_get_driver_color(self, _patch_dtm):
        session = _mock_session()
        color = _get_driver_color('VER', session, exact_match=True)
        assert isinstance(color, str)


class TestPublicAPI:
    def test_get_team_name(self, _patch_dtm):
        session = _mock_session()
        assert get_team_name('red bull', session,
                             exact_match=True) == 'Red Bull Racing'

    def test_get_team_name_short(self, _patch_dtm):
        session = _mock_session()
        assert get_team_name('red bull', session,
                             short=True, exact_match=True) == 'RB'

    def test_get_team_name_by_driver(self, _patch_dtm):
        session = _mock_session()
        assert get_team_name_by_driver('VER', session,
                                       exact_match=True) == 'Red Bull Racing'

    def test_get_driver_name(self, _patch_dtm):
        session = _mock_session()
        assert get_driver_name('VER', session,
                               exact_match=True) == 'Max Verstappen'

    def test_get_driver_abbreviation(self, _patch_dtm):
        session = _mock_session()
        assert get_driver_abbreviation('max verstappen', session,
                                       exact_match=True) == 'VER'

    def test_get_driver_names_by_team(self, _patch_dtm):
        session = _mock_session()
        names = get_driver_names_by_team('red bull', session, exact_match=True)
        assert 'Max Verstappen' in names
        assert 'Sergio Perez' in names

    def test_get_driver_abbreviations_by_team(self, _patch_dtm):
        session = _mock_session()
        abbs = get_driver_abbreviations_by_team('red bull', session,
                                                exact_match=True)
        assert 'VER' in abbs and 'PER' in abbs

    def test_get_driver_color_mapping(self, _patch_dtm):
        session = _mock_session()
        mapping = get_driver_color_mapping(session, colormap='fastf1')
        assert 'VER' in mapping
        assert 'HAM' in mapping

    def test_get_driver_color_mapping_official(self, _patch_dtm):
        session = _mock_session()
        mapping = get_driver_color_mapping(session, colormap='official')
        assert 'VER' in mapping

    def test_get_driver_color_mapping_invalid(self, _patch_dtm):
        session = _mock_session()
        with pytest.raises(ValueError, match="Invalid colormap"):
            get_driver_color_mapping(session, colormap='nope')

    def test_list_team_names(self, _patch_dtm):
        session = _mock_session()
        names = list_team_names(session)
        assert 'Red Bull Racing' in names

    def test_list_team_names_short(self, _patch_dtm):
        session = _mock_session()
        names = list_team_names(session, short=True)
        assert 'RB' in names

    def test_list_driver_abbreviations(self, _patch_dtm):
        session = _mock_session()
        abbs = list_driver_abbreviations(session)
        assert 'VER' in abbs

    def test_list_driver_names(self, _patch_dtm):
        session = _mock_session()
        names = list_driver_names(session)
        assert 'Max Verstappen' in names

    def test_set_default_colormap_valid(self):
        from fastf1.plotting import _interface
        orig = _interface._DEFAULT_COLOR_MAP
        try:
            set_default_colormap('official')
            assert _interface._DEFAULT_COLOR_MAP == 'official'
        finally:
            _interface._DEFAULT_COLOR_MAP = orig

    def test_set_default_colormap_invalid(self):
        with pytest.raises(ValueError, match="Invalid colormap"):
            set_default_colormap('nope')


class TestReplaceMagicAuto:
    def test_replaces_auto(self, _patch_dtm):
        session = _mock_session()
        style = {'color': 'auto', 'linestyle': 'solid'}
        result = _replace_magic_auto('red bull', style, session,
                                     'fastf1', ['color'])
        assert result['color'] == '#00ff00'
        assert result['linestyle'] == 'solid'

    def test_nested_auto(self, _patch_dtm):
        session = _mock_session()
        style = {'outer': {'color': 'auto'}, 'linestyle': 'solid'}
        result = _replace_magic_auto('red bull', style, session,
                                     'fastf1', ['color'])
        assert result['outer']['color'] == '#00ff00'

    def test_no_auto_unchanged(self, _patch_dtm):
        session = _mock_session()
        style = {'color': '#123456'}
        result = _replace_magic_auto('red bull', style, session,
                                     'fastf1', ['color'])
        assert result['color'] == '#123456'
