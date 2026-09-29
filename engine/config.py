"""
engine/config.py

All settings for the whole project live here, in one place.
Two kinds of settings:
  1. SECRETS (API keys, URLs) -> loaded from the .env file, never hard-coded.
  2. PERSONA/NICHE settings -> plain Python values you can edit to swap
     the demo creator from "fitness" to "beauty" or "finance" without
     touching any other file in the project.
"""

import os
from dotenv import load_dotenv

# This line reads the ".env" file (if it exists) and loads its values
# into the environment, so os.getenv(...) below can find them.
load_dotenv()

# ---------------------------------------------------------------------
# 1. SECRETS - pulled from .env. Do not put real keys directly in this
#    file; put them in .env instead (which is git-ignored).
# ---------------------------------------------------------------------
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY", "")
HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
BANK_ID = os.getenv("BANK_ID", "creator-alex")

# ---------------------------------------------------------------------
# 2. PERSONA / NICHE - change these to re-theme the whole demo.
#    (The actual seed content lives in data/seed.py, which reads NICHE
#    and CREATOR_NAME from here so everything stays in sync.)
# ---------------------------------------------------------------------
NICHE = "fitness"
CREATOR_NAME = "Alex Rivera"
TREND_KEYWORDS = [
    "high protein snacks",
    "home workout",
    "morning routine",
    "gym motivation",
    "creatine",
]
TREND_GEO = "IN"  # Google Trends country code. "IN" = India.

# A quick startup check so beginners get a friendly error instead of a
# confusing crash three files deep.
def check_config():
    missing = []
    if not HINDSIGHT_API_KEY:
        missing.append("HINDSIGHT_API_KEY")
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if missing:
        raise RuntimeError(
            "Missing required settings in your .env file: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill these in."
        )
