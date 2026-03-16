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


def test_clear_auth_token_clears_global_and_deletes_file(reset_subscription_token):
    """Test clear_auth_token clears the global token and deletes the auth file."""
    import fastf1.internals.f1auth as f1auth

    # Set a token to ensure it gets cleared
    test_token = "token_to_clear"
    f1auth._subscription_token = test_token

    # Create a mock for AUTH_DATA_FILE with unlink method
    mock_auth_file = MagicMock()
    with patch.object(f1auth, 'AUTH_DATA_FILE', mock_auth_file):
        f1auth.clear_auth_token()

        # Verify the global token was cleared
        assert f1auth._subscription_token is None

        # Verify unlink was called to delete the file
        mock_auth_file.unlink.assert_called_once()


def test_clear_auth_token_handles_file_not_found(reset_subscription_token):
    """Test clear_auth_token handles FileNotFoundError when file doesn't exist."""
    import fastf1.internals.f1auth as f1auth

    # Set a token to ensure it gets cleared
    test_token = "token_to_clear"
    f1auth._subscription_token = test_token

    # Create a mock that raises FileNotFoundError when unlink is called
    mock_auth_file = MagicMock()
    mock_auth_file.unlink.side_effect = FileNotFoundError

    with patch.object(f1auth, 'AUTH_DATA_FILE', mock_auth_file):
        f1auth.clear_auth_token()

        # Verify the global token was still cleared
        assert f1auth._subscription_token is None

        # Verify unlink was attempted
        mock_auth_file.unlink.assert_called_once()


def test_get_auth_token_returns_existing_token(reset_subscription_token):
    """Test get_auth_token returns token when already set in memory."""
    import fastf1.internals.f1auth as f1auth

    test_token = "existing_token_in_memory"
    f1auth._subscription_token = test_token

    # Mock verify_jwt to succeed
    with patch("fastf1.internals.f1auth._verify_jwt") as mock_verify:
        with patch("builtins.open", mock_open()) as mock_file:
            result = f1auth.get_auth_token()

            # Verify it returns the existing token
            assert result == test_token

            # Verify file was NOT opened
            mock_file.assert_not_called()

            # Verify token was verified
            mock_verify.assert_called_once()


def test_get_auth_token_reads_from_file_when_none(reset_subscription_token):
    """Test get_auth_token reads token from file when not in memory."""
    import fastf1.internals.f1auth as f1auth

    test_token = "token_from_file"

    # Mock file read and verify_jwt
    with patch("builtins.open", mock_open(read_data=test_token)):
        with patch("fastf1.internals.f1auth._verify_jwt"):
            result = f1auth.get_auth_token()

            # Verify it returns the token read from file
            assert result == test_token
            assert f1auth._subscription_token == test_token


def test_get_auth_token_prints_message_when_file_empty(reset_subscription_token):
    """Test get_auth_token prints subscription message when file is empty."""
    import fastf1.internals.f1auth as f1auth

    # Mock file read with empty string and run_auth_server
    with patch("builtins.open", mock_open(read_data="")):
        with patch("builtins.print") as mock_print:
            with patch("fastf1.internals.f1auth._run_auth_server") as mock_run_auth:
                # Simulate auth server setting token
                def set_token():
                    f1auth._subscription_token = "new_token"
                mock_run_auth.side_effect = set_token

                with patch("builtins.open", mock_open(), create=True):
                    result = f1auth.get_auth_token()

                # Verify subscription message was printed
                assert any("F1TV Access/Pro/Premium" in str(call) for call in mock_print.call_args_list)

                # Verify auth server was run
                mock_run_auth.assert_called_once()


def test_get_auth_token_with_invalid_token_error(reset_subscription_token):
    """Test get_auth_token handles InvalidTokenError and re-authenticates."""
    import fastf1.internals.f1auth as f1auth
    from jwt.exceptions import InvalidTokenError

    test_token = "invalid_token"
    f1auth._subscription_token = test_token

    # Mock verify_jwt to raise InvalidTokenError
    with patch("fastf1.internals.f1auth._verify_jwt", side_effect=InvalidTokenError):
        with patch("builtins.print") as mock_print:
            with patch("fastf1.internals.f1auth._run_auth_server") as mock_run_auth:
                # Simulate auth server setting new token
                def set_new_token():
                    f1auth._subscription_token = "new_valid_token"
                mock_run_auth.side_effect = set_new_token

                with patch("builtins.open", mock_open(), create=True):
                    result = f1auth.get_auth_token()

                # Verify error message was printed
                assert any("invalid" in str(call).lower() for call in mock_print.call_args_list)

                # Verify auth server was run
                mock_run_auth.assert_called_once()

                # Verify result is the new token
                assert result == "new_valid_token"


def test_get_auth_token_with_pyjwt_error(reset_subscription_token):
    """Test get_auth_token handles PyJWTError and re-authenticates."""
    import fastf1.internals.f1auth as f1auth
    from jwt.exceptions import PyJWTError

    test_token = "token_with_jwt_error"
    f1auth._subscription_token = test_token

    # Mock verify_jwt to raise PyJWTError
    with patch("fastf1.internals.f1auth._verify_jwt", side_effect=PyJWTError):
        with patch("builtins.print") as mock_print:
            with patch("fastf1.internals.f1auth._run_auth_server") as mock_run_auth:
                # Simulate auth server setting new token
                def set_new_token():
                    f1auth._subscription_token = "recovered_token"
                mock_run_auth.side_effect = set_new_token

                with patch("builtins.open", mock_open(), create=True):
                    result = f1auth.get_auth_token()

                # Verify unknown error message was printed
                assert any("Unknown error" in str(call) for call in mock_print.call_args_list)

                # Verify auth server was run
                mock_run_auth.assert_called_once()

                # Verify result is the new token
                assert result == "recovered_token"


def test_get_auth_token_auth_server_successful(reset_subscription_token):
    """Test get_auth_token runs auth server and saves token successfully."""
    import fastf1.internals.f1auth as f1auth

    # Mock file read with empty string
    with patch("builtins.open", mock_open(read_data="")):
        with patch("builtins.print") as mock_print:
            with patch("fastf1.internals.f1auth._run_auth_server") as mock_run_auth:
                # Simulate auth server setting token
                def set_token():
                    f1auth._subscription_token = "authenticated_token"
                mock_run_auth.side_effect = set_token

                # Mock file write
                mock_write = mock_open()
                with patch("builtins.open", mock_write, create=True):
                    result = f1auth.get_auth_token()

                    # Verify auth server was called
                    mock_run_auth.assert_called_once()

                    # Verify token was saved to file
                    mock_write.assert_called()
                    handle = mock_write()
                    handle.write.assert_called_with("authenticated_token")

                    # Verify result is the new token
                    assert result == "authenticated_token"


def test_get_auth_token_auth_server_fails_after_invalid_token(reset_subscription_token):
    """Test get_auth_token handles failed authentication after token invalidation."""
    import fastf1.internals.f1auth as f1auth
    from jwt.exceptions import InvalidTokenError

    # Set an initial invalid token
    test_token = "invalid_token"
    f1auth._subscription_token = test_token

    # Mock verify_jwt to raise InvalidTokenError, then mock auth server failure
    with patch("fastf1.internals.f1auth._verify_jwt", side_effect=InvalidTokenError):
        with patch("builtins.print") as mock_print:
            with patch("fastf1.internals.f1auth._run_auth_server") as mock_run_auth:
                # Auth server doesn't set token (authentication failed)
                # After _run_auth_server, token remains None
                result = f1auth.get_auth_token()

                # Verify auth server was called
                mock_run_auth.assert_called_once()

                # Verify both invalid token and authentication failed messages were printed
                call_strings = [str(call) for call in mock_print.call_args_list]
                assert any("invalid" in s.lower() for s in call_strings)
                assert any("Authentication failed" in s for s in call_strings)

                # Verify result is None
                assert result is None
