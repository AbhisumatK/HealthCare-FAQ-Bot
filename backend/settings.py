import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env", ".env"), override=True)


@dataclass
class Settings:
    scaledown_api_url: str = os.getenv("SCALEDOWN_API_URL", "")
    scaledown_api_key: str = os.getenv("SCALEDOWN_API_KEY", "")
    scaledown_compress_url: str = os.getenv("SCALEDOWN_COMPRESS_URL", "https://api.scaledown.xyz/compress/raw/")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    persist_dir: str = os.path.join("data", "chroma")
    facts_path: str = os.path.join("data", "medical_facts.json")


settings = Settings()