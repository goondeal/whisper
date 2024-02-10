from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    # JWT_PUBLIC_KEY: str
    JWT_PRIVATE_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60
    API_VERSION: str = '/api/v1'

    # the modern way to read configuration file instead of the inner class Config, see:
    # https://fastapi.tiangolo.com/advanced/settings/#the-env-file
    model_config = SettingsConfigDict(env_file=".env")
