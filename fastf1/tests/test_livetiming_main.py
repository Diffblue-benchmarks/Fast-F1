import sys
import tempfile
from unittest import mock

import pytest

# Mock sys.argv and sys.exit before importing __main__ to prevent argument parsing
_orig_argv = sys.argv
sys.argv = ['__main__.py', 'save', 'dummy.txt']

# Mock SignalRClient.start to prevent actual execution
with mock.patch('fastf1.livetiming.client.SignalRClient.start'):
    from fastf1.livetiming import __main__

# Restore original argv
sys.argv = _orig_argv


class TestSave:
    """Test the save function for live timing data."""

    @mock.patch('fastf1.livetiming.__main__.SignalRClient')
    def test_save_with_append_false(self, mock_client_class):
        """Test save function with append=False (overwrite mode)."""
        mock_client_instance = mock.MagicMock()
        mock_client_class.return_value = mock_client_instance

        args = mock.MagicMock()
        args.file = 'test_output.txt'
        args.append = False
        args.debug = False
        args.timeout = 60

        __main__.save(args)

        mock_client_class.assert_called_once_with(
            'test_output.txt', filemode='w', debug=False, timeout=60
        )
        mock_client_instance.start.assert_called_once()

    @mock.patch('fastf1.livetiming.__main__.SignalRClient')
    def test_save_with_append_true(self, mock_client_class):
        """Test save function with append=True (append mode)."""
        mock_client_instance = mock.MagicMock()
        mock_client_class.return_value = mock_client_instance

        args = mock.MagicMock()
        args.file = 'test_output.txt'
        args.append = True
        args.debug = True
        args.timeout = 120

        __main__.save(args)

        mock_client_class.assert_called_once_with(
            'test_output.txt', filemode='a', debug=True, timeout=120
        )
        mock_client_instance.start.assert_called_once()


class TestConvert:
    """Test the convert function for extracting messages from debug data."""

    def test_convert_with_valid_data(self, tmp_path, capsys):
        """Test convert function with valid input data."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        # Sample raw SignalR data
        test_data = [
            '{"M":[{"H":"Streaming","M":"method1","A":["message1"]}]}\n',
            '{"M":[{"H":"Streaming","M":"method2","A":["message2"]}]}\n',
            '{"M":[{"H":"Other","M":"method3","A":["message3"]}]}\n'
        ]

        input_file.write_text(''.join(test_data))

        args = mock.MagicMock()
        args.input = str(input_file)
        args.output = str(output_file)

        __main__.convert(args)

        # Verify output file was created
        assert output_file.exists()

        # Verify output contains expected messages
        output_content = output_file.read_text()
        assert "['message1']" in output_content
        assert "['message2']" in output_content
        # message3 should not be included as it's not from "Streaming" hub
        assert "message3" not in output_content

        # Verify printed message
        captured = capsys.readouterr()
        assert "Completed with 0 error(s)" in captured.out

    def test_convert_with_errors(self, tmp_path, capsys):
        """Test convert function with some invalid JSON data."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        # Mix of valid and invalid data
        test_data = [
            '{"M":[{"H":"Streaming","M":"method1","A":["valid_message"]}]}\n',
            'invalid json line\n',
            '{"M":[{"H":"Streaming","M":"method2","A":["another_valid"]}]}\n',
            'another bad line\n'
        ]

        input_file.write_text(''.join(test_data))

        args = mock.MagicMock()
        args.input = str(input_file)
        args.output = str(output_file)

        __main__.convert(args)

        # Verify output file was created
        assert output_file.exists()

        # Verify valid messages were written
        output_content = output_file.read_text()
        assert "valid_message" in output_content
        assert "another_valid" in output_content

        # Verify error count in printed message
        captured = capsys.readouterr()
        assert "Completed with 2 error(s)" in captured.out

    def test_convert_empty_input(self, tmp_path, capsys):
        """Test convert function with empty input file."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_text('')

        args = mock.MagicMock()
        args.input = str(input_file)
        args.output = str(output_file)

        __main__.convert(args)

        # Verify output file was created (should be empty)
        assert output_file.exists()
        assert output_file.read_text() == ''

        # Verify printed message
        captured = capsys.readouterr()
        assert "Completed with 0 error(s)" in captured.out
