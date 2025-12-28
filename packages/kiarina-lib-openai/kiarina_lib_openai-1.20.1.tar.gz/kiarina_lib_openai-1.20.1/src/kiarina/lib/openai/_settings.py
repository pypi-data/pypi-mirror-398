from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KIARINA_LIB_OPENAI_")

    api_key: SecretStr | None = None
    """OpenAI API key"""

    organization_id: str | None = None
    """OpenAI organization ID"""

    base_url: str | None = None
    """Custom base URL for OpenAI API"""


settings_manager = SettingsManager(OpenAISettings, multi=True)
