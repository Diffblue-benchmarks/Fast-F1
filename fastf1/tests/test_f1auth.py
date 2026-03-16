"""Tests for fastf1.internals.f1auth module."""
import pytest
from unittest.mock import mock_open, patch, MagicMock


@pytest.fixture
def reset_subscription_token():
    """Reset the global subscription token before and after each test."""
    import fastf1.internals.f1auth as f1auth
    original_token = f1auth._subscription_token
    f1auth._subscription_token = None
    yield
    f1auth._subscription_token = original_token


def test_print_auth_token_when_token_is_none(reset_subscription_token):
    """Test print_auth_token reads from file when token is None."""
    import fastf1.internals.f1auth as f1auth

    test_token = "test_subscription_token_12345"

    # Mock file read and print
    with patch("builtins.open", mock_open(read_data=test_token)):
        with patch("builtins.print") as mock_print:
            f1auth.print_auth_token()

            # Verify print was called with the token
            mock_print.assert_called_once_with(test_token)

            # Verify the global token was set
            assert f1auth._subscription_token == test_token


def test_print_auth_token_when_token_is_set(reset_subscription_token):
    """Test print_auth_token uses existing token without reading file."""
    import fastf1.internals.f1auth as f1auth

    test_token = "existing_token_67890"
    f1auth._subscription_token = test_token

    # Mock print but not file operations
    with patch("builtins.print") as mock_print:
        with patch("builtins.open", mock_open()) as mock_file:
            f1auth.print_auth_token()

            # Verify print was called with the existing token
            mock_print.assert_called_once_with(test_token)

            # Verify file was NOT opened (token already exists)
            mock_file.assert_not_called()


def test_print_auth_token_with_empty_file(reset_subscription_token):
    """Test print_auth_token handles empty file gracefully."""
    import fastf1.internals.f1auth as f1auth

    # Mock file read with empty string
    with patch("builtins.open", mock_open(read_data="")):
        with patch("builtins.print") as mock_print:
            f1auth.print_auth_token()

            # Verify print was called with empty string
            mock_print.assert_called_once_with("")

            # Verify the global token was set to empty string
            assert f1auth._subscription_token == ""
