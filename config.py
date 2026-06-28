"""
config.py - Central configuration for the AI Assistant.

Provider selection:
  Set LLM_PROVIDER in .env to switch between backends.
  Supported: openrouter | openai | anthropic
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR  = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data"
DOCS_DIR  = DATA_DIR / "documents"
CSV_PATH  = DATA_DIR / "structured" / "branch_performance.csv"
CHROMA_DIR = DATA_DIR / "chroma_db"
FEEDBACK_DB = BASE_DIR / "feedback" / "feedback.db"

# LLM provider — switch by setting LLM_PROVIDER in .env
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")  # openrouter | openai | anthropic

# Models — change these to switch models without touching agent code
PROD_MODEL = os.getenv("PROD_MODEL", "anthropic/claude-sonnet-4.5")
DEV_MODEL  = os.getenv("DEV_MODEL",  "openai/gpt-4o-mini")

# Which model agents actually use
ACTIVE_MODEL = PROD_MODEL

# Provider credentials and base URLs
OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL     = "https://api.openai.com/v1"

ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL  = "https://api.anthropic.com/v1"  # via OpenAI-compat layer

# Embeddings (always via OpenRouter unless overridden)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")

# RAG
CHUNK_SIZE           = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP        = int(os.getenv("CHUNK_OVERLAP", 100))
TOP_K                = int(os.getenv("TOP_K", 5))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.35))
COLLECTION_NAME      = "enterprise_docs"

# MCP
MCP_SERVER_SCRIPT = str(BASE_DIR / "tools" / "mcp_server.py")
