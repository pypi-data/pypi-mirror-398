import os
import typer
from pathlib import Path

APP_NAME = "locknkey"
CONFIG_DIR = typer.get_app_dir(APP_NAME)
CREDENTIALS_FILE = Path(CONFIG_DIR) / "credentials.json"
SESSION_FILE = Path(CONFIG_DIR) / "session.json"

def ensure_config_dir():
    Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
