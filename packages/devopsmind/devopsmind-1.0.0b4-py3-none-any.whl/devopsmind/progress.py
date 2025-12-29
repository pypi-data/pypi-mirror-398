import json
from pathlib import Path

from .constants import DATA_DIR

STATE_FILE = DATA_DIR / "state.json"


# -------------------------------------------------
# 🏆 AUTHORITATIVE XP → RANK LADDER (REFERENCE ONLY)
# -------------------------------------------------
# NOTE:
# XP & Rank are DERIVED elsewhere.
# This ladder is kept only for UI / legacy compatibility.
XP_LEVELS = [
    (0, "Beginner"),
    (1000, "Apprentice"),
    (5000, "Operator"),
    (10000, "Engineer"),
    (20000, "Specialist"),
    (35000, "Advanced"),
    (55000, "Expert"),
    (80000, "Master"),
    (120000, "Architect"),
    (180000, "Grandmaster"),
    (260000, "Legend"),
    (370000, "Mythic"),
    (520000, "Eternal"),
    (750000, "Ascendant"),
    (1_000_000, "Vanguard"),
    (1_500_000, "Paragon"),
    (2_000_000, "Virtuoso"),
    (3_000_000, "Transcendent"),
    (5_000_000, "Celestial"),
    (10_000_000, "Infinite"),
]


# -----------------------------
# Badge / Achievement Rules
# -----------------------------
# NOTE:
# - Badges are permanent, write-once facts
# - XP & Rank are DERIVED elsewhere
# - This module persists FACTS only
#
# ⚠️ XP IS NEVER MUTATED HERE

CHALLENGE_BADGES = {}  # intentionally empty


# -------------------------------------------------
# State I/O
# -------------------------------------------------
def load_state():
    """
    Load local cached state.

    This state is NOT authoritative.
    It exists only as a UI / cache layer.
    """

    if not STATE_FILE.exists():
        return {
            "profile": {},
            "xp": 0,  # legacy / UI compatibility only
            "badges": [],
            "achievements_unlocked": [],
            "progress": {
                "completed": [],
                "by_stack": {},
                "by_difficulty": {},
            },
            "attempts": {},
        }

    state = json.loads(STATE_FILE.read_text())

    # ---- Backward compatibility ----
    state.setdefault("profile", {})
    state.setdefault("xp", 0)  # legacy only
    state.setdefault("badges", [])
    state.setdefault("achievements_unlocked", [])

    progress = state.setdefault("progress", {})
    progress.setdefault("completed", [])
    progress.setdefault("by_stack", {})
    progress.setdefault("by_difficulty", {})

    state.setdefault("attempts", {})

    # -------------------------------------------------
    # 🔥 LEGACY MIGRATION (SAFE & IDEMPOTENT)
    # -------------------------------------------------
    if state.get("achievements_unlocked") and not state.get("badges"):
        state["badges"] = list(state["achievements_unlocked"])
        save_state(state)

    return state


def save_state(state):
    """
    Persist local cached state.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


# -------------------------------------------------
# Badge persistence (FACTS ONLY)
# -------------------------------------------------
def persist_earned_badges(state, earned_badges):
    """
    Persist externally-computed earned badges.

    RULES:
    - Does NOT decide eligibility
    - Does NOT mutate XP
    - Badges are write-once facts
    """

    if not earned_badges:
        return

    badges = set(state.get("badges", []))
    achievements = set(state.get("achievements_unlocked", []))

    for badge_id in earned_badges:
        badges.add(badge_id)
        achievements.add(badge_id)

    state["badges"] = sorted(badges)
    state["achievements_unlocked"] = sorted(achievements)


# -------------------------------------------------
# Challenge completion (FACT RECORDING ONLY)
# -------------------------------------------------
def record_completion(
    challenge_id,
    stack=None,
    difficulty=None,
    earned_badges=None,
):
    """
    Record factual challenge completion.

    IMPORTANT GUARANTEES:
    - XP is NOT accepted
    - XP is NOT mutated
    - Rank is NOT touched
    - Duplicate completions are ignored
    """

    state = load_state()
    progress = state["progress"]

    # Prevent double counting
    if challenge_id in progress["completed"]:
        return state

    # -----------------------------
    # Record immutable facts
    # -----------------------------
    progress["completed"].append(challenge_id)

    if stack:
        progress["by_stack"][stack] = progress["by_stack"].get(stack, 0) + 1

    if difficulty:
        progress["by_difficulty"][difficulty] = (
            progress["by_difficulty"].get(difficulty, 0) + 1
        )

    # Persist externally-earned badges
    persist_earned_badges(state, earned_badges or [])

    save_state(state)
    return state
