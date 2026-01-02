from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class ZenithSettings(BaseSettings):
    """
    Centralized settings for ZenithAuth. 
    Can be loaded from environment variables (e.g., ZENITH_SECRET_KEY).
    """
    # Security Settings
    SECRET_KEY: str = Field(..., validation_alias="ZENITH_SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MIN_PASSWORD_LENGTH: int = 12
    REQUIRE_NON_ALPHA: bool = True

    # Redis Settings
    REDIS_URL: str = Field("redis://localhost:6379/0", validation_alias="ZENITH_REDIS_URL")
    
    # Password Policy
    MIN_PASSWORD_LENGTH: int = 12

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )