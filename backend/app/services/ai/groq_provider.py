from groq import Groq

from app.config import settings
from app.services.ai.base import AIProvider


class GroqProvider(AIProvider):
    """
    Default/primary AI provider, backed by the Groq API.
    """

    name = "groq"

    def __init__(self):
        if not settings.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Add it to backend/.env to enable AI Insights."
            )

        self._client = Groq(api_key=settings.groq_api_key)
        self._model = settings.groq_model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1800,
        )

        return response.choices[0].message.content
