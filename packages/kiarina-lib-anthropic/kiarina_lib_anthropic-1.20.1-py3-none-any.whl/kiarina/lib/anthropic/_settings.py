from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class AnthropicSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KIARINA_LIB_ANTHROPIC_")

    api_key: SecretStr | None = None
    """Anthropic API key"""

    base_url: str | None = None
    """Custom base URL for Anthropic API"""


settings_manager = SettingsManager(AnthropicSettings, multi=True)
