from google.auth import jwt
from google.auth.transport.requests import Request

from .get_credentials import get_credentials
from .._settings import GoogleAuthSettings


def get_self_signed_jwt(
    settings_key: str | None = None,
    *,
    settings: GoogleAuthSettings | None = None,
    audience: str,
) -> str:
    """
    Get a self-signed JWT
    """
    credentials = get_credentials(settings_key, settings=settings)

    jwt_creds = jwt.Credentials.from_signing_credentials(credentials, audience=audience)  # type: ignore[no-untyped-call]
    # Generate a self-signed JWT. Does not communicate over the network
    jwt_creds.refresh(Request())  # type: ignore[no-untyped-call]

    return jwt_creds.token.decode("utf-8")  # type: ignore[no-any-return]
