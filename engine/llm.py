"""
engine/llm.py

This is the ONLY file that talks to Groq (the LLM) directly. Used for:
- generic "no memory" baseline answers (F11 comparison)
- rewriting captions in the creator's voice (F7)
- formatting fallbacks when we need strict JSON back
"""

from groq import Groq

from .config import GROQ_API_KEY, GROQ_MODEL
from .utils import safe_call, extract_json

_client = Groq(api_key=GROQ_API_KEY)


def chat(system: str, user: str, temperature: float = 0.4) -> str:
    """Plain chat call. Returns the model's reply as a string."""

    def _call():
        response = _client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content

    return safe_call(_call)


def chat_json(system: str, user: str):
    """
    Same as chat(), but instructs the model to reply with ONLY JSON, then
    parses it. Returns a Python dict/list, or None if parsing failed
    (callers should handle the None case with a friendly fallback).
    """
    strict_system = system + " Respond ONLY with valid JSON, no prose, no code fences."
    text = chat(strict_system, user, temperature=0.2)
    return extract_json(text)
