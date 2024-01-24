from enum import StrEnum, auto

from pydantic_settings import BaseSettings, SettingsConfigDict


class WhisperModelSize(StrEnum):
    TINY = auto()
    BASE = auto()
    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    environment: str = "local"

    title: str = "Vidoso Api"
    description: str = ""
    version: str
    base_url: str
    docs_url: str
    openapi_url: str

    whisper_model: WhisperModelSize
    sentence_transformer_model: str = "paraphrase-mpnet-base-v2"
