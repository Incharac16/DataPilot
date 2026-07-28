from abc import ABC, abstractmethod


class AIProvider(ABC):
    """
    Common interface every AI provider must implement.

    To add a new provider later (e.g. Gemini, OpenAI):
      1. Add a module here, e.g. app/services/ai/gemini_provider.py, with a
         class that extends AIProvider and implements `generate`.
      2. Register it in `_PROVIDERS` in app/services/ai/factory.py.
      3. Add its settings (api key, model name, ...) to app/config.py.

    No other file needs to change — routers and insights_service.py only
    ever call `get_ai_provider()` and use the AIProvider interface below.
    """

    #: Short machine-readable identifier, e.g. "groq". Used as the value of
    #: the AI_PROVIDER environment variable and as the factory registry key.
    name: str = "base"

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a system + user prompt to the underlying LLM and return the
        text of the model's response.

        Implementations should let failures (missing/invalid API key,
        network errors, provider-side errors) raise as real exceptions
        rather than returning an error string — callers rely on this to
        distinguish a successful insight from a failed one.
        """
        raise NotImplementedError
