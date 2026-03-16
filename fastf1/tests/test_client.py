import json
import logging
import time
from io import StringIO
from unittest.mock import MagicMock, Mock, patch, mock_open, call

import pytest
from signalrcore.messages.completion_message import CompletionMessage

from fastf1.livetiming.client import messages_from_raw, SignalRClient


class TestMessagesFromRaw:
    """Tests for messages_from_raw function"""

    def test_valid_messages_extraction(self):
        """Test extraction of valid messages from raw SignalR data"""
        raw_data = [
            "{'M': [{'H': 'Streaming', 'A': ['test_message_1']}]}",
            "{'M': [{'H': 'Streaming', 'A': ['test_message_2']}]}"
        ]

        result, errorcount = messages_from_raw(raw_data)

        assert len(result) == 2
        assert result[0] == ['test_message_1']
        assert result[1] == ['test_message_2']
        assert errorcount == 0

    def test_json_decode_errors(self):
        """Test handling of JSON decode errors (lines 33-35)"""
        raw_data = [
            "{'M': [{'H': 'Streaming', 'A': ['valid_message']}]}",
            "invalid json data here",
            "another invalid entry"
        ]

        result, errorcount = messages_from_raw(raw_data)

        assert len(result) == 1
        assert result[0] == ['valid_message']
        assert errorcount == 2

    def test_empty_messages(self):
        """Test data with no messages (line 36)"""
        raw_data = [
            "{'M': []}",
            "{'X': 'some_other_data'}"
        ]

        result, errorcount = messages_from_raw(raw_data)

        assert len(result) == 0
        assert errorcount == 0

    def test_non_streaming_hub(self):
        """Test filtering of non-streaming hub messages (lines 38-39)"""
        raw_data = [
            "{'M': [{'H': 'OtherHub', 'A': ['should_ignore']}]}",
            "{'M': [{'H': 'Streaming', 'A': ['should_include']}]}"
        ]

        result, errorcount = messages_from_raw(raw_data)

        assert len(result) == 1
        assert result[0] == ['should_include']

    def test_message_without_hub(self):
        """Test messages without hub field (line 38)"""
        raw_data = [
            "{'M': [{'A': ['message_without_hub']}]}"
        ]

        result, errorcount = messages_from_raw(raw_data)

        assert len(result) == 0

    def test_string_replacements(self):
        """Test that string replacements work (lines 28-30)"""
        raw_data = [
            "{'M': [{'H': 'Streaming', 'A': [True, False]}]}"
        ]

        result, errorcount = messages_from_raw(raw_data)

        assert len(result) == 1
        assert errorcount == 0

    def test_multiple_messages_per_entry(self):
        """Test multiple messages in single entry (line 37)"""
        raw_data = [
            "{'M': [{'H': 'Streaming', 'A': ['msg1']}, {'H': 'Streaming', 'A': ['msg2']}]}"
        ]

        result, errorcount = messages_from_raw(raw_data)

        assert len(result) == 2
        assert result[0] == ['msg1']
        assert result[1] == ['msg2']


class TestSignalRClientInit:
    """Tests for SignalRClient.__init__"""

    def test_debug_mode_raises_error(self):
        """Test that debug mode raises ValueError (lines 92-93)"""
        with pytest.raises(ValueError) as excinfo:
            SignalRClient("test.txt", debug=True)

        assert "Debug mode is no longer supported" in str(excinfo.value)

    def test_default_initialization(self):
        """Test initialization with default parameters (lines 84-124)"""
        client = SignalRClient("test_output.txt")

        assert client.filename == "test_output.txt"
        assert client.filemode == "w"
        assert client.timeout == 60
        assert client._no_auth is False
        assert client._connection is None
        assert client._is_connected is False
        assert client._output_file is None
        assert client._t_last_message is None
        assert isinstance(client.logger, logging.Logger)
        assert len(client.topics) > 0

    def test_custom_initialization(self):
        """Test initialization with custom parameters (lines 105-107)"""
        client = SignalRClient(
            "custom.txt",
            filemode="a",
            timeout=120,
            no_auth=True
        )

        assert client.filename == "custom.txt"
        assert client.filemode == "a"
        assert client.timeout == 120
        assert client._no_auth is True

    def test_custom_logger(self):
        """Test initialization with custom logger (lines 120-121)"""
        custom_logger = logging.getLogger("CustomLogger")
        client = SignalRClient("test.txt", logger=custom_logger)

        assert client.logger == custom_logger

    def test_default_logger_creation(self):
        """Test default logger creation (lines 114-119)"""
        client = SignalRClient("test.txt")

        assert client.logger.name == "SignalR"
        assert client.logger.level == logging.INFO


class TestSignalRClientOnMessage:
    """Tests for SignalRClient._on_message"""

    def test_completion_message_handling(self):
        """Test handling of CompletionMessage (lines 129-133)"""
        client = SignalRClient("test.txt")
        client._output_file = StringIO()

        result_dict = {
            "key1": "value1",
            "key2": {"nested": "data"}
        }
        msg = CompletionMessage(
            invocation_id="test_id",
            result=result_dict,
            error=None
        )

        with patch('time.time', return_value=1234567890):
            client._on_message(msg)

        assert client._t_last_message == 1234567890
        output = client._output_file.getvalue()
        assert "key1" in output
        assert "key2" in output

    def test_list_message_handling(self):
        """Test handling of list messages (lines 135-136)"""
        client = SignalRClient("test.txt")
        client._output_file = StringIO()

        msg = ["data1", "data2"]

        with patch('time.time', return_value=1234567890):
            client._on_message(msg)

        assert client._t_last_message == 1234567890
        output = client._output_file.getvalue()
        assert "data1" in output
        assert "data2" in output

    def test_unknown_message_type(self):
        """Test handling of unknown message type (lines 138-140)"""
        client = SignalRClient("test.txt")
        client._output_file = StringIO()

        msg = "invalid_message_type"

        with patch('time.time', return_value=1234567890):
            client._on_message(msg)

        assert client._t_last_message == 1234567890
        # Output file should not have been written to
        assert client._output_file.getvalue() == ""

    def test_file_write_exception(self):
        """Test exception handling during file write (lines 145-146)"""
        client = SignalRClient("test.txt")
        mock_file = Mock()
        mock_file.write.side_effect = IOError("Write failed")
        client._output_file = mock_file

        msg = ["test_data"]

        # Should not raise exception, just log it
        client._on_message(msg)

        # Verify write was attempted
        mock_file.write.assert_called_once()


class TestSignalRClientCallbacks:
    """Tests for SignalRClient callback methods"""

    def test_on_connect(self):
        """Test _on_connect callback (lines 148-150)"""
        client = SignalRClient("test.txt")
        assert client._is_connected is False

        client._on_connect()

        assert client._is_connected is True

    def test_on_close(self):
        """Test _on_close callback (lines 152-154)"""
        client = SignalRClient("test.txt")
        client._is_connected = True

        client._on_close()

        assert client._is_connected is False

    def test_exit(self):
        """Test _exit method (lines 207-209)"""
        client = SignalRClient("test.txt")
        mock_connection = Mock()
        mock_file = Mock()
        client._connection = mock_connection
        client._output_file = mock_file

        client._exit()

        mock_connection.stop.assert_called_once()
        mock_file.close.assert_called_once()


class TestSignalRClientRun:
    """Tests for SignalRClient._run method"""

    @patch('fastf1.livetiming.client.requests.options')
    @patch('fastf1.livetiming.client.HubConnectionBuilder')
    @patch('builtins.open', new_callable=mock_open)
    @patch('time.sleep')
    def test_run_with_auth(self, mock_sleep, mock_file, mock_builder, mock_requests):
        """Test _run method with authentication (lines 156-190)"""
        client = SignalRClient("test.txt", no_auth=False)

        # Mock requests response
        mock_response = Mock()
        mock_response.cookies = {'AWSALBCORS': 'test_cookie_value'}
        mock_requests.return_value = mock_response

        # Mock HubConnectionBuilder
        mock_hub_instance = Mock()
        mock_builder_chain = Mock()
        mock_builder.return_value = mock_builder_chain
        mock_builder_chain.with_url.return_value = mock_builder_chain
        mock_builder_chain.configure_logging.return_value = mock_builder_chain
        mock_builder_chain.build.return_value = mock_hub_instance

        # Mock connection
        mock_hub_instance.start = Mock()
        client._is_connected = True  # Skip the wait loop

        client._run()

        # Verify file was opened
        mock_file.assert_called_once_with("test.txt", "w")

        # Verify requests.options was called
        mock_requests.assert_called_once()

        # Verify cookie was set
        assert "AWSALBCORS=test_cookie_value" in client.headers.get("Cookie", "")

        # Verify connection was created and started
        mock_hub_instance.on_open.assert_called_once()
        mock_hub_instance.on_close.assert_called_once()
        mock_hub_instance.on.assert_called_once_with('feed', client._on_message)
        mock_hub_instance.start.assert_called_once()
        mock_hub_instance.send.assert_called_once()

    @patch('fastf1.livetiming.client.requests.options')
    @patch('fastf1.livetiming.client.HubConnectionBuilder')
    @patch('builtins.open', new_callable=mock_open)
    @patch('time.sleep')
    def test_run_without_auth(self, mock_sleep, mock_file, mock_builder, mock_requests):
        """Test _run method without authentication (line 168)"""
        client = SignalRClient("test.txt", no_auth=True)

        # Mock requests response
        mock_response = Mock()
        mock_response.cookies = {'AWSALBCORS': 'test_cookie_value'}
        mock_requests.return_value = mock_response

        # Mock HubConnectionBuilder
        mock_hub_instance = Mock()
        mock_builder_chain = Mock()
        mock_builder.return_value = mock_builder_chain
        mock_builder_chain.with_url.return_value = mock_builder_chain
        mock_builder_chain.configure_logging.return_value = mock_builder_chain
        mock_builder_chain.build.return_value = mock_hub_instance

        client._is_connected = True  # Skip the wait loop

        client._run()

        # Verify builder was called with None access_token_factory
        mock_builder_chain.with_url.assert_called_once()
        call_args = mock_builder_chain.with_url.call_args
        options = call_args[1]['options']
        assert options['access_token_factory'] is None


class TestSignalRClientSupervise:
    """Tests for SignalRClient._supervise method"""

    @patch('time.sleep')
    @patch('time.time')
    def test_supervise_timeout(self, mock_time, mock_sleep):
        """Test _supervise timeout behavior (lines 192-205)"""
        client = SignalRClient("test.txt", timeout=5)
        mock_connection = Mock()
        mock_file = Mock()
        client._connection = mock_connection
        client._output_file = mock_file

        # Simulate time progression to trigger timeout
        # Need enough time values for logging calls too
        time_values = [100, 100, 106, 106, 106]
        mock_time.side_effect = time_values

        client._supervise()

        # Verify exit was called
        mock_connection.stop.assert_called_once()
        mock_file.close.assert_called_once()

    @patch('time.sleep')
    @patch('time.time')
    def test_supervise_no_timeout(self, mock_time, mock_sleep):
        """Test _supervise with timeout disabled (lines 196-197)"""
        client = SignalRClient("test.txt", timeout=0)

        # Simulate time progression
        mock_time.return_value = 100

        # Stop after a few iterations
        mock_sleep.side_effect = [None, None, Exception("Stop loop")]

        try:
            client._supervise()
        except Exception:
            pass

        # Should have slept multiple times without exiting
        assert mock_sleep.call_count == 3


class TestSignalRClientStart:
    """Tests for SignalRClient.start and async_start methods"""

    @patch.object(SignalRClient, '_exit')
    @patch.object(SignalRClient, '_supervise')
    @patch.object(SignalRClient, '_run')
    def test_start_normal(self, mock_run, mock_supervise, mock_exit):
        """Test start method normal flow (lines 211-220)"""
        client = SignalRClient("test.txt")

        client.start()

        mock_run.assert_called_once()
        mock_supervise.assert_called_once()
        mock_exit.assert_not_called()

    @patch.object(SignalRClient, '_exit')
    @patch.object(SignalRClient, '_supervise')
    @patch.object(SignalRClient, '_run')
    def test_start_keyboard_interrupt(self, mock_run, mock_supervise, mock_exit):
        """Test start method with keyboard interrupt (lines 218-220)"""
        client = SignalRClient("test.txt")
        mock_supervise.side_effect = KeyboardInterrupt()

        client.start()

        mock_run.assert_called_once()
        mock_supervise.assert_called_once()
        mock_exit.assert_called_once()

    def test_async_start_not_implemented(self):
        """Test async_start raises NotImplementedError (lines 222-229)"""
        import asyncio

        client = SignalRClient("test.txt")

        with pytest.raises(NotImplementedError) as excinfo:
            # Run the coroutine using asyncio.run
            asyncio.run(client.async_start())

        assert "no longer provided" in str(excinfo.value)
