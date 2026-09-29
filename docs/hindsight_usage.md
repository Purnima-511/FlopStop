# How Hindsight Is Used In This Project

> Fill in the "Where used (code link)" column with real GitHub links once your repo is
> pushed, e.g. `engine/checkers.py#L14`.

| Hindsight capability | Where used (code link) | Why it matters |
|---|---|---|
| Memory bank + mission + disposition | `engine/memory.py::ensure_bank()` | Isolated per-creator memory space; `skepticism=4` makes it act like a tough editor, not a cheerleader |
| `retain` with timestamp / context / document_id | `scripts/seed_bank.py`, `app.py` (Log a Post tab), `engine/trends.py::retain_snapshot()` | Lets the agent reason in time ("this trended 3 weeks ago") and keep typed memories (`post_result`, `sponsored_post`, `caption_sample`, `trend_snapshot`) |
| `recall` | `engine/checkers.py::voice_check()`, sidebar observations in `app.py` | Raw retrieval — used where we want the actual past text (caption samples), not a reasoned answer |
| `reflect` | `engine/checkers.py::mistake_catcher()`, `engine/checkers.py::trend_advice()` | Reasoned, cited, memory-grounded decisions that apply directives and mental models automatically |
| Directives | `data/seed.py::DIRECTIVES`, `engine/memory.py::create_directive()` | Non-negotiable rules (e.g. "never approve back-to-back sponsored posts") the agent always obeys, instead of hoping a long prompt covers every case |
| Mental models | `data/seed.py::MENTAL_MODELS`, "Playbook & Insights" tab | A self-updating "Creator Playbook" that improves as new posts are logged, instead of a static prompt |
| Observations | "What I've learned about you" (sidebar + Playbook tab) | Patterns Hindsight discovers on its own, no custom logic needed |

## The before/after story

- **Interaction 1 (generic):** Ask "what should I post this week?" with no memory → generic
  advice like "post consistently, use trending audio."
- **Interaction 5 (personalized):** After a few Mistake Catcher / Voice Checker runs, the
  agent starts citing Alex's actual past posts and voice style unprompted.
- **Interaction 20 (feels like a manager):** The agent connects dots across post history,
  sponsorship timing, past trend snapshots, and audience feedback the way a manager who's
  worked with the creator for months would — e.g. catching that a new draft echoes a
  post that flopped three months ago, or noticing a trend spiking for the second time
  after being skipped the first time.

## Honest limitations

- A few Hindsight API calls (creating directives/mental models, refreshing a mental
  model, reading `reflect()`'s cited sources) were implemented against the best
  available documentation but not fully confirmed — see the `[VERIFY]` notes in
  `engine/memory.py`. The app degrades gracefully if any of these don't match the
  live API exactly.
- Google Trends (via `pytrends`) only exposes a rolling recent window — the "memory"
  of older trend snapshots comes entirely from what this app retains into Hindsight,
  not from Google Trends itself.
- This is a demo built on synthetic persona data (clearly labelled in `data/seed.py`);
  it does not pull real Instagram/YouTube data. A real integration would use the
  Instagram Graph API and YouTube Data API (requires a Business/Creator account and
  developer app approval) — noted as a next step, not built here.
