import json
import os
import tempfile
import warnings
from datetime import datetime, timedelta

import pytest

from fastf1.livetiming.data import LiveTimingData


@pytest.fixture
def temp_livetiming_file():
    """Create a temporary livetiming data file for testing."""
    def _create_file(content):
        fd, path = tempfile.mkstemp(suffix='.txt')
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        return path
    return _create_file


def test_livetiming_data_init_basic():
    """Test LiveTimingData initialization with basic parameters."""
    # Target lines: 56, 58, 60, 62, 64
    ltd = LiveTimingData('file1.txt', 'file2.txt')

    assert ltd.files == ('file1.txt', 'file2.txt')
    assert ltd.data == {}
    assert ltd.errorcount == 0
    assert ltd._files_read is False
    assert ltd._start_date is None


def test_livetiming_data_init_with_deprecated_kwarg():
    """Test LiveTimingData initialization with deprecated remove_duplicates kwarg."""
    # Target lines: 66, 67
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        ltd = LiveTimingData('file1.txt', remove_duplicates=True)

        assert len(w) == 1
        assert "remove_duplicates" in str(w[0].message)
        assert "no longer available" in str(w[0].message)


def test_fix_json_method():
    """Test _fix_json method fixes F1's non-compliant JSON."""
    # Target lines: 162, 165
    ltd = LiveTimingData()

    # Test single quotes to double quotes
    result = ltd._fix_json("['test', 'data']")
    assert result == '["test", "data"]'

    # Test True/False conversion
    result = ltd._fix_json('{"key": True, "other": False}')
    assert result == '{"key": true, "other": false}'

    # Test combined fixes
    result = ltd._fix_json("{'status': True, 'active': False}")
    assert result == '{"status": true, "active": false}'


def test_add_to_category_new_category():
    """Test _add_to_category creates new category."""
    # Target lines: 168, 169
    ltd = LiveTimingData()

    entry = [timedelta(seconds=10), {"data": "test"}]
    ltd._add_to_category('TestCategory', entry)

    assert 'TestCategory' in ltd.data
    assert ltd.data['TestCategory'] == [entry]


def test_add_to_category_existing_category():
    """Test _add_to_category appends to existing category."""
    # Target line: 171
    ltd = LiveTimingData()

    entry1 = [timedelta(seconds=10), {"data": "test1"}]
    entry2 = [timedelta(seconds=20), {"data": "test2"}]

    ltd._add_to_category('TestCategory', entry1)
    ltd._add_to_category('TestCategory', entry2)

    assert len(ltd.data['TestCategory']) == 2
    assert ltd.data['TestCategory'][0] == entry1
    assert ltd.data['TestCategory'][1] == entry2


def test_parse_line_valid_data():
    """Test _parse_line with valid JSON data."""
    # Target lines: 136, 137, 138, 144, 145, 152, 153, 154, 156, 158
    ltd = LiveTimingData()

    # First line sets start date (lines 152-154)
    timestamp = datetime.utcnow().isoformat() + 'Z'
    line = f'["Category1", {{"key": "value"}}, "{timestamp}"]'
    ltd._parse_line(line)

    assert ltd._start_date is not None
    assert 'Category1' in ltd.data
    assert len(ltd.data['Category1']) == 1
    assert ltd.data['Category1'][0][0] == timedelta(seconds=0)

    # Second line uses the established start date (line 156)
    timestamp2 = (ltd._start_date + timedelta(seconds=30)).isoformat() + 'Z'
    line2 = f'["Category2", {{"key2": "value2"}}, "{timestamp2}"]'
    ltd._parse_line(line2)

    assert 'Category2' in ltd.data
    assert ltd.data['Category2'][0][0] == timedelta(seconds=30)


def test_parse_line_invalid_json():
    """Test _parse_line with invalid JSON increments error count."""
    # Target lines: 139, 140, 141
    ltd = LiveTimingData()

    # Invalid JSON
    line = 'not valid json at all'
    ltd._parse_line(line)

    assert ltd.errorcount == 1
    assert len(ltd.data) == 0


def test_parse_line_invalid_datetime():
    """Test _parse_line with invalid datetime increments error count."""
    # Target lines: 145, 146, 147
    ltd = LiveTimingData()

    # Valid JSON but invalid datetime
    line = '["Category", {"key": "value"}, "invalid-datetime"]'
    ltd._parse_line(line)

    assert ltd.errorcount == 1
    assert len(ltd.data) == 0


def test_try_set_correct_start_date_with_started_status():
    """Test _try_set_correct_start_date finds and sets correct start date."""
    # Target lines: 176, 177, 178, 186, 187, 188, 195, 196, 197, 198, 199, 200
    ltd = LiveTimingData()

    start_time = datetime(2023, 5, 15, 14, 0, 0).isoformat() + 'Z'
    data = [
        '["OtherCategory", {"data": "test"}, "2023-05-15T13:00:00.000Z"]',
        f'["SessionStatus", {{"StatusSeries": [{{"SessionStatus": "Started", "Utc": "{start_time}"}}]}}, "2023-05-15T14:00:00.000Z"]',
        '["AnotherCategory", {"data": "test2"}, "2023-05-15T15:00:00.000Z"]'
    ]

    ltd._try_set_correct_start_date(data)

    assert ltd._start_date is not None
    assert ltd._start_date.year == 2023
    assert ltd._start_date.month == 5
    assert ltd._start_date.day == 15
    assert ltd._start_date.hour == 14


def test_try_set_correct_start_date_with_dict_statusseries():
    """Test _try_set_correct_start_date with StatusSeries as dict."""
    # Target lines: 206, 207, 208, 209, 210, 211
    ltd = LiveTimingData()

    start_time = datetime(2023, 5, 15, 14, 30, 0).isoformat() + 'Z'
    # StatusSeries as dict instead of list
    data = [
        f'["SessionStatus", {{"StatusSeries": {{"0": {{"SessionStatus": "Started", "Utc": "{start_time}"}}}}}}, "2023-05-15T14:30:00.000Z"]'
    ]

    ltd._try_set_correct_start_date(data)

    assert ltd._start_date is not None
    assert ltd._start_date.hour == 14
    assert ltd._start_date.minute == 30


def test_try_set_correct_start_date_not_found():
    """Test _try_set_correct_start_date when 'Started' status not found."""
    # Target lines: 181, 183
    ltd = LiveTimingData()

    data = [
        '["Category1", {"data": "test"}, "2023-05-15T13:00:00.000Z"]',
        '["Category2", {"data": "test2"}, "2023-05-15T15:00:00.000Z"]'
    ]

    ltd._try_set_correct_start_date(data)

    # Start date should remain None since no 'Started' status was found
    assert ltd._start_date is None


def test_try_set_correct_start_date_json_error():
    """Test _try_set_correct_start_date with JSON decode error."""
    # Target lines: 189, 190, 192
    ltd = LiveTimingData()

    data = [
        'invalid json but contains SessionStatus and Started keywords'
    ]

    initial_errorcount = ltd.errorcount
    ltd._try_set_correct_start_date(data)

    # Should handle the error gracefully
    assert ltd._start_date is None


def test_try_set_correct_start_date_invalid_utc():
    """Test _try_set_correct_start_date with invalid Utc field."""
    # Target lines: 200, 201, 202, 203, 205
    ltd = LiveTimingData()

    # StatusSeries with invalid Utc value (to_datetime returns None)
    data = [
        '["SessionStatus", {"StatusSeries": [{"SessionStatus": "Started", "Utc": "invalid"}]}, "2023-05-15T14:00:00.000Z"]'
    ]

    ltd._try_set_correct_start_date(data)

    # to_datetime returns None for invalid datetime, so start_date stays None
    assert ltd._start_date is None


def test_try_set_correct_start_date_missing_utc():
    """Test _try_set_correct_start_date with missing Utc field."""
    # Target lines: 201, 202, 203, 205
    ltd = LiveTimingData()

    # StatusSeries without Utc field
    data = [
        '["SessionStatus", {"StatusSeries": [{"SessionStatus": "Started"}]}, "2023-05-15T14:00:00.000Z"]'
    ]

    initial_errorcount = ltd.errorcount
    ltd._try_set_correct_start_date(data)

    assert ltd.errorcount > initial_errorcount
    assert ltd._start_date is None


def test_try_set_correct_start_date_dict_invalid_utc():
    """Test _try_set_correct_start_date with dict StatusSeries and invalid Utc."""
    # Target lines: 210, 211, 212, 213, 214, 216
    ltd = LiveTimingData()

    # StatusSeries as dict with invalid Utc (to_datetime returns None)
    data = [
        '["SessionStatus", {"StatusSeries": {"0": {"SessionStatus": "Started", "Utc": "invalid"}}}, "2023-05-15T14:00:00.000Z"]'
    ]

    ltd._try_set_correct_start_date(data)

    # to_datetime returns None for invalid datetime, so start_date stays None
    assert ltd._start_date is None


def test_load_single_file_first_file(temp_livetiming_file):
    """Test _load_single_file with first file."""
    # Target lines: 121, 122, 124, 125, 127, 130
    timestamp1 = datetime.utcnow().isoformat() + 'Z'
    timestamp2 = (datetime.utcnow() + timedelta(seconds=10)).isoformat() + 'Z'

    content = f'["Category1", {{"key": "value"}}, "{timestamp1}"]\n'
    content += f'["Category2", {{"key2": "value2"}}, "{timestamp2}"]\n'

    file_path = temp_livetiming_file(content)

    try:
        ltd = LiveTimingData(file_path)

        with open(file_path) as f:
            data = f.readlines()

        ltd._load_single_file(data, is_first_file=True, next_line=None)

        assert 'Category1' in ltd.data
        assert 'Category2' in ltd.data
        assert hasattr(ltd, '_previous_files')
        assert ltd._previous_files is True
    finally:
        os.unlink(file_path)


def test_load_single_file_with_overlap(temp_livetiming_file):
    """Test _load_single_file stops at overlapping line."""
    # Target lines: 125, 126
    timestamp1 = datetime.utcnow().isoformat() + 'Z'
    timestamp2 = (datetime.utcnow() + timedelta(seconds=10)).isoformat() + 'Z'
    timestamp3 = (datetime.utcnow() + timedelta(seconds=20)).isoformat() + 'Z'

    line1 = f'["Category1", {{"key": "value"}}, "{timestamp1}"]\n'
    line2 = f'["Category2", {{"key2": "value2"}}, "{timestamp2}"]\n'
    line3 = f'["Category3", {{"key3": "value3"}}, "{timestamp3}"]\n'

    content = line1 + line2 + line3

    file_path = temp_livetiming_file(content)

    try:
        ltd = LiveTimingData(file_path)

        with open(file_path) as f:
            data = f.readlines()

        # Simulate overlap by setting next_line to line2
        ltd._load_single_file(data, is_first_file=False, next_line=line2)

        # Should only process line1, stop at line2
        assert 'Category1' in ltd.data
        assert 'Category2' not in ltd.data
        assert 'Category3' not in ltd.data
    finally:
        os.unlink(file_path)


def test_load_with_single_file(temp_livetiming_file):
    """Test load method with a single file."""
    # Target lines: 79, 82, 83, 84, 89, 91, 93, 95, 98, 99, 101, 104, 106, 108, 111, 114
    timestamp = datetime.utcnow().isoformat() + 'Z'
    content = f'["TestCategory", {{"test": "data"}}, "{timestamp}"]\n'

    file_path = temp_livetiming_file(content)

    try:
        ltd = LiveTimingData(file_path)
        ltd.load()

        assert ltd._files_read is True
        assert 'TestCategory' in ltd.data
    finally:
        os.unlink(file_path)


def test_load_with_multiple_files(temp_livetiming_file):
    """Test load method with multiple files."""
    # Target lines: 79, 82, 83, 84, 89, 91, 93, 95, 98, 99, 101, 104, 106, 108, 111, 114
    timestamp1 = datetime.utcnow().isoformat() + 'Z'
    timestamp2 = (datetime.utcnow() + timedelta(seconds=10)).isoformat() + 'Z'
    timestamp3 = (datetime.utcnow() + timedelta(seconds=20)).isoformat() + 'Z'

    content1 = f'["Category1", {{"data": "file1"}}, "{timestamp1}"]\n'
    content2 = f'["Category2", {{"data": "file2"}}, "{timestamp2}"]\n'
    content3 = f'["Category3", {{"data": "file3"}}, "{timestamp3}"]\n'

    file1 = temp_livetiming_file(content1)
    file2 = temp_livetiming_file(content2)
    file3 = temp_livetiming_file(content3)

    try:
        ltd = LiveTimingData(file1, file2, file3)
        ltd.load()

        assert ltd._files_read is True
        assert 'Category1' in ltd.data
        assert 'Category2' in ltd.data
        assert 'Category3' in ltd.data
    finally:
        os.unlink(file1)
        os.unlink(file2)
        os.unlink(file3)


def test_load_with_overlapping_files(temp_livetiming_file):
    """Test load method with overlapping files."""
    # Target lines: 106, 108
    timestamp1 = datetime.utcnow().isoformat() + 'Z'
    timestamp2 = (datetime.utcnow() + timedelta(seconds=10)).isoformat() + 'Z'
    timestamp3 = (datetime.utcnow() + timedelta(seconds=20)).isoformat() + 'Z'

    line1 = f'["Category1", {{"data": "line1"}}, "{timestamp1}"]\n'
    line2 = f'["Category2", {{"data": "line2"}}, "{timestamp2}"]\n'
    line3 = f'["Category3", {{"data": "line3"}}, "{timestamp3}"]\n'

    # File 1 has line1 and line2
    content1 = line1 + line2
    # File 2 has line2 (overlap) and line3
    content2 = line2 + line3

    file1 = temp_livetiming_file(content1)
    file2 = temp_livetiming_file(content2)

    try:
        ltd = LiveTimingData(file1, file2)
        ltd.load()

        assert ltd._files_read is True
        # Should have all categories but line2 should not be duplicated
        assert 'Category1' in ltd.data
        assert 'Category2' in ltd.data
        assert 'Category3' in ltd.data
        # Category2 should appear only once (from file1)
        assert len(ltd.data['Category2']) == 1
    finally:
        os.unlink(file1)
        os.unlink(file2)


def test_get_method(temp_livetiming_file):
    """Test get method returns data for a category."""
    # Target lines: 227, 228, 229
    timestamp = datetime.utcnow().isoformat() + 'Z'
    content = f'["TestCategory", {{"test": "data"}}, "{timestamp}"]\n'

    file_path = temp_livetiming_file(content)

    try:
        ltd = LiveTimingData(file_path)

        # Should trigger load on first call
        result = ltd.get('TestCategory')

        assert ltd._files_read is True
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0][1] == {"test": "data"}
    finally:
        os.unlink(file_path)


def test_has_method_returns_true(temp_livetiming_file):
    """Test has method returns True when category exists."""
    # Target lines: 240, 241, 242
    timestamp = datetime.utcnow().isoformat() + 'Z'
    content = f'["TestCategory", {{"test": "data"}}, "{timestamp}"]\n'

    file_path = temp_livetiming_file(content)

    try:
        ltd = LiveTimingData(file_path)

        # Should trigger load on first call
        result = ltd.has('TestCategory')

        assert ltd._files_read is True
        assert result is True
    finally:
        os.unlink(file_path)


def test_has_method_returns_false(temp_livetiming_file):
    """Test has method returns False when category doesn't exist."""
    # Target lines: 240, 241, 242
    timestamp = datetime.utcnow().isoformat() + 'Z'
    content = f'["TestCategory", {{"test": "data"}}, "{timestamp}"]\n'

    file_path = temp_livetiming_file(content)

    try:
        ltd = LiveTimingData(file_path)

        result = ltd.has('NonExistentCategory')

        assert ltd._files_read is True
        assert result is False
    finally:
        os.unlink(file_path)


def test_list_categories_method(temp_livetiming_file):
    """Test list_categories method returns all categories."""
    # Target lines: 253, 254, 255
    timestamp1 = datetime.utcnow().isoformat() + 'Z'
    timestamp2 = (datetime.utcnow() + timedelta(seconds=10)).isoformat() + 'Z'

    content = f'["Category1", {{"test": "data1"}}, "{timestamp1}"]\n'
    content += f'["Category2", {{"test": "data2"}}, "{timestamp2}"]\n'

    file_path = temp_livetiming_file(content)

    try:
        ltd = LiveTimingData(file_path)

        # Should trigger load on first call
        categories = ltd.list_categories()

        assert ltd._files_read is True
        assert isinstance(categories, list)
        assert 'Category1' in categories
        assert 'Category2' in categories
    finally:
        os.unlink(file_path)
