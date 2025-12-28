import os

import google.auth.compute_engine.credentials
import google.oauth2.credentials
import google.oauth2.service_account
from google.auth import impersonated_credentials
import pytest

from kiarina.lib.google.auth import get_credentials


@pytest.mark.xfail(
    not os.path.exists(
        os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    ),
    reason="ADC file not set",
)
def test_default(load_settings):
    credentials = get_credentials("default")
    assert isinstance(
        credentials,
        (
            google.auth.compute_engine.credentials.Credentials,
            google.oauth2.service_account.Credentials,
            google.oauth2.credentials.Credentials,
        ),
    )


def test_service_account_file(load_settings):
    credentials = get_credentials("service_account_file")
    assert isinstance(credentials, google.oauth2.service_account.Credentials)


def test_service_account_data(load_settings):
    credentials = get_credentials("service_account_data")
    assert isinstance(credentials, google.oauth2.service_account.Credentials)


def test_impersonate_service_account(load_settings):
    credentials = get_credentials("service_account_impersonate")
    assert isinstance(credentials, impersonated_credentials.Credentials)


def test_user_account_file(load_settings):
    credentials = get_credentials("user_account_file")
    assert isinstance(credentials, google.oauth2.credentials.Credentials)


def test_user_account_data(load_settings):
    credentials = get_credentials("user_account_data")
    assert isinstance(credentials, google.oauth2.credentials.Credentials)
