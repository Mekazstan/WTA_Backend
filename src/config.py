from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus

class Settings(BaseSettings):
    DATABASE_URL: str
    MONGO_USERNAME: str
    MONGO_PASSWORD: str
    MONGO_CLUSTER: str
    MONGO_DB_NAME: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    
    @property
    def MONGO_URI(self) -> str:
        escaped_username = quote_plus(self.MONGO_USERNAME)
        escaped_password = quote_plus(self.MONGO_PASSWORD)
        return (
            f"mongodb+srv://{escaped_username}:{escaped_password}@{self.MONGO_CLUSTER}.dwm7ggh.mongodb.net/?retryWrites=true&w=majority&appName={self.MONGO_CLUSTER}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

# Instantiate the Config object
Config = Settings()
