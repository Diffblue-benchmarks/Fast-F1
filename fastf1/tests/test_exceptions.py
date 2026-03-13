import warnings

import pytest

import fastf1.exceptions as exc


class TestExceptionHierarchy:
    def test_data_not_loaded_error_is_exception(self):
        assert issubclass(exc.DataNotLoadedError, Exception)

    def test_ergast_error_is_exception(self):
        assert issubclass(exc.ErgastError, Exception)

    def test_ergast_json_error_is_ergast_error(self):
        assert issubclass(exc.ErgastJsonError, exc.ErgastError)

    def test_ergast_invalid_request_is_ergast_error(self):
        assert issubclass(exc.ErgastInvalidRequestError, exc.ErgastError)

    def test_no_lap_data_error_has_default_message(self):
        err = exc.NoLapDataError()
        assert "Failed to load session" in str(err)

    def test_fuzzy_match_error_is_value_error(self):
        assert issubclass(exc.FuzzyMatchError, ValueError)

    def test_fastf1_critical_error_is_runtime_error(self):
        assert issubclass(exc.FastF1CriticalError, RuntimeError)

    def test_rate_limit_exceeded_is_critical(self):
        assert issubclass(exc.RateLimitExceededError, exc.FastF1CriticalError)


class TestDeprecatedExceptions:
    def test_invalid_session_error_deprecated(self):
        with warnings.catch_warnings():
            warnings.simplefilter("always")
            with pytest.warns(match="deprecated"):
                cls = exc.InvalidSessionError
        assert issubclass(cls, Exception)

    def test_nonexistent_attribute_raises(self):
        with pytest.raises(AttributeError):
            _ = exc.SomethingThatDoesNotExist
