from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path

class Settings(BaseSettings):
    data_dir: Path = Field(
        default=Path.home() / ".pyenvdoctor",
        description="Chemin de stockage des données de configuration"
    )
    
    log_level: str = Field(
        default="INFO",
        json_schema_extra={"choices": ["DEBUG", "INFO", "WARNING", "ERROR"]}
    )
    
    max_workers: int = Field(
        default=4,
        ge=1,
        le=8,
        description="Nombre maximum de threads de travail"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

config = Settings()