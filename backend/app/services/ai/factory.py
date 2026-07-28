from app.config import settings
from app.services.ai.base import AIProvider
from app.services.ai.groq_provider import GroqProvider

# Registry of available providers, keyed by the AI_PROVIDER env var value.
# Groq is implemented and is the default/primary provider. To add another
# provider (Gemini, OpenAI, ...) later: implement it as an AIProvider
# subclass in its own module and add one line here — no other code changes
# needed.
_PROVIDERS: dict[str, type[AIProvider]] = {
    "groq": GroqProvider,
}


def get_ai_provider() -> AIProvider:
    """
    Instantiate the AI provider selected by settings.ai_provider (default:
    "groq"). Raises ValueError — which routers/insights.py turns into a
    clean 503 — if the configured provider isn't registered, or if the
    provider itself isn't fully configured (e.g. missing API key).
    """
    provider_key = (settings.ai_provider or "groq").strip().lower()

    provider_cls = _PROVIDERS.get(provider_key)
    if provider_cls is None:
        supported = ", ".join(sorted(_PROVIDERS)) or "none"
        raise ValueError(
            f"Unsupported AI_PROVIDER '{provider_key}'. Supported providers: {supported}"
        )

    return provider_cls()
