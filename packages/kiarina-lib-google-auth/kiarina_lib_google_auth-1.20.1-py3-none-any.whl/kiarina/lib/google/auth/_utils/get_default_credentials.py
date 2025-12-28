import google.auth.compute_engine.credentials
import google.oauth2.credentials
import google.oauth2.service_account
from google.auth import default


def get_default_credentials() -> (
    google.auth.compute_engine.credentials.Credentials
    | google.oauth2.credentials.Credentials
    | google.oauth2.service_account.Credentials
):
    """
    Get default Google credentials

    Default credentials are determined in the following priority order:

    - `google.oauth2.service_account.Credentials`
        - When the GOOGLE_APPLICATION_CREDENTIALS environment variable is set
    - `google.oauth2.credentials.Credentials`
        - When credentials set by the gcloud auth application-default login command exist
    - `google.auth.compute_engine.credentials.Credentials`
        - When running on GCP and the metadata server is available
    """
    credentials, _ = default()  # type: ignore[no-untyped-call]

    assert isinstance(
        credentials,
        (
            google.auth.compute_engine.credentials.Credentials,
            google.oauth2.credentials.Credentials,
            google.oauth2.service_account.Credentials,
        ),
    ), f"Invalid credentials type: {type(credentials)}"

    return credentials
