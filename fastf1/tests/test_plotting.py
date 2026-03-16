import warnings
from unittest.mock import Mock, patch, MagicMock

import pytest

from fastf1.plotting._plotting import (
    setup_mpl,
    _enable_timple,
    _enable_fastf1_color_scheme,
    _COLOR_PALETTE
)


class TestSetupMpl:
    """Tests for setup_mpl function"""

    def test_deprecated_misc_mpl_mods_kwarg(self):
        """Test warning for deprecated misc_mpl_mods argument (lines 55, 56)"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            setup_mpl(mpl_timedelta_support=False, misc_mpl_mods=True)

            assert len(w) == 1
            assert issubclass(w[0].category, FutureWarning)
            assert "misc_mpl_mods" in str(w[0].message)
            assert "dropped" in str(w[0].message)

    def test_deprecated_misc_mpl_mods_args(self):
        """Test warning for deprecated positional arguments (lines 55, 56)"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            setup_mpl(False, None, True)  # positional arg triggers warning

            assert len(w) == 1
            assert issubclass(w[0].category, FutureWarning)
            assert "misc_mpl_mods" in str(w[0].message)

    @patch('fastf1.plotting._plotting._enable_timple')
    def test_enable_timple_when_requested(self, mock_enable_timple):
        """Test _enable_timple is called when mpl_timedelta_support=True (lines 62, 63)"""
        setup_mpl(mpl_timedelta_support=True, color_scheme=None)

        mock_enable_timple.assert_called_once()

    @patch('fastf1.plotting._plotting._enable_timple')
    def test_skip_timple_when_not_requested(self, mock_enable_timple):
        """Test _enable_timple is not called when mpl_timedelta_support=False"""
        setup_mpl(mpl_timedelta_support=False, color_scheme=None)

        mock_enable_timple.assert_not_called()

    @patch('fastf1.plotting._plotting._enable_fastf1_color_scheme')
    def test_enable_fastf1_color_scheme(self, mock_enable_color_scheme):
        """Test _enable_fastf1_color_scheme is called when color_scheme='fastf1' (lines 64, 65)"""
        setup_mpl(mpl_timedelta_support=False, color_scheme='fastf1')

        mock_enable_color_scheme.assert_called_once()

    @patch('fastf1.plotting._plotting._enable_fastf1_color_scheme')
    def test_skip_color_scheme_when_none(self, mock_enable_color_scheme):
        """Test _enable_fastf1_color_scheme is not called when color_scheme=None"""
        setup_mpl(mpl_timedelta_support=False, color_scheme=None)

        mock_enable_color_scheme.assert_not_called()


class TestEnableTimple:
    """Tests for _enable_timple function"""

    @patch('fastf1.plotting._plotting.timple')
    def test_enable_timple_creates_and_enables(self, mock_timple_module):
        """Test that _enable_timple creates Timple object and calls enable (lines 72, 79, 82)"""
        mock_timple_instance = MagicMock()
        mock_timple_module.Timple.return_value = mock_timple_instance

        _enable_timple()

        # Check that Timple was instantiated with correct arguments (line 79)
        mock_timple_module.Timple.assert_called_once_with(
            converter='concise',
            formatter_args={
                'show_offset_zero': False,
                'formats': [
                    "%d %day",
                    "%H:00",
                    "%H:%m",
                    "%M:%s.0",
                    "%M:%s.%ms"
                ]
            }
        )

        # Check that enable was called (line 82)
        mock_timple_instance.enable.assert_called_once()


class TestEnableFastf1ColorScheme:
    """Tests for _enable_fastf1_color_scheme function"""

    @patch('fastf1.plotting._plotting.plt')
    @patch('fastf1.plotting._plotting.cycler')
    def test_sets_all_rcparams(self, mock_cycler, mock_plt):
        """Test that all plt.rcParams are set correctly (lines 86-105)"""
        mock_rcparams = {}
        mock_plt.rcParams = mock_rcparams
        mock_cycler.return_value = 'mocked_cycler'

        _enable_fastf1_color_scheme()

        # Test all the rcParams that should be set (lines 86-105)
        assert mock_rcparams['figure.facecolor'] == '#292625'
        assert mock_rcparams['axes.edgecolor'] == '#2d2928'
        assert mock_rcparams['xtick.color'] == '#f1f2f3'
        assert mock_rcparams['ytick.color'] == '#f1f2f3'
        assert mock_rcparams['axes.labelcolor'] == '#F1f2f3'
        assert mock_rcparams['axes.facecolor'] == '#1e1c1b'
        # Note: axes.titlesize is set twice (line 93 and 97), final value is '19'
        assert mock_rcparams['axes.titlesize'] == '19'
        assert mock_rcparams['font.weight'] == 'medium'
        assert mock_rcparams['text.color'] == '#F1F1F3'
        assert mock_rcparams['axes.titlepad'] == '12'
        assert mock_rcparams['axes.titleweight'] == 'light'
        assert mock_rcparams['axes.prop_cycle'] == 'mocked_cycler'
        assert mock_rcparams['legend.fancybox'] is False
        assert mock_rcparams['legend.facecolor'] == (0.1, 0.1, 0.1, 0.7)
        assert mock_rcparams['legend.edgecolor'] == (0.1, 0.1, 0.1, 0.9)
        assert mock_rcparams['savefig.transparent'] is False
        assert mock_rcparams['axes.axisbelow'] is True

        # Check that cycler was called with the color palette (line 100)
        mock_cycler.assert_called_once_with('color', _COLOR_PALETTE)
