"""
data/seed.py

*** THIS IS SYNTHETIC DEMO DATA, clearly labelled as such. ***
It represents a fictional creator, "Alex Rivera", so the agent has a
realistic history to reason over from the very first run.

Dates are stored as "days_ago" (an integer) instead of fixed calendar
dates, so no matter when you run scripts/seed_bank.py, the story still
reads naturally ("On 2026-09-01, Alex posted..." etc. gets filled in
with a real, recent date at seed time).

To swap the niche (fitness -> beauty/finance), edit engine/config.py
AND rewrite the text below to match - the structure (fields, contexts,
document_ids) can stay the same.
"""

PERSONA = {
    "name": "Alex Rivera",
    "age": 27,
    "niche": "fitness and wellness",
    "location": "Hyderabad, India",
    "platforms": "Instagram (~48K followers, main), YouTube (~9K subscribers, secondary)",
    "voice": (
        "casual, energetic, short sentences, lowercase openers, ends with a question, "
        'uses "let\'s go", max 2 emojis, never hard-sells'
    ),
    "sponsors": ["PureFuel (protein powder)", "StrideX (fitness tracker watch)"],
}

# ---------------------------------------------------------------------
# 15 past posts. Each `text` has a {date} placeholder filled in by
# scripts/seed_bank.py using days_ago at seeding time.
# Mix (per spec): 4 short-Reel wins, 3 Q&A wins, 2 sponsored flops,
# 1 sponsored win (personal-story style, and doubles as the
# contradiction trigger), 2 long-form flops, 2 day-in-my-life wins,
# 1 contradiction-seed statement post. = 15 total.
# ---------------------------------------------------------------------
POSTS = [
    {
        "id": "post-001", "days_ago": 110, "platform": "instagram", "format": "short_reel",
        "sponsored": False, "context": "post_result", "outcome": "strong win",
        "likes": 12400, "comments": 340,
        "text": (
            'On {date}, Alex posted a 25-second Instagram Reel titled "5-minute morning workout, '
            'no equipment". It got 12,400 likes, 340 comments and 2,100 saves, about 3x Alex\'s '
            "average engagement. Comments praised the fast cuts and said it felt easy to start. "
            "Outcome: strong win. Format: short Reel."
        ),
    },
    {
        "id": "post-002", "days_ago": 95, "platform": "instagram", "format": "short_reel",
        "sponsored": False, "context": "post_result", "outcome": "strong win",
        "likes": 10800, "comments": 290,
        "text": (
            'On {date}, Alex posted a 20-second Instagram Reel titled "3 moves for stronger legs, '
            'no equipment needed". It got 10,800 likes, 290 comments and 1,800 saves, well above '
            "Alex's average engagement. Comments said the moves felt achievable and asked for a "
            "follow-up video. Outcome: strong win. Format: short Reel."
        ),
    },
    {
        "id": "post-003", "days_ago": 80, "platform": "instagram", "format": "short_reel",
        "sponsored": False, "context": "post_result", "outcome": "strong win",
        "likes": 13100, "comments": 410,
        "text": (
            'On {date}, Alex posted a 30-second Instagram Reel titled "quick core workout, no gym '
            'needed". It got 13,100 likes, 410 comments and 2,300 saves, Alex\'s best-performing '
            "Reel that month. Many comments said they saved it to try later. "
            "Outcome: strong win. Format: short Reel."
        ),
    },
    {
        "id": "post-004", "days_ago": 40, "platform": "instagram", "format": "short_reel",
        "sponsored": False, "context": "post_result", "outcome": "strong win",
        "likes": 9800, "comments": 260,
        "text": (
            'On {date}, Alex posted a 40-second Instagram Reel titled "stretch routine before bed". '
            "It got 9,800 likes, 260 comments and 1,650 saves, about 2.5x Alex's average "
            "engagement. Comments said it helped them sleep better. Outcome: strong win. "
            "Format: short Reel."
        ),
    },
    {
        "id": "post-005", "days_ago": 100, "platform": "instagram", "format": "qa",
        "sponsored": False, "context": "post_result", "outcome": "strong win",
        "likes": 0, "comments": 520,
        "text": (
            "On {date}, Alex posted an Instagram Stories Q&A. It received 520 replies, the "
            "highest ever for a Stories session. Followers said they liked talking directly to "
            "Alex about training struggles. Outcome: strong win. Format: Q&A."
        ),
    },
    {
        "id": "post-006", "days_ago": 65, "platform": "instagram", "format": "qa",
        "sponsored": False, "context": "post_result", "outcome": "strong win",
        "likes": 0, "comments": 410,
        "text": (
            'On {date}, Alex hosted an Instagram Stories "ask me anything" about their fitness '
            "journey. It received 410 replies and several follower DMs saying it was relatable. "
            "Outcome: strong win. Format: Q&A."
        ),
    },
    {
        "id": "post-007", "days_ago": 25, "platform": "instagram", "format": "live_qa",
        "sponsored": False, "context": "post_result", "outcome": "strong win",
        "likes": 0, "comments": 380,
        "text": (
            "On {date}, Alex went live on Instagram to answer questions about supplements and "
            "recovery. The session had 380 live comments and was replayed over 2,000 times. "
            "Followers appreciated the honest, non-salesy answers. Outcome: strong win. "
            "Format: live Q&A."
        ),
    },
    {
        "id": "post-008", "days_ago": 88, "platform": "instagram", "format": "sponsored_post",
        "sponsored": True, "context": "sponsored_post", "outcome": "flop",
        "likes": 3900, "comments": 0,
        "text": (
            "On {date}, Alex posted a sponsored Instagram post for PureFuel protein powder using "
            'a formal product-pitch caption. It got 3,900 likes, 41% below Alex\'s average '
            'engagement. Several comments called it "too salesy" and said it "sounds like an ad". '
            "Outcome: flop. Lesson: hard-sell sponsored captions underperform for Alex's audience."
        ),
    },
    {
        "id": "post-009", "days_ago": 83, "platform": "instagram", "format": "sponsored_post",
        "sponsored": True, "context": "sponsored_post", "outcome": "flop",
        "likes": 4200, "comments": 0,
        "text": (
            "On {date}, just 5 days after the PureFuel sponsored post, Alex posted another "
            "sponsored Instagram post for the StrideX fitness tracker. It got 4,200 likes, well "
            'below average, and comments included "another ad already?" and "feels like all '
            'sponsored content lately". Outcome: flop. Lesson: back-to-back sponsored posts '
            "within a short window hurt engagement."
        ),
    },
    {
        "id": "post-010", "days_ago": 20, "platform": "instagram", "format": "sponsored_post",
        "sponsored": True, "context": "sponsored_post", "outcome": "strong win",
        "likes": 11200, "comments": 0,
        "text": (
            "On {date}, Alex posted a sponsored Instagram post sharing a personal story about "
            "trying a magnesium supplement to help with sleep, written in a casual, low-key tone "
            "with no hard sell and tagging the brand naturally. It got 11,200 likes, well above "
            "Alex's average engagement, and comments were positive, several asking where to buy "
            "it. Outcome: strong sponsored win. Format: personal-story sponsored post. "
            "Note: this post promoted a supplement, which contradicts an earlier public statement "
            'where Alex said "I never recommend supplements, real food is enough."'
        ),
    },
    {
        "id": "post-011", "days_ago": 70, "platform": "youtube", "format": "long_form",
        "sponsored": False, "context": "post_result", "outcome": "flop",
        "likes": 0, "comments": 0, "views": 800,
        "text": (
            'On {date}, Alex posted a 12-minute YouTube tutorial "Build a home gym on a budget". '
            "It reached only 800 views versus Alex's average of 4,000 for that channel. Several "
            "comments said it felt like a sponsored video even though it was not. Outcome: flop. "
            "Format: long-form tutorial."
        ),
    },
    {
        "id": "post-012", "days_ago": 45, "platform": "youtube", "format": "long_form",
        "sponsored": False, "context": "post_result", "outcome": "flop",
        "likes": 0, "comments": 0, "views": 950,
        "text": (
            'On {date}, Alex posted a 45-minute YouTube video "Full HIIT workout, fully explained". '
            'It got only 950 views versus an average of 4,200, and comments said it felt long and '
            '"like a lecture" compared to Alex\'s usual short, punchy content. Outcome: flop. '
            "Format: long-form tutorial."
        ),
    },
    {
        "id": "post-013", "days_ago": 55, "platform": "instagram", "format": "vlog",
        "sponsored": False, "context": "post_result", "outcome": "strong win",
        "likes": 14500, "comments": 500,
        "text": (
            'On {date}, Alex posted an Instagram Reel "day in my life as a fitness creator in '
            'Hyderabad". It got 14,500 likes and 500 comments, Alex\'s highest-performing post '
            "that month. Comments said it felt personal and authentic. Outcome: strong win. "
            "Format: day-in-my-life."
        ),
    },
    {
        "id": "post-014", "days_ago": 15, "platform": "instagram", "format": "vlog",
        "sponsored": False, "context": "post_result", "outcome": "strong win",
        "likes": 13800, "comments": 470,
        "text": (
            'On {date}, Alex posted a "day in my life: meal prep, training, and a rest day" Reel. '
            "It got 13,800 likes and 470 comments, comments especially liked seeing the rest day "
            "included honestly. Outcome: strong win. Format: day-in-my-life."
        ),
    },
    {
        "id": "post-015", "days_ago": 60, "platform": "instagram", "format": "statement",
        "sponsored": False, "context": "post_result", "outcome": "neutral",
        "likes": 6000, "comments": 150,
        "text": (
            'On {date}, Alex posted an Instagram caption saying "I never recommend supplements, '
            "real food is enough\" as part of a caption about nutrition myths. It got a normal "
            "amount of engagement and several comments agreed with the stance. This is a public "
            "statement Alex made about supplements."
        ),
    },
]

# ---------------------------------------------------------------------
# 8 caption samples (all high-performing, so the "voice" learned is the
# winning voice) + 1 explicit style summary memory.
# ---------------------------------------------------------------------
CAPTIONS = [
    'Alex\'s caption on Instagram (won, 12.4K likes): "no gym? no excuse. 5 mins, let\'s go 💪 which move are you trying first?"',
    'Alex\'s caption on Instagram (won, 10.8K likes): "legs don\'t lie. 3 moves, zero excuses. which one\'s your nemesis?"',
    'Alex\'s caption on Instagram (won, 13.1K likes): "core day. no gym, no problem. ready to feel it tomorrow?"',
    'Alex\'s caption on Instagram (won, 9.8K likes): "wind down right. 5 stretches before bed, let\'s go. what\'s your bedtime ritual?"',
    'Alex\'s caption on Instagram (won, 520 Q&A replies): "ask me anything, i mean anything 👀 drop your questions below"',
    'Alex\'s caption on Instagram (won, 14.5K likes): "day in my life: coffee, sweat, more coffee. what\'s missing from yours?"',
    'Alex\'s caption on Instagram (won, 11.2K likes, sponsored): "used this to help me wind down before bed, and honestly it\'s growing on me. anyone else struggle to sleep after a hard session?"',
    'Alex\'s caption on Instagram (won, 13.8K likes): "meal prep sundays hit different. what\'s on your plate this week?"',
]

VOICE_SUMMARY = (
    "Alex's caption style: lowercase openers, short punchy sentences under 12 words, ends with a "
    "question to drive comments, at most 2 emojis, never uses corporate words like \"elevate\" or "
    '"unlock".'
)

# ---------------------------------------------------------------------
# 5 hard-rule directives. Hindsight directives need a short `name` (a
# label) plus the actual rule `content`.
# ---------------------------------------------------------------------
DIRECTIVES = [
    {
        "name": "Sponsorship spacing",
        "content": "Never approve a sponsored post that is within 7 days of another sponsored post.",
    },
    {
        "name": "No hard-sell sponsored captions",
        "content": "Never recommend a caption that uses a hard-sell tone; sponsored content must be personal-story style.",
    },
    {
        "name": "Flag contradictions",
        "content": "Always flag any claim that contradicts something Alex said publicly before (cite the earlier post).",
    },
    {
        "name": "Cite evidence",
        "content": "Always cite the specific past post(s) that support any warning or recommendation.",
    },
    {
        "name": "No medical or guaranteed-results claims",
        "content": 'Never suggest medical or guaranteed-results claims (e.g., "lose 5kg in a week").',
    },
]

# ---------------------------------------------------------------------
# 3 mental models (self-updating summaries).
# ---------------------------------------------------------------------
MENTAL_MODELS = [
    {
        "name": "Creator Playbook",
        "source_query": "What content formats, topics, tones, and posting patterns work best for "
                         "Alex, and what should Alex avoid?",
    },
    {
        "name": "Audience Dislikes",
        "source_query": "What does Alex's audience consistently criticize or disengage from?",
    },
    {
        "name": "Sponsorship Rules of Thumb",
        "source_query": "How should Alex structure sponsored content based on past sponsored results?",
    },
]

# ---------------------------------------------------------------------
# 3 weekly trend snapshots (days_ago: 21, 14, 7) telling the
# "high protein snacks trended before and was skipped" story.
# ---------------------------------------------------------------------
TREND_HISTORY = [
    {
        "days_ago": 21,
        "document_id": "trend-snapshot-1",
        "text": (
            'Trend snapshot for the fitness niche, week of {date}: "high protein snacks" interest '
            'rose 55% versus the prior 3 weeks (India). Related rising searches: '
            '"high protein breakfast", "protein snack ideas", "protein bites recipe". '
            "Alex did not post about this trend that week."
        ),
    },
    {
        "days_ago": 14,
        "document_id": "trend-snapshot-2",
        "text": (
            'Trend snapshot for the fitness niche, week of {date}: "high protein snacks" interest '
            'cooled slightly, down 10% versus the previous week (India), while "home workout" held '
            'steady. Related rising searches: "protein snack ideas". Alex did not post about high '
            "protein snacks this week either."
        ),
    },
    {
        "days_ago": 7,
        "document_id": "trend-snapshot-3",
        "text": (
            'Trend snapshot for the fitness niche, week of {date}: "high protein snacks" interest '
            'rose 62% versus the prior 3 weeks (India), the strongest spike yet. Related rising '
            'searches: "high protein breakfast", "protein snack ideas", "protein packed meals". '
            "This is the second time this trend has spiked in the last month, and Alex has not "
            "posted about it either time."
        ),
    },
]
