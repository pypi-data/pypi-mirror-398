from pathlib import Path
import json

SNAPSHOT_PATH = Path.home() / ".devopsmind" / "snapshot.json"


def _apply_snapshot_xp(state: dict) -> dict:
    """
    Ensure snapshot XP is reflected everywhere (including header).
    """
    if not SNAPSHOT_PATH.exists():
        return state

    try:
        snapshot = json.loads(SNAPSHOT_PATH.read_text())
    except Exception:
        return state

    # Only apply if this snapshot belongs to the active user
    profile = state.get("profile", {}) or {}
    if snapshot.get("user_id") != profile.get("user_id"):
        return state

    # Apply authoritative XP & rank
    state["xp"] = snapshot.get("xp", state.get("xp", 0))
    state.setdefault("profile", {})
    state["profile"]["rank"] = snapshot.get(
        "rank",
        state["profile"].get("rank"),
    )

    return state
