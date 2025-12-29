from typing import Optional
from pathlib import Path
import yaml

from .play import play as _play
from .validator import validate_only as _validate_only
from .stats import stats as _stats
from .challenge_resolver import find_challenge_by_id
from .state import get_active_username

WORKSPACE_DIR = Path.home() / "workspace"


# -------------------------------------------------
# Ensure active profile is always loaded
# -------------------------------------------------
def _ensure_profile_loaded():
    # Profiles are managed by CLI / mode.
    # Engine only checks presence, never logs in.
    return get_active_username()


# -------------------------------------------------
# Play
# -------------------------------------------------
def play(challenge_id: Optional[str] = None):
    _ensure_profile_loaded()
    return _play(challenge_id)


# -------------------------------------------------
# Validate (ENGINE — pure metadata passthrough)
# -------------------------------------------------
def validate_only(challenge_id: Optional[str] = None):
    _ensure_profile_loaded()

    if not challenge_id:
        return {"error": "Please provide a challenge id."}

    workspace = WORKSPACE_DIR / challenge_id
    if not workspace.exists():
        return {
            "error": "Workspace not found. Run `devopsmind play <challenge>` first."
        }

    challenge_dir = find_challenge_by_id(challenge_id)
    if not challenge_dir:
        return {"error": "Challenge not found."}

    meta_file = challenge_dir / "challenge.yaml"
    try:
        meta = yaml.safe_load(meta_file.read_text()) or {}
    except Exception:
        meta = {}

    result = _validate_only(
        challenge_id=challenge_id,
        stack=meta.get("stack"),
        difficulty=meta.get("difficulty"),
        skills=meta.get("skills", []),
        xp=meta.get("xp"),
    )

    # 🔒 IMPORTANT:
    # Engine must NEVER print or render achievements.
    # Achievement IDs are returned and resolved by UI layer.

    return result


# -------------------------------------------------
# Stats
# -------------------------------------------------
def stats():
    data = _stats()
    return (
        f"👤 {data.get('username')}\n"
        f"🧠 XP: {data.get('xp')}\n"
        f"🏅 Rank: {data.get('profile', {}).get('rank')}\n"
        f"✅ Completed: {len(data.get('progress', {}).get('completed', []))}"
    )


__all__ = ["play", "validate_only", "stats"]

