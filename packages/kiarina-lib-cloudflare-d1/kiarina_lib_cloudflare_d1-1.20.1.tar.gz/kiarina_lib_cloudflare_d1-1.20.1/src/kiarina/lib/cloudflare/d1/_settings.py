from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class D1Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KIARINA_LIB_CLOUDFLARE_D1_")

    database_id: str


settings_manager = SettingsManager(D1Settings, multi=True)
