"""
app.py

The Streamlit UI. This file should stay "thin": it collects input,
calls functions from engine/, and displays results. All the actual
logic (talking to Hindsight and Groq) lives in the engine/ folder.

Run with:  python -m streamlit run app.py
"""

from datetime import datetime

import pandas as pd
import streamlit as st

from engine import memory, checkers, trends
from engine.config import CREATOR_NAME, NICHE, TREND_KEYWORDS, TREND_GEO, check_config
from engine.utils import AppError, extract_json
from data.seed import POSTS, PERSONA

st.set_page_config(page_title="Creator Memory Agent", layout="wide")


# -----------------------------------------------------------------
# Startup: friendly error if .env isn't filled in, and a cached
# Hindsight client so we don't reconnect on every rerun.
# -----------------------------------------------------------------
try:
    check_config()
except RuntimeError as e:
    st.error(str(e))
    st.stop()


@st.cache_resource
def get_client():
    memory.ensure_bank()
    return memory.client


get_client()

# ---- session state defaults (all session-only, never touches Hindsight) ----
if "last_sources" not in st.session_state:
    st.session_state["last_sources"] = None
if "logged_posts" not in st.session_state:
    # Posts logged during THIS session (F8). Kept separately from the static
    # demo data in data/seed.py so the engagement chart can include them
    # immediately without re-fetching everything from Hindsight.
    st.session_state["logged_posts"] = []
if "mistake_history" not in st.session_state:
    # Every Mistake Catcher check run this session (newest first), for the
    # "check history" panel and the Home dashboard's recent activity feed.
    st.session_state["mistake_history"] = []


def sanitize_markdown(text: str) -> str:
    """
    LLM-generated markdown sometimes breaks a table cell across several
    literal newlines instead of using one line per row. Streamlit's
    markdown renderer doesn't handle that gracefully - it draws garbled,
    overlapping text. This holds onto any "continuation" lines (lines
    with no pipe character, appearing between real table rows) and
    stitches them onto the front of the next real row line, so each row
    ends up back on one line the way markdown tables expect. It's a
    no-op on normal text that has no tables.
    """
    if not text:
        return text
    lines = text.split("\n")
    fixed = []
    pending = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        has_pipe = "|" in stripped
        is_separator = bool(stripped) and set(stripped) <= set("|-: ")
        if has_pipe:
            if pending and not is_separator:
                line = " ".join(pending) + " " + line.strip()
                pending = []
            fixed.append(line)
            in_table = True
        elif in_table and stripped:
            pending.append(stripped)
        else:
            if pending:
                fixed.extend(pending)
                pending = []
            fixed.append(line)
            if stripped == "":
                in_table = False
    if pending:
        fixed.extend(pending)
    return "\n".join(fixed)


def render_memory_panel():
    """
    Sidebar block showing what memory was used for the last answer.
    reflect()'s `based_on` has three separate lists: memories, directives,
    and mental_models used to produce the answer.
    """
    st.sidebar.subheader("🧠 Memory Panel")
    sources = st.session_state.get("last_sources")
    if not sources:
        st.sidebar.caption("Run a check to see which memories it used.")
        return

    memories = getattr(sources, "memories", None) or []
    directives_used = getattr(sources, "directives", None) or []
    models_used = getattr(sources, "mental_models", None) or []

    if not memories and not directives_used and not models_used:
        st.sidebar.caption("No specific memories were cited for that answer.")
        return

    if memories:
        st.sidebar.markdown("**Memories used:**")
        for m in memories[:5]:
            st.sidebar.markdown(f"- {m.text}")
    if directives_used:
        st.sidebar.markdown("**Directives applied:**")
        for d in directives_used[:5]:
            st.sidebar.markdown(f"- **{d.name}:** {d.content}")
    if models_used:
        st.sidebar.markdown("**Mental models consulted:**")
        for mm in models_used[:3]:
            preview = mm.text[:180] + ("..." if len(mm.text) > 180 else "")
            st.sidebar.markdown(f"- {preview}")


def render_recent_posts():
    """
    Sidebar block confirming what's actually been saved to memory this
    session. This exists specifically so logging a post gives immediate,
    visible proof it was written to Hindsight - not just a toast message
    that disappears.
    """
    st.sidebar.subheader("🆕 Recently Uploaded Posts")
    logged = st.session_state.get("logged_posts", [])
    if not logged:
        st.sidebar.caption("Nothing logged yet this session. Use 'Log a Post' - it'll show up here once saved.")
        return
    for p in reversed(logged[-6:]):
        st.sidebar.markdown(f"✅ **{p.get('topic', p['id'])}**")
        st.sidebar.caption(f"{p.get('platform', '?')} · {p.get('format', '?')} · {p.get('outcome', '?')} · {p.get('date', '')}")


# -----------------------------------------------------------------
# Header
# -----------------------------------------------------------------
st.title("🧠 Creator Memory Agent")
st.caption(
    "Most AI content tools give generic advice. This one remembers what actually worked "
    f"for {CREATOR_NAME}, catches mistakes before they post, writes captions in their own "
    "voice, and spots trends they've ignored before."
)
st.markdown(f"**Active creator:** {CREATOR_NAME} &nbsp;|&nbsp; **Niche:** {NICHE}")

render_memory_panel()
render_recent_posts()


tab_home, tab_mistake, tab_voice, tab_trends, tab_log, tab_playbook, tab_browse = st.tabs(
    [
        "🏠 Home",
        "🚫 Mistake Catcher",
        "🎙️ Voice Checker",
        "📈 Trend Radar",
        "✍️ Log a Post",
        "📖 Playbook & Insights",
        "🗂️ All Memories",
    ]
)


# ===================================================================
# TAB 0: Home dashboard - snapshot of the creator + the bank + this
# session's activity. Read-only: doesn't call retain/create anything.
# ===================================================================
with tab_home:
    st.subheader(f"{PERSONA['name']}'s snapshot")

    persona_col, stats_col = st.columns([1, 2])
    with persona_col:
        with st.container(border=True):
            st.markdown(f"### {PERSONA['name']}")
            st.write(f"**Niche:** {PERSONA['niche'].title()}")
            st.write(f"**Location:** {PERSONA['location']}")
            st.write(f"**Platforms:** {PERSONA['platforms']}")
            st.write(f"**Sponsors:** {', '.join(PERSONA['sponsors'])}")
            st.caption(f"Voice: {PERSONA['voice']}")

    with stats_col:
        try:
            directive_count = len(memory.list_directives())
        except AppError:
            directive_count = 0
        try:
            model_count = len(memory.get_playbook())
        except AppError:
            model_count = 0
        total_memories = memory.count_all_memories()
        checks_this_session = len(st.session_state["mistake_history"])
        logged_this_session = len(st.session_state["logged_posts"])

        m1, m2, m3 = st.columns(3)
        m1.metric("Total memories in bank", total_memories)
        m2.metric("Active directives", directive_count)
        m3.metric("Mental models", model_count)
        m4, m5 = st.columns(2)
        m4.metric("Checks run this session", checks_this_session)
        m5.metric("Posts logged this session", logged_this_session)

    st.divider()
    st.subheader("What each tab does")
    cards = [
        ("🚫 Mistake Catcher", "Flags risky drafts before you post - cites the exact past post and rule."),
        ("🎙️ Voice Checker", "Scores a caption's voice match and rewrites it in your own voice."),
        ("📈 Trend Radar", "Shows current niche trends and whether to post now, watch, or skip."),
        ("✍️ Log a Post", "Log a new result so the agent updates instantly."),
        ("📖 Playbook & Insights", "Self-updating playbook, a weekly content brief, and the engagement chart."),
        ("🗂️ All Memories", "Browse and search everything stored, for manual reference."),
    ]
    cols = st.columns(3)
    for i, (card_title, desc) in enumerate(cards):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{card_title}**")
                st.caption(desc)

    st.divider()
    st.subheader("Recent activity")
    history = st.session_state["mistake_history"]
    if history:
        badge_map = {"safe": "🟢", "risky": "🟡", "likely_flop": "🔴"}
        for h in history[:5]:
            st.markdown(f"{badge_map.get(h['risk_level'], '🟡')} `{h['time']}` — {h['draft']}")
    else:
        st.caption("No checks run yet this session - head to Mistake Catcher to try one.")


# ===================================================================
# TAB 1: Mistake Catcher (F3) + With/Without Memory toggle (F11)
# ===================================================================
with tab_mistake:
    st.subheader("Check a draft before you post it")
    draft = st.text_area("What are you thinking of posting?", height=100, key="mistake_draft")
    col_a, col_b = st.columns(2)
    with col_a:
        platform = st.selectbox("Platform", ["instagram", "youtube"], key="mistake_platform")
    with col_b:
        is_sponsored = st.checkbox("This is a sponsored post", key="mistake_sponsored")

    if st.button("Check my draft", type="primary"):
        if not draft.strip():
            st.warning("Type a draft first.")
        else:
            with st.spinner("Checking against memory..."):
                try:
                    result = checkers.mistake_catcher(draft, platform, is_sponsored)
                    # Store the result AND force an immediate rerun. Streamlit draws
                    # the sidebar before this button's code runs, so without the
                    # rerun the Memory Panel would always show last click's data,
                    # one step behind. Rerunning makes the sidebar redraw with the
                    # value we just set, right away.
                    st.session_state["last_mistake_result"] = result
                    st.session_state["last_sources"] = result.get("based_on")
                    st.session_state["mistake_history"].insert(
                        0,
                        {
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "draft": draft[:80] + ("..." if len(draft) > 80 else ""),
                            "risk_level": result.get("risk_level"),
                        },
                    )
                    st.rerun()
                except AppError:
                    st.error("Couldn't reach memory right now. Retrying failed, try again in a moment.")

    # Read from session_state (not from inside the button block) so the result
    # keeps showing across reruns, including the one triggered above.
    result = st.session_state.get("last_mistake_result")
    if result:
        badge = {"safe": "🟢 SAFE", "risky": "🟡 RISKY", "likely_flop": "🔴 LIKELY FLOP"}.get(
            result.get("risk_level"), "🟡 UNKNOWN"
        )
        st.markdown(f"### {badge}")
        st.write(result.get("reason", ""))
        if result.get("contradiction"):
            st.error(f"⚠️ Contradiction: {result['contradiction']}")
        if result.get("evidence"):
            st.markdown("**Evidence from past posts:**")
            for e in result["evidence"]:
                st.markdown(f"- {e}")
        if result.get("suggestion"):
            st.success(f"**Suggestion:** {result['suggestion']}")

        # --- Confidence indicator ---
        based_on = result.get("based_on")
        memories_used = getattr(based_on, "memories", None) or []
        if not result.get("evidence") and not memories_used:
            st.info("ℹ️ Low confidence — no matching history found for this exact topic yet.")
        else:
            count = len(memories_used) if memories_used else len(result.get("evidence", []))
            st.caption(f"Based on {count} related memor{'y' if count == 1 else 'ies'}.")

    # --- Check history (this session) ---
    history = st.session_state["mistake_history"]
    if len(history) > 1:
        with st.expander(f"📜 Check history ({len(history)} checks this session)"):
            badge_map = {"safe": "🟢", "risky": "🟡", "likely_flop": "🔴"}
            for h in history:
                st.markdown(f"{badge_map.get(h['risk_level'], '🟡')} `{h['time']}` — {h['draft']}")

    st.divider()
    st.subheader("With memory vs. without memory")
    question = st.text_input("Ask a content question to compare", value="What should I post this week?")
    if st.button("Compare answers"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**❌ Generic AI (no memory)**")
            with st.spinner("Thinking generically..."):
                try:
                    st.markdown(sanitize_markdown(checkers.generic_answer(question)))
                except AppError:
                    st.error("Couldn't reach the AI right now.")
        with col2:
            st.markdown(f"**✅ Grounded in {CREATOR_NAME}'s memory**")
            with st.spinner("Reflecting on memory..."):
                try:
                    grounded = memory.reflect(question, context="content planning")
                    st.markdown(sanitize_markdown(getattr(grounded, "text", str(grounded))))
                except AppError:
                    st.error("Couldn't reach memory right now.")


# ===================================================================
# TAB 2: Voice Checker (F7)
# ===================================================================
with tab_voice:
    st.subheader("Check (and rewrite) a caption in the creator's voice")
    caption_draft = st.text_area(
        "Paste a draft caption",
        height=100,
        placeholder='e.g. "Elevate your fitness journey with our premium protein blend!"',
    )
    if st.button("Check my caption", type="primary"):
        if not caption_draft.strip():
            st.warning("Paste a caption first.")
        else:
            with st.spinner("Comparing against past captions..."):
                try:
                    voice_result = checkers.voice_check(caption_draft)
                    st.session_state["last_voice_result"] = voice_result
                except AppError:
                    st.error("Couldn't reach memory right now. Retrying failed, try again in a moment.")

    voice_result = st.session_state.get("last_voice_result")
    if voice_result:
        st.metric("Voice match", f"{voice_result.get('voice_match_percent', 0)}%")
        if voice_result.get("issues"):
            st.markdown("**Issues:**")
            for issue in voice_result["issues"]:
                st.markdown(f"- {issue}")
        if voice_result.get("rewrite"):
            st.markdown("**Rewrite in the creator's voice:**")
            st.code(voice_result["rewrite"], language=None)
        if voice_result.get("changes_explained"):
            st.markdown("**What changed:**")
            for c in voice_result["changes_explained"]:
                st.markdown(f"- {c}")


# ===================================================================
# TAB 3: Trend Radar (F9)
# ===================================================================
with tab_trends:
    st.subheader("What's trending in your niche")
    if st.button("Fetch latest trends"):
        with st.spinner("Checking Google Trends..."):
            raw = trends.fetch_trends(TREND_KEYWORDS, geo=TREND_GEO)
            st.session_state["trend_raw"] = raw

    raw = st.session_state.get("trend_raw")
    if raw:
        badge = "🟢 LIVE" if raw["source"] == "live" else "🟡 CACHED"
        st.markdown(f"**Data source:** {badge}")

        summary = trends.summarize_trends(raw)
        st.session_state["trend_summary"] = summary

        chart_df = pd.DataFrame(
            {item["keyword"]: [item["change_pct"]] for item in summary}
        ).T.rename(columns={0: "% change (last 7 vs prior)"})
        st.bar_chart(chart_df)

        if st.button("Save this week's snapshot to memory"):
            with st.spinner("Saving snapshot..."):
                try:
                    text = trends.retain_snapshot(summary, NICHE)
                    st.success("Snapshot saved.")
                    st.caption(text)
                except AppError:
                    st.error("Couldn't save the snapshot right now.")

        if st.button("Ask the agent what to do about these trends", type="primary"):
            with st.spinner("Reflecting on trend history..."):
                try:
                    advice = checkers.trend_advice(summary)
                    st.session_state["trend_advice"] = advice
                except AppError:
                    st.error("Couldn't reach memory right now.")

        advice = st.session_state.get("trend_advice")
        if advice:
            action_badge = {"post_now": "🟢 POST NOW", "watch": "🟡 WATCH", "skip": "🔴 SKIP"}
            for row in advice:
                st.markdown(f"#### {row.get('trend', '')} — {action_badge.get(row.get('action'), row.get('action'))}")
                st.write(row.get("reason", ""))
                if row.get("past_evidence"):
                    st.caption(f"Evidence: {row['past_evidence']}")
    else:
        st.info("Click 'Fetch latest trends' to get started (works offline using the cached demo data).")


# ===================================================================
# TAB 4: Log a Post (F8) - the "live learning" demo moment
# ===================================================================
with tab_log:
    st.subheader("Log a new post result")
    st.caption("After logging, go back to Mistake Catcher and re-run a similar draft - the answer will change.")

    if st.session_state.pop("just_logged", False):
        st.success("Saved! Go re-run a similar draft in Mistake Catcher to see it learn.")

    with st.form("log_post_form"):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", value=datetime.now())
            platform = st.selectbox("Platform", ["instagram", "youtube"])
            post_format = st.text_input("Format", placeholder="short_reel, long_form, qa, vlog...")
        with col2:
            likes = st.number_input("Likes", min_value=0, value=0)
            comments = st.number_input("Comments", min_value=0, value=0)
            outcome = st.selectbox("Outcome", ["strong win", "win", "neutral", "flop"])
        sponsored = st.checkbox("Sponsored post")
        topic = st.text_input("Topic / title")
        feedback = st.text_area("Audience feedback (what did comments say?)")

        submitted = st.form_submit_button("Save this post to memory", type="primary")

    if submitted:
        if not topic.strip():
            st.warning("Add a topic/title first.")
        else:
            date_str = date.strftime("%Y-%m-%d")
            doc_id = f"logged-{date_str}-{topic[:20].replace(' ', '-')}"
            text = (
                f'On {date_str}, the creator posted a {post_format or "post"} titled "{topic}" on '
                f"{platform}{' (sponsored)' if sponsored else ''}. It got {likes} likes and "
                f"{comments} comments. Audience feedback: {feedback or 'none recorded'}. "
                f"Outcome: {outcome}."
            )
            try:
                memory.retain(
                    text=text,
                    context="sponsored_post" if sponsored else "post_result",
                    timestamp=datetime.combine(date, datetime.min.time()),
                    document_id=doc_id,
                    metadata={"platform": platform, "sponsored": sponsored},
                )
                # Track it locally too, so the sidebar's "Recently Uploaded
                # Posts" and the engagement chart below can reflect it right
                # away without re-listing everything from Hindsight. This only
                # runs if memory.retain() above didn't raise - so appearing
                # here is real confirmation the save succeeded.
                st.session_state["logged_posts"].append(
                    {
                        "id": doc_id,
                        "topic": topic,
                        "platform": platform,
                        "format": post_format or "unknown",
                        "likes": likes,
                        "outcome": outcome,
                        "date": date_str,
                    }
                )
                st.session_state["just_logged"] = True
                st.rerun()  # refresh so sidebar + chart pick up the new post right away
            except AppError:
                st.error("Couldn't save right now, try again in a moment.")


# ===================================================================
# TAB 5: Playbook & Insights (F5, F6, F12) + Weekly Brief (F14) + Export
# ===================================================================
with tab_playbook:
    st.subheader("Creator Playbook")
    if st.button("Refresh playbook"):
        for model in memory.get_playbook():
            memory.refresh_mental_model(model.id)
        st.success("Refresh requested - this runs in the background, give it a minute then reload this tab.")

    models = memory.get_playbook()
    if not models:
        st.info(
            "No mental models yet. Either scripts/seed_bank.py hasn't been run, or the "
            "background generation is still finishing (mental models are created "
            "asynchronously - give it a minute after seeding, then reload this page)."
        )
    for model in models:
        content = sanitize_markdown(model.content) if model.content else "*(still generating - check back in a moment)*"
        with st.expander(f"📘 {model.name}"):
            st.markdown(content)

    st.divider()
    st.subheader("What I've learned about you")
    st.caption("Generated automatically by Hindsight in the background - may lag behind your latest posts.")
    try:
        observations = memory.recall("patterns about the creator's content performance", types=["observation"])
        obs_results = getattr(observations, "results", [])
    except AppError:
        obs_results = []
    if obs_results:
        for obs in obs_results:
            st.markdown(f"- {obs.text}")
    else:
        st.caption("Still learning, log more posts.")

    st.divider()
    st.subheader("Engagement by post")
    st.caption("Includes the seeded demo history plus anything you've logged this session.")
    combined_posts = POSTS + st.session_state["logged_posts"]
    chart_data = pd.DataFrame(
        [
            {"post": p["id"], "format": p.get("format", "?"), "likes": p.get("likes", 0), "outcome": p.get("outcome", "?")}
            for p in combined_posts
        ]
    )
    st.bar_chart(chart_data.set_index("post")["likes"])

    # --- F14: Weekly Content Brief ---
    st.divider()
    st.subheader("📅 Weekly Content Brief")
    st.caption("Combines the playbook, active directives, and the last fetched trend data into a 5-day plan.")
    if st.button("Plan my week", type="primary"):
        with st.spinner("Planning your week..."):
            try:
                trend_summary = st.session_state.get("trend_summary")
                trend_note = ""
                if trend_summary:
                    trend_note = " Current trend snapshot: " + ", ".join(
                        f'{t["keyword"]} ({t["label"]})' for t in trend_summary
                    ) + "."
                query = (
                    "Plan the creator's next 5 days of content using the Creator Playbook, "
                    "the active directives, and past post performance." + trend_note +
                    ' Respond ONLY with a JSON list of exactly 5 days: '
                    '[{"day": "Monday", "format": "string", "topic": "string", "reason": "string"}, ...]'
                )
                answer = memory.reflect(query, context="weekly planning", budget="high")
                plan = extract_json(getattr(answer, "text", str(answer)))
                st.session_state["weekly_plan"] = plan
                st.session_state["weekly_plan_raw"] = getattr(answer, "text", str(answer))
            except AppError:
                st.error("Couldn't reach memory right now.")

    plan = st.session_state.get("weekly_plan")
    if plan and isinstance(plan, list):
        for day in plan:
            with st.container(border=True):
                st.markdown(f"**{day.get('day', '')}** — {day.get('format', '')}")
                st.write(day.get("topic", ""))
                if day.get("reason"):
                    st.caption(day["reason"])
    elif st.session_state.get("weekly_plan_raw"):
        st.warning("Couldn't parse a structured plan - showing the raw answer instead:")
        st.markdown(sanitize_markdown(st.session_state["weekly_plan_raw"]))

    # --- Export ---
    st.divider()
    st.subheader("📤 Export")
    st.caption("Bundle the directives + playbook into one file you can share outside the app.")
    if st.button("Prepare creator report"):
        lines = [f"# {CREATOR_NAME} — Creator Report", "", f"_Niche: {NICHE}_", "", "## Active Directives"]
        for d in memory.list_directives():
            lines.append(f"- **{d.name}:** {d.content}")
        lines.append("")
        lines.append("## Creator Playbook")
        for model in memory.get_playbook():
            lines.append(f"### {model.name}")
            lines.append(model.content or "_(still generating)_")
            lines.append("")
        st.session_state["report_text"] = "\n".join(lines)

    if st.session_state.get("report_text"):
        st.download_button(
            "Download report (.md)",
            data=st.session_state["report_text"],
            file_name=f"{CREATOR_NAME.replace(' ', '_').lower()}_creator_report.md",
            mime="text/markdown",
        )


# ===================================================================
# TAB 6: All Memories - manual browse/search (for creator reference)
# ===================================================================
with tab_browse:
    st.subheader("Browse everything stored in memory")
    st.caption(
        "A plain list of every memory retained so far - seeded history plus anything "
        "logged this session - so you (the creator) can scroll and check things "
        "yourself, not just ask the AI."
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("Search memories", placeholder="e.g. sponsored, protein, reel...")
    with col2:
        context_filter = st.selectbox(
            "Filter by type",
            ["all", "post_result", "sponsored_post", "caption_sample", "trend_snapshot"],
        )

    if st.button("Load memories", type="primary"):
        with st.spinner("Fetching..."):
            try:
                items = memory.list_all_memories(search_query=search or None, limit=200)
                if context_filter != "all":
                    items = [i for i in items if getattr(i, "context", None) == context_filter]
                st.session_state["browsed_memories"] = items
            except AppError:
                st.error("Couldn't load memories right now.")

    items = st.session_state.get("browsed_memories")
    if items:
        st.caption(f"{len(items)} memories found")

        def _memory_date(item):
            val = getattr(item, "occurred_start", None) or getattr(item, "var_date", None) or getattr(item, "mentioned_at", None)
            return str(val)[:10] if val else ""

        rows = [{"Date": _memory_date(i), "Type": i.context or "", "Text": i.text} for i in items]
        df = pd.DataFrame(rows).sort_values("Date", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Click 'Load memories' to see everything stored so far.")
