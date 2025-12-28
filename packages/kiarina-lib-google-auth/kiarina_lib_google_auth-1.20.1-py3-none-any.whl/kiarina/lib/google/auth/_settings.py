import json
import os
from typing import Any, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class GoogleAuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KIARINA_LIB_GOOGLE_AUTH_")

    type: Literal["default", "service_account", "user_account", "api_key"] = "default"

    # --------------------------------------------------
    # Fields (common)
    # --------------------------------------------------

    project_id: str | None = None

    impersonate_service_account: str | None = None
    """
    Email address of the service account to impersonate

    The source principal requires the roles/iam.serviceAccountTokenCreator role.
    Note that this required permission is not included in the roles/owner role.
    """

    scopes: list[str] = Field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/cloud-platform",  # All GCP resources
            "https://www.googleapis.com/auth/drive",  # Google Drive resources
            "https://www.googleapis.com/auth/spreadsheets",  # Google Sheets resources
        ]
    )
    """
    List of scopes to request during the authentication

    Specify the scopes required for impersonation authentication.
    Specify the scopes required for user account authentication.
    """

    # --------------------------------------------------
    # Fields (service_account)
    # --------------------------------------------------

    service_account_email: str | None = None

    service_account_file: str | None = None
    """Path to the service account key file"""

    service_account_data: SecretStr | None = None
    """Service account key data in JSON format"""

    # --------------------------------------------------
    # Fields (user_account)
    # --------------------------------------------------

    user_account_email: str | None = None

    client_secret_file: str | None = None
    """Path to the client secret file"""

    client_secret_data: SecretStr | None = None
    """Client secret data in JSON format"""

    authorized_user_file: str | None = None
    """Path to the authorized user file"""

    authorized_user_data: SecretStr | None = None
    """
    Authorized user data in JSON format

    If expired, retrieve from cache.
    If cache is not available, use for refresh.
    Refreshed credentials will be cached.
    """

    # --------------------------------------------------
    # Fields (api_key)
    # --------------------------------------------------

    api_key: SecretStr | None = None
    """API key for accessing Google APIs"""

    # --------------------------------------------------
    # Validators
    # --------------------------------------------------

    @field_validator(
        "service_account_file",
        "client_secret_file",
        "authorized_user_file",
        mode="before",
    )
    @classmethod
    def expand_user(cls, v: str | None) -> str | None:
        return os.path.expanduser(v) if isinstance(v, str) else v

    # --------------------------------------------------
    # Methods
    # --------------------------------------------------

    def get_service_account_data(self) -> dict[str, Any] | None:
        if not self.service_account_data:
            return None

        return json.loads(self.service_account_data.get_secret_value())  # type: ignore[no-any-return]

    def get_client_secret_data(self) -> dict[str, Any] | None:
        if not self.client_secret_data:
            return None

        return json.loads(self.client_secret_data.get_secret_value())  # type: ignore[no-any-return]

    def get_authorized_user_data(self) -> dict[str, Any] | None:
        if not self.authorized_user_data:
            return None

        return json.loads(self.authorized_user_data.get_secret_value())  # type: ignore[no-any-return]


settings_manager = SettingsManager(GoogleAuthSettings, multi=True)
