import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE)

def get_required_environment_variable(variable_name: str) -> str:
    value = os.getenv(variable_name)

    if not value:
        raise RuntimeError(
            f"{variable_name} was not found in the environment"
        )

    return value

FINNHUB_API_TOKEN = get_required_environment_variable("FINNHUB_API_TOKEN")

TWELVE_DATA_API_KEY = get_required_environment_variable("TWELVE_DATA_API_KEY")

GEMINI_API_KEY = get_required_environment_variable("GEMINI_API_KEY")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")