"""Tests for plotting/_plotting.py."""
import warnings
from unittest.mock import patch, MagicMock

import pytest


class TestSetupMpl:
    def test_setup_no_args(self):
        from fastf1.plotting._plotting import setup_mpl
        # should not raise
        setup_mpl(mpl_timedelta_support=False, color_scheme=None)

    def test_setup_fastf1_color_scheme(self):
        from fastf1.plotting._plotting import setup_mpl
        setup_mpl(mpl_timedelta_support=False, color_scheme='fastf1')

    def test_setup_timedelta_support(self):
        from fastf1.plotting._plotting import setup_mpl
        setup_mpl(mpl_timedelta_support=True, color_scheme=None)

    def test_deprecated_misc_mpl_mods_warns(self):
        from fastf1.plotting._plotting import setup_mpl
        with pytest.warns(FutureWarning, match="misc_mpl_mods"):
            setup_mpl(mpl_timedelta_support=False, color_scheme=None,
                      misc_mpl_mods=True)


class TestEnableFastf1ColorScheme:
    def test_sets_rcparams(self):
        from matplotlib import pyplot as plt
        from fastf1.plotting._plotting import _enable_fastf1_color_scheme
        _enable_fastf1_color_scheme()
        assert plt.rcParams['figure.facecolor'] == '#292625'
        assert plt.rcParams['text.color'] == '#F1F1F3'


class TestColorPalette:
    def test_palette_is_list(self):
        from fastf1.plotting._plotting import _COLOR_PALETTE
        assert isinstance(_COLOR_PALETTE, list)
        assert len(_COLOR_PALETTE) > 0
        assert all(c.startswith('#') for c in _COLOR_PALETTE)
