from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    scout_model: str = "gemini-1.5-flash"
    red_team_model: str = "gpt-4o"
    blue_team_model: str = "deepseek-coder:7b"
    ollama_host: str = "http://127.0.0.1:11434"
    max_retries: int = 5
    command_timeout_seconds: int = 120
    use_docker: bool = True
    output_dir: Path = Path("reports")


settings = Settings()
