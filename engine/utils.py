"""
engine/utils.py

Small helpers used everywhere else in the project:

- safe_call(): calls any function, and if it fails (timeout, rate limit,
  server hiccup), waits a little and tries again a few times before
  giving up with a friendly error. This is what keeps the Streamlit app
  from ever showing a scary red stack trace to a user.

- extract_json(): the AI models we use are asked to reply with pure
  JSON, but they sometimes wrap it in ```json fences or add a stray
  sentence before/after. This function digs the real JSON out safely.
"""

import time
import json
import re


class AppError(Exception):
    """A friendly error we can show directly in the Streamlit UI."""
    pass


def safe_call(fn, *args, retries: int = 3, backoff: float = 1.5, **kwargs):
    """
    Call fn(*args, **kwargs). If it raises an exception, wait and retry,
    up to `retries` times, waiting longer each time (exponential backoff).
    If it still fails after all retries, raise a clean AppError instead
    of the raw (often confusing) underlying exception.
    """
    last_error = None
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001 - intentionally broad; see note below
            # NOTE: once you know the exact exception classes Hindsight/Groq
            # raise (timeouts, 429 rate limits, etc.), you can narrow this
            # "except Exception" down. Broad is fine to start with.
            last_error = e
            time.sleep(backoff ** attempt)
    raise AppError(f"Call failed after {retries} tries: {last_error}")


def extract_json(text: str):
    """
    Pull the first valid JSON object or array out of a block of text.
    Handles cases like:
        ```json
        {"a": 1}
        ```
    or:
        Sure! Here's the JSON: {"a": 1}
    Returns None if nothing parseable is found.
    """
    if not text:
        return None

    # Strip markdown code fences like ```json or ```
    cleaned = re.sub(r"```(?:json)?", "", text).strip()

    # Try to find a {...} object first, then a [...] array.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = cleaned.find(opener)
        end = cleaned.rfind(closer)
        if start != -1 and end > start:
            candidate = cleaned[start:end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    return None
