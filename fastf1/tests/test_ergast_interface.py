import warnings

import pytest

import fastf1.ergast.interface as ergast_iface


class TestErgastInterfaceDeprecations:
    def test_ergast_error_deprecated(self):
        with pytest.warns(match="deprecated"):
            cls = ergast_iface.ErgastError
        from fastf1.exceptions import ErgastError
        assert cls is ErgastError

    def test_ergast_json_error_deprecated(self):
        with pytest.warns(match="deprecated"):
            cls = ergast_iface.ErgastJsonError
        from fastf1.exceptions import ErgastJsonError
        assert cls is ErgastJsonError

    def test_ergast_invalid_request_deprecated(self):
        with pytest.warns(match="deprecated"):
            cls = ergast_iface.ErgastInvalidRequestError
        from fastf1.exceptions import ErgastInvalidRequestError
        assert cls is ErgastInvalidRequestError

    def test_nonexistent_attribute_raises(self):
        with pytest.raises(AttributeError):
            _ = ergast_iface.DoesNotExist


class TestErgastResponseMixin:
    def test_total_results(self):
        mixin = ergast_iface.ErgastResponseMixin(
            response_headers={'total': '42'},
            query_filters={},
            metadata={},
            selectors={}
        )
        assert mixin.total_results == 42

    def test_total_results_default(self):
        mixin = ergast_iface.ErgastResponseMixin(
            response_headers={},
            query_filters={},
            metadata={},
            selectors={}
        )
        assert mixin.total_results == 0

    def test_is_complete_true(self):
        mixin = ergast_iface.ErgastResponseMixin(
            response_headers={
                'offset': '0', 'limit': '100', 'total': '50'
            },
            query_filters={},
            metadata={},
            selectors={}
        )
        assert mixin.is_complete is True

    def test_is_complete_false_nonzero_offset(self):
        mixin = ergast_iface.ErgastResponseMixin(
            response_headers={
                'offset': '10', 'limit': '100', 'total': '50'
            },
            query_filters={},
            metadata={},
            selectors={}
        )
        assert mixin.is_complete is False

    def test_is_complete_false_limit_less_than_total(self):
        mixin = ergast_iface.ErgastResponseMixin(
            response_headers={
                'offset': '0', 'limit': '30', 'total': '50'
            },
            query_filters={},
            metadata={},
            selectors={}
        )
        assert mixin.is_complete is False
