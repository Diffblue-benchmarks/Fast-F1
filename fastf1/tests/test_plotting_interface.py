import pytest
import warnings
from unittest.mock import Mock, patch, MagicMock

from fastf1.plotting._interface import override_team_constants, add_sorted_driver_legend
from fastf1.plotting._base import Team, TeamColorConstants, Driver, DriverTeamMapping


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


class TestAddSortedDriverLegend:
    """Tests for add_sorted_driver_legend function."""

    def test_add_sorted_driver_legend_basic(self):
        """Test add_sorted_driver_legend with basic setup (3 arguments returned)."""
        # This test targets lines 850, 852-856, 868-869, 876-884, 887, 889-893, 895

        # Create mock session
        mock_session = Mock()

        # Create mock teams
        team1 = Team(
            name="Mercedes",
            normalized_name="mercedes",
            short_name="Mercedes",
            colors=TeamColorConstants(official="#00d2be", fastf1="#00d2be")
        )
        team2 = Team(
            name="Ferrari",
            normalized_name="ferrari",
            short_name="Ferrari",
            colors=TeamColorConstants(official="#dc0000", fastf1="#dc0000")
        )

        # Create mock drivers
        driver1 = Driver(team=team1, abbreviation="HAM", name="Hamilton", normalized_name="hamilton")
        driver2 = Driver(team=team1, abbreviation="RUS", name="Russell", normalized_name="russell")
        driver3 = Driver(team=team2, abbreviation="LEC", name="Leclerc", normalized_name="leclerc")

        team1.drivers = [driver1, driver2]
        team2.drivers = [driver3]

        # Create mock driver-team mapping
        mock_dtm = DriverTeamMapping(
            year="2023",
            teams=[team1, team2]
        )

        # Create mock axes
        mock_ax = MagicMock()
        mock_legend = Mock()
        mock_ax.legend.return_value = mock_legend

        # Create mock handles and labels
        handle1, handle2, handle3 = Mock(), Mock(), Mock()
        labels = ["Hamilton", "Leclerc", "Russell"]
        handles = [handle1, handle3, handle2]

        # Mock _parse_legend_args to return 3-tuple
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._get_driver') as mock_get_driver, \
             patch('matplotlib.legend._parse_legend_args', return_value=(handles, labels, {})):

            # Setup _get_driver to return the appropriate driver
            mock_get_driver.side_effect = [driver1, driver3, driver2]

            # Call the function
            result = add_sorted_driver_legend(mock_ax, mock_session)

            # Verify the result
            assert result == mock_legend

            # Verify ax.legend was called with sorted handles and labels
            mock_ax.legend.assert_called_once()
            call_args = mock_ax.legend.call_args
            sorted_handles = call_args[0][0]
            sorted_labels = call_args[0][1]

            # Verify sorting: Mercedes drivers (Hamilton, Russell) before Ferrari (Leclerc)
            assert sorted_labels == ["Hamilton", "Russell", "Leclerc"]
            assert sorted_handles == [handle1, handle2, handle3]

    def test_add_sorted_driver_legend_with_four_return_values(self):
        """Test add_sorted_driver_legend when _parse_legend_args returns 4 values."""
        # This test targets lines 850, 852-854, 858, 868-869, 876-884, 887, 889-893, 895

        # Create mock session
        mock_session = Mock()

        # Create mock team and driver
        team1 = Team(
            name="Red Bull",
            normalized_name="red bull",
            short_name="Red Bull",
            colors=TeamColorConstants(official="#0600ef", fastf1="#0600ef")
        )
        driver1 = Driver(team=team1, abbreviation="VER", name="Verstappen", normalized_name="verstappen")
        team1.drivers = [driver1]

        # Create mock driver-team mapping
        mock_dtm = DriverTeamMapping(year="2023", teams=[team1])

        # Create mock axes
        mock_ax = MagicMock()
        mock_legend = Mock()
        mock_ax.legend.return_value = mock_legend

        # Create mock handles and labels
        handle1 = Mock()
        labels = ["Verstappen"]
        handles = [handle1]
        extra_args = (1, 2)

        # Mock _parse_legend_args to return 4-tuple
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._get_driver', return_value=driver1), \
             patch('matplotlib.legend._parse_legend_args', return_value=(handles, labels, extra_args, {'loc': 'upper right'})):

            # Call the function with extra kwargs
            result = add_sorted_driver_legend(mock_ax, mock_session, loc='upper right')

            # Verify the result
            assert result == mock_legend

            # Verify ax.legend was called with extra_args
            mock_ax.legend.assert_called_once()
            call_args = mock_ax.legend.call_args
            assert call_args[0][0] == [handle1]
            assert call_args[0][1] == ["Verstappen"]
            assert call_args[0][2:] == extra_args

    def test_add_sorted_driver_legend_with_attribute_error(self):
        """Test add_sorted_driver_legend when AttributeError is raised."""
        # This test targets lines 850, 852-853, 860-866, 868-869, 876-884, 887, 889-893, 895

        # Create mock session
        mock_session = Mock()

        # Create mock team and driver
        team1 = Team(
            name="Alpine",
            normalized_name="alpine",
            short_name="Alpine",
            colors=TeamColorConstants(official="#0090ff", fastf1="#0090ff")
        )
        driver1 = Driver(team=team1, abbreviation="ALO", name="Alonso", normalized_name="alonso")
        team1.drivers = [driver1]

        # Create mock driver-team mapping
        mock_dtm = DriverTeamMapping(year="2023", teams=[team1])

        # Create mock axes
        mock_ax = MagicMock()
        mock_legend = Mock()
        mock_ax.legend.return_value = mock_legend

        # Create mock handles and labels from get_legend_handles_labels
        handle1 = Mock()
        mock_ax.get_legend_handles_labels.return_value = ([handle1], ["Alonso"])

        # Mock _parse_legend_args to raise AttributeError
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._get_driver', return_value=driver1), \
             patch('matplotlib.legend._parse_legend_args', side_effect=AttributeError("Test error")), \
             pytest.warns(UserWarning, match="Failed to parse optional legend arguments correctly"):

            # Call the function
            result = add_sorted_driver_legend(mock_ax, mock_session, handles=[handle1], labels=["Alonso"])

            # Verify the result
            assert result == mock_legend

            # Verify ax.get_legend_handles_labels was called
            mock_ax.get_legend_handles_labels.assert_called_once()

            # Verify ax.legend was called
            mock_ax.legend.assert_called_once()

    def test_add_sorted_driver_legend_multiple_teams_sorted(self):
        """Test that drivers are sorted by team index then driver index."""
        # This test targets lines 850, 852-856, 868-869, 876-884, 887, 889-893, 895

        # Create mock session
        mock_session = Mock()

        # Create three teams
        team1 = Team(
            name="Team A",
            normalized_name="team a",
            short_name="Team A",
            colors=TeamColorConstants(official="#111111", fastf1="#111111")
        )
        team2 = Team(
            name="Team B",
            normalized_name="team b",
            short_name="Team B",
            colors=TeamColorConstants(official="#222222", fastf1="#222222")
        )
        team3 = Team(
            name="Team C",
            normalized_name="team c",
            short_name="Team C",
            colors=TeamColorConstants(official="#333333", fastf1="#333333")
        )

        # Create drivers
        driver1 = Driver(team=team1, abbreviation="DR1", name="Driver1", normalized_name="driver1")
        driver2 = Driver(team=team1, abbreviation="DR2", name="Driver2", normalized_name="driver2")
        driver3 = Driver(team=team2, abbreviation="DR3", name="Driver3", normalized_name="driver3")
        driver4 = Driver(team=team3, abbreviation="DR4", name="Driver4", normalized_name="driver4")

        team1.drivers = [driver1, driver2]
        team2.drivers = [driver3]
        team3.drivers = [driver4]

        # Create mock driver-team mapping
        mock_dtm = DriverTeamMapping(year="2023", teams=[team1, team2, team3])

        # Create mock axes
        mock_ax = MagicMock()
        mock_legend = Mock()
        mock_ax.legend.return_value = mock_legend

        # Create handles and labels in random order
        h1, h2, h3, h4 = Mock(), Mock(), Mock(), Mock()
        # Provide in order: Driver4, Driver2, Driver3, Driver1
        labels = ["Driver4", "Driver2", "Driver3", "Driver1"]
        handles = [h4, h2, h3, h1]

        # Mock _parse_legend_args
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._get_driver') as mock_get_driver, \
             patch('matplotlib.legend._parse_legend_args', return_value=(handles, labels, {})):

            # Setup _get_driver to return the appropriate driver
            mock_get_driver.side_effect = [driver4, driver2, driver3, driver1]

            # Call the function
            result = add_sorted_driver_legend(mock_ax, mock_session)

            # Verify sorting: Team A (Driver1, Driver2), then Team B (Driver3), then Team C (Driver4)
            call_args = mock_ax.legend.call_args
            sorted_labels = call_args[0][1]
            sorted_handles = call_args[0][0]

            assert sorted_labels == ["Driver1", "Driver2", "Driver3", "Driver4"]
            assert sorted_handles == [h1, h2, h3, h4]

    def test_add_sorted_driver_legend_with_kwargs(self):
        """Test add_sorted_driver_legend passes through kwargs correctly."""
        # This test targets lines 850, 852-856, 868-869, 876-884, 887, 889-893, 895

        # Create mock session
        mock_session = Mock()

        # Create mock team and driver
        team1 = Team(
            name="McLaren",
            normalized_name="mclaren",
            short_name="McLaren",
            colors=TeamColorConstants(official="#ff8700", fastf1="#ff8700")
        )
        driver1 = Driver(team=team1, abbreviation="NOR", name="Norris", normalized_name="norris")
        team1.drivers = [driver1]

        # Create mock driver-team mapping
        mock_dtm = DriverTeamMapping(year="2023", teams=[team1])

        # Create mock axes
        mock_ax = MagicMock()
        mock_legend = Mock()
        mock_ax.legend.return_value = mock_legend

        # Create mock handles and labels
        handle1 = Mock()

        # Mock _parse_legend_args
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._get_driver', return_value=driver1), \
             patch('matplotlib.legend._parse_legend_args', return_value=([handle1], ["Norris"], {'loc': 'best', 'fontsize': 12})):

            # Call the function with kwargs
            result = add_sorted_driver_legend(mock_ax, mock_session, loc='best', fontsize=12)

            # Verify the result
            assert result == mock_legend

            # Verify kwargs were passed through
            call_args = mock_ax.legend.call_args
            assert call_args[1] == {'loc': 'best', 'fontsize': 12}
