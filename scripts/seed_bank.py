"""
scripts/seed_bank.py

Run this ONCE before starting the app:
    python scripts/seed_bank.py

It creates the memory bank and loads it with the demo creator's history
(posts, captions, directives, mental models, trend snapshots), so the
agent starts "already knowing" the creator instead of an empty slate.

Safe to re-run: it skips seeding if a marker file (data/.seeded) already
exists. Force a re-seed with:
    python scripts/seed_bank.py --force
"""

import sys
import os
from datetime import datetime, timedelta

# Let this script find the `engine` and `data` packages one folder up.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine import memory
from engine.config import check_config, NICHE
from data import seed


MARKER_PATH = os.path.join(os.path.dirname(__file__), "..", "data", ".seeded")


def already_seeded() -> bool:
    return os.path.exists(MARKER_PATH)


def mark_seeded():
    with open(MARKER_PATH, "w") as f:
        f.write(f"Seeded at {datetime.now().isoformat()}\n")


def days_ago_to_timestamp(days_ago: int) -> datetime:
    return datetime.now() - timedelta(days=days_ago)


def main():
    force = "--force" in sys.argv

    if already_seeded() and not force:
        print("Already seeded (found data/.seeded). Run with --force to re-seed.")
        return

    print("Checking your .env settings...")
    check_config()

    print("Step 1/6: Creating (or confirming) the memory bank...")
    memory.ensure_bank()

    print("Step 2/6: Loading past posts...")
    for post in seed.POSTS:
        timestamp = days_ago_to_timestamp(post["days_ago"])
        date_str = timestamp.strftime("%Y-%m-%d")
        text = post["text"].format(date=date_str)
        memory.retain(
            text=text,
            context=post["context"],
            timestamp=timestamp,
            document_id=post["id"],
            metadata={"platform": post["platform"], "sponsored": post["sponsored"]},
        )
    print(f"  -> loaded {len(seed.POSTS)} posts")

    print("Step 3/6: Loading caption samples and voice summary...")
    for i, caption_text in enumerate(seed.CAPTIONS, start=1):
        memory.retain(text=caption_text, context="caption_sample", document_id=f"caption-{i:03d}")
    memory.retain(text=seed.VOICE_SUMMARY, context="caption_sample", document_id="caption-style-summary")
    print(f"  -> loaded {len(seed.CAPTIONS)} captions + 1 style summary")

    print("Step 4/6: Loading trend history...")
    for snapshot in seed.TREND_HISTORY:
        timestamp = days_ago_to_timestamp(snapshot["days_ago"])
        date_str = timestamp.strftime("%Y-%m-%d")
        text = snapshot["text"].format(date=date_str)
        memory.retain(
            text=text,
            context="trend_snapshot",
            timestamp=timestamp,
            document_id=snapshot["document_id"],
        )
    print(f"  -> loaded {len(seed.TREND_HISTORY)} trend snapshots")

    print("Step 5/6: Creating directives (hard rules)...")
    for directive in seed.DIRECTIVES:
        memory.create_directive(directive["name"], directive["content"])
    print(f"  -> created {len(seed.DIRECTIVES)} directives")

    print("Step 6/6: Creating mental models...")
    print("  (these generate in the BACKGROUND - give it a minute before checking the Playbook tab)")
    for model in seed.MENTAL_MODELS:
        memory.create_mental_model(model["name"], model["source_query"])
    print(f"  -> requested {len(seed.MENTAL_MODELS)} mental models")

    mark_seeded()
    print("\nDone! Now run: streamlit run app.py")


if __name__ == "__main__":
    main()
