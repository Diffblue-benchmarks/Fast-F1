import logging
import warnings

import pytest

from fastf1.exceptions import FastF1CriticalError
from fastf1.logger import (
    LoggingManager,
    get_logger,
    set_log_level,
    soft_exceptions,
)


class TestLoggingManager:
    def test_get_child_returns_logger(self):
        logger = LoggingManager.get_child('test_child')
        assert isinstance(logger, logging.Logger)
        assert 'fastf1.test_child' in logger.name

    def test_set_level(self):
        original = LoggingManager._console_handler.level
        try:
            LoggingManager.set_level(logging.WARNING)
            assert LoggingManager._console_handler.level == logging.WARNING
        finally:
            LoggingManager.set_level(original)


class TestGetLogger:
    def test_returns_child_logger(self):
        logger = get_logger('mymodule')
        assert isinstance(logger, logging.Logger)
        assert 'fastf1.mymodule' in logger.name


class TestSetLogLevel:
    def test_set_level_with_int(self):
        original = LoggingManager._console_handler.level
        try:
            set_log_level(logging.DEBUG)
            assert LoggingManager._console_handler.level == logging.DEBUG
        finally:
            LoggingManager.set_level(original)

    def test_set_level_with_string(self):
        original = LoggingManager._console_handler.level
        try:
            set_log_level('WARNING')
            assert LoggingManager._console_handler.level == logging.WARNING
        finally:
            LoggingManager.set_level(original)

    def test_set_level_with_lowercase_string(self):
        original = LoggingManager._console_handler.level
        try:
            set_log_level('debug')
            assert LoggingManager._console_handler.level == logging.DEBUG
        finally:
            LoggingManager.set_level(original)


class TestSoftExceptions:
    def test_normal_execution_returns_value(self):
        logger = get_logger('test')
        original_debug = LoggingManager.debug
        LoggingManager.debug = False

        @soft_exceptions('test', 'test error', logger)
        def good_func():
            return 42

        try:
            assert good_func() == 42
        finally:
            LoggingManager.debug = original_debug

    def test_exception_is_caught_in_non_debug_mode(self):
        logger = get_logger('test')
        original_debug = LoggingManager.debug
        LoggingManager.debug = False

        @soft_exceptions('test', 'test error', logger)
        def bad_func():
            raise ValueError("boom")

        try:
            result = bad_func()
            assert result is None
        finally:
            LoggingManager.debug = original_debug

    def test_exception_is_raised_in_debug_mode(self):
        logger = get_logger('test')
        original_debug = LoggingManager.debug
        LoggingManager.debug = True

        @soft_exceptions('test', 'test error', logger)
        def bad_func():
            raise ValueError("boom")

        try:
            with pytest.raises(ValueError, match="boom"):
                bad_func()
        finally:
            LoggingManager.debug = original_debug

    def test_critical_error_always_raised(self):
        logger = get_logger('test')
        original_debug = LoggingManager.debug
        LoggingManager.debug = False

        @soft_exceptions('test', 'test error', logger)
        def critical_func():
            raise FastF1CriticalError("critical!")

        try:
            with pytest.raises(FastF1CriticalError, match="critical!"):
                critical_func()
        finally:
            LoggingManager.debug = original_debug
