from typing import TypeAlias

import google.auth.compute_engine.credentials
import google.oauth2.credentials
import google.oauth2.service_account
from google.auth import impersonated_credentials

Credentials: TypeAlias = (
    google.auth.compute_engine.credentials.Credentials
    | google.oauth2.service_account.Credentials
    | google.oauth2.credentials.Credentials
    | impersonated_credentials.Credentials
)
