import google.auth.transport.requests
import google.oauth2.id_token

def verify_request(request, allowed_service_account: str, allowed_audience: str) -> bool:
    """
    Verifies that an incoming request is from a trusted source (e.g., Cloud Tasks)
    using ID tokens.

    Args:
        request: A Flask/Django-like request object with headers.
        allowed_service_account: The expected service account email.
        allowed_audience: The expected audience.

    Returns:
        bool: True if the request is verified, False otherwise.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False

    token = auth_header.split(" ")[1]
    request_adapter = google.auth.transport.requests.Request()

    try:
        decoded_token = google.oauth2.id_token.verify_oauth2_token(
            token,
            request_adapter,
            audience=allowed_audience
        )
        if decoded_token.get("email") != allowed_service_account:
            return False
        return True
    except Exception as e:
        print(f"Auth error: {e}")
        return False
