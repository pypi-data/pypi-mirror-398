import google.oauth2.service_account
import pytest

from kiarina.lib.google.auth import settings_manager, get_service_account_credentials


def test_file(load_settings):
    settings = settings_manager.get_settings("service_account_file")
    credentials = get_service_account_credentials(
        service_account_file=settings.service_account_file
    )
    assert isinstance(credentials, google.oauth2.service_account.Credentials)


def test_nonexistent_file():
    with pytest.raises(ValueError, match="Service account file does not exist"):
        get_service_account_credentials(
            service_account_file="/path/to/nonexistent/file.json"
        )


def test_data(load_settings):
    settings = settings_manager.get_settings("service_account_data")
    credentials = get_service_account_credentials(
        service_account_data=settings.get_service_account_data()
    )
    assert isinstance(credentials, google.oauth2.service_account.Credentials)
