from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./lagent.db"
    
    # Model settings
    OPENAI_API_KEY: str | None = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    # Alias often used
    OPENAI_BASE_URL: str | None = None
    MODEL_NAME: str = "gpt-3.5-turbo"
    # Alias often used
    OPENAI_MODEL_NAME: str | None = None
    API_CODE: str | None = None
    
    # Security
    MAX_STEPS: int = 20
    FC_TIMEOUT: int = 60
    DEBUG: bool = False
    
    # Tool Usage Policies
    MIN_TOOL_USE: int = 1
    MAX_TOOL_USE: int = 15
    
    # Cost Settings
    # Default example price
    INPUT_PRICE_PER_1K: float = 0.0015
    # Default example price
    OUTPUT_PRICE_PER_1K: float = 0.002
    CURRENCY_UNIT: str = "CNY"
    
    # Model Configuration Source: 'env' or 'db'
    MODEL_CONFIG_SOURCE: str = "env" 
    
    # Interception
    FINAL_ANSWER_MARKER: str = "###FINAL_ANSWER###"
    
    # Function Calling Support
    SUPPORTS_FUNCTION_CALLING: bool = False
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings():
    return Settings()

def init_config():
    """
    Initialize the configuration by creating a .env file in the current working directory.
    """
    import shutil
    import os
    from pathlib import Path
    
    cwd = Path.cwd()
    env_path = cwd / ".env"
    
    if env_path.exists():
        print(f"Config file already exists at: {env_path}")
        return

    # Locate template within the package
    package_dir = Path(__file__).parent
    template_path = package_dir / "env_template"
    
    if not template_path.exists():
        print(f"Error: Template file not found at {template_path}")
        return
        
    shutil.copy(template_path, env_path)
    print(f"Initialized configuration file at: {env_path}")
    print("Please edit .env to set your Models config.")
