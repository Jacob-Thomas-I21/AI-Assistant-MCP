"""core/llm.py — LLM wrapper using LangChain + OpenRouter."""
from langchain_openai import ChatOpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODEL_NAME


def get_llm(streaming: bool = False, temperature: float = 0.0):
    """Return a LangChain ChatOpenAI instance pointed at OpenRouter.

    Swap provider: change OPENROUTER_BASE_URL and OPENROUTER_API_KEY in .env.
    E.g. for direct OpenAI: base_url="https://api.openai.com/v1"
    """
    return ChatOpenAI(
        model=MODEL_NAME,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=temperature,
        streaming=streaming,
        default_headers={
            "HTTP-Referer": "https://github.com/ai-assistant-assessment",
            "X-Title": "AI Enterprise Assistant",
        },
    )
