from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


@lru_cache(maxsize=1)
def get_llm(api_key: str | None = None) -> ChatOpenAI:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")
    load_dotenv(project_root.parent / ".env")
    resolved_api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Add it to a .env file or environment variable."
        )

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        api_key=resolved_api_key,
    )