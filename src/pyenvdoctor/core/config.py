from pydantic import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    data_dir: Path = Path.home() / ".pyenvdoctor"
    log_level: str = "INFO"
    max_workers: int = 4
    
    class Config:
        env_file = ".env"

config = Settings()
