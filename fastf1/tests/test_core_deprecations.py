import warnings

import pytest

import fastf1.core as core


class TestCoreDeprecatedAccess:
    def test_no_lap_data_error_deprecated(self):
        with pytest.warns(match="deprecated"):
            cls = core.NoLapDataError
        from fastf1.exceptions import NoLapDataError
        assert cls is NoLapDataError

    def test_data_not_loaded_error_deprecated(self):
        with pytest.warns(match="deprecated"):
            cls = core.DataNotLoadedError
        from fastf1.exceptions import DataNotLoadedError
        assert cls is DataNotLoadedError

    def test_invalid_session_error_deprecated(self):
        with pytest.warns(match="deprecated"):
            cls = core.InvalidSessionError

    def test_nonexistent_attribute_raises(self):
        with pytest.raises(AttributeError):
            _ = core.DoesNotExist
