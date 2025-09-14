import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    MONGODB_URI: str = os.getenv("Database_URI")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecret")
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"

# Create a single instance for use across the app
settings = Settings()
