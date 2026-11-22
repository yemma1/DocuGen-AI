import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DOCS_DIR = BASE_DIR / "generated_docs"
FRONTEND_DIR = BASE_DIR / "frontend"
METADATA_FILE = UPLOAD_DIR / "metadata.json"

# Application Settings
APP_NAME = "DocuGen AI"
APP_DESCRIPTION = "Professional Python Code Documentation Generator powered by AST Static Analysis & Explanation Engine"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# Server Configuration
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

# File Upload Settings
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".py"}

# AI Integration (Optional OpenAI)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# CORS Origins
CORS_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "*",
]

# Ensure required directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)
