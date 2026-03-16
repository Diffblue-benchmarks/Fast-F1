import pytest
import warnings
from unittest.mock import Mock, patch, MagicMock

from fastf1.plotting._interface import override_team_constants, add_sorted_driver_legend, list_team_names, get_driver_color_mapping, get_driver_style, get_team_name_by_driver, get_team_name, _get_team_exact, _get_team_fuzzy
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


class TestListTeamNames:
    """Tests for list_team_names function."""

    def test_list_team_names_default(self):
        """Test list_team_names returns full team names by default."""
        # This test targets lines 787, 793

        # Create mock session
        mock_session = Mock()

        # Create mock teams
        team1 = Team(
            name="Mercedes-AMG Petronas F1 Team",
            normalized_name="mercedes",
            short_name="Mercedes",
            colors=TeamColorConstants(official="#00d2be", fastf1="#00d2be")
        )
        team2 = Team(
            name="Scuderia Ferrari",
            normalized_name="ferrari",
            short_name="Ferrari",
            colors=TeamColorConstants(official="#dc0000", fastf1="#dc0000")
        )
        team3 = Team(
            name="Red Bull Racing",
            normalized_name="red bull",
            short_name="Red Bull",
            colors=TeamColorConstants(official="#0600ef", fastf1="#0600ef")
        )

        # Create mock driver-team mapping with teams_by_normalized dict
        mock_dtm = Mock()
        mock_dtm.teams_by_normalized = {
            "mercedes": team1,
            "ferrari": team2,
            "red bull": team3
        }

        # Mock _get_driver_team_mapping
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm):
            # Call the function without short parameter (default: False)
            result = list_team_names(mock_session)

            # Verify the result contains full team names
            assert len(result) == 3
            assert "Mercedes-AMG Petronas F1 Team" in result
            assert "Scuderia Ferrari" in result
            assert "Red Bull Racing" in result

    def test_list_team_names_short(self):
        """Test list_team_names returns short team names when short=True."""
        # This test targets lines 787, 789, 790

        # Create mock session
        mock_session = Mock()

        # Create mock teams
        team1 = Team(
            name="Mercedes-AMG Petronas F1 Team",
            normalized_name="mercedes",
            short_name="Mercedes",
            colors=TeamColorConstants(official="#00d2be", fastf1="#00d2be")
        )
        team2 = Team(
            name="Scuderia Ferrari",
            normalized_name="ferrari",
            short_name="Ferrari",
            colors=TeamColorConstants(official="#dc0000", fastf1="#dc0000")
        )
        team3 = Team(
            name="Red Bull Racing",
            normalized_name="red bull",
            short_name="Red Bull",
            colors=TeamColorConstants(official="#0600ef", fastf1="#0600ef")
        )

        # Create mock driver-team mapping with teams_by_normalized dict
        mock_dtm = Mock()
        mock_dtm.teams_by_normalized = {
            "mercedes": team1,
            "ferrari": team2,
            "red bull": team3
        }

        # Mock _get_driver_team_mapping
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm):
            # Call the function with short=True
            result = list_team_names(mock_session, short=True)

            # Verify the result contains short team names
            assert len(result) == 3
            assert "Mercedes" in result
            assert "Ferrari" in result
            assert "Red Bull" in result


class TestGetDriverColorMapping:
    """Tests for get_driver_color_mapping function."""

    def test_get_driver_color_mapping_default(self):
        """Test get_driver_color_mapping with default colormap."""
        # This test targets lines 753, 755-756, 758-761, 771

        # Create mock session
        mock_session = Mock()

        # Create mock teams
        team1 = Team(
            name="Mercedes",
            normalized_name="mercedes",
            short_name="Mercedes",
            colors=TeamColorConstants(official="#00d2be", fastf1="#00ffcc")
        )
        team2 = Team(
            name="Ferrari",
            normalized_name="ferrari",
            short_name="Ferrari",
            colors=TeamColorConstants(official="#dc0000", fastf1="#ff0000")
        )

        # Create mock drivers
        driver1 = Driver(team=team1, abbreviation="HAM", name="Hamilton", normalized_name="hamilton")
        driver2 = Driver(team=team2, abbreviation="LEC", name="Leclerc", normalized_name="leclerc")

        # Create mock driver-team mapping
        mock_dtm = Mock()
        mock_dtm.drivers_by_abbreviation = {
            "HAM": driver1,
            "LEC": driver2
        }

        # Mock _get_driver_team_mapping
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm):
            # Call the function with default colormap
            result = get_driver_color_mapping(mock_session)

            # Verify the result uses fastf1 colors (since default is 'fastf1')
            assert len(result) == 2
            assert result["HAM"] == "#00ffcc"
            assert result["LEC"] == "#ff0000"

    def test_get_driver_color_mapping_fastf1(self):
        """Test get_driver_color_mapping with fastf1 colormap explicitly."""
        # This test targets lines 753, 758-761, 771

        # Create mock session
        mock_session = Mock()

        # Create mock team
        team1 = Team(
            name="Red Bull",
            normalized_name="red bull",
            short_name="Red Bull",
            colors=TeamColorConstants(official="#0600ef", fastf1="#1e41ff")
        )

        # Create mock driver
        driver1 = Driver(team=team1, abbreviation="VER", name="Verstappen", normalized_name="verstappen")

        # Create mock driver-team mapping
        mock_dtm = Mock()
        mock_dtm.drivers_by_abbreviation = {
            "VER": driver1
        }

        # Mock _get_driver_team_mapping
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm):
            # Call the function with fastf1 colormap
            result = get_driver_color_mapping(mock_session, colormap='fastf1')

            # Verify the result uses fastf1 colors
            assert len(result) == 1
            assert result["VER"] == "#1e41ff"

    def test_get_driver_color_mapping_official(self):
        """Test get_driver_color_mapping with official colormap."""
        # This test targets lines 753, 763-766, 771

        # Create mock session
        mock_session = Mock()

        # Create mock teams
        team1 = Team(
            name="McLaren",
            normalized_name="mclaren",
            short_name="McLaren",
            colors=TeamColorConstants(official="#ff8700", fastf1="#ff9900")
        )
        team2 = Team(
            name="Alpine",
            normalized_name="alpine",
            short_name="Alpine",
            colors=TeamColorConstants(official="#0090ff", fastf1="#00aaff")
        )

        # Create mock drivers
        driver1 = Driver(team=team1, abbreviation="NOR", name="Norris", normalized_name="norris")
        driver2 = Driver(team=team2, abbreviation="ALO", name="Alonso", normalized_name="alonso")

        # Create mock driver-team mapping
        mock_dtm = Mock()
        mock_dtm.drivers_by_abbreviation = {
            "NOR": driver1,
            "ALO": driver2
        }

        # Mock _get_driver_team_mapping
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm):
            # Call the function with official colormap
            result = get_driver_color_mapping(mock_session, colormap='official')

            # Verify the result uses official colors
            assert len(result) == 2
            assert result["NOR"] == "#ff8700"
            assert result["ALO"] == "#0090ff"

    def test_get_driver_color_mapping_invalid_colormap(self):
        """Test get_driver_color_mapping with invalid colormap raises ValueError."""
        # This test targets lines 753, 769

        # Create mock session
        mock_session = Mock()

        # Create mock team
        team1 = Team(
            name="Haas",
            normalized_name="haas",
            short_name="Haas",
            colors=TeamColorConstants(official="#ff1e00", fastf1="#ff3333")
        )

        # Create mock driver
        driver1 = Driver(team=team1, abbreviation="MAG", name="Magnussen", normalized_name="magnussen")

        # Create mock driver-team mapping
        mock_dtm = Mock()
        mock_dtm.drivers_by_abbreviation = {
            "MAG": driver1
        }

        # Mock _get_driver_team_mapping
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm):
            # Call the function with invalid colormap
            with pytest.raises(ValueError, match="Invalid colormap 'invalid'"):
                get_driver_color_mapping(mock_session, colormap='invalid')


class TestGetDriverStyle:
    """Tests for get_driver_style function."""

    def test_get_driver_style_empty_style_raises_error(self):
        """Test get_driver_style with empty style raises ValueError."""
        # This test targets line 659

        # Create mock session
        mock_session = Mock()

        # Create mock team and driver
        team1 = Team(
            name="Mercedes",
            normalized_name="mercedes",
            short_name="Mercedes",
            colors=TeamColorConstants(official="#00d2be", fastf1="#00d2be")
        )
        driver1 = Driver(team=team1, abbreviation="HAM", name="Hamilton", normalized_name="hamilton")
        team1.drivers = [driver1]

        # Mock _get_driver
        with patch('fastf1.plotting._interface._get_driver', return_value=driver1):
            # Call with empty string
            with pytest.raises(ValueError, match="The provided style info is empty!"):
                get_driver_style("HAM", "", mock_session)

            # Call with empty list
            with pytest.raises(ValueError, match="The provided style info is empty!"):
                get_driver_style("HAM", [], mock_session)

    def test_get_driver_style_string_style_converted_to_list(self):
        """Test get_driver_style converts string style to list."""
        # This test targets line 662

        # Create mock session
        mock_session = Mock()

        # Create mock team and driver
        team1 = Team(
            name="Ferrari",
            normalized_name="ferrari",
            short_name="Ferrari",
            colors=TeamColorConstants(official="#dc0000", fastf1="#dc0000")
        )
        driver1 = Driver(team=team1, abbreviation="LEC", name="Leclerc", normalized_name="leclerc")
        team1.drivers = [driver1]

        # Mock _get_driver and _get_team_color
        with patch('fastf1.plotting._interface._get_driver', return_value=driver1), \
             patch('fastf1.plotting._interface._get_team_color', return_value="#dc0000"):
            # Call with string style
            result = get_driver_style("LEC", "color", mock_session)

            # Verify the result
            assert result == {"color": "#dc0000"}

    def test_get_driver_style_unsupported_option_raises_error(self):
        """Test get_driver_style with unsupported style option raises ValueError."""
        # This test targets line 678

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

        # Mock _get_driver
        with patch('fastf1.plotting._interface._get_driver', return_value=driver1):
            # Call with unsupported style option
            with pytest.raises(ValueError, match="'invalid_option' is not a supported styling option"):
                get_driver_style("VER", ["invalid_option"], mock_session)

    def test_get_driver_style_custom_style_not_enough_variants(self):
        """Test get_driver_style with custom style that has insufficient variants."""
        # This test targets lines 685-686

        # Create mock session
        mock_session = Mock()

        # Create mock team with two drivers
        team1 = Team(
            name="McLaren",
            normalized_name="mclaren",
            short_name="McLaren",
            colors=TeamColorConstants(official="#ff8700", fastf1="#ff8700")
        )
        driver1 = Driver(team=team1, abbreviation="NOR", name="Norris", normalized_name="norris")
        driver2 = Driver(team=team1, abbreviation="PIA", name="Piastri", normalized_name="piastri")
        team1.drivers = [driver1, driver2]

        # Mock _get_driver to return the second driver (idx=1)
        with patch('fastf1.plotting._interface._get_driver', return_value=driver2):
            # Call with only one custom style (but driver idx is 1, needs at least 2)
            custom_style = [{'color': 'red'}]
            with pytest.raises(ValueError, match="The provided custom style info does not contain enough variants"):
                get_driver_style("PIA", custom_style, mock_session)

    def test_get_driver_style_custom_style_invalid_format(self):
        """Test get_driver_style with custom style that is not a dict."""
        # This test targets line 691

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

        # Mock _get_driver
        with patch('fastf1.plotting._interface._get_driver', return_value=driver1):
            # Call with custom style that is not a dict (use a list with non-string element)
            # The first element must NOT be a string to enter the else block
            custom_style = [123]  # integer instead of dict
            with pytest.raises(ValueError, match="The provided style info has an invalid format!"):
                get_driver_style("ALO", custom_style, mock_session)

    def test_get_driver_style_custom_style_with_auto_color(self):
        """Test get_driver_style with custom style and 'auto' color replacement."""
        # This test targets line 685 and validates the custom style path

        # Create mock session
        mock_session = Mock()

        # Create mock team and driver
        team1 = Team(
            name="Haas",
            normalized_name="haas",
            short_name="Haas",
            colors=TeamColorConstants(official="#ff1e00", fastf1="#ff1e00")
        )
        driver1 = Driver(team=team1, abbreviation="MAG", name="Magnussen", normalized_name="magnussen")
        team1.drivers = [driver1]

        # Mock _get_driver and _replace_magic_auto
        with patch('fastf1.plotting._interface._get_driver', return_value=driver1), \
             patch('fastf1.plotting._interface._replace_magic_auto', return_value={'color': '#ff1e00', 'linestyle': 'solid'}):
            # Call with valid custom style
            custom_style = [{'color': 'auto', 'linestyle': 'solid'}]
            result = get_driver_style("MAG", custom_style, mock_session)

            # Verify the result
            assert result == {'color': '#ff1e00', 'linestyle': 'solid'}


class TestGetTeamNameByDriver:
    """Tests for get_team_name_by_driver function."""

    def test_get_team_name_by_driver_full_name(self):
        """Test get_team_name_by_driver returns full team name when short=False."""
        # This test targets lines 271, 272, 274, 277

        # Create mock session
        mock_session = Mock()

        # Create mock team
        team1 = Team(
            name="Mercedes-AMG Petronas F1 Team",
            normalized_name="mercedes",
            short_name="Mercedes",
            colors=TeamColorConstants(official="#00d2be", fastf1="#00d2be")
        )

        # Create mock driver
        driver1 = Driver(team=team1, abbreviation="HAM", name="Hamilton", normalized_name="hamilton")
        team1.drivers = [driver1]

        # Mock _get_driver
        with patch('fastf1.plotting._interface._get_driver', return_value=driver1):
            # Call the function with short=False (default)
            result = get_team_name_by_driver("HAM", mock_session, short=False)

            # Verify the result returns the full team name
            assert result == "Mercedes-AMG Petronas F1 Team"

    def test_get_team_name_by_driver_short_name(self):
        """Test get_team_name_by_driver returns short team name when short=True."""
        # This test targets lines 271, 272, 274, 275

        # Create mock session
        mock_session = Mock()

        # Create mock team
        team1 = Team(
            name="Scuderia Ferrari",
            normalized_name="ferrari",
            short_name="Ferrari",
            colors=TeamColorConstants(official="#dc0000", fastf1="#dc0000")
        )

        # Create mock driver
        driver1 = Driver(team=team1, abbreviation="LEC", name="Leclerc", normalized_name="leclerc")
        team1.drivers = [driver1]

        # Mock _get_driver
        with patch('fastf1.plotting._interface._get_driver', return_value=driver1):
            # Call the function with short=True
            result = get_team_name_by_driver("LEC", mock_session, short=True)

            # Verify the result returns the short team name
            assert result == "Ferrari"


class TestGetTeamName:
    """Tests for get_team_name function."""

    def test_get_team_name_full_name_default(self):
        """Test get_team_name returns full team name when short=False (default)."""
        # This test targets lines 233, 238

        # Create mock session
        mock_session = Mock()

        # Create mock team
        team1 = Team(
            name="Mercedes-AMG Petronas F1 Team",
            normalized_name="mercedes",
            short_name="Mercedes",
            colors=TeamColorConstants(official="#00d2be", fastf1="#00d2be")
        )

        # Mock _get_team
        with patch('fastf1.plotting._interface._get_team', return_value=team1) as mock_get_team:
            # Call the function with default parameters (short=False, exact_match=False)
            result = get_team_name("Mercedes", mock_session)

            # Verify _get_team was called with correct parameters
            mock_get_team.assert_called_once_with("Mercedes", mock_session, exact_match=False)

            # Verify the result returns the full team name
            assert result == "Mercedes-AMG Petronas F1 Team"

    def test_get_team_name_short_name(self):
        """Test get_team_name returns short team name when short=True."""
        # This test targets lines 233, 235, 236

        # Create mock session
        mock_session = Mock()

        # Create mock team
        team1 = Team(
            name="Scuderia Ferrari",
            normalized_name="ferrari",
            short_name="Ferrari",
            colors=TeamColorConstants(official="#dc0000", fastf1="#dc0000")
        )

        # Mock _get_team
        with patch('fastf1.plotting._interface._get_team', return_value=team1) as mock_get_team:
            # Call the function with short=True
            result = get_team_name("Ferrari", mock_session, short=True)

            # Verify _get_team was called with correct parameters
            mock_get_team.assert_called_once_with("Ferrari", mock_session, exact_match=False)

            # Verify the result returns the short team name
            assert result == "Ferrari"

    def test_get_team_name_with_exact_match(self):
        """Test get_team_name with exact_match=True passes parameter correctly."""
        # This test targets lines 233, 238 with exact_match parameter

        # Create mock session
        mock_session = Mock()

        # Create mock team
        team1 = Team(
            name="Red Bull Racing",
            normalized_name="red bull",
            short_name="Red Bull",
            colors=TeamColorConstants(official="#0600ef", fastf1="#0600ef")
        )

        # Mock _get_team
        with patch('fastf1.plotting._interface._get_team', return_value=team1) as mock_get_team:
            # Call the function with exact_match=True
            result = get_team_name("red bull", mock_session, exact_match=True)

            # Verify _get_team was called with exact_match=True
            mock_get_team.assert_called_once_with("red bull", mock_session, exact_match=True)

            # Verify the result returns the full team name
            assert result == "Red Bull Racing"

    def test_get_team_name_short_with_exact_match(self):
        """Test get_team_name with both short=True and exact_match=True."""
        # This test targets lines 233, 235, 236 with exact_match parameter

        # Create mock session
        mock_session = Mock()

        # Create mock team
        team1 = Team(
            name="McLaren F1 Team",
            normalized_name="mclaren",
            short_name="McLaren",
            colors=TeamColorConstants(official="#ff8700", fastf1="#ff8700")
        )

        # Mock _get_team
        with patch('fastf1.plotting._interface._get_team', return_value=team1) as mock_get_team:
            # Call the function with both short=True and exact_match=True
            result = get_team_name("mclaren", mock_session, short=True, exact_match=True)

            # Verify _get_team was called with correct parameters
            mock_get_team.assert_called_once_with("mclaren", mock_session, exact_match=True)

            # Verify the result returns the short team name
            assert result == "McLaren"


class TestGetTeamExact:
    """Tests for _get_team_exact function."""

    def test_get_team_exact_by_full_team_name(self):
        """Test _get_team_exact when identifier matches the full team name."""
        # This test targets lines 150-152, 155, 159-161 (the for loop)

        # Create mock session
        mock_session = Mock()

        # Create mock teams with different normalized and full names
        team1 = Team(
            name="Mercedes-AMG Petronas F1 Team",
            normalized_name="mercedes",
            short_name="Mercedes",
            colors=TeamColorConstants(official="#00d2be", fastf1="#00d2be")
        )
        team2 = Team(
            name="Scuderia Ferrari",
            normalized_name="ferrari",
            short_name="Ferrari",
            colors=TeamColorConstants(official="#dc0000", fastf1="#dc0000")
        )

        # Create mock driver-team mapping
        mock_dtm = Mock()
        mock_dtm.teams_by_normalized = {
            "mercedes": team1,
            "ferrari": team2
        }

        # Mock _get_driver_team_mapping and _normalize_string
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._normalize_string', side_effect=lambda x: x):
            # Call with full team name (not the normalized version)
            # This should trigger the for loop to find the match
            result = _get_team_exact("scuderia ferrari", mock_session)

            # Verify the correct team was returned
            assert result == team2
            assert result.name == "Scuderia Ferrari"

    def test_get_team_exact_no_match_raises_keyerror(self):
        """Test _get_team_exact raises KeyError when no match is found."""
        # This test targets lines 150-152, 155, 159-160, 163

        # Create mock session
        mock_session = Mock()

        # Create mock teams
        team1 = Team(
            name="Red Bull Racing",
            normalized_name="red bull",
            short_name="Red Bull",
            colors=TeamColorConstants(official="#0600ef", fastf1="#0600ef")
        )

        # Create mock driver-team mapping
        mock_dtm = Mock()
        mock_dtm.teams_by_normalized = {
            "red bull": team1
        }

        # Mock _get_driver_team_mapping and _normalize_string
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._normalize_string', side_effect=lambda x: x):
            # Call with an identifier that doesn't match anything
            with pytest.raises(KeyError, match="No team found for 'nonexistent team' \\(exact match only\\)"):
                _get_team_exact("nonexistent team", mock_session)


class TestGetTeamFuzzy:
    """Tests for _get_team_fuzzy function."""

    def test_get_team_fuzzy_with_common_words_removed(self):
        """Test _get_team_fuzzy removes common words and finds exact match."""
        # This test targets lines 114, 115, 117, 118, 121, 122, 147

        mock_session = Mock()

        # Create mock teams
        team1 = Team(
            name="Red Bull Racing",
            normalized_name="red bull",
            short_name="Red Bull",
            colors=TeamColorConstants(official="#0600ef", fastf1="#0600ef")
        )

        # Create mock driver-team mapping
        mock_dtm = Mock()
        mock_dtm.teams_by_normalized = {
            "red bull": team1
        }

        # Mock _get_driver_team_mapping and _normalize_string
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._normalize_string', return_value="red bull racing"):
            # Call with identifier containing common words that should be removed
            result = _get_team_fuzzy("Red Bull Racing F1 Team", mock_session)

            # Verify the correct team was returned
            assert result == team1

    def test_get_team_fuzzy_exact_normalized_match(self):
        """Test _get_team_fuzzy with exact normalized team name match."""
        # This test targets lines 114, 115, 117, 118, 121, 122, 147

        mock_session = Mock()

        # Create mock teams
        team1 = Team(
            name="Mercedes",
            normalized_name="mercedes",
            short_name="Mercedes",
            colors=TeamColorConstants(official="#00d2be", fastf1="#00d2be")
        )

        # Create mock driver-team mapping
        mock_dtm = Mock()
        mock_dtm.teams_by_normalized = {
            "mercedes": team1
        }

        # Mock _get_driver_team_mapping and _normalize_string
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._normalize_string', return_value="mercedes"):
            # Call with exact normalized match
            result = _get_team_fuzzy("mercedes", mock_session)

            # Verify the correct team was returned
            assert result == team1

    def test_get_team_fuzzy_full_name_match(self):
        """Test _get_team_fuzzy matches full team name."""
        # This test targets lines 114, 115, 117, 118, 126, 127, 132, 147

        mock_session = Mock()

        # Create mock teams
        team1 = Team(
            name="Scuderia Ferrari",
            normalized_name="ferrari",
            short_name="Ferrari",
            colors=TeamColorConstants(official="#dc0000", fastf1="#dc0000")
        )

        # Create mock driver-team mapping
        mock_dtm = Mock()
        mock_dtm.teams_by_normalized = {
            "ferrari": team1
        }

        # Mock _get_driver_team_mapping and _normalize_string
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._normalize_string', return_value="scuderia ferrari"):
            # Call with identifier matching full team name
            result = _get_team_fuzzy("Scuderia Ferrari", mock_session)

            # Verify the correct team was returned
            assert result == team1

    def test_get_team_fuzzy_short_name_match(self):
        """Test _get_team_fuzzy matches team short name."""
        # This test targets lines 114, 115, 117, 118, 126, 127, 132, 147

        mock_session = Mock()

        # Create mock teams
        team1 = Team(
            name="Aston Martin Aramco Cognizant F1 Team",
            normalized_name="aston martin",
            short_name="Aston Martin",
            colors=TeamColorConstants(official="#006f62", fastf1="#00665e")
        )

        # Create mock driver-team mapping
        mock_dtm = Mock()
        mock_dtm.teams_by_normalized = {
            "aston martin": team1
        }

        # Mock _get_driver_team_mapping and _normalize_string
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._normalize_string', return_value="aston martin"):
            # Call with identifier matching short name
            result = _get_team_fuzzy("Aston Martin", mock_session)

            # Verify the correct team was returned
            assert result == team1

    def test_get_team_fuzzy_partial_normalized_match(self):
        """Test _get_team_fuzzy with partial string match in normalized name."""
        # This test targets lines 114, 115, 117, 118, 126, 127, 132, 147

        mock_session = Mock()

        # Create mock teams
        team1 = Team(
            name="McLaren Formula 1 Team",
            normalized_name="mclaren",
            short_name="McLaren",
            colors=TeamColorConstants(official="#ff8700", fastf1="#ff8700")
        )

        # Create mock driver-team mapping
        mock_dtm = Mock()
        mock_dtm.teams_by_normalized = {
            "mclaren": team1
        }

        # Mock _get_driver_team_mapping and _normalize_string
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._normalize_string', return_value="mcl"):
            # Call with partial identifier
            result = _get_team_fuzzy("mcl", mock_session)

            # Verify the correct team was returned
            assert result == team1

    def test_get_team_fuzzy_with_fuzzy_matching_exact(self):
        """Test _get_team_fuzzy with fuzzy matching that returns exact match."""
        # This test targets lines 114, 115, 117, 118, 135, 136, 137, 141, 147

        mock_session = Mock()

        # Create mock teams
        team1 = Team(
            name="Alpine F1 Team",
            normalized_name="alpine",
            short_name="Alpine",
            colors=TeamColorConstants(official="#0090ff", fastf1="#0090ff")
        )
        team2 = Team(
            name="Haas F1 Team",
            normalized_name="haas",
            short_name="Haas",
            colors=TeamColorConstants(official="#ffffff", fastf1="#ffffff")
        )

        # Create mock driver-team mapping
        mock_dtm = Mock()
        mock_dtm.teams_by_normalized = {
            "alpine": team1,
            "haas": team2
        }

        # Mock _get_driver_team_mapping and _normalize_string
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._normalize_string', return_value="alpn"), \
             patch('fastf1.internals.fuzzy.fuzzy_matcher', return_value=(0, True)):
            # Call with identifier requiring fuzzy match
            result = _get_team_fuzzy("alpn", mock_session)

            # Verify the correct team was returned
            assert result == team1

    def test_get_team_fuzzy_with_fuzzy_matching_not_exact(self):
        """Test _get_team_fuzzy with fuzzy matching that is not exact and logs warning."""
        # This test targets lines 114, 115, 117, 118, 135, 136, 137, 141, 143, 144, 147

        mock_session = Mock()

        # Create mock teams
        team1 = Team(
            name="Williams Racing",
            normalized_name="williams",
            short_name="Williams",
            colors=TeamColorConstants(official="#005aff", fastf1="#005aff")
        )
        team2 = Team(
            name="Alfa Romeo Racing",
            normalized_name="alfa romeo",
            short_name="Alfa Romeo",
            colors=TeamColorConstants(official="#900000", fastf1="#900000")
        )

        # Create mock driver-team mapping
        mock_dtm = Mock()
        mock_dtm.teams_by_normalized = {
            "williams": team1,
            "alfa romeo": team2
        }

        # Mock _get_driver_team_mapping, _normalize_string, and fuzzy_matcher
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._normalize_string', return_value="wiliams"), \
             patch('fastf1.internals.fuzzy.fuzzy_matcher', return_value=(0, False)), \
             patch('fastf1.plotting._interface._logger') as mock_logger:
            # Call with identifier requiring fuzzy match (misspelled)
            result = _get_team_fuzzy("wiliams", mock_session)

            # Verify the correct team was returned
            assert result == team1

            # Verify warning was logged
            mock_logger.warning.assert_called_once()
            args = mock_logger.warning.call_args[0]
            assert "Correcting user input" in args[0]
            assert "wiliams" in args[0]
            assert "williams" in args[0]

    def test_get_team_fuzzy_removes_all_common_words(self):
        """Test _get_team_fuzzy removes all common words (racing, team, f1, scuderia)."""
        # This test targets lines 114, 115, 117, 118, 121, 122, 147

        mock_session = Mock()

        # Create mock teams
        team1 = Team(
            name="AlphaTauri",
            normalized_name="alphatauri",
            short_name="AlphaTauri",
            colors=TeamColorConstants(official="#2b4562", fastf1="#2b4562")
        )

        # Create mock driver-team mapping
        mock_dtm = Mock()
        mock_dtm.teams_by_normalized = {
            "alphatauri": team1
        }

        # Mock _get_driver_team_mapping and _normalize_string
        # The identifier will have all common words which should be stripped
        with patch('fastf1.plotting._interface._get_driver_team_mapping', return_value=mock_dtm), \
             patch('fastf1.plotting._interface._normalize_string', return_value="scuderia alphatauri racing team f1"):
            # Call with identifier containing all common words
            result = _get_team_fuzzy("Scuderia AlphaTauri Racing Team F1", mock_session)

            # Verify the correct team was returned
            assert result == team1
