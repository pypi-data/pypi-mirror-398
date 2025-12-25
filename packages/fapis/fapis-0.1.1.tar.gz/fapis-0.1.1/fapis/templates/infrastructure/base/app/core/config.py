from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	"""Application settings loaded from environment variables."""
	
	app_name: str = "FastAPI Starter"
	version: str = "0.1.1"
	debug: bool = False
	
	# Server Configuration
	host: str = "0.0.0.0"
	port: int = 8000
	
	# CORS Configuration
	cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
	
	model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

