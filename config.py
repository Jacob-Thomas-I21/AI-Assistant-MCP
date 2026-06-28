"""
config.py — Central configuration for the AI Assistant.
Load settings from .env file with sensible defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "documents"
CSV_PATH = DATA_DIR / "structured" / "branch_performance.csv"
CHROMA_DIR = DATA_DIR / "chroma_db"
FEEDBACK_DB = BASE_DIR / "feedback" / "feedback.db"

# ── LLM ───────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")

# ── Embeddings ─────────────────────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")

# ── RAG ────────────────────────────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))
TOP_K = int(os.getenv("TOP_K", 5))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.35))
COLLECTION_NAME = "enterprise_docs"

# ── MCP Server ─────────────────────────────────────────────────────────────
MCP_SERVER_SCRIPT = str(BASE_DIR / "tools" / "mcp_server.py")
