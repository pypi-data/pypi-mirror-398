import google.auth.compute_engine.credentials
import google.oauth2.credentials
import google.oauth2.service_account
from google.auth import impersonated_credentials

from .._types.credentials import Credentials
from .._types.credentials_cache import CredentialsCache
from .._utils.get_default_credentials import get_default_credentials
from .._utils.get_service_account_credentials import get_service_account_credentials
from .._utils.get_user_account_credentials import get_user_account_credentials
from .._settings import GoogleAuthSettings, settings_manager


def get_credentials(
    settings_key: str | None = None,
    *,
    settings: GoogleAuthSettings | None = None,
    scopes: list[str] | None = None,
    cache: CredentialsCache | None = None,
) -> Credentials:
    if settings is None:
        settings = settings_manager.get_settings(settings_key)

    credentials: Credentials

    if settings.type == "default":
        credentials = get_default_credentials()

    elif settings.type == "service_account":
        credentials = get_service_account_credentials(
            service_account_file=settings.service_account_file,
            service_account_data=settings.get_service_account_data(),
            scopes=scopes or settings.scopes,
        )

    elif settings.type == "user_account":
        credentials = get_user_account_credentials(
            authorized_user_file=settings.authorized_user_file,
            authorized_user_data=settings.get_authorized_user_data(),
            scopes=scopes or settings.scopes,
            cache=cache,
        )

    else:
        raise ValueError(f"Unsupported credentials type: {settings.type}")

    if settings.impersonate_service_account:
        credentials = impersonated_credentials.Credentials(  # type: ignore[no-untyped-call]
            source_credentials=credentials,
            target_principal=settings.impersonate_service_account,
            target_scopes=scopes or settings.scopes,
        )

    assert isinstance(
        credentials,
        (
            google.auth.compute_engine.credentials.Credentials,
            google.oauth2.service_account.Credentials,
            google.oauth2.credentials.Credentials,
            impersonated_credentials.Credentials,
        ),
    ), f"Invalid credentials type: {type(credentials)}"

    return credentials
