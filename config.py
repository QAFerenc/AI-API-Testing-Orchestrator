import os

from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types


PROJECT_DIR = Path(__file__).resolve().parent

load_dotenv(
    PROJECT_DIR / ".env",
    override=False
)


def get_api_key():

    api_key = os.getenv("GOOGLE_API_KEY", "").strip()

    if api_key:

        return api_key

    try:

        from google.colab import userdata

        api_key = userdata.get("GOOGLE_API_KEY")

        if api_key and api_key.strip():

            return api_key.strip()

    except Exception:

        pass

    raise RuntimeError(
        "GOOGLE_API_KEY is not configured. "
        "Set an environment variable, create a "
        ".env file, or configure Google Colab Secrets."
    )


AI_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite"
]

MAX_RETRIES = 3

ai_client = genai.Client(
    api_key=get_api_key(),
    http_options=types.HttpOptions(
        timeout=20000
    )
)
