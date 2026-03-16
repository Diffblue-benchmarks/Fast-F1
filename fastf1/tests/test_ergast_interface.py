import json
import warnings
from unittest import mock

import pytest

import fastf1.ergast.interface as interface
import fastf1.ergast.structure as API
from fastf1 import exceptions


class TestModuleGetattr:
    """Test the deprecated module-level __getattr__ function."""

    def test_getattr_ergast_error_warning(self):
        """Test accessing deprecated ErgastError via __getattr__."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = interface.__getattr__("ErgastError")
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            assert result == exceptions.ErgastError

    def test_getattr_invalid_attribute(self):
        """Test accessing invalid attribute raises AttributeError."""
        with pytest.raises(AttributeError, match="has no attribute"):
            interface.__getattr__("NonExistentAttribute")


class TestErgastResponseMixin:
    """Test ErgastResponseMixin class methods."""

    def test_ergast_constructor_property(self):
        """Test _ergast_constructor property returns Ergast class."""
        mixin = interface.ErgastResponseMixin(
            response_headers={},
            query_filters={},
            metadata={},
            selectors={}
        )
        assert mixin._ergast_constructor == interface.Ergast

    def test_total_results_with_missing_header(self):
        """Test total_results when 'total' header is missing."""
        mixin = interface.ErgastResponseMixin(
            response_headers={},
            query_filters={},
            metadata={},
            selectors={}
        )
        assert mixin.total_results == 0

    def test_is_complete_with_nonzero_offset(self):
        """Test is_complete returns False when offset is non-zero."""
        mixin = interface.ErgastResponseMixin(
            response_headers={'offset': '10', 'limit': '100', 'total': '50'},
            query_filters={},
            metadata={},
            selectors={}
        )
        assert mixin.is_complete is False

    def test_is_complete_with_limit_less_than_total(self):
        """Test is_complete returns False when limit < total."""
        mixin = interface.ErgastResponseMixin(
            response_headers={'offset': '0', 'limit': '10', 'total': '50'},
            query_filters={},
            metadata={},
            selectors={}
        )
        assert mixin.is_complete is False

    def test_is_complete_true(self):
        """Test is_complete returns True when limit >= total and offset is 0."""
        mixin = interface.ErgastResponseMixin(
            response_headers={'offset': '0', 'limit': '100', 'total': '50'},
            query_filters={},
            metadata={},
            selectors={}
        )
        assert mixin.is_complete is True

    def test_get_next_result_page_no_more_data(self):
        """Test get_next_result_page raises ValueError when no more data."""
        mixin = interface.ErgastResponseMixin(
            response_headers={'offset': '40', 'limit': '30', 'total': '50'},
            query_filters={},
            metadata={},
            selectors={}
        )
        with pytest.raises(ValueError, match="No more data after this response"):
            mixin.get_next_result_page()

    @mock.patch.object(interface.Ergast, '_build_default_result')
    def test_get_next_result_page_success(self, mock_build):
        """Test get_next_result_page returns next page successfully."""
        mock_build.return_value = mock.MagicMock()
        mixin = interface.ErgastResponseMixin(
            response_headers={'offset': '0', 'limit': '30', 'total': '100'},
            query_filters={},
            metadata={'endpoint': 'test', 'table': 'test'},
            selectors={'season': 2020}
        )
        result = mixin.get_next_result_page()
        mock_build.assert_called_once()
        assert result is not None

    def test_get_prev_result_page_no_more_data(self):
        """Test get_prev_result_page raises ValueError when offset is 0."""
        mixin = interface.ErgastResponseMixin(
            response_headers={'offset': '0', 'limit': '30', 'total': '100'},
            query_filters={},
            metadata={},
            selectors={}
        )
        with pytest.raises(ValueError, match="No more data before this response"):
            mixin.get_prev_result_page()

    @mock.patch.object(interface.Ergast, '_build_default_result')
    def test_get_prev_result_page_success(self, mock_build):
        """Test get_prev_result_page returns previous page successfully."""
        mock_build.return_value = mock.MagicMock()
        mixin = interface.ErgastResponseMixin(
            response_headers={'offset': '50', 'limit': '30', 'total': '100'},
            query_filters={},
            metadata={'endpoint': 'test', 'table': 'test'},
            selectors={'season': 2020}
        )
        result = mixin.get_prev_result_page()
        mock_build.assert_called_once()
        assert result is not None


class TestErgastResultFrame:
    """Test ErgastResultFrame class methods."""

    def test_init_with_both_data_and_response(self):
        """Test __init__ raises ValueError when both data and response provided."""
        with pytest.raises(ValueError, match="Cannot initialize"):
            interface.ErgastResultFrame(
                data=[{'test': 'data'}],
                response=[{'test': 'response'}],
                category={}
            )

    def test_prepare_response_with_finalizer(self):
        """Test _prepare_response calls finalizer when present in category."""
        def mock_finalizer(data):
            return [{'finalized': True}]

        category = {
            'method': lambda nested, cat, flat, cast: flat.update(nested),
            'sub': [],
            'finalize': mock_finalizer
        }
        response = [{'test': 'data'}]
        result = interface.ErgastResultFrame._prepare_response(response, category, True)
        assert result == [{'finalized': True}]

    def test_constructor_sliced_horizontal(self):
        """Test _constructor_sliced_horizontal returns ErgastResultSeries."""
        frame = interface.ErgastResultFrame(data=[])
        assert frame._constructor_sliced_horizontal == interface.ErgastResultSeries


class TestErgastRawResponse:
    """Test ErgastRawResponse class methods."""

    def test_init_without_auto_cast(self):
        """Test __init__ without auto_cast does not call _prepare_response."""
        query_result = [{'test': 'data'}]
        category = {'type': list, 'map': {}, 'sub': []}
        response = interface.ErgastRawResponse(
            query_result=query_result,
            category=category,
            auto_cast=False,
            response_headers={},
            query_filters={},
            metadata={},
            selectors={}
        )
        assert response == query_result

    def test_prepare_response(self):
        """Test _prepare_response calls _auto_cast."""
        category = {'type': list, 'map': {}, 'sub': [], 'name': 'test'}
        query_result = [{'key': '123'}]
        with mock.patch.object(interface.ErgastRawResponse, '_auto_cast', return_value=query_result):
            result = interface.ErgastRawResponse._prepare_response(query_result, category)
            assert result == query_result

    def test_auto_cast_with_list_type(self):
        """Test _auto_cast handles list type category."""
        category = {'type': list, 'map': {'key': {'type': int}}, 'sub': []}
        data = [{'key': '123'}, {'key': '456'}]
        result = interface.ErgastRawResponse._auto_cast(data, category)
        assert result[0]['key'] == 123
        assert result[1]['key'] == 456

    def test_auto_cast_with_dict_type(self):
        """Test _auto_cast handles dict type category."""
        category = {'type': dict, 'map': {'key': {'type': int}}, 'sub': []}
        data = {'key': '789'}
        result = interface.ErgastRawResponse._auto_cast(data, category)
        assert result['key'] == 789

    def test_auto_cast_item_with_missing_key(self):
        """Test _auto_cast_item handles missing keys gracefully."""
        category = {'type': dict, 'map': {'key': {'type': int}}, 'sub': []}
        data = {'other': 'value'}
        result = interface.ErgastRawResponse._auto_cast_item(data, category)
        assert 'key' not in result
        assert result['other'] == 'value'

    def test_auto_cast_item_with_subcategory(self):
        """Test _auto_cast_item handles subcategories."""
        subcategory = {'name': 'subdata', 'type': dict, 'map': {'subkey': {'type': float}}, 'sub': []}
        category = {'type': dict, 'map': {}, 'sub': [subcategory]}
        data = {'subdata': {'subkey': '3.14'}}
        result = interface.ErgastRawResponse._auto_cast_item(data, category)
        assert result['subdata']['subkey'] == 3.14

    def test_auto_cast_item_with_missing_subcategory(self):
        """Test _auto_cast_item handles missing subcategory gracefully."""
        subcategory = {'name': 'missing', 'type': dict, 'map': {}, 'sub': []}
        category = {'type': dict, 'map': {}, 'sub': [subcategory]}
        data = {'other': 'value'}
        result = interface.ErgastRawResponse._auto_cast_item(data, category)
        assert 'missing' not in result


class TestErgastSimpleResponse:
    """Test ErgastSimpleResponse class methods."""

    def test_constructor_returns_ergast_result_frame(self):
        """Test _constructor property returns ErgastResultFrame."""
        response = interface.ErgastSimpleResponse(
            response_headers={},
            query_filters={},
            metadata={},
            selectors={},
            data=[]
        )
        assert response._constructor == interface.ErgastResultFrame


class TestErgast:
    """Test Ergast class methods."""

    def test_build_url_with_grid_position(self):
        """Test _build_url with grid_position parameter."""
        url = interface.Ergast._build_url('results', grid_position=1)
        assert '/grid/1' in url

    def test_build_url_with_fastest_rank(self):
        """Test _build_url with fastest_rank parameter."""
        url = interface.Ergast._build_url('results', fastest_rank=1)
        assert '/fastest/1' in url

    def test_build_url_driver_as_endpoint(self):
        """Test _build_url with driver as endpoint."""
        url = interface.Ergast._build_url('drivers', driver='hamilton')
        assert 'drivers/hamilton' in url
        assert url.count('drivers') == 1

    def test_build_url_driver_as_selector(self):
        """Test _build_url with driver as selector."""
        url = interface.Ergast._build_url('results', driver='hamilton')
        assert '/drivers/hamilton' in url
        assert '/results' in url

    def test_build_url_constructor_as_endpoint(self):
        """Test _build_url with constructor as endpoint."""
        url = interface.Ergast._build_url('constructors', constructor='ferrari')
        assert 'constructors/ferrari' in url
        assert url.count('constructors') == 1

    def test_build_url_constructor_as_selector(self):
        """Test _build_url with constructor as selector."""
        url = interface.Ergast._build_url('results', constructor='ferrari')
        assert '/constructors/ferrari' in url
        assert '/results' in url

    def test_build_url_circuit_as_endpoint(self):
        """Test _build_url with circuit as endpoint."""
        url = interface.Ergast._build_url('circuits', circuit='monza')
        assert 'circuits/monza' in url
        assert url.count('circuits') == 1

    def test_build_url_circuit_as_selector(self):
        """Test _build_url with circuit as selector."""
        url = interface.Ergast._build_url('results', circuit='monza')
        assert '/circuits/monza' in url
        assert '/results' in url

    def test_build_url_status_as_endpoint(self):
        """Test _build_url with status as endpoint."""
        url = interface.Ergast._build_url('status', status='1')
        assert 'status/1' in url
        assert url.count('status') == 1

    def test_build_url_status_as_selector(self):
        """Test _build_url with status as selector."""
        url = interface.Ergast._build_url('results', status='1')
        assert '/status/1' in url
        assert '/results' in url

    def test_build_url_standings_position_driver(self):
        """Test _build_url with standings_position for driverStandings."""
        url = interface.Ergast._build_url('driverStandings', standings_position=1)
        assert 'driverStandings/1' in url

    def test_build_url_standings_position_constructor(self):
        """Test _build_url with standings_position for constructorStandings."""
        url = interface.Ergast._build_url('constructorStandings', standings_position=1)
        assert 'constructorStandings/1' in url

    def test_build_url_results_position_as_endpoint(self):
        """Test _build_url with results_position for results endpoint."""
        url = interface.Ergast._build_url('results', results_position=1)
        assert 'results/1' in url

    def test_build_url_results_position_as_selector(self):
        """Test _build_url with results_position as selector."""
        url = interface.Ergast._build_url('drivers', results_position=1)
        assert '/results/1' in url

    def test_build_url_lap_number_as_endpoint(self):
        """Test _build_url with lap_number as endpoint."""
        url = interface.Ergast._build_url('laps', lap_number=5)
        assert 'laps/5' in url

    def test_build_url_lap_number_as_selector(self):
        """Test _build_url with lap_number as selector."""
        url = interface.Ergast._build_url('drivers', lap_number=5)
        assert '/laps/5' in url

    def test_build_url_stop_number_as_endpoint(self):
        """Test _build_url with stop_number as endpoint."""
        url = interface.Ergast._build_url('pitstops', stop_number=2)
        assert 'pitstops/2' in url

    def test_build_url_stop_number_as_selector(self):
        """Test _build_url with stop_number as selector."""
        url = interface.Ergast._build_url('drivers', stop_number=2)
        assert '/pitstops/2' in url

    @mock.patch('fastf1.req.Cache.requests_get')
    def test_get_json_parse_error(self, mock_get):
        """Test _get handles JSON parse errors."""
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'invalid json'
        mock_get.return_value = mock_response

        with mock.patch('fastf1.req.Cache.delete_response') as mock_delete:
            with pytest.raises(exceptions.ErgastJsonError, match="Failed to parse"):
                interface.Ergast._get('http://test.url', {})
            mock_delete.assert_called_once_with('http://test.url')

    @mock.patch('fastf1.req.Cache.requests_get')
    def test_get_invalid_request(self, mock_get):
        """Test _get handles invalid request responses."""
        mock_response = mock.MagicMock()
        mock_response.status_code = 404
        mock_response.reason = 'Not Found'
        mock_get.return_value = mock_response

        with pytest.raises(exceptions.ErgastInvalidRequestError, match="Invalid request"):
            interface.Ergast._get('http://test.url', {})

    @mock.patch.object(interface.Ergast, '_get')
    @mock.patch.object(interface.Ergast, '_build_url')
    def test_build_result_raw_type(self, mock_build_url, mock_get):
        """Test _build_result with raw result type."""
        mock_build_url.return_value = 'http://test.url'
        mock_get.return_value = {
            'MRData': {
                'total': '10',
                'RaceTable': {
                    'Races': [{'raceName': 'Test Race'}]
                }
            }
        }
        category = {'name': 'Races', 'type': list, 'map': {}, 'sub': []}
        result = interface.Ergast._build_result(
            endpoint='races',
            table='RaceTable',
            category=category,
            subcategory=None,
            result_type='raw',
            auto_cast=True,
            limit=10,
            offset=0,
            selectors={}
        )
        assert isinstance(result, interface.ErgastRawResponse)

    @mock.patch.object(interface.Ergast, '_get')
    @mock.patch.object(interface.Ergast, '_build_url')
    def test_build_result_pandas_simple(self, mock_build_url, mock_get):
        """Test _build_result with pandas result type and no subcategory."""
        mock_build_url.return_value = 'http://test.url'
        mock_get.return_value = {
            'MRData': {
                'total': '10',
                'SeasonTable': {
                    'Seasons': [{'season': '2020'}]
                }
            }
        }
        category = {
            'name': 'Seasons',
            'type': list,
            'map': {'season': {'type': int}},
            'sub': [],
            'method': lambda nested, cat, flat, cast: flat.update(nested)
        }
        result = interface.Ergast._build_result(
            endpoint='seasons',
            table='SeasonTable',
            category=category,
            subcategory=None,
            result_type='pandas',
            auto_cast=True,
            limit=10,
            offset=0,
            selectors={}
        )
        assert isinstance(result, interface.ErgastSimpleResponse)
