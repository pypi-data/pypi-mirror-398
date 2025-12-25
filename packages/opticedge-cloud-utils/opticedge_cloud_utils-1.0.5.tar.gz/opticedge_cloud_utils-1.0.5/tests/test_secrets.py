# tests/test_secrets.py
from unittest.mock import patch, MagicMock
import pytest
from google.api_core.exceptions import GoogleAPICallError
from opticedge_cloud_utils.secrets import get_secret


@patch("opticedge_cloud_utils.secrets.secretmanager.SecretManagerServiceClient")
def test_get_secret_success(mock_client_cls):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.payload.data = b"super-secret-value"
    mock_client.access_secret_version.return_value = mock_response
    mock_client_cls.return_value = mock_client

    result = get_secret("test-project", "my-secret")

    assert result == "super-secret-value"
    mock_client.access_secret_version.assert_called_once_with(
        request={"name": "projects/test-project/secrets/my-secret/versions/latest"}
    )


@patch("opticedge_cloud_utils.secrets.secretmanager.SecretManagerServiceClient")
def test_get_secret_failure(mock_client_cls):
    mock_client = MagicMock()
    mock_client.access_secret_version.side_effect = GoogleAPICallError("API error")
    mock_client_cls.return_value = mock_client

    with pytest.raises(RuntimeError) as excinfo:
        get_secret("test-project", "my-secret")

    assert "Failed to fetch secret 'my-secret'" in str(excinfo.value)
