import warnings

import pytest

import fastf1


class TestModuleInit:
    def test_version_exists(self):
        assert hasattr(fastf1, '__version__')
        assert isinstance(fastf1.__version__, str)

    def test_version_short_exists(self):
        assert hasattr(fastf1, '__version_short__')
        assert isinstance(fastf1.__version_short__, str)

    def test_deprecated_rate_limit_error_access(self):
        with pytest.warns(match="deprecated"):
            cls = fastf1.RateLimitExceededError
        from fastf1.exceptions import RateLimitExceededError
        assert cls is RateLimitExceededError

    def test_nonexistent_attribute_raises(self):
        with pytest.raises(AttributeError):
            _ = fastf1.DoesNotExistAtAll
