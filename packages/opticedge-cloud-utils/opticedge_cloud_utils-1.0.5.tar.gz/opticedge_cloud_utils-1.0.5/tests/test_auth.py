# tests/test_auth.py
import pytest
from unittest.mock import patch, MagicMock
from opticedge_cloud_utils.auth import verify_request

@pytest.fixture
def allowed_values():
    return {
        "allowed_service_account": "service-account@example.com",
        "allowed_audience": "https://example.com/task"
    }

@pytest.fixture
def mock_request():
    req = MagicMock()
    # ensure headers attribute exists and is dict-like
    req.headers = {}
    return req

@patch("google.oauth2.id_token.verify_oauth2_token")
@patch("google.auth.transport.requests.Request")
def test_valid_request(mock_request_adapter, mock_verify_token, mock_request, allowed_values):
    # Mock decoded token to match allowed service account
    mock_verify_token.return_value = {"email": allowed_values["allowed_service_account"]}

    mock_request.headers = {"Authorization": "Bearer fake-token"}

    result = verify_request(
        mock_request,
        allowed_service_account=allowed_values["allowed_service_account"],
        allowed_audience=allowed_values["allowed_audience"]
    )

    assert result is True
    mock_verify_token.assert_called_once()

@patch("google.oauth2.id_token.verify_oauth2_token")
@patch("google.auth.transport.requests.Request")
def test_invalid_service_account(mock_request_adapter, mock_verify_token, mock_request, allowed_values):
    # Token email does not match
    mock_verify_token.return_value = {"email": "other@example.com"}

    mock_request.headers = {"Authorization": "Bearer fake-token"}

    result = verify_request(
        mock_request,
        allowed_service_account=allowed_values["allowed_service_account"],
        allowed_audience=allowed_values["allowed_audience"]
    )

    assert result is False

def test_missing_authorization_header(mock_request, allowed_values):
    # No Authorization header
    mock_request.headers = {}

    result = verify_request(
        mock_request,
        allowed_service_account=allowed_values["allowed_service_account"],
        allowed_audience=allowed_values["allowed_audience"]
    )

    assert result is False

@patch("google.oauth2.id_token.verify_oauth2_token")
@patch("google.auth.transport.requests.Request")
def test_invalid_token_raises_exception(mock_request_adapter, mock_verify_token, mock_request, allowed_values):
    # Simulate token verification failure
    mock_verify_token.side_effect = Exception("Invalid token")

    mock_request.headers = {"Authorization": "Bearer fake-token"}

    result = verify_request(
        mock_request,
        allowed_service_account=allowed_values["allowed_service_account"],
        allowed_audience=allowed_values["allowed_audience"]
    )

    assert result is False
