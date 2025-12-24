import os
from typing import Optional


def get_host() -> str:
    return os.getenv(
        "KOLENA_API_URL",
        os.getenv("RESTRUCTURED_API_URL", "https://agents-api.kolena.com"),
    )


def get_api_key() -> Optional[str]:
    return os.getenv("KOLENA_API_KEY") or os.getenv("RESTRUCTURED_API_KEY")
