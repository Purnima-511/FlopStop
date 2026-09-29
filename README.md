# Creator Memory Agent

A memory-powered AI co-pilot for content creators, built on [Hindsight](https://hindsight.vectorize.io/).

> Most AI content tools give generic advice. This one remembers what actually worked
> for *this specific creator*, catches mistakes before they post, writes captions in
> their own voice, and spots trends they've ignored before — getting sharper with
> every post.

Demo persona: **Alex Rivera**, a fitness/wellness creator (Instagram + YouTube).
The niche is configurable — see `engine/config.py`.

---

## What it does

| Tab | What it does |
|---|---|
| 🚫 Mistake Catcher | Flags risky drafts (past flops, contradictions, broken rules), cites the exact past post |
| 🎙️ Voice Checker | Scores a caption's voice match and rewrites it in the creator's own voice |
| 📈 Trend Radar | Pulls Google Trends data, remembers past trend snapshots, tells you post_now / watch / skip |
| ✍️ Log a Post | Log a new result — the agent updates instantly and changes future answers |
| 📖 Playbook & Insights | A self-updating "what works for this creator" summary, plus an engagement chart |

---

## Requirements

- Python 3.10+
- A free [Hindsight Cloud](https://ui.hindsight.vectorize.io) account + API key
- A free [Groq](https://groq.com) account + API key

If you haven't installed anything yet, see the "getting started" checklist below.

### Getting started (first time only)
1. Install **Python 3.10+** from [python.org](https://python.org/downloads) (on Windows, tick "Add Python to PATH" during install).
2. Install **VS Code** from [code.visualstudio.com](https://code.visualstudio.com).
3. Install **Git** from [git-scm.com](https://git-scm.com/downloads).
4. Open this folder in VS Code, then open a terminal inside it (`View > Terminal`).

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy the example env file and fill in your real API keys
cp .env.example .env
# (on Windows: copy .env.example .env)
# then open .env in VS Code and paste in your Hindsight + Groq keys

# 3. Seed the memory bank with demo data (run once)
python scripts/seed_bank.py

# 4. Run the app (use this exact form if "streamlit" isn't recognized as a command)
python -m streamlit run app.py
```

Streamlit will open a browser tab automatically (usually `http://localhost:8501`).

**Note on timing:** directives (hard rules) are created instantly, but mental models
(the "Creator Playbook") generate in the *background* after seeding — give it 30-60
seconds after `seed_bank.py` finishes before checking the "Playbook & Insights" tab,
or just click "Refresh playbook" again in a minute.

---

## Project structure

```
creator-memory-agent/
├── app.py                 # Streamlit UI (no business logic)
├── engine/
│   ├── config.py           # env vars + persona/niche settings
│   ├── memory.py            # ALL Hindsight calls live here
│   ├── llm.py                # ALL Groq calls live here
│   ├── checkers.py           # mistake_catcher, voice_check, trend_advice, generic_answer
│   ├── trends.py              # Google Trends fetch/summarize/cache
│   └── utils.py                # retry wrapper + JSON extractor
├── data/
│   ├── seed.py             # synthetic demo persona data (clearly labelled as such)
│   └── trend_cache.json     # prefilled offline demo cache
├── scripts/
│   └── seed_bank.py        # one-time: create bank + load seed data
├── docs/
│   └── hindsight_usage.md  # write-up of how Hindsight is used (fill in before submitting)
├── .env.example
└── requirements.txt
```

**Rule the code follows:** the engine never imports Streamlit, and the UI never talks to
Hindsight or Groq directly — everything goes through `engine/memory.py` and `engine/llm.py`.
This keeps the logic testable and lets you swap the UI later without rewriting the brain.

---

## Things marked [VERIFY] in the code

A few Hindsight calls (creating directives, creating mental models, refreshing a mental
model, and reading "sources" off a `reflect()` answer) weren't confirmed against the live
docs when this was written. They're wrapped in `try/except` so the app never crashes —
worst case, you'll see a `[VERIFY]` warning printed in the terminal telling you exactly
what to check. Confirm the real method names at:
- https://hindsight.vectorize.io/sdks/python
- https://hindsight.vectorize.io/developer/api/mental-models

If a call fails, the app degrades gracefully (e.g. falls back to a plain `recall()` for
the Memory Panel) rather than breaking.

---

## Troubleshooting

- **"Missing required settings in your .env file"** → you haven't filled in `.env` yet, or named it something else. It must be exactly `.env` in the project root.
- **Trend Radar shows CACHED, not LIVE** → Google Trends rate-limited the request (common). The cached demo data still works fine for showing the feature.
- **Streamlit says "command not found"** → run `pip install -r requirements.txt` again, then make sure you're using the same Python that has Streamlit installed (`python -m streamlit run app.py` also works).
- **Seeding twice** → it's safe, `scripts/seed_bank.py` skips itself if already seeded. Use `--force` to redo it.

---

## Notes on the demo data

Everything in `data/seed.py` is **synthetic** — a fictional creator's post history, written
to be realistic so the agent has something meaningful to reason over from the first run.
`data/trend_cache.json` is also synthetic, generated so the Trend Radar tab works fully
offline.
