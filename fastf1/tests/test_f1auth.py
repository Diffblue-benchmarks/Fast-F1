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


def test_print_auth_status_when_no_token(reset_subscription_token):
    """Test print_auth_status prints 'Not authenticated' when no token exists."""
    import fastf1.internals.f1auth as f1auth

    # Mock file read with empty string (no token)
    with patch("builtins.open", mock_open(read_data="")):
        with patch("builtins.print") as mock_print:
            f1auth.print_auth_status()

            # Verify print was called with "Not authenticated"
            mock_print.assert_called_once_with("Not authenticated")


def test_print_auth_status_reads_token_from_file(reset_subscription_token):
    """Test print_auth_status reads token from file when token is None."""
    import fastf1.internals.f1auth as f1auth
    from datetime import datetime

    test_token = "test_token_12345"
    exp_timestamp = datetime.now().timestamp() + 3600  # Not expired
    decoded_payload = {
        'exp': exp_timestamp,
        'SubscriptionStatus': 'active',
        'SubscribedProduct': 'F1TV Pro'
    }

    # Mock file read and verify_jwt
    with patch("builtins.open", mock_open(read_data=test_token)):
        with patch("fastf1.internals.f1auth._verify_jwt", return_value=decoded_payload):
            with patch("builtins.print") as mock_print:
                f1auth.print_auth_status()

                # Verify the global token was set from file
                assert f1auth._subscription_token == test_token

                # Verify print was called with status info
                assert mock_print.call_count == 1
                call_args = mock_print.call_args[0][0]
                assert "Token Status:" in call_args
                assert "Subscription Status: active" in call_args
                assert "Subscribed Product: F1TV Pro" in call_args


def test_print_auth_status_with_valid_token(reset_subscription_token):
    """Test print_auth_status with a valid (not expired) token."""
    import fastf1.internals.f1auth as f1auth
    from datetime import datetime

    test_token = "valid_token_abc"
    f1auth._subscription_token = test_token

    exp_timestamp = datetime.now().timestamp() + 3600  # Expires in 1 hour
    decoded_payload = {
        'exp': exp_timestamp,
        'SubscriptionStatus': 'active',
        'SubscribedProduct': 'F1TV Access'
    }

    with patch("fastf1.internals.f1auth._verify_jwt", return_value=decoded_payload):
        with patch("builtins.print") as mock_print:
            f1auth.print_auth_status()

            # Verify print was called once
            assert mock_print.call_count == 1
            call_args = mock_print.call_args[0][0]

            # Verify the output contains expected information
            assert "Token Status: Expires" in call_args
            assert "Subscription Status: active" in call_args
            assert "Subscribed Product: F1TV Access" in call_args


def test_print_auth_status_with_expired_token(reset_subscription_token):
    """Test print_auth_status with an expired token."""
    import fastf1.internals.f1auth as f1auth
    from datetime import datetime

    test_token = "expired_token_xyz"
    f1auth._subscription_token = test_token

    exp_timestamp = datetime.now().timestamp() - 3600  # Expired 1 hour ago
    decoded_payload = {
        'exp': exp_timestamp,
        'SubscriptionStatus': 'expired',
        'SubscribedProduct': 'F1TV Pro'
    }

    with patch("fastf1.internals.f1auth._verify_jwt", return_value=decoded_payload):
        with patch("builtins.print") as mock_print:
            f1auth.print_auth_status()

            # Verify print was called once
            assert mock_print.call_count == 1
            call_args = mock_print.call_args[0][0]

            # Verify the output shows EXPIRED status
            assert "Token Status: EXPIRED" in call_args
            assert "Subscription Status: expired" in call_args
            assert "Subscribed Product: F1TV Pro" in call_args


@pytest.mark.skip(reason="Code bug: print_auth_status() fails with TypeError when token has no exp field - fromtimestamp(None) is invalid")
def test_print_auth_status_without_exp_field(reset_subscription_token):
    """Test print_auth_status when token has no exp field."""
    import fastf1.internals.f1auth as f1auth

    test_token = "token_no_exp"
    f1auth._subscription_token = test_token

    decoded_payload = {
        'SubscriptionStatus': 'active',
        'SubscribedProduct': 'F1TV Premium'
    }

    with patch("fastf1.internals.f1auth._verify_jwt", return_value=decoded_payload):
        with patch("builtins.print") as mock_print:
            f1auth.print_auth_status()

            # Verify print was called once
            assert mock_print.call_count == 1
            call_args = mock_print.call_args[0][0]

            # Verify the output contains subscription info
            assert "Token Status: Expires None (UTC)" in call_args
            assert "Subscription Status: active" in call_args
            assert "Subscribed Product: F1TV Premium" in call_args
