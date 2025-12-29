import json
import hashlib
from pathlib import Path

from .constants import DATA_DIR
from .snapshot import snapshot_exists, restore_snapshot
from .state import (
    get_profile_state,
    set_profile_state,
    get_restore_decision,
    set_restore_decision,
    get_active_username,
    set_active_username,
)

PROFILES_DIR = DATA_DIR / "profiles"


# -------------------------------------------------
# 🔐 Email hashing (LOCKED)
# -------------------------------------------------

def hash_email(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


# -------------------------------------------------
# Helpers (PUBLIC — DO NOT REMOVE)
# -------------------------------------------------

def _profile_path(username: str) -> Path:
    return PROFILES_DIR / f"{username}.json"


def _infer_single_local_profile():
    if not PROFILES_DIR.exists():
        return None
    profiles = list(PROFILES_DIR.glob("*.json"))
    if len(profiles) == 1:
        return profiles[0].stem
    return None


def _ensure_restore_decision(email_hash: str) -> bool:
    decision = get_restore_decision(email_hash)
    if decision is not None:
        return decision

    choice = input(
        "⚠️ Existing progress found for this account.\n"
        "Restore cloud progress now? [Y/n]: "
    ).strip().lower()

    decision = choice in ("", "y", "yes")
    set_restore_decision(email_hash, decision)

    if decision:
        restore_snapshot(email_hash)

    return decision


# -------------------------------------------------
# Profile Read-Only Operations
# -------------------------------------------------

def show_profile():
    username = get_active_username()
    profile = None

    if username:
        path = _profile_path(username)
        if path.exists():
            profile = json.loads(path.read_text())

    if not profile:
        profile = get_profile_state() or None

    if not profile:
        return "❌ Active profile not found."

    return "\n".join(
        [
            f"👤 Username: {profile.get('username')}",
            f"🎮 Gamer: {profile.get('gamer')}",
            f"🆔 User ID: {profile.get('user_id')}",
        ]
    )


def list_profiles():
    if PROFILES_DIR.exists():
        names = sorted(p.stem for p in PROFILES_DIR.glob("*.json"))
        if names:
            active = get_active_username() or _infer_single_local_profile()
            return "\n".join(
                ("👉 " if n == active else "   ") + n for n in names
            )

    profile = get_profile_state() or None
    if profile:
        return f"👉 {profile.get('username')}"

    return "No profiles found."
