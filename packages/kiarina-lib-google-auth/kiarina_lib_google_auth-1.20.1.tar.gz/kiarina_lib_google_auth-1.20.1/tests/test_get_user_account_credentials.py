from google.oauth2.credentials import Credentials
import pytest

from kiarina.lib.google.auth import (
    CredentialsCache,
    settings_manager,
    get_user_account_credentials,
)


def test_file(load_settings):
    settings = settings_manager.get_settings("user_account_file")
    credentials = get_user_account_credentials(
        authorized_user_file=settings.authorized_user_file,
        scopes=settings.scopes,
    )
    assert isinstance(credentials, Credentials)


def test_nonexistent_file():
    with pytest.raises(ValueError, match="Authorized user file does not exist"):
        get_user_account_credentials(
            authorized_user_file="/path/to/nonexistent/file.json",
            scopes=["https://www.googleapis.com/auth/devstorage.read_only"],
        )


def test_data(load_settings):
    settings = settings_manager.get_settings("user_account_data")
    credentials = get_user_account_credentials(
        authorized_user_data=settings.get_authorized_user_data(),
        scopes=settings.scopes,
    )
    assert isinstance(credentials, Credentials)


def test_cache(load_settings):
    set_counter = 0

    class InMemoryCache(CredentialsCache):
        def __init__(self):
            self._cache: str | None = None

        def get(self) -> str | None:
            return self._cache

        def set(self, value: str) -> None:
            self._cache = value

            nonlocal set_counter
            set_counter += 1

    cache = InMemoryCache()

    settings = settings_manager.get_settings("user_account_data")
    credentials = get_user_account_credentials(
        authorized_user_data=settings.get_authorized_user_data(),
        scopes=settings.scopes,
        cache=cache,
    )

    assert isinstance(credentials, Credentials)
    assert credentials.valid is True
    assert cache.get() is not None
    assert set_counter == 1

    credentials2 = get_user_account_credentials(
        authorized_user_data=settings.get_authorized_user_data(),
        scopes=settings.scopes,
        cache=cache,
    )

    assert isinstance(credentials2, Credentials)
    assert credentials2.valid is True
    assert credentials2.token == credentials.token
    assert set_counter == 1  # Cache should be used, so set() not called
