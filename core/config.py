import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str
    REDIS_URL: str
    REDIS_PASSWORD: str | None
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    JWT_SECRET: str
    HF_MODEL_NAME: str
    GCS_BUCKET_NAME: str
    GOOGLE_APPLICATION_CREDENTIALS: str | None
    PORT: int = 8080

    class Config:
        env_file = '.env'

    def __init__(self, **data):
        super().__init__(**data)