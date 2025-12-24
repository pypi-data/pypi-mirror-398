from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "test-project"
    APP_VERSION: str = "0.1.0"

    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    MIDDESK_API_KEY: str
    MIDDESK_BASE_URL: str = "https://api.middesk.com/v1"
    DOME_API_KEY: str
    DOME_BASE_URL: str = "https://api.domeapi.io/v1"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
