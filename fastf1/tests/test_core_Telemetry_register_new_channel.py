"""Tests for Telemetry.register_new_channel method"""
import pytest

from fastf1 import core


class TestTelemetryRegisterNewChannel:
    """Tests for Telemetry.register_new_channel method"""

    def test_register_new_channel_invalid_signal_type(self):
        """Test register_new_channel with invalid signal type"""
        # Attempt to register a channel with an invalid signal type
        with pytest.raises(ValueError, match="Unknown signal type"):
            core.Telemetry.register_new_channel('TestChannel', 'invalid_type')

    def test_register_new_channel_continuous_without_interpolation_method(self):
        """Test register_new_channel with continuous signal type but no interpolation method"""
        # Attempt to register a continuous channel without interpolation method
        with pytest.raises(ValueError, match="signal_type='continuous' requires interpolation_method"):
            core.Telemetry.register_new_channel('TestChannel', 'continuous')

    def test_register_new_channel_discrete(self):
        """Test register_new_channel with discrete signal type"""
        # Register a discrete channel
        channel_name = 'TestDiscreteChannel'
        core.Telemetry.register_new_channel(channel_name, 'discrete')

        # Verify the channel was registered correctly
        assert channel_name in core.Telemetry._CHANNELS
        assert core.Telemetry._CHANNELS[channel_name]['type'] == 'discrete'
        assert core.Telemetry._CHANNELS[channel_name]['method'] is None

        # Clean up
        del core.Telemetry._CHANNELS[channel_name]

    def test_register_new_channel_continuous_with_interpolation_method(self):
        """Test register_new_channel with continuous signal type and interpolation method"""
        # Register a continuous channel with interpolation method
        channel_name = 'TestContinuousChannel'
        core.Telemetry.register_new_channel(channel_name, 'continuous', 'linear')

        # Verify the channel was registered correctly
        assert channel_name in core.Telemetry._CHANNELS
        assert core.Telemetry._CHANNELS[channel_name]['type'] == 'continuous'
        assert core.Telemetry._CHANNELS[channel_name]['method'] == 'linear'

        # Clean up
        del core.Telemetry._CHANNELS[channel_name]

    def test_register_new_channel_excluded(self):
        """Test register_new_channel with excluded signal type"""
        # Register an excluded channel
        channel_name = 'TestExcludedChannel'
        core.Telemetry.register_new_channel(channel_name, 'excluded')

        # Verify the channel was registered correctly
        assert channel_name in core.Telemetry._CHANNELS
        assert core.Telemetry._CHANNELS[channel_name]['type'] == 'excluded'
        assert core.Telemetry._CHANNELS[channel_name]['method'] is None

        # Clean up
        del core.Telemetry._CHANNELS[channel_name]
