"""
engine/memory.py

This is the ONLY file in the project that talks to Hindsight directly.
Everything else (checkers.py, app.py, seed_bank.py) calls the functions
below instead of importing hindsight_client itself. That way, if the
Hindsight API ever changes, you only fix it in one place.

Core ideas:
- retain()  -> save a memory (a fact, a post result, a caption, etc.)
- recall()  -> raw search: "give me memories related to X"
- reflect() -> reasoned answer: "given everything you know, answer X",
               using directives + mental models + memories together.

IMPORTANT - things marked [VERIFY]:
Some Hindsight features (creating directives, creating mental models,
refreshing a mental model, and reading "sources" off a reflect() answer)
were not 100% confirmed against the live docs when this file was written.
Before relying on them, check:
  https://hindsight.vectorize.io/developer/api/mental-models
  https://hindsight.vectorize.io/sdks/python
Each spot below is wrapped in a try/except so the app *degrades
gracefully* instead of crashing if a method name is slightly different
than guessed here.
"""

from hindsight_client import Hindsight

from .config import HINDSIGHT_API_KEY, HINDSIGHT_BASE_URL, BANK_ID, CREATOR_NAME, NICHE
from .utils import safe_call, AppError

# One shared client for the whole app.
client = Hindsight(base_url=HINDSIGHT_BASE_URL, api_key=HINDSIGHT_API_KEY, timeout=60.0)


def ensure_bank():
    """
    Create the memory bank for this creator if it doesn't exist yet.
    Safe to call every time the app starts - if the bank already
    exists, Hindsight (or our except block) just quietly moves on.
    """
    try:
        client.create_bank(
            bank_id=BANK_ID,
            name=f"{CREATOR_NAME} ({NICHE} creator)",
            mission=(
                "Track this creator's post performance, audience feedback, "
                "sponsorships, caption voice, and trend decisions. "
                "Help avoid repeated mistakes."
            ),
            # Disposition shapes reflect()'s "personality": skepticism makes
            # it a tougher editor instead of a cheerleader. Each is 1-5.
            disposition={"skepticism": 4, "literalism": 3, "empathy": 3},
        )
    except Exception:
        # Bank almost certainly already exists - that's fine.
        pass


def _stringify_metadata(metadata: dict):
    """
    Hindsight requires metadata VALUES to be strings - it rejects booleans,
    numbers, etc. Rather than remembering to str() everything at every call
    site, we sanitize it once, here, so it's never an issue anywhere else
    in the app (seed_bank.py, the Log a Post tab, trends.py, ...).
    """
    if not metadata:
        return metadata
    return {k: str(v) for k, v in metadata.items()}


def retain(text: str, context: str, timestamp=None, document_id: str = None, metadata: dict = None):
    """Save one memory. `context` is a short label like 'post_result'."""
    return safe_call(
        client.retain,
        bank_id=BANK_ID,
        content=text,
        context=context,
        timestamp=timestamp,
        document_id=document_id,
        metadata=_stringify_metadata(metadata),
        retain_async=False,  # False = searchable immediately (good for demos)
    )


def recall(query: str, types: list = None, budget: str = "mid", max_tokens: int = 4096):
    """Raw search: returns the memories most relevant to `query`."""
    kwargs = dict(bank_id=BANK_ID, query=query, budget=budget, max_tokens=max_tokens)
    if types:
        kwargs["types"] = types
    return safe_call(client.recall, **kwargs)


def reflect(query: str, context: str = None, budget: str = "mid", apply_all_directives: bool = True):
    """
    Reasoned answer: Hindsight combines memories + directives + mental
    models and answers `query`, citing what it used.

    apply_all_directives=True forces every active directive into context
    for this call, instead of leaving it up to the agent to decide a
    directive is relevant enough to look up. For a "hard rules" feature
    like the Mistake Catcher, we want the rules checked every time.
    """
    kwargs = dict(bank_id=BANK_ID, query=query, budget=budget, apply_all_directives=apply_all_directives)
    if context:
        kwargs["context"] = context
    return safe_call(client.reflect, **kwargs)


def list_directives():
    """Returns a plain list of directives (each has .id, .name, .content, .priority, .is_active)."""
    try:
        response = safe_call(client.list_directives, bank_id=BANK_ID)
        return response.items if response else []
    except AppError:
        return []


def list_mental_models():
    """
    Returns a plain list of mental models, WITH their content and source
    query filled in (detail="content" - without it, the API only returns
    metadata like name/id/timestamps, no actual text).
    """
    try:
        response = safe_call(client.list_mental_models, bank_id=BANK_ID, detail="content")
        return response.items if response else []
    except AppError:
        return []


def get_reflect_sources(reflect_answer):
    """
    Pull out which memories/directives/mental models a reflect() answer
    was based on, for the sidebar "Memory Panel". reflect() returns this
    under `.based_on`, which has three lists: .memories, .directives,
    .mental_models (each item has a .text or .content field).
    """
    return getattr(reflect_answer, "based_on", None)


def create_directive(name: str, content: str, priority: int = 0):
    """Create one hard-rule directive. Returns the created directive, or None on failure."""
    try:
        return safe_call(
            client.create_directive,
            bank_id=BANK_ID, name=name, content=content, priority=priority, is_active=True,
        )
    except Exception as e:
        print(f"[WARN] Could not create directive '{name}': {e}")
        return None


def create_mental_model(name: str, source_query: str):
    """
    Create one mental model. This runs reflect() in the BACKGROUND and
    returns immediately with an operation id - the actual content may
    take a little while to appear in list_mental_models()/get_playbook().
    """
    try:
        return safe_call(
            client.create_mental_model, bank_id=BANK_ID, name=name, source_query=source_query,
        )
    except Exception as e:
        print(f"[WARN] Could not create mental model '{name}': {e}")
        return None


def refresh_mental_model(mental_model_id: str):
    """Ask Hindsight to regenerate one mental model's content from current memories."""
    try:
        return safe_call(client.refresh_mental_model, bank_id=BANK_ID, mental_model_id=mental_model_id)
    except Exception as e:
        print(f"[WARN] Could not refresh mental model '{mental_model_id}': {e}")
        return None


def get_playbook():
    """Convenience helper for the 'Playbook & Insights' tab."""
    return list_mental_models()


def list_all_memories(search_query: str = None, limit: int = 200):
    """
    Returns a plain list of every memory in the bank (optionally filtered
    by a search query). Used for the "All Memories" browser tab so a
    creator can manually scroll/search their own history, not just get
    AI answers about it.
    """
    try:
        response = safe_call(client.list_memories, bank_id=BANK_ID, search_query=search_query, limit=limit)
        return response.items if response else []
    except AppError:
        return []


def count_all_memories():
    """Cheap total-count check (limit=1) for the Home dashboard's stats row."""
    try:
        response = safe_call(client.list_memories, bank_id=BANK_ID, limit=1)
        return response.total if response else 0
    except AppError:
        return 0
