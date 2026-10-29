"""Core configuration and settings for Kisan Shakti backend."""
import os
from pathlib import Path
from typing import List

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings:
    def __init__(self):
        # Load from .env manually if exists
        self._load_env_file(BASE_DIR / ".env")

        self.APP_NAME: str = os.getenv("APP_NAME", "Kisan Shakti")
        self.APP_ENV: str = os.getenv("APP_ENV", "development")
        self.DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.HOST: str = os.getenv("HOST", "127.0.0.1")

        # Database
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'kisan_shakti.db'}")

        # Model paths
        self.DISEASE_MODEL_PATH: str = os.getenv(
            "DISEASE_MODEL_PATH", str(BASE_DIR / "models" / "disease" / "plant_disease_model.pth")
        )
        self.DISEASE_CLASS_MAP: str = os.getenv(
            "DISEASE_CLASS_MAP", str(BASE_DIR / "models" / "disease" / "class_mapping.json")
        )
        self.DISEASE_METADATA: str = os.getenv(
            "DISEASE_METADATA", str(BASE_DIR / "models" / "disease" / "metadata.json")
        )
        self.CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.60"))

        # Knowledge Base
        self.KNOWLEDGE_BASE_DIR: str = os.getenv(
            "KNOWLEDGE_BASE_DIR", str(BASE_DIR / "knowledge_base" / "documents")
        )
        self.INDEX_DIR: str = os.getenv(
            "INDEX_DIR", str(BASE_DIR / "knowledge_base" / "index")
        )

        # Data paths
        self.SCHEMES_DATA_PATH: str = os.getenv(
            "SCHEMES_DATA_PATH", str(BASE_DIR / "data" / "schemes" / "schemes.json")
        )
        self.EXPERTS_DATA_PATH: str = os.getenv(
            "EXPERTS_DATA_PATH", str(BASE_DIR / "data" / "experts" / "kvk_directory.json")
        )
        self.CROPS_DATA_PATH: str = os.getenv(
            "CROPS_DATA_PATH", str(BASE_DIR / "data" / "crops" / "crop_rules.json")
        )

        # Security & Limits
        self.CORS_ORIGINS: List[str] = [
            "http://localhost:8501",
            "http://127.0.0.1:8501",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        self.MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

        # Optional external API keys
        self.GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        self.GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        self.BHASHINI_API_KEY: str = os.getenv("BHASHINI_API_KEY", "")

    def _load_env_file(self, env_path: Path):
        """Simple, zero-dependency .env file parser."""
        if not env_path.exists():
            return
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key not in os.environ:
                        os.environ[key] = val
        except Exception:
            pass


settings = Settings()
