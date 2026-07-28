"""
Modular AI provider layer.

Anything in this package that needs to know about the LLM provider talks to
it through `AIProvider` (see base.py) and `get_ai_provider()` (see factory.py).
Nothing outside this package should import a specific provider class
(e.g. GroqProvider) directly — go through the factory so swapping/adding a
provider never requires touching callers like `insights_service.py`.
"""
