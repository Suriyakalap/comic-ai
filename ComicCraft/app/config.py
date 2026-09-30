from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    gemini_api_key: str = ""
    hf_api_key: str = ""

    gemini_text_model: str = "gemini-3.5-flash-lite"
    hf_image_model: str = "stabilityai/stable-diffusion-3-medium-diffusers"

    image_provider: str = "huggingface"

    mock_mode: bool = False

    panel_count: int = 5

    host: str = "127.0.0.1"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

PANELS_DIR = STATIC_DIR / "panels"
EXPORTS_DIR = STATIC_DIR / "exports"


PANELS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

EXPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)