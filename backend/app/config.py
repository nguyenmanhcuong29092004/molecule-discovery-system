from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Molecule Discovery System"
    debug: bool = False
    secret_key: str
    
    database_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str
    
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )

settings = Settings()