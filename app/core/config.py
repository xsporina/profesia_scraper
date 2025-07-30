from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    
    POSTGRES_SERVER: str = ""
    POSTGRES_PORT: int = 54321
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    DEEPSEEK_NAME: str = ""
    DEEPSEEK_PASSWORD: str = ""

    CHROME_ARGS: list[str] = [
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--headless=new",  # Use new headless mode (less detectable)
        
        # Anti-detection flags
        "--disable-blink-features=AutomationControlled",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-default-apps",
        "--disable-web-security",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1920,1080",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]

    JOB_LIST_URL: str = "https://www.profesia.sk/en/work/information-technology/"
    DEEPSEEK_URL: str = "https://chat.deepseek.com/"

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()