import json
from pathlib import Path

STATE_DIR = Path.home() / ".devopsmind"
STATE_PATH = STATE_DIR / "state.json"
ACTIVE_PROFILE_FILE = STATE_DIR / "active_profile"

# -------------------------------------------------
# State IO
# -------------------------------------------------

def load_state():
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text())


def save_state(state: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


def is_first_run():
    return not STATE_PATH.exists()


# -------------------------------------------------
# Auth (CLIENT-SIDE = UX ONLY)
# -------------------------------------------------
# IMPORTANT:
# - Client stores NO passwords
# - Client stores NO hashes
# - Client stores NO salts
# - Password is entered and sent to Worker
# - Worker decides if online features are allowed

def ensure_auth_state(state: dict):
    state.setdefault("auth", {})
    state["auth"].setdefault("lock_enabled", False)


def is_auth_locked():
    state = load_state()
    return state.get("auth", {}).get("lock_enabled", False)


def set_auth_lock(enabled: bool):
    state = load_state()
    ensure_auth_state(state)
    state["auth"]["lock_enabled"] = enabled
    save_state(state)


# -------------------------------------------------
# Session (IN-MEMORY ONLY)
# -------------------------------------------------
# Session means:
# "This process is currently authenticated with the Worker"

_SESSION_UNLOCKED = False


def mark_session_unlocked():
    global _SESSION_UNLOCKED
    _SESSION_UNLOCKED = True


def is_session_unlocked():
    return _SESSION_UNLOCKED


def reset_session():
    """
    Logout:
    - Ends online session
    - Switches to offline mode
    - Does NOT delete any local data
    """
    global _SESSION_UNLOCKED
    _SESSION_UNLOCKED = False

    state = load_state()
    state["mode"] = "offline"
    save_state(state)


# -------------------------------------------------
# Profile State
# -------------------------------------------------

def get_profile_state():
    state = load_state()
    return state.get("profile", {})


def set_profile_state(profile: dict):
    state = load_state()
    state["profile"] = profile
    save_state(state)


# -------------------------------------------------
# Restore Decision (Cloud → Local)
# -------------------------------------------------
# User chooses whether to restore cloud snapshot
# This decision is stored locally per account

def get_restore_decision(email_hash: str):
    state = load_state()
    return state.get("restore_decision", {}).get(email_hash)


def set_restore_decision(email_hash: str, decision: bool):
    state = load_state()
    decisions = state.setdefault("restore_decision", {})
    decisions[email_hash] = decision
    save_state(state)


# -------------------------------------------------
# Active Profile (POINTER ONLY)
# -------------------------------------------------
# This file only stores the active username
# It is NOT sensitive

def get_active_username():
    if ACTIVE_PROFILE_FILE.exists():
        value = ACTIVE_PROFILE_FILE.read_text().strip()
        return value or None
    return None


def set_active_username(username: str):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    ACTIVE_PROFILE_FILE.write_text(username)
