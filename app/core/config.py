import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "GymFlow API"
    GYM_NAME: str = "Future Fitness Gym"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/gymflow_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-please-change")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
