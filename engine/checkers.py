"""
engine/checkers.py

The four "brain" functions of the app. None of these know anything about
Streamlit - app.py just calls these and displays the result. This
separation is what makes the code easy to test and easy to swap the UI
later (e.g. for a website instead of Streamlit).
"""

import json
from types import SimpleNamespace

from . import memory
from . import llm
from .utils import extract_json


def mistake_catcher(draft: str, platform: str = "instagram", is_sponsored: bool = False) -> dict:
    """
    F3 - CORE FEATURE #1.
    Given a draft post idea, ask Hindsight to check it against past
    flops, contradictions, directives, and sponsorship timing rules.
    """
    if not draft or not draft.strip():
        return {
            "risk_level": "safe",
            "reason": "No draft provided.",
            "evidence": [],
            "contradiction": None,
            "suggestion": "",
            "based_on": None,
        }

    query = (
        f"Creator wants to post: {draft}. Platform: {platform}. "
        f"Sponsored: {is_sponsored}. "
        "Check for: similar past flops, contradictions with past public statements, "
        "violated directives, and sponsorship timing issues. Cite specific past posts. "
        "Respond ONLY with JSON in this exact shape: "
        '{"risk_level": "safe|risky|likely_flop", "reason": "string", '
        '"evidence": ["string", ...], "contradiction": "string or null", '
        '"suggestion": "string"}'
    )

    answer = memory.reflect(query, context="pre-post safety review", budget="mid")
    based_on = memory.get_reflect_sources(answer)

    # reflect() doesn't always populate based_on.memories, even when its
    # answer clearly drew on specific past posts (the "evidence" list in
    # the parsed JSON below often has real citations even when based_on
    # comes back empty). Rather than let the sidebar Memory Panel show
    # nothing in that case, fall back to a direct recall() on the draft
    # text, so there's always something real to point to.
    memories_used = getattr(based_on, "memories", None) if based_on else None
    if not memories_used:
        fallback = memory.recall(draft, budget="mid")
        memories_used = getattr(fallback, "results", []) or []
        based_on = SimpleNamespace(
            memories=memories_used,
            directives=getattr(based_on, "directives", []) if based_on else [],
            mental_models=getattr(based_on, "mental_models", []) if based_on else [],
        )

    parsed = extract_json(getattr(answer, "text", str(answer)))

    if parsed is None:
        # Reflect didn't give clean JSON - degrade gracefully instead of crashing.
        return {
            "risk_level": "risky",
            "reason": getattr(answer, "text", str(answer)),
            "evidence": [],
            "contradiction": None,
            "suggestion": "Could not parse a structured answer - see reason above.",
            "based_on": based_on,
        }

    if not parsed.get("evidence"):
        # No relevant memory found on this exact topic yet.
        parsed.setdefault("risk_level", "safe")
        parsed.setdefault("reason", "No history on this topic yet, so confidence is low.")

    parsed["based_on"] = based_on
    return parsed


def voice_check(draft_caption: str) -> dict:
    """
    F7 - CORE FEATURE #2.
    Recall real caption samples + the voice-style summary, then have
    Groq score and rewrite the draft caption in that voice.
    """
    if not draft_caption or not draft_caption.strip():
        return {"voice_match_percent": 0, "issues": ["No caption provided."], "rewrite": "", "changes_explained": []}

    draft_caption = draft_caption[:1500]  # guard against very long input

    recalled = memory.recall("Alex's caption style and past high-performing captions", budget="mid")
    samples = [
        r.text for r in getattr(recalled, "results", [])
        if "caption" in r.text.lower() or "style" in r.text.lower()
    ]

    low_confidence = len(samples) < 3
    samples_text = "\n".join(f"- {s}" for s in samples) if samples else "(no samples recalled yet)"

    system = "You are a strict brand-voice editor for a fitness content creator."
    user = (
        f"Here are real examples of the creator's past captions and voice style:\n{samples_text}\n\n"
        f"Here is a NEW draft caption to check:\n\"{draft_caption}\"\n\n"
        "Score voice match from 0-100, list specific issues (word choice, length, tone, "
        "emoji use, whether it ends with a question), and rewrite the draft in this voice. "
        "Respond ONLY with JSON: "
        '{"voice_match_percent": int, "issues": ["string", ...], "rewrite": "string", '
        '"changes_explained": ["string", ...]}'
    )

    result = llm.chat_json(system, user)
    if result is None:
        result = {
            "voice_match_percent": 0,
            "issues": ["Could not score this caption right now, try again."],
            "rewrite": "",
            "changes_explained": [],
        }

    if low_confidence:
        result.setdefault("issues", [])
        result["issues"].insert(0, "Low confidence: fewer than 3 caption samples were found in memory yet.")

    return result


def trend_advice(summary: list) -> list:
    """
    F9. Given this week's trend summary, ask Hindsight to decide
    post_now / watch / skip for each trend, using past posts and past
    trend snapshots (including trends the creator skipped before).
    """
    if not summary:
        return []

    compact = ", ".join(
        f'{item["keyword"]} ({item["label"]}, {item["change_pct"]:+.1f}%)' for item in summary
    )

    query = (
        f"Current niche trends: {compact}. "
        "Using the creator's past posts and earlier trend snapshots, for each trend decide: "
        "post_now, watch, or skip. Prefer trends matching content formats that won before for "
        "this creator. Point out any trend that also trended earlier and was skipped. "
        "Cite specific past posts or snapshots. "
        'Respond ONLY with a JSON list: [{"trend": "string", "action": "post_now|watch|skip", '
        '"reason": "string", "past_evidence": "string"}]'
    )

    answer = memory.reflect(query, context="trend planning", budget="mid")
    parsed = extract_json(getattr(answer, "text", str(answer)))
    return parsed if isinstance(parsed, list) else []


def generic_answer(question: str) -> str:
    """
    F11 - the "without memory" side of the comparison. Plain Groq call,
    zero access to Hindsight, so it's necessarily generic advice.
    """
    system = "You are a generic social media advice assistant with no knowledge of any specific creator."
    return llm.chat(system, question)
