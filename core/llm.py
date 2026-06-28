"""core/llm.py - LangChain LLM wrapper with multi-provider support."""
from langchain_openai import ChatOpenAI
from config import (
    LLM_PROVIDER,
    ACTIVE_MODEL,
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL,
    OPENAI_API_KEY, OPENAI_BASE_URL,
    ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL,
)

# Provider config lookup
_PROVIDERS = {
    "openrouter": {
        "api_key": OPENROUTER_API_KEY,
        "base_url": OPENROUTER_BASE_URL,
        "default_headers": {
            "HTTP-Referer": "https://github.com/ai-assistant-mcp",
            "X-Title": "AI Enterprise Assistant",
        },
    },
    "openai": {
        "api_key": OPENAI_API_KEY,
        "base_url": OPENAI_BASE_URL,
        "default_headers": {},
    },
    "anthropic": {
        # Anthropic via OpenAI-compatible endpoint (use openrouter for cleaner Anthropic access)
        "api_key": ANTHROPIC_API_KEY,
        "base_url": ANTHROPIC_BASE_URL,
        "default_headers": {},
    },
}


def get_llm(streaming: bool = False, temperature: float = 0.0, model: str = None):
    """
    Return a LangChain ChatOpenAI instance for the configured provider.

    Provider is set via LLM_PROVIDER in .env (openrouter | openai | anthropic).
    Model defaults to ACTIVE_MODEL (production) unless overridden.

    Example — swap to dev model for a lightweight call:
        get_llm(model=DEV_MODEL)
    """
    provider = _PROVIDERS.get(LLM_PROVIDER)
    if provider is None:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{LLM_PROVIDER}'. "
            f"Must be one of: {list(_PROVIDERS.keys())}"
        )

    return ChatOpenAI(
        model=model or ACTIVE_MODEL,
        api_key=provider["api_key"],
        base_url=provider["base_url"],
        temperature=temperature,
        streaming=streaming,
        default_headers=provider["default_headers"],
    )
