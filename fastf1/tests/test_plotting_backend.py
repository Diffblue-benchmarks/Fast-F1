import warnings
from unittest.mock import Mock, patch

import pytest

from fastf1.plotting._backend import (
    _generate_team,
    _load_drivers_from_f1_livetiming
)
from fastf1.plotting._base import Team, TeamColorConstants


class TestLoadDriversFromF1Livetiming:
    """Tests for _load_drivers_from_f1_livetiming function"""

    def test_unsupported_year_warning(self, caplog):
        """Test warning when year is not in Constants (line 46)"""
        api_path = "2099/test/path"
        year = "2099"

        mock_driver_info = {
            "1": {
                "TeamName": "Test Team",
                "TeamColour": "FF0000",
                "Tla": "TST",
                "FirstName": "Test",
                "LastName": "Driver"
            }
        }

        with patch('fastf1.plotting._backend.fastf1._api.driver_info', return_value=mock_driver_info):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                with caplog.at_level('WARNING'):
                    result = _load_drivers_from_f1_livetiming(api_path=api_path, year=year)

                    # Check for the UserWarning about unsupported year
                    assert len(w) >= 1
                    assert "No built-in team name/color constants for 2099" in str(w[0].message)
                    # Check for logger warning about auto-generated team
                    assert "Auto-generating unknown team:" in caplog.text
                    assert len(result) == 1

    def test_skip_driver_with_empty_abbreviation(self, caplog):
        """Test skipping driver with empty abbreviation (lines 68, 72, 73)"""
        api_path = "2024/test/path"
        year = "2024"

        mock_driver_info = {
            "1": {
                "TeamName": "Mercedes",
                "TeamColour": "00D2BE",
                "Tla": "",  # Empty abbreviation
                "FirstName": "Lewis",
                "LastName": "Hamilton"
            },
            "44": {
                "TeamName": "Mercedes",
                "TeamColour": "00D2BE",
                "Tla": "HAM",
                "FirstName": "Lewis",
                "LastName": "Hamilton"
            }
        }

        with patch('fastf1.plotting._backend.fastf1._api.driver_info', return_value=mock_driver_info):
            with caplog.at_level('DEBUG'):  # Capture DEBUG level for line 72
                result = _load_drivers_from_f1_livetiming(api_path=api_path, year=year)

                # Should skip driver with empty abbreviation
                assert "Skipping driver with incomplete data" in caplog.text
                assert "Skipping driver entry:" in caplog.text
                # Should only have one driver (the valid one)
                assert len(result[0].drivers) == 1
                assert result[0].drivers[0].abbreviation == "HAM"

    def test_skip_driver_with_whitespace_only_name(self, caplog):
        """Test skipping driver with whitespace-only name (lines 68, 72, 73)"""
        api_path = "2024/test/path"
        year = "2024"

        mock_driver_info = {
            "1": {
                "TeamName": "Ferrari",
                "TeamColour": "DC0000",
                "Tla": "LEC",
                "FirstName": "  ",
                "LastName": "  "
            }
        }

        with patch('fastf1.plotting._backend.fastf1._api.driver_info', return_value=mock_driver_info):
            with caplog.at_level('WARNING'):
                result = _load_drivers_from_f1_livetiming(api_path=api_path, year=year)

                assert "Skipping driver with incomplete data" in caplog.text
                # Should have no drivers since the only one was skipped
                assert len(result) == 0

    def test_auto_generate_unknown_team(self, caplog):
        """Test auto-generating team when no match found (lines 82, 84, 86)"""
        api_path = "2024/test/path"
        year = "2024"

        # Create a driver for a team that doesn't match any pre-configured teams
        mock_driver_info = {
            "99": {
                "TeamName": "Brand New Racing Team F1",
                "TeamColour": "ABCDEF",
                "Tla": "NEW",
                "FirstName": "New",
                "LastName": "Driver"
            }
        }

        with patch('fastf1.plotting._backend.fastf1._api.driver_info', return_value=mock_driver_info):
            with caplog.at_level('WARNING'):
                result = _load_drivers_from_f1_livetiming(api_path=api_path, year=year)

                # Should log warning about auto-generating team
                assert "Auto-generating unknown team:" in caplog.text
                assert len(result) == 1
                assert result[0].name == "Brand New Racing Team F1"
                assert result[0].drivers[0].abbreviation == "NEW"


class TestGenerateTeam:
    """Tests for _generate_team function"""

    def test_generate_team_basic(self):
        """Test basic team generation (lines 104-133)"""
        team_name = "Scuderia Ferrari F1 Team"
        team_color = "#dc0000"

        result = _generate_team(team_name, team_color)

        assert result.name == team_name
        assert result.short_name == "Ferrari"
        assert result.normalized_name == "ferrari"
        assert result.colors.official == team_color
        assert result.colors.fastf1 == team_color

    def test_generate_team_with_racing_prefix(self):
        """Test team generation preserving Racing at start (line 109, 111)"""
        team_name = "Racing Bulls F1 Team"
        team_color = "#6692ff"

        result = _generate_team(team_name, team_color)

        # "Racing" at the start should be preserved
        assert "Racing Bulls" in result.short_name
        assert result.normalized_name == "racing bulls"

    def test_generate_team_with_racing_not_at_start(self):
        """Test team generation removing Racing when not at start (line 111)"""
        team_name = "Force Racing F1 Team"
        team_color = "#f596c8"

        result = _generate_team(team_name, team_color)

        # "Racing" not at the start should be removed
        assert "Racing" not in result.short_name
        assert "Force" in result.short_name

    def test_generate_team_removes_double_spaces(self):
        """Test team generation removes double spaces (lines 117-118)"""
        team_name = "Test  Team  F1  Racing"
        team_color = "#ffffff"

        result = _generate_team(team_name, team_color)

        # Should not have double spaces
        assert "  " not in result.short_name

    def test_generate_team_strips_whitespace(self):
        """Test team generation strips leading/trailing whitespace (line 114)"""
        team_name = "   Mercedes F1 Team   "
        team_color = "#00d2be"

        result = _generate_team(team_name, team_color)

        # Should not have leading/trailing spaces
        assert not result.short_name.startswith(" ")
        assert not result.short_name.endswith(" ")

    def test_generate_team_complex_name(self):
        """Test team generation with complex name processing"""
        team_name = "Scuderia AlphaTauri Racing F1 Team"
        team_color = "#2b4562"

        result = _generate_team(team_name, team_color)

        assert result.name == team_name
        assert result.colors.official == team_color
        # Verify normalized name is lowercase
        assert result.normalized_name == result.normalized_name.lower()

    def test_generate_team_minimal_name(self):
        """Test team generation with minimal team name"""
        team_name = "Team"
        team_color = "#123456"

        result = _generate_team(team_name, team_color)

        assert result.name == team_name
        assert result.short_name == ""  # "Team" gets removed
        assert result.normalized_name == ""
        assert result.colors.official == team_color
