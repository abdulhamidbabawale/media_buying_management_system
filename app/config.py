import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    MONGODB_URI: str = os.getenv("DATABASE_URI")
    DB_NAME: str = os.getenv("DB_NAME")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecret")
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

# Create a single instance for use across the app
settings = Settings()
