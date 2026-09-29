"""
engine/trends.py

Pulls "what's trending" data from Google Trends via pytrends (no API key
needed), summarizes it, and turns it into a memory that gets retained
into Hindsight so the agent can later say "this trended before and you
skipped it."

pytrends is unofficial and gets rate-limited (HTTP 429) often, so every
function here falls back to a local JSON cache file. We ship a prefilled
cache (data/trend_cache.json) so the demo works even with no internet.
"""

import json
import os
from datetime import datetime, timedelta

from . import memory
from .config import TREND_GEO

CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trend_cache.json")


def _load_cache():
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(data: dict):
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception:
        pass  # cache is a nice-to-have, never crash the app over it


def fetch_trends(keywords: list, geo: str = None, timeframe: str = "today 1-m") -> dict:
    """
    Try to fetch live data from Google Trends. Google Trends only allows
    5 keywords per request, and rate-limits aggressively, so on ANY
    failure we fall back to the cached file and mark it as such.
    Returns: {"source": "live"|"cache", "keywords": [...], "data": {...}}
    """
    geo = geo or TREND_GEO
    try:
        from pytrends.request import TrendReq

        pytrend = TrendReq(hl="en-US", tz=330)
        pytrend.build_payload(keywords[:5], timeframe=timeframe, geo=geo)

        interest = pytrend.interest_over_time()
        try:
            related = pytrend.related_queries()
        except Exception:
            related = {}

        result = {
            "source": "live",
            "keywords": keywords,
            "fetched_at": datetime.now().isoformat(),
            "interest_over_time": interest.to_dict() if interest is not None else {},
            "related_queries": {
                k: (v["rising"].to_dict() if v and v.get("rising") is not None else {})
                for k, v in (related or {}).items()
            },
        }
        _save_cache(result)
        return result

    except Exception as e:
        print(f"[trends] Live fetch failed ({e}), falling back to cache.")
        cached = _load_cache()
        if cached:
            cached["source"] = "cache"
            return cached
        # No cache and no internet - return an empty, clearly-labelled shape
        return {"source": "cache", "keywords": keywords, "interest_over_time": {}, "related_queries": {}}


def summarize_trends(raw: dict) -> list:
    """
    Turn raw pytrends-shaped data into a simple list of:
      {"keyword": str, "change_pct": float, "label": "rising"|"falling"|"steady", "related": [str, str, str]}

    NOTE: pytrends' interest_over_time() gives a *live* window only
    (it does not remember last month's numbers for you) - that long-term
    memory is exactly what Hindsight's retain/reflect gives us instead.
    This function just describes the *current* snapshot.
    """
    summary = []
    interest = raw.get("interest_over_time", {})
    related = raw.get("related_queries", {})

    for keyword in raw.get("keywords", []):
        series = interest.get(keyword, {})
        values = list(series.values()) if isinstance(series, dict) else []

        if len(values) >= 7:
            last_7 = values[-7:]
            prior = values[:-7] or values  # everything before the last 7 days
            avg_recent = sum(last_7) / len(last_7)
            avg_prior = sum(prior) / len(prior) if prior else avg_recent
            change_pct = ((avg_recent - avg_prior) / avg_prior * 100) if avg_prior else 0
        else:
            change_pct = 0  # not enough data (e.g. cache is empty/synthetic)

        if change_pct > 25:
            label = "rising"
        elif change_pct < -25:
            label = "falling"
        else:
            label = "steady"

        rising_related = list(related.get(keyword, {}).keys())[:3]

        summary.append({
            "keyword": keyword,
            "change_pct": round(change_pct, 1),
            "label": label,
            "related": rising_related,
        })

    return summary


def snapshot_to_text(summary: list, date_str: str, niche: str) -> str:
    """Turn a summary list into one natural-language memory."""
    lines = [f"Trend snapshot for the {niche} niche, week of {date_str}:"]
    for item in summary:
        related_text = f" Related rising searches: {', '.join(item['related'])}." if item["related"] else ""
        lines.append(
            f' "{item["keyword"]}" interest is {item["label"]} '
            f'({item["change_pct"]:+.1f}% vs the prior period).{related_text}'
        )
    return " ".join(lines)


def retain_snapshot(summary: list, niche: str):
    """Save this week's trend snapshot into Hindsight memory."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    text = snapshot_to_text(summary, date_str, niche)
    slug = "-".join(k["keyword"].replace(" ", "-") for k in summary[:2])
    memory.retain(
        text=text,
        context="trend_snapshot",
        timestamp=datetime.now(),
        document_id=f"trend-{date_str}-{slug}",
    )
    return text
