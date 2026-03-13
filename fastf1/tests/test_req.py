import time
from unittest.mock import patch

import pytest

from fastf1.exceptions import RateLimitExceededError
from fastf1.req import (
    Cache,
    _CallsPerIntervalLimitRaise,
    _MinIntervalLimitDelay,
    _NoCacheContext,
)


class TestMinIntervalLimitDelay:
    def test_first_call_no_delay(self):
        limiter = _MinIntervalLimitDelay(0.5)
        start = time.time()
        limiter.limit()
        elapsed = time.time() - start
        assert elapsed < 0.1

    def test_rapid_call_causes_delay(self):
        limiter = _MinIntervalLimitDelay(0.2)
        limiter.limit()
        start = time.time()
        limiter.limit()
        elapsed = time.time() - start
        assert elapsed >= 0.15  # allow small tolerance


class TestCallsPerIntervalLimitRaise:
    def test_under_limit_no_error(self):
        limiter = _CallsPerIntervalLimitRaise(5, 60.0, "test limit")
        for _ in range(4):
            limiter.limit()

    def test_exceeding_limit_raises(self):
        limiter = _CallsPerIntervalLimitRaise(3, 60.0, "test limit")
        limiter.limit()
        limiter.limit()
        with pytest.raises(RateLimitExceededError, match="test limit"):
            limiter.limit()


class TestCacheConvertSize:
    def test_zero_bytes(self):
        assert Cache._convert_size(0) == "0B"

    def test_bytes(self):
        result = Cache._convert_size(500)
        assert "B" in result

    def test_kilobytes(self):
        result = Cache._convert_size(1024)
        assert "KB" in result

    def test_megabytes(self):
        result = Cache._convert_size(1024 * 1024)
        assert "MB" in result

    def test_gigabytes(self):
        result = Cache._convert_size(1024 ** 3)
        assert "GB" in result


class TestCacheDataOkForUse:
    def setup_method(self):
        self._orig_force = Cache._FORCE_RENEW
        self._orig_ignore = Cache._IGNORE_VERSION
        self._orig_version = Cache._API_CORE_VERSION

    def teardown_method(self):
        Cache._FORCE_RENEW = self._orig_force
        Cache._IGNORE_VERSION = self._orig_ignore
        Cache._API_CORE_VERSION = self._orig_version

    def test_force_renew_returns_false(self):
        Cache._FORCE_RENEW = True
        Cache._IGNORE_VERSION = False
        cached = {'version': Cache._API_CORE_VERSION, 'data': None}
        assert Cache._data_ok_for_use(cached) is False

    def test_ignore_version_returns_true(self):
        Cache._FORCE_RENEW = False
        Cache._IGNORE_VERSION = True
        cached = {'version': -1, 'data': None}
        assert Cache._data_ok_for_use(cached) is True

    def test_matching_version_returns_true(self):
        Cache._FORCE_RENEW = False
        Cache._IGNORE_VERSION = False
        cached = {'version': Cache._API_CORE_VERSION, 'data': None}
        assert Cache._data_ok_for_use(cached) is True

    def test_mismatched_version_returns_false(self):
        Cache._FORCE_RENEW = False
        Cache._IGNORE_VERSION = False
        cached = {'version': Cache._API_CORE_VERSION + 1, 'data': None}
        assert Cache._data_ok_for_use(cached) is False


class TestCacheCustomFilter:
    def test_filter_rejects_ergast_error(self):
        class FakeResponse:
            text = "Unable to select database"
        assert Cache._custom_cache_filter(FakeResponse()) is False

    def test_filter_accepts_normal_response(self):
        class FakeResponse:
            text = '{"some": "data"}'
        assert Cache._custom_cache_filter(FakeResponse()) is True


class TestNoCacheContext:
    def setup_method(self):
        self._orig = Cache._tmp_disabled

    def teardown_method(self):
        Cache._tmp_disabled = self._orig

    def test_context_disables_and_reenables(self):
        Cache._tmp_disabled = False
        with _NoCacheContext():
            assert Cache._tmp_disabled is True
        assert Cache._tmp_disabled is False

    def test_set_disabled_and_enabled(self):
        Cache._tmp_disabled = False
        Cache.set_disabled()
        assert Cache._tmp_disabled is True
        Cache.set_enabled()
        assert Cache._tmp_disabled is False


class TestCacheGetDefaultPath:
    def test_returns_string_or_none(self):
        result = Cache._get_default_cache_path()
        assert result is None or isinstance(result, str)
