import logging
from importlib import import_module
from importlib.metadata import version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._helpers.get_credentials import get_credentials
    from ._helpers.get_self_signed_jwt import get_self_signed_jwt
    from ._settings import GoogleAuthSettings, settings_manager
    from ._types.credentials import Credentials
    from ._types.credentials_cache import CredentialsCache
    from ._utils.get_default_credentials import get_default_credentials
    from ._utils.get_service_account_credentials import get_service_account_credentials
    from ._utils.get_user_account_credentials import get_user_account_credentials

__version__ = version("kiarina-lib-google-auth")

__all__ = [
    # ._helpers
    "get_credentials",
    "get_self_signed_jwt",
    # ._settings
    "GoogleAuthSettings",
    "settings_manager",
    # ._types
    "Credentials",
    "CredentialsCache",
    # ._utils
    "get_default_credentials",
    "get_service_account_credentials",
    "get_user_account_credentials",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # ._helpers
        "get_credentials": "._helpers.get_credentials",
        "get_self_signed_jwt": "._helpers.get_self_signed_jwt",
        # ._settings
        "GoogleAuthSettings": "._settings",
        "settings_manager": "._settings",
        # ._types
        "Credentials": "._types.credentials",
        "CredentialsCache": "._types.credentials_cache",
        # ._utils
        "get_default_credentials": "._utils.get_default_credentials",
        "get_service_account_credentials": "._utils.get_service_account_credentials",
        "get_user_account_credentials": "._utils.get_user_account_credentials",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
