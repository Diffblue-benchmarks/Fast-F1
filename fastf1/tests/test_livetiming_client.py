"""Tests for livetiming/client.py - messages_from_raw and SignalRClient init."""
import json
import logging
import time
from unittest.mock import MagicMock, patch

import pytest

from fastf1.livetiming.client import SignalRClient, messages_from_raw


class TestMessagesFromRaw:
    def test_empty_input(self):
        data, errors = messages_from_raw([])
        assert data == []
        assert errors == 0

    def test_valid_streaming_messages(self):
        msg = json.dumps({
            'M': [{
                'H': 'Streaming',
                'M': 'feed',
                'A': ['TimingData', {'Lines': {}}, '2023-01-01T00:00:00Z']
            }]
        })
        data, errors = messages_from_raw([msg])
        assert len(data) == 1
        assert data[0][0] == 'TimingData'

    def test_non_streaming_hub_ignored(self):
        msg = json.dumps({
            'M': [{
                'H': 'OtherHub',
                'M': 'method',
                'A': ['data']
            }]
        })
        data, errors = messages_from_raw([msg])
        assert data == []

    def test_no_messages_key(self):
        msg = json.dumps({'C': 'something', 'M': []})
        data, errors = messages_from_raw([msg])
        assert data == []

    def test_invalid_json(self):
        data, errors = messages_from_raw(['not valid json {{{'])
        assert data == []
        assert errors == 1

    def test_multiple_messages(self):
        msgs = [
            json.dumps({
                'M': [{
                    'H': 'Streaming', 'M': 'feed',
                    'A': ['Cat1', {}, '']
                }]
            }),
            json.dumps({
                'M': [{
                    'H': 'Streaming', 'M': 'feed',
                    'A': ['Cat2', {}, '']
                }]
            }),
        ]
        data, errors = messages_from_raw(msgs)
        assert len(data) == 2

    def test_fixes_json_quotes(self):
        raw = "{'M': [{'H': 'Streaming', 'M': 'feed', 'A': ['X', {}, '']}]}"
        data, errors = messages_from_raw([raw])
        assert len(data) == 1


class TestSignalRClientInit:
    def test_basic_init(self):
        client = SignalRClient('test.txt', timeout=30)
        assert client.filename == 'test.txt'
        assert client.timeout == 30
        assert client._is_connected is False

    def test_debug_raises(self):
        with pytest.raises(ValueError, match="Debug mode"):
            SignalRClient('test.txt', debug=True)

    def test_custom_logger(self):
        logger = logging.getLogger('test')
        client = SignalRClient('test.txt', logger=logger)
        assert client.logger is logger

    def test_topics_populated(self):
        client = SignalRClient('test.txt')
        assert 'CarData.z' in client.topics
        assert 'TimingData' in client.topics

    def test_async_start_raises(self):
        client = SignalRClient('test.txt')
        with pytest.raises(NotImplementedError):
            import asyncio
            asyncio.get_event_loop().run_until_complete(client.async_start())


class TestSignalRClientCallbacks:
    def test_on_connect(self):
        client = SignalRClient('test.txt')
        assert client._is_connected is False
        client._on_connect()
        assert client._is_connected is True

    def test_on_close(self):
        client = SignalRClient('test.txt')
        client._is_connected = True
        client._on_close()
        assert client._is_connected is False

    def test_on_message_list(self):
        client = SignalRClient('test.txt')
        client._output_file = MagicMock()
        client._on_message(['some', 'data'])
        client._output_file.write.assert_called_once()
        client._output_file.flush.assert_called_once()

    def test_on_message_completion(self):
        from signalrcore.messages.completion_message import CompletionMessage
        client = SignalRClient('test.txt')
        client._output_file = MagicMock()
        msg = MagicMock(spec=CompletionMessage)
        msg.result = {'Key1': 'val1', 'Key2': 'val2'}
        client._on_message(msg)
        client._output_file.write.assert_called_once()

    def test_on_message_unknown_type(self):
        client = SignalRClient('test.txt')
        client._output_file = MagicMock()
        client._on_message("unexpected string")
        client._output_file.write.assert_not_called()
