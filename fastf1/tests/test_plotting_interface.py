import pytest
from unittest.mock import Mock, patch

from fastf1.plotting._interface import override_team_constants
from fastf1.plotting._base import Team, TeamColorConstants


class TestOverrideTeamConstants:
    """Tests for override_team_constants function."""

    def test_override_official_color(self):
        """Test override_team_constants when official_color is provided."""
        # This test targets lines 937, 939-940

        # Create a mock session
        mock_session = Mock()

        # Create a Team object with initial values
        mock_team = Team(
            name="Mercedes",
            normalized_name="mercedes",
            short_name="Mercedes",
            colors=TeamColorConstants(
                official="#00d2be",
                fastf1="#00d2be"
            )
        )

        # Mock _get_team to return our test team
        with patch('fastf1.plotting._interface._get_team', return_value=mock_team):
            # Call the function with official_color
            override_team_constants(
                "mercedes",
                mock_session,
                official_color="#ff0000"
            )

            # Verify the official color was changed
            assert mock_team.colors.official == "#ff0000"
            # Verify fastf1 color and short_name were not changed
            assert mock_team.colors.fastf1 == "#00d2be"
            assert mock_team.short_name == "Mercedes"

    def test_override_fastf1_color(self):
        """Test override_team_constants when fastf1_color is provided."""
        # This test targets lines 937, 941-942

        # Create a mock session
        mock_session = Mock()

        # Create a Team object with initial values
        mock_team = Team(
            name="Ferrari",
            normalized_name="ferrari",
            short_name="Ferrari",
            colors=TeamColorConstants(
                official="#dc0000",
                fastf1="#dc0000"
            )
        )

        # Mock _get_team to return our test team
        with patch('fastf1.plotting._interface._get_team', return_value=mock_team):
            # Call the function with fastf1_color
            override_team_constants(
                "ferrari",
                mock_session,
                fastf1_color="#00ff00"
            )

            # Verify the fastf1 color was changed
            assert mock_team.colors.fastf1 == "#00ff00"
            # Verify official color and short_name were not changed
            assert mock_team.colors.official == "#dc0000"
            assert mock_team.short_name == "Ferrari"

    def test_override_short_name(self):
        """Test override_team_constants when short_name is provided."""
        # This test targets lines 937, 943-944

        # Create a mock session
        mock_session = Mock()

        # Create a Team object with initial values
        mock_team = Team(
            name="Red Bull Racing",
            normalized_name="red bull",
            short_name="Red Bull",
            colors=TeamColorConstants(
                official="#0600ef",
                fastf1="#0600ef"
            )
        )

        # Mock _get_team to return our test team
        with patch('fastf1.plotting._interface._get_team', return_value=mock_team):
            # Call the function with short_name
            override_team_constants(
                "red bull",
                mock_session,
                short_name="RBR"
            )

            # Verify the short_name was changed
            assert mock_team.short_name == "RBR"
            # Verify colors were not changed
            assert mock_team.colors.official == "#0600ef"
            assert mock_team.colors.fastf1 == "#0600ef"

    def test_override_all_parameters(self):
        """Test override_team_constants when all parameters are provided."""
        # This test targets lines 937, 939-944 (all branches)

        # Create a mock session
        mock_session = Mock()

        # Create a Team object with initial values
        mock_team = Team(
            name="McLaren",
            normalized_name="mclaren",
            short_name="McLaren",
            colors=TeamColorConstants(
                official="#ff8700",
                fastf1="#ff8700"
            )
        )

        # Mock _get_team to return our test team
        with patch('fastf1.plotting._interface._get_team', return_value=mock_team):
            # Call the function with all parameters
            override_team_constants(
                "mclaren",
                mock_session,
                official_color="#111111",
                fastf1_color="#222222",
                short_name="MCL"
            )

            # Verify all values were changed
            assert mock_team.colors.official == "#111111"
            assert mock_team.colors.fastf1 == "#222222"
            assert mock_team.short_name == "MCL"

    def test_override_with_exact_match(self):
        """Test that override_team_constants calls _get_team with exact_match=True."""
        # This test verifies line 937: exact_match parameter is passed correctly

        # Create a mock session
        mock_session = Mock()

        # Create a Team object
        mock_team = Team(
            name="Alpine",
            normalized_name="alpine",
            short_name="Alpine",
            colors=TeamColorConstants(
                official="#0090ff",
                fastf1="#0090ff"
            )
        )

        # Mock _get_team and verify it's called with exact_match=True
        with patch('fastf1.plotting._interface._get_team', return_value=mock_team) as mock_get_team:
            override_team_constants(
                "alpine",
                mock_session,
                short_name="ALP"
            )

            # Verify _get_team was called with exact_match=True
            mock_get_team.assert_called_once_with("alpine", mock_session, exact_match=True)

    def test_override_no_parameters(self):
        """Test override_team_constants when no override parameters are provided."""
        # This test verifies line 937 is executed but no changes are made

        # Create a mock session
        mock_session = Mock()

        # Create a Team object with initial values
        initial_official_color = "#ff1e00"
        initial_fastf1_color = "#ff1e00"
        initial_short_name = "Haas F1"

        mock_team = Team(
            name="Haas F1 Team",
            normalized_name="haas",
            short_name=initial_short_name,
            colors=TeamColorConstants(
                official=initial_official_color,
                fastf1=initial_fastf1_color
            )
        )

        # Mock _get_team to return our test team
        with patch('fastf1.plotting._interface._get_team', return_value=mock_team):
            # Call the function with no override parameters
            override_team_constants(
                "haas",
                mock_session
            )

            # Verify nothing was changed (all None branches were taken)
            assert mock_team.colors.official == initial_official_color
            assert mock_team.colors.fastf1 == initial_fastf1_color
            assert mock_team.short_name == initial_short_name
