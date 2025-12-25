import os
from typing import Any
from dotenv import load_dotenv


CONFIG_API_ACCESS_TOKEN = "API_ACCESS_TOKEN "
CONFIG_API_URL = "API_URL"
CONFIG_ASSISTANT_ID = "ASSISTANT_ID"
CONFIG_KEYS = {CONFIG_API_ACCESS_TOKEN, CONFIG_API_URL, CONFIG_ASSISTANT_ID}


class Config:
    def __init__(self) -> None:
        """Initialize the config for the scoutcli."""
        # Load environment variables from .env file if it exists
        load_dotenv()
        self.config = {key: os.getenv(f"{key}") for key in CONFIG_KEYS}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the config."""
        return self.config.get(key, default)
