import io
import logging
import multiprocessing
from unittest import mock

import pytest

from fastf1.testing import (
    LogOutputHandle,
    SubprocessTestError,
    capture_log,
    run_in_subprocess
)
import fastf1.testing


class TestRunInSubprocess:
    """Test the run_in_subprocess function for subprocess execution."""

    def test_run_in_subprocess_success(self):
        """Test run_in_subprocess executes function successfully."""
        # Reset the global flag to test the configuration path
        original_flag = fastf1.testing._MP_CONFIGURED
        fastf1.testing._MP_CONFIGURED = False

        try:
            # Simple function that runs successfully
            def simple_func(value):
                # Simple function that just returns
                return value

            # Mock set_start_method to avoid RuntimeError
            with mock.patch('multiprocessing.set_start_method') as mock_set_method:
                # This should execute without error (covers lines 18, 30, 31, 34, 36, 37, 38)
                run_in_subprocess(simple_func, 42)

                # Verify set_start_method was called with 'spawn'
                mock_set_method.assert_called_once_with('spawn')

            # Verify the flag was set
            assert fastf1.testing._MP_CONFIGURED is True
        finally:
            fastf1.testing._MP_CONFIGURED = original_flag

    def test_run_in_subprocess_with_kwargs(self):
        """Test run_in_subprocess with keyword arguments."""
        def func_with_kwargs(value, **kwargs):
            # Simple function that returns
            return value

        # Mock to avoid RuntimeError on already configured context
        with mock.patch('multiprocessing.set_start_method'):
            # Test with keyword arguments (covers lines 36, 37, 38)
            run_in_subprocess(func_with_kwargs, 10, foo='bar', baz=123)

    def test_run_in_subprocess_raises_error(self):
        """Test run_in_subprocess raises SubprocessTestError on failure."""
        def failing_func():
            raise ValueError('This should fail')

        # Mock to avoid RuntimeError on already configured context
        with mock.patch('multiprocessing.set_start_method'):
            # Should raise SubprocessTestError when subprocess exits with non-zero code
            # (covers lines 39, 40)
            with pytest.raises(SubprocessTestError):
                run_in_subprocess(failing_func)

    def test_run_in_subprocess_with_system_exit(self):
        """Test run_in_subprocess handles SystemExit with non-zero code."""
        def exit_func():
            import sys
            sys.exit(1)

        # Mock to avoid RuntimeError on already configured context
        with mock.patch('multiprocessing.set_start_method'):
            # Should raise SubprocessTestError when subprocess exits with non-zero code
            # (covers lines 39, 40)
            with pytest.raises(SubprocessTestError):
                run_in_subprocess(exit_func)


class TestLogOutputHandle:
    """Test the LogOutputHandle class for capturing log output."""

    def test_init(self):
        """Test LogOutputHandle initialization."""
        stream = io.StringIO()
        handler = logging.StreamHandler(stream=stream)

        # Test initialization (covers lines 54, 55, 56)
        log_handle = LogOutputHandle(handler, stream)

        assert log_handle.stream_handler is handler
        assert log_handle.stream is stream

    def test_text_property(self):
        """Test LogOutputHandle.text property returns captured output."""
        stream = io.StringIO()
        handler = logging.StreamHandler(stream=stream)
        log_handle = LogOutputHandle(handler, stream)

        # Write some data to the stream via the handler
        handler.emit(logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Test message',
            args=(),
            exc_info=None
        ))

        # Test text property (covers lines 59, 62, 63)
        text = log_handle.text

        assert 'Test message' in text

    def test_text_property_flushes_handler(self):
        """Test LogOutputHandle.text flushes handler before reading."""
        stream = io.StringIO()
        handler = logging.StreamHandler(stream=stream)
        handler.setFormatter(logging.Formatter('%(message)s'))
        log_handle = LogOutputHandle(handler, stream)

        # Add a log record
        logger = logging.getLogger('test_flush')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.info('Flush test message')

        # Access text property which should flush (covers lines 62, 63)
        text = log_handle.text

        assert 'Flush test message' in text


class TestCaptureLog:
    """Test the capture_log function for capturing logging output."""

    def test_capture_log_default_level(self):
        """Test capture_log with default INFO level."""
        # Capture the initial state
        logger = logging.getLogger()
        original_handlers = logger.handlers[:]
        original_level = logger.level

        try:
            # Test capture_log with default level (covers lines 66, 79, 80, 81, 82, 83, 84, 85, 86, 88)
            log_handle = capture_log()

            assert isinstance(log_handle, LogOutputHandle)
            assert logger.level == logging.INFO

            # Test that logging works
            test_logger = logging.getLogger('test')
            test_logger.info('Test info message')

            text = log_handle.text
            assert 'Test info message' in text

        finally:
            # Restore logger state
            logger.setLevel(original_level)
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            for handler in original_handlers:
                logger.addHandler(handler)

    def test_capture_log_custom_level(self):
        """Test capture_log with custom log level."""
        logger = logging.getLogger()
        original_handlers = logger.handlers[:]
        original_level = logger.level

        try:
            # Test with WARNING level (covers lines 79, 80, 85)
            log_handle = capture_log(level=logging.WARNING)

            assert logger.level == logging.WARNING

            # INFO should not be captured
            test_logger = logging.getLogger('test')
            test_logger.info('This should not appear')
            test_logger.warning('This should appear')

            text = log_handle.text
            assert 'This should not appear' not in text
            assert 'This should appear' in text

        finally:
            # Restore logger state
            logger.setLevel(original_level)
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            for handler in original_handlers:
                logger.addHandler(handler)

    def test_capture_log_removes_existing_handlers(self):
        """Test capture_log removes existing handlers."""
        logger = logging.getLogger()
        original_handlers = logger.handlers[:]
        original_level = logger.level

        try:
            # Add a custom dummy handler that we can identify
            class CustomTestHandler(logging.Handler):
                pass

            custom_handler = CustomTestHandler()
            logger.addHandler(custom_handler)

            # Verify custom handler is present
            custom_handlers_before = [h for h in logger.handlers if isinstance(h, CustomTestHandler)]
            assert len(custom_handlers_before) == 1

            # capture_log should remove all existing handlers (covers lines 82, 83)
            log_handle = capture_log()

            # Custom handler should be removed
            custom_handlers_after = [h for h in logger.handlers if isinstance(h, CustomTestHandler)]
            assert len(custom_handlers_after) == 0

            # The new stream handler should be present
            assert log_handle.stream_handler in logger.handlers

        finally:
            # Restore logger state
            logger.setLevel(original_level)
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            for handler in original_handlers:
                logger.addHandler(handler)

    def test_capture_log_returns_handle(self):
        """Test capture_log returns LogOutputHandle instance."""
        logger = logging.getLogger()
        original_handlers = logger.handlers[:]
        original_level = logger.level

        try:
            # Test return value (covers line 88)
            log_handle = capture_log()

            assert isinstance(log_handle, LogOutputHandle)
            assert isinstance(log_handle.stream_handler, logging.StreamHandler)
            assert isinstance(log_handle.stream, io.StringIO)

        finally:
            # Restore logger state
            logger.setLevel(original_level)
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            for handler in original_handlers:
                logger.addHandler(handler)
