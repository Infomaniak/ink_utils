"""Pluggable AI client used to generate translations."""
from typing import Any

import requests

import config


def generate_translations(prompt: str) -> str:
    """Send the prompt to the AI provider and return its raw text response.

    Replace this stub with the actual provider call (HTTP request, SDK, ...).
    Until then, raises so callers can't silently get an empty result.
    """
    return _translate_using_openai(prompt, endpoint=config.get_global("loco", "translation_endpoint"))


def _translate_using_openai(prompt: str, endpoint: str) -> Any:
    url = endpoint + "/v1/chat/completions"
    headers = {
        "Authorization": "Bearer",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "euria-code",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()  # Raise error if http error occurred

    return response.json()["choices"][0]["message"]["content"]
