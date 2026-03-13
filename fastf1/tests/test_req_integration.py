"""Integration tests for req.py Cache with mocked HTTP."""
import os
import pickle
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from fastf1.req import Cache


class TestCacheEnableCache:
    def test_enable_cache_valid_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = Cache._CACHE_DIR
            try:
                Cache.enable_cache(tmpdir, use_requests_cache=False)
                assert Cache._CACHE_DIR == tmpdir
            finally:
                Cache._CACHE_DIR = orig_dir

    def test_enable_cache_nonexistent_dir_raises(self):
        with pytest.raises(NotADirectoryError):
            Cache.enable_cache('/nonexistent/path/1234567890')

    def test_enable_cache_force_renew(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = Cache._CACHE_DIR
            orig_renew = Cache._FORCE_RENEW
            try:
                Cache.enable_cache(tmpdir, force_renew=True,
                                   use_requests_cache=False)
                assert Cache._FORCE_RENEW is True
            finally:
                Cache._CACHE_DIR = orig_dir
                Cache._FORCE_RENEW = orig_renew

    def test_enable_cache_ignore_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = Cache._CACHE_DIR
            orig_ignore = Cache._IGNORE_VERSION
            try:
                Cache.enable_cache(tmpdir, ignore_version=True,
                                   use_requests_cache=False)
                assert Cache._IGNORE_VERSION is True
            finally:
                Cache._CACHE_DIR = orig_dir
                Cache._IGNORE_VERSION = orig_ignore


class TestCacheRequestsGet:
    @patch.object(Cache, '_enable_default_cache')
    def test_uncached_request(self, mock_enable):
        orig_session = Cache._requests_session
        orig_cached = Cache._requests_session_cached
        orig_disabled = Cache._tmp_disabled

        try:
            Cache._requests_session_cached = None
            Cache._tmp_disabled = False

            mock_session = MagicMock()
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_session.get.return_value = mock_resp
            Cache._requests_session = mock_session

            result = Cache.requests_get('http://example.com/test')
            assert result.status_code == 200
            mock_session.get.assert_called_once()
        finally:
            Cache._requests_session = orig_session
            Cache._requests_session_cached = orig_cached
            Cache._tmp_disabled = orig_disabled

    @patch.object(Cache, '_enable_default_cache')
    def test_requests_get_when_disabled(self, mock_enable):
        orig_session = Cache._requests_session
        orig_disabled = Cache._tmp_disabled

        try:
            Cache._tmp_disabled = True

            mock_session = MagicMock()
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_session.get.return_value = mock_resp
            Cache._requests_session = mock_session

            result = Cache.requests_get('http://example.com/test')
            mock_session.get.assert_called_once()
        finally:
            Cache._requests_session = orig_session
            Cache._tmp_disabled = orig_disabled


class TestCacheRequestsPost:
    @patch.object(Cache, '_enable_default_cache')
    def test_uncached_post(self, mock_enable):
        orig_session = Cache._requests_session
        orig_cached = Cache._requests_session_cached
        orig_disabled = Cache._tmp_disabled

        try:
            Cache._requests_session_cached = None
            Cache._tmp_disabled = False

            mock_session = MagicMock()
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_session.post.return_value = mock_resp
            Cache._requests_session = mock_session

            result = Cache.requests_post('http://example.com/test',
                                         data='body')
            assert result.status_code == 200
            mock_session.post.assert_called_once()
        finally:
            Cache._requests_session = orig_session
            Cache._requests_session_cached = orig_cached
            Cache._tmp_disabled = orig_disabled


class TestCacheClearCache:
    def test_clear_cache_removes_ff1pkl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # create some .ff1pkl files
            path1 = os.path.join(tmpdir, 'test.ff1pkl')
            path2 = os.path.join(tmpdir, 'other.txt')
            with open(path1, 'w') as f:
                f.write('test')
            with open(path2, 'w') as f:
                f.write('test')

            Cache.clear_cache(cache_dir=tmpdir)
            assert not os.path.exists(path1)
            assert os.path.exists(path2)  # non-.ff1pkl kept

    def test_clear_cache_nonexistent_raises(self):
        with pytest.raises(NotADirectoryError):
            Cache.clear_cache(cache_dir='/nonexistent/path/1234567890')


class TestCacheGetCacheInfo:
    def test_no_cache_returns_none(self):
        orig = Cache._CACHE_DIR
        try:
            Cache._CACHE_DIR = None
            path, size = Cache.get_cache_info()
            assert path is None
            assert size is None
        finally:
            Cache._CACHE_DIR = orig

    def test_with_cache_returns_info(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orig = Cache._CACHE_DIR
            try:
                Cache._CACHE_DIR = tmpdir
                path, size = Cache.get_cache_info()
                assert path == tmpdir
                assert isinstance(size, int)
            finally:
                Cache._CACHE_DIR = orig


class TestCacheWriteAndRead:
    def test_write_cache_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test.ff1pkl')
            Cache._write_cache({'test': 42}, path)
            assert os.path.exists(path)

            with open(path, 'rb') as f:
                cached = pickle.load(f)
            assert cached['data'] == {'test': 42}
            assert cached['version'] == Cache._API_CORE_VERSION


class TestCacheMetaRepr:
    def test_repr_no_cache(self):
        orig = Cache._CACHE_DIR
        try:
            Cache._CACHE_DIR = None
            r = repr(Cache)
            assert 'not configured' in r
        finally:
            Cache._CACHE_DIR = orig

    def test_repr_with_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orig = Cache._CACHE_DIR
            try:
                Cache._CACHE_DIR = tmpdir
                r = repr(Cache)
                assert tmpdir in r
            finally:
                Cache._CACHE_DIR = orig
