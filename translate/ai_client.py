"""Pluggable AI client used to generate translations.

This is intentionally a thin stub: the real HTTP wiring is left for a follow-up
once the backend / provider choice is settled. The function signature is what
the rest of the translate pipeline depends on.
"""


class AIClientError(RuntimeError):
    pass


def generate_translations(prompt: str) -> str:
    """Send the prompt to the AI provider and return its raw text response.

    Replace this stub with the actual provider call (HTTP request, SDK, ...).
    Until then, raises so callers can't silently get an empty result.
    """
    raise AIClientError(
        "AI client is not configured yet. Implement `translate.ai_client.generate_translations` "
        "to call the configured AI provider."
    )
