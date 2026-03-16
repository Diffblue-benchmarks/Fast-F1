import numpy as np
import pandas as pd
import pytest
from unittest.mock import Mock, patch, MagicMock

import fastf1.exceptions
from fastf1.mvapi.data import CircuitInfo, get_circuit_info


class TestCircuitInfoAddMarkerDistance:
    """Tests for CircuitInfo.add_marker_distance method."""

    def test_add_marker_distance_with_data_not_loaded_error(self):
        """Test add_marker_distance when telemetry data is not loaded."""
        # This test targets lines 77-82: DataNotLoadedError handling

        # Create a CircuitInfo instance with empty dataframes
        circuit_info = CircuitInfo(
            corners=pd.DataFrame(columns=['X', 'Y', 'Number', 'Letter', 'Angle', 'Distance']),
            marshal_lights=pd.DataFrame(columns=['X', 'Y', 'Number', 'Letter', 'Angle', 'Distance']),
            marshal_sectors=pd.DataFrame(columns=['X', 'Y', 'Number', 'Letter', 'Angle', 'Distance']),
            rotation=0.0
        )

        # Create a mock lap that raises DataNotLoadedError
        mock_lap = Mock()
        mock_lap.get_telemetry.side_effect = fastf1.exceptions.DataNotLoadedError("Telemetry data not loaded")

        # Should not raise an error, just log a warning
        circuit_info.add_marker_distance(mock_lap)

        # Verify get_telemetry was called
        mock_lap.get_telemetry.assert_called_once_with(frequency='original')

    def test_add_marker_distance_with_empty_telemetry(self):
        """Test add_marker_distance when telemetry data is empty."""
        # This test targets lines 84-87: empty telemetry handling

        # Create a CircuitInfo instance with sample data
        corners_df = pd.DataFrame({
            'X': [100.0, 200.0],
            'Y': [150.0, 250.0],
            'Number': [1, 2],
            'Letter': ['', ''],
            'Angle': [0.0, 45.0],
            'Distance': [np.nan, np.nan]
        })

        circuit_info = CircuitInfo(
            corners=corners_df,
            marshal_lights=pd.DataFrame(columns=['X', 'Y', 'Number', 'Letter', 'Angle', 'Distance']),
            marshal_sectors=pd.DataFrame(columns=['X', 'Y', 'Number', 'Letter', 'Angle', 'Distance']),
            rotation=0.0
        )

        # Create a mock lap that returns empty telemetry
        mock_lap = Mock()
        empty_telemetry = pd.DataFrame(columns=['X', 'Y', 'Distance', 'Source'])
        mock_lap.get_telemetry.return_value = empty_telemetry

        # Should not raise an error, just log a warning
        circuit_info.add_marker_distance(mock_lap)

        # Verify get_telemetry was called
        mock_lap.get_telemetry.assert_called_once_with(frequency='original')

    def test_add_marker_distance_with_valid_telemetry(self):
        """Test add_marker_distance with valid telemetry data."""
        # This test targets lines 89-117: main computation logic

        # Create a CircuitInfo instance with sample markers
        corners_df = pd.DataFrame({
            'X': [100.0, 200.0, 300.0],
            'Y': [150.0, 250.0, 350.0],
            'Number': [1, 2, 3],
            'Letter': ['', '', 'A'],
            'Angle': [0.0, 45.0, 90.0],
            'Distance': [np.nan, np.nan, np.nan]
        })

        marshal_lights_df = pd.DataFrame({
            'X': [110.0],
            'Y': [160.0],
            'Number': [1],
            'Letter': [''],
            'Angle': [10.0],
            'Distance': [np.nan]
        })

        marshal_sectors_df = pd.DataFrame({
            'X': [120.0],
            'Y': [170.0],
            'Number': [1],
            'Letter': [''],
            'Angle': [20.0],
            'Distance': [np.nan]
        })

        circuit_info = CircuitInfo(
            corners=corners_df,
            marshal_lights=marshal_lights_df,
            marshal_sectors=marshal_sectors_df,
            rotation=0.0
        )

        # Create mock telemetry data with position values
        telemetry_data = pd.DataFrame({
            'X': [95.0, 105.0, 195.0, 205.0, 295.0, 305.0, 108.0, 118.0],
            'Y': [145.0, 155.0, 245.0, 255.0, 345.0, 355.0, 158.0, 168.0],
            'Distance': [0.0, 100.0, 200.0, 300.0, 400.0, 500.0, 150.0, 175.0],
            'Source': ['pos', 'pos', 'pos', 'pos', 'pos', 'pos', 'pos', 'pos']
        })

        mock_lap = Mock()
        mock_lap.get_telemetry.return_value = telemetry_data

        # Call the method
        circuit_info.add_marker_distance(mock_lap)

        # Verify that Distance values were added to the dataframes
        assert not circuit_info.corners['Distance'].isna().all()
        assert not circuit_info.marshal_lights['Distance'].isna().all()
        assert not circuit_info.marshal_sectors['Distance'].isna().all()

        # Verify the distances are from the telemetry data
        for dist in circuit_info.corners['Distance']:
            assert dist in telemetry_data['Distance'].values

        for dist in circuit_info.marshal_lights['Distance']:
            assert dist in telemetry_data['Distance'].values

        for dist in circuit_info.marshal_sectors['Distance']:
            assert dist in telemetry_data['Distance'].values

    def test_add_marker_distance_with_single_marker(self):
        """Test add_marker_distance with a single marker."""
        # Additional test to cover edge case with single marker (lines 97, 107, 112)

        circuit_info = CircuitInfo(
            corners=pd.DataFrame({
                'X': [100.0],
                'Y': [150.0],
                'Number': [1],
                'Letter': [''],
                'Angle': [0.0],
                'Distance': [np.nan]
            }),
            marshal_lights=pd.DataFrame(columns=['X', 'Y', 'Number', 'Letter', 'Angle', 'Distance']),
            marshal_sectors=pd.DataFrame(columns=['X', 'Y', 'Number', 'Letter', 'Angle', 'Distance']),
            rotation=0.0
        )

        telemetry_data = pd.DataFrame({
            'X': [95.0, 105.0, 200.0],
            'Y': [145.0, 155.0, 250.0],
            'Distance': [0.0, 100.0, 200.0],
            'Source': ['pos', 'pos', 'pos']
        })

        mock_lap = Mock()
        mock_lap.get_telemetry.return_value = telemetry_data

        circuit_info.add_marker_distance(mock_lap)

        # Should have exactly one distance value
        assert len(circuit_info.corners['Distance']) == 1
        assert not np.isnan(circuit_info.corners['Distance'].iloc[0])


class TestGetCircuitInfo:
    """Tests for get_circuit_info function."""

    @patch('fastf1.mvapi.data.get_circuit')
    def test_get_circuit_info_with_empty_data(self, mock_get_circuit):
        """Test get_circuit_info when API returns empty data."""
        # This test targets lines 131-133: empty data handling

        mock_get_circuit.return_value = None

        result = get_circuit_info(year=2023, circuit_key=1)

        assert result is None
        mock_get_circuit.assert_called_once_with(year=2023, circuit_key=1)

    @patch('fastf1.mvapi.data.get_circuit')
    def test_get_circuit_info_with_valid_data(self, mock_get_circuit):
        """Test get_circuit_info with valid API data."""
        # This test targets lines 135-164: full data processing

        mock_data = {
            'corners': [
                {
                    'trackPosition': {'x': 100.5, 'y': 200.7},
                    'number': 1,
                    'letter': 'A',
                    'angle': 45.0
                },
                {
                    'trackPosition': {'x': 300.2, 'y': 400.9},
                    'number': 2,
                    'letter': '',
                    'angle': 90.0
                }
            ],
            'marshalLights': [
                {
                    'trackPosition': {'x': 150.0, 'y': 250.0},
                    'number': 1,
                    'letter': '',
                    'angle': 30.0
                }
            ],
            'marshalSectors': [
                {
                    'trackPosition': {'x': 180.0, 'y': 280.0},
                    'number': 1,
                    'letter': 'B',
                    'angle': 60.0
                }
            ],
            'rotation': 15.5
        }

        mock_get_circuit.return_value = mock_data

        result = get_circuit_info(year=2023, circuit_key=1)

        assert result is not None
        assert isinstance(result, CircuitInfo)

        # Check corners
        assert len(result.corners) == 2
        assert result.corners.iloc[0]['X'] == 100.5
        assert result.corners.iloc[0]['Y'] == 200.7
        assert result.corners.iloc[0]['Number'] == 1
        assert result.corners.iloc[0]['Letter'] == 'A'
        assert result.corners.iloc[0]['Angle'] == 45.0
        assert np.isnan(result.corners.iloc[0]['Distance'])

        # Check marshal lights
        assert len(result.marshal_lights) == 1
        assert result.marshal_lights.iloc[0]['X'] == 150.0
        assert result.marshal_lights.iloc[0]['Y'] == 250.0
        assert result.marshal_lights.iloc[0]['Number'] == 1

        # Check marshal sectors
        assert len(result.marshal_sectors) == 1
        assert result.marshal_sectors.iloc[0]['X'] == 180.0
        assert result.marshal_sectors.iloc[0]['Y'] == 280.0
        assert result.marshal_sectors.iloc[0]['Letter'] == 'B'

        # Check rotation
        assert result.rotation == 15.5

    @patch('fastf1.mvapi.data.get_circuit')
    def test_get_circuit_info_with_missing_fields(self, mock_get_circuit):
        """Test get_circuit_info with missing optional fields."""
        # This test targets lines 140-146: handling missing fields with defaults

        mock_data = {
            'corners': [
                {
                    'trackPosition': {},  # Missing x and y
                    # Missing number, letter, angle
                }
            ],
            'marshalLights': [],
            'marshalSectors': []
            # Missing rotation
        }

        mock_get_circuit.return_value = mock_data

        result = get_circuit_info(year=2023, circuit_key=1)

        assert result is not None
        assert isinstance(result, CircuitInfo)

        # Check that defaults are applied
        assert len(result.corners) == 1
        assert result.corners.iloc[0]['X'] == 0.0  # default
        assert result.corners.iloc[0]['Y'] == 0.0  # default
        assert result.corners.iloc[0]['Number'] == 0  # default
        assert result.corners.iloc[0]['Letter'] == ''  # default
        assert result.corners.iloc[0]['Angle'] == 0.0  # default

        assert len(result.marshal_lights) == 0
        assert len(result.marshal_sectors) == 0
        assert result.rotation == 0.0  # default

    @patch('fastf1.mvapi.data.get_circuit')
    def test_get_circuit_info_with_empty_categories(self, mock_get_circuit):
        """Test get_circuit_info when categories are missing from response."""
        # This test targets line 138: handling missing categories with empty list

        mock_data = {
            # Missing corners, marshalLights, marshalSectors
            'rotation': 10.0
        }

        mock_get_circuit.return_value = mock_data

        result = get_circuit_info(year=2023, circuit_key=1)

        assert result is not None
        assert isinstance(result, CircuitInfo)

        # All dataframes should be empty but with correct columns
        assert len(result.corners) == 0
        assert len(result.marshal_lights) == 0
        assert len(result.marshal_sectors) == 0
        assert list(result.corners.columns) == ['X', 'Y', 'Number', 'Letter', 'Angle', 'Distance']
        assert result.rotation == 10.0

    @patch('fastf1.mvapi.data.get_circuit')
    def test_get_circuit_info_with_partial_track_position(self, mock_get_circuit):
        """Test get_circuit_info with partial trackPosition data."""
        # This test targets lines 141-142: handling partial trackPosition

        mock_data = {
            'corners': [
                {
                    'trackPosition': {'x': 100.0},  # Missing y
                    'number': 1,
                    'letter': '',
                    'angle': 0.0
                },
                {
                    'trackPosition': {'y': 200.0},  # Missing x
                    'number': 2,
                    'letter': '',
                    'angle': 0.0
                }
            ],
            'marshalLights': [],
            'marshalSectors': [],
            'rotation': 0.0
        }

        mock_get_circuit.return_value = mock_data

        result = get_circuit_info(year=2023, circuit_key=1)

        assert result is not None
        assert len(result.corners) == 2
        assert result.corners.iloc[0]['X'] == 100.0
        assert result.corners.iloc[0]['Y'] == 0.0  # default for missing y
        assert result.corners.iloc[1]['X'] == 0.0  # default for missing x
        assert result.corners.iloc[1]['Y'] == 200.0
