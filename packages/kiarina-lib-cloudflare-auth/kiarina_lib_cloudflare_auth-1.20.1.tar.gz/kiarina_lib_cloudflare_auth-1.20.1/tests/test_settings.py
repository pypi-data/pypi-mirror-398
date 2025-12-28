from kiarina.lib.cloudflare.auth import settings_manager


def test_settings():
    settings_manager.user_config = {
        "default": {
            "account_id": "test",
            "api_token": "testtoken",
        },
    }
    settings = settings_manager.settings
    assert settings.account_id == "test"
    assert settings.api_token.get_secret_value() == "testtoken"
