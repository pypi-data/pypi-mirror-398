from kiarina.lib.google.auth import get_self_signed_jwt


def test_get_self_signed_jwt(load_settings):
    jwt = get_self_signed_jwt(
        "service_account_file",
        audience="https://blazeworks.jp/",
    )
    assert jwt.count(".") == 2
