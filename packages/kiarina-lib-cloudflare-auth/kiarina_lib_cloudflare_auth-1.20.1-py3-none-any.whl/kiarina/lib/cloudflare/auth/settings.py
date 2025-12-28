from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class CloudflareAuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KIARINA_LIB_CLOUDFLARE_AUTH_")

    account_id: str

    api_token: SecretStr


settings_manager = SettingsManager(CloudflareAuthSettings, multi=True)
