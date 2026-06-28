"""core/embeddings.py — OpenRouter API embeddings."""
from langchain_openai import OpenAIEmbeddings
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, EMBEDDING_MODEL

# module-level singleton so the model isn't reloaded on every call
_embeddings = None


def get_embeddings() -> OpenAIEmbeddings:
    """Return the shared OpenAI/OpenRouter embeddings instance."""
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base=OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "https://github.com/ai-assistant-assessment",
                "X-Title": "AI Enterprise Assistant",
            }
        )
    return _embeddings
