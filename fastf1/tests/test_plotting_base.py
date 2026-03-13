import pytest

from fastf1.plotting._base import (
    CompoundTypes,
    Driver,
    DriverTeamMapping,
    Team,
    TeamColorConstants,
    TeamConstants,
    _normalize_string,
    color_dict_validator,
    hex_color_validator,
    team_key_validator,
)


class TestHexColorValidator:
    def test_valid_6_digit(self):
        assert hex_color_validator('#ff5500') == '#ff5500'

    def test_valid_8_digit_with_alpha(self):
        assert hex_color_validator('#ff550080') == '#ff550080'

    def test_invalid_uppercase(self):
        with pytest.raises(ValueError):
            hex_color_validator('#FF5500')

    def test_invalid_no_hash(self):
        with pytest.raises(ValueError):
            hex_color_validator('ff5500')

    def test_invalid_length(self):
        with pytest.raises(ValueError):
            hex_color_validator('#fff')

    def test_invalid_chars(self):
        with pytest.raises(ValueError):
            hex_color_validator('#gggggg')


class TestColorDictValidator:
    def test_valid_dict(self):
        d = {'a': '#ff0000', 'b': '#00ff00'}
        assert color_dict_validator(d) == d

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            color_dict_validator({'a': 'not_a_color'})


class TestTeamKeyValidator:
    def test_valid_keys(self):
        colors = TeamColorConstants(official='#ff0000', fastf1='#00ff00')
        d = {'red bull': TeamConstants(short_name='RB', colors=colors)}
        assert team_key_validator(d) == d

    def test_uppercase_key_rejected(self):
        colors = TeamColorConstants(official='#ff0000', fastf1='#00ff00')
        d = {'Red Bull': TeamConstants(short_name='RB', colors=colors)}
        with pytest.raises(ValueError, match="must be lower case"):
            team_key_validator(d)

    def test_numeric_key_rejected(self):
        colors = TeamColorConstants(official='#ff0000', fastf1='#00ff00')
        d = {'team123': TeamConstants(short_name='T', colors=colors)}
        with pytest.raises(ValueError, match="only letters and spaces"):
            team_key_validator(d)


class TestNormalizeString:
    def test_plain_ascii(self):
        assert _normalize_string('Hamilton') == 'Hamilton'

    def test_accented_chars(self):
        result = _normalize_string('Pérez')
        assert result == 'Perez'

    def test_multiple_accents(self):
        result = _normalize_string('Räikkönen')
        assert 'a' in result.lower()
        assert 'o' in result.lower()

    def test_empty_string(self):
        assert _normalize_string('') == ''


class TestCompoundTypes:
    def test_soft(self):
        assert CompoundTypes.Soft.value == "SOFT"

    def test_medium(self):
        assert CompoundTypes.Medium.value == "MEDIUM"

    def test_hard(self):
        assert CompoundTypes.Hard.value == "HARD"

    def test_wet(self):
        assert CompoundTypes.Wet.value == "WET"

    def test_unknown(self):
        assert CompoundTypes.Unknown.value == "UNKNOWN"


class TestTeamAndDriver:
    def _make_team(self):
        colors = TeamColorConstants(official='#ff0000', fastf1='#00ff00')
        return Team(
            short_name='RB',
            colors=colors,
            name='Red Bull Racing',
            normalized_name='red bull',
        )

    def test_team_add_driver(self):
        team = self._make_team()
        driver = Driver(
            team=team, abbreviation='VER',
            name='Max Verstappen', normalized_name='max verstappen'
        )
        team.add_driver(driver)
        assert len(team.drivers) == 1
        assert team.drivers[0].abbreviation == 'VER'

    def test_team_add_duplicate_driver_raises(self):
        team = self._make_team()
        d1 = Driver(team=team, abbreviation='VER',
                     name='Max Verstappen', normalized_name='max verstappen')
        team.add_driver(d1)
        with pytest.raises(ValueError, match="already exists"):
            team.add_driver(d1)

    def test_driver_duplicate_abbreviation_raises(self):
        team = self._make_team()
        d1 = Driver(team=team, abbreviation='VER',
                     name='Max Verstappen', normalized_name='max verstappen')
        team.add_driver(d1)
        with pytest.raises(ValueError, match="Duplicate"):
            Driver(team=team, abbreviation='VER',
                   name='Other Driver', normalized_name='other driver')


class TestDriverTeamMapping:
    def test_mapping_indexes(self):
        colors = TeamColorConstants(official='#ff0000', fastf1='#00ff00')
        team = Team(
            short_name='RB', colors=colors,
            name='Red Bull Racing', normalized_name='red bull',
        )
        d1 = Driver(team=team, abbreviation='VER',
                     name='Max Verstappen', normalized_name='max verstappen')
        team.add_driver(d1)
        d2 = Driver(team=team, abbreviation='PER',
                     name='Sergio Perez', normalized_name='sergio perez')
        team.add_driver(d2)

        dtm = DriverTeamMapping(year='2024', teams=[team])
        assert dtm.drivers_by_abbreviation['VER'] is d1
        assert dtm.drivers_by_abbreviation['PER'] is d2
        assert dtm.drivers_by_normalized['max verstappen'] is d1
        assert dtm.teams_by_normalized['red bull'] is team
