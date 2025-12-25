from google.cloud import secretmanager
from google.api_core.exceptions import GoogleAPICallError

def get_secret(project_id: str, secret_name: str) -> str:
    """Retrieve the latest version of a secret from Secret Manager."""
    try:
        secret_client = secretmanager.SecretManagerServiceClient()

        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("utf-8")
    except GoogleAPICallError as e:
        raise RuntimeError(f"Failed to fetch secret '{secret_name}'") from e
