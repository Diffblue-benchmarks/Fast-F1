import logging
from unittest import mock

import pytest

from fastf1 import logger
from fastf1.exceptions import FastF1CriticalError


class TestLoggingManager:
    """Test the LoggingManager class for logging configuration."""

    def test_set_level(self):
        """Test set_level method sets console handler level."""
        # Set to WARNING level
        logger.LoggingManager.set_level(logging.WARNING)
        assert logger.LoggingManager._console_handler.level == logging.WARNING

        # Set to DEBUG level
        logger.LoggingManager.set_level(logging.DEBUG)
        assert logger.LoggingManager._console_handler.level == logging.DEBUG

        # Reset to INFO for other tests
        logger.LoggingManager.set_level(logging.INFO)


class TestSetLogLevel:
    """Test the set_log_level function with various input types."""

    def test_set_log_level_with_string(self):
        """Test set_log_level with string input converts to level."""
        # Test with string input (covers lines 81-83)
        logger.set_log_level('WARNING')
        assert logger.LoggingManager._console_handler.level == logging.WARNING

        logger.set_log_level('DEBUG')
        assert logger.LoggingManager._console_handler.level == logging.DEBUG

        logger.set_log_level('ERROR')
        assert logger.LoggingManager._console_handler.level == logging.ERROR

        # Reset to INFO for other tests
        logger.set_log_level(logging.INFO)

    def test_set_log_level_with_int(self):
        """Test set_log_level with integer input."""
        logger.set_log_level(logging.WARNING)
        assert logger.LoggingManager._console_handler.level == logging.WARNING

        # Reset to INFO for other tests
        logger.set_log_level(logging.INFO)


class TestSoftExceptions:
    """Test the soft_exceptions decorator for error handling."""

    def test_soft_exceptions_with_success(self):
        """Test soft_exceptions when function executes successfully."""
        test_logger = logging.getLogger('test')

        # Save original debug state
        original_debug = logger.LoggingManager.debug

        try:
            # Set debug to False to trigger the try-except block (line 111)
            logger.LoggingManager.debug = False

            @logger.soft_exceptions('test_data', 'Test failed', test_logger)
            def successful_function():
                return 'success'

            # This should execute without error (covers line 112)
            result = successful_function()
            assert result == 'success'
        finally:
            # Restore original debug state
            logger.LoggingManager.debug = original_debug

    def test_soft_exceptions_with_critical_error(self):
        """Test soft_exceptions re-raises FastF1CriticalError."""
        test_logger = logging.getLogger('test')

        # Save original debug state
        original_debug = logger.LoggingManager.debug

        try:
            # Set debug to False to trigger error handling (lines 111, 113, 115)
            logger.LoggingManager.debug = False

            @logger.soft_exceptions('test_data', 'Test failed', test_logger)
            def critical_error_function():
                raise FastF1CriticalError('Critical error occurred')

            # FastF1CriticalError should be re-raised (covers lines 113, 115)
            with pytest.raises(FastF1CriticalError):
                critical_error_function()
        finally:
            # Restore original debug state
            logger.LoggingManager.debug = original_debug

    def test_soft_exceptions_with_regular_exception(self):
        """Test soft_exceptions logs and catches regular exceptions."""
        test_logger = logging.getLogger('test')

        # Save original debug state
        original_debug = logger.LoggingManager.debug

        try:
            # Set debug to False to trigger error handling (lines 111, 116, 117, 118)
            logger.LoggingManager.debug = False

            @logger.soft_exceptions('test_data', 'Test operation failed', test_logger)
            def error_function():
                raise ValueError('Some error occurred')

            # Mock the logger to verify warning and debug are called
            with mock.patch.object(test_logger, 'warning') as mock_warning:
                with mock.patch.object(test_logger, 'debug') as mock_debug:
                    # Should not raise, but log the error (covers lines 116, 117, 118)
                    result = error_function()

                    # Verify result is None (function didn't return anything)
                    assert result is None

                    # Verify warning was called with the message
                    mock_warning.assert_called_once_with('Test operation failed')

                    # Verify debug was called with traceback info
                    mock_debug.assert_called_once()
                    call_args = mock_debug.call_args
                    assert 'Traceback for failure in test_data' in call_args[0][0]
                    assert 'exc_info' in call_args[1]
        finally:
            # Restore original debug state
            logger.LoggingManager.debug = original_debug

    def test_soft_exceptions_with_debug_enabled(self):
        """Test soft_exceptions passes through when debug is enabled."""
        test_logger = logging.getLogger('test')

        # Save original debug state
        original_debug = logger.LoggingManager.debug

        try:
            # Set debug to True to bypass error handling (line 121)
            logger.LoggingManager.debug = True

            @logger.soft_exceptions('test_data', 'Test failed', test_logger)
            def error_function():
                raise ValueError('Some error occurred')

            # With debug=True, exception should propagate
            with pytest.raises(ValueError):
                error_function()
        finally:
            # Restore original debug state
            logger.LoggingManager.debug = original_debug
