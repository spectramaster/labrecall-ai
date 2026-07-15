from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    labrecall_mode: Literal["fixture", "cloud"] = "fixture"
    database_url: str | None = None
    database_secret_arn: str | None = None
    aws_region: str = "us-east-1"
    bedrock_embed_model: str = "amazon.titan-embed-text-v2:0"
    bedrock_text_model: str = "amazon.nova-lite-v1:0"
    memory_namespace: str = "public-demo"
    retrieval_limit: int = 5
    embedding_dimensions: int = 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
