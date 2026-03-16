import pytest

from fastf1.plotting._base import (
    CompoundTypes,
    Driver,
    Team,
    TeamColorConstants,
    TeamConstants,
    color_dict_validator,
    hex_color_validator,
    team_key_validator,
)


class TestHexColorValidator:
    """Test hex_color_validator function."""

    def test_hex_color_validator_with_invalid_color(self):
        """Test hex_color_validator raises ValueError for invalid hex colors."""
        # Test uppercase hex color (line 37)
        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_color_validator("#ABCDEF")

        # Test invalid format (not hex)
        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_color_validator("not-a-color")

        # Test wrong length
        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_color_validator("#abc")

        # Test missing hash
        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_color_validator("abcdef")

    def test_hex_color_validator_with_valid_color(self):
        """Test hex_color_validator accepts valid hex colors."""
        # Test 6-digit lowercase hex
        result = hex_color_validator("#abcdef")
        assert result == "#abcdef"

        # Test 8-digit lowercase hex (with alpha)
        result = hex_color_validator("#abcdef00")
        assert result == "#abcdef00"


class TestColorDictValidator:
    """Test color_dict_validator function."""

    def test_color_dict_validator_with_invalid_color(self):
        """Test color_dict_validator raises ValueError for invalid hex colors in dict."""
        # Test with uppercase hex color value (line 46)
        invalid_dict = {
            CompoundTypes.Soft: "#FF0000"
        }
        with pytest.raises(ValueError, match="Invalid hex color"):
            color_dict_validator(invalid_dict)

        # Test with invalid format
        invalid_dict = {
            CompoundTypes.Medium: "not-a-color"
        }
        with pytest.raises(ValueError, match="Invalid hex color"):
            color_dict_validator(invalid_dict)

    def test_color_dict_validator_with_valid_colors(self):
        """Test color_dict_validator accepts valid hex colors in dict."""
        valid_dict = {
            CompoundTypes.Soft: "#ff0000",
            CompoundTypes.Medium: "#00ff00"
        }
        result = color_dict_validator(valid_dict)
        assert result == valid_dict


class TestTeamKeyValidator:
    """Test team_key_validator function."""

    def test_team_key_validator_with_non_alpha_characters(self):
        """Test team_key_validator raises ValueError for keys with non-alpha characters."""
        # Create mock team constants
        mock_team = TeamConstants(
            short_name="Test",
            colors=TeamColorConstants(official="#ff0000", fastf1="#00ff00")
        )

        # Test with numeric characters (line 54)
        invalid_dict = {
            "team123": mock_team
        }
        with pytest.raises(ValueError, match="Invalid team key.*only letters and spaces allowed"):
            team_key_validator(invalid_dict)

        # Test with special characters
        invalid_dict = {
            "team-name": mock_team
        }
        with pytest.raises(ValueError, match="Invalid team key.*only letters and spaces allowed"):
            team_key_validator(invalid_dict)

    def test_team_key_validator_with_uppercase(self):
        """Test team_key_validator raises ValueError for uppercase keys."""
        # Create mock team constants
        mock_team = TeamConstants(
            short_name="Test",
            colors=TeamColorConstants(official="#ff0000", fastf1="#00ff00")
        )

        # Test with uppercase letters (line 58)
        invalid_dict = {
            "TeamName": mock_team
        }
        with pytest.raises(ValueError, match="Invalid team key.*must be lower case"):
            team_key_validator(invalid_dict)

        # Test with mixed case
        invalid_dict = {
            "team Name": mock_team
        }
        with pytest.raises(ValueError, match="Invalid team key.*must be lower case"):
            team_key_validator(invalid_dict)

    def test_team_key_validator_with_valid_keys(self):
        """Test team_key_validator accepts valid lowercase alphabetic keys."""
        mock_team = TeamConstants(
            short_name="Test",
            colors=TeamColorConstants(official="#ff0000", fastf1="#00ff00")
        )

        # Test with lowercase letters only
        valid_dict = {
            "teamname": mock_team
        }
        result = team_key_validator(valid_dict)
        assert result == valid_dict

        # Test with lowercase letters and spaces
        valid_dict = {
            "team name": mock_team
        }
        result = team_key_validator(valid_dict)
        assert result == valid_dict


class TestTeamAddDriver:
    """Test Team.add_driver method."""

    def test_add_driver_duplicate(self):
        """Test add_driver raises ValueError when adding duplicate driver."""
        # Create a team
        team = Team(
            short_name="Test Team",
            colors=TeamColorConstants(official="#ff0000", fastf1="#00ff00"),
            name="Test Team Full",
            normalized_name="test team"
        )

        # Create a driver (without validation to avoid circular dependency)
        driver = Driver.model_construct(
            team=team,
            abbreviation="TST",
            name="Test Driver",
            normalized_name="test driver"
        )

        # Add driver first time (should succeed)
        team.add_driver(driver)
        assert driver in team.drivers

        # Try to add same driver again (line 107)
        with pytest.raises(ValueError, match="Driver .* already exists"):
            team.add_driver(driver)

    def test_add_driver_success(self):
        """Test add_driver successfully adds unique driver."""
        team = Team(
            short_name="Test Team",
            colors=TeamColorConstants(official="#ff0000", fastf1="#00ff00"),
            name="Test Team Full",
            normalized_name="test team"
        )

        driver1 = Driver.model_construct(
            team=team,
            abbreviation="DR1",
            name="Driver One",
            normalized_name="driver one"
        )

        driver2 = Driver.model_construct(
            team=team,
            abbreviation="DR2",
            name="Driver Two",
            normalized_name="driver two"
        )

        team.add_driver(driver1)
        team.add_driver(driver2)

        assert len(team.drivers) == 2
        assert driver1 in team.drivers
        assert driver2 in team.drivers


class TestDriverEnsureUnique:
    """Test Driver.ensure_unique validator."""

    def test_ensure_unique_duplicate_abbreviation(self):
        """Test ensure_unique raises ValueError for duplicate abbreviations."""
        # Create a team
        team = Team(
            short_name="Test Team",
            colors=TeamColorConstants(official="#ff0000", fastf1="#00ff00"),
            name="Test Team Full",
            normalized_name="test team"
        )

        # Add first driver directly to team.drivers list to bypass add_driver check
        driver1 = Driver.model_construct(
            team=team,
            abbreviation="DUP",
            name="Driver One",
            normalized_name="driver one"
        )
        team.drivers.append(driver1)

        # Try to create second driver with same abbreviation (line 121)
        with pytest.raises(ValueError, match="Duplicate driver: DUP"):
            Driver(
                team=team,
                abbreviation="DUP",
                name="Driver Two",
                normalized_name="driver two"
            )

    def test_ensure_unique_different_abbreviations(self):
        """Test ensure_unique allows different abbreviations."""
        team = Team(
            short_name="Test Team",
            colors=TeamColorConstants(official="#ff0000", fastf1="#00ff00"),
            name="Test Team Full",
            normalized_name="test team"
        )

        # Create first driver
        driver1 = Driver(
            team=team,
            abbreviation="DR1",
            name="Driver One",
            normalized_name="driver one"
        )
        team.drivers.append(driver1)

        # Create second driver with different abbreviation
        driver2 = Driver(
            team=team,
            abbreviation="DR2",
            name="Driver Two",
            normalized_name="driver two"
        )

        # Should succeed
        assert driver2.abbreviation == "DR2"
        assert driver2.team == team
