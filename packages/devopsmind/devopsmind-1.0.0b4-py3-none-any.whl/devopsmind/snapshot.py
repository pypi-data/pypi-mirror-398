import hashlib
import json
import requests
from datetime import datetime

from .progress import load_state, save_state
from .constants import RELAY_URL
from .stats import stats as load_stats   # ✅ single XP source


# -------------------------------------------------
# 🏆 AUTHORITATIVE XP → RANK LADDER (LOCKED)
# -------------------------------------------------
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


def derive_rank_from_xp(xp: int) -> str:
    current = XP_LEVELS[0][1]
    for threshold, rank in XP_LEVELS:
        if xp >= threshold:
            current = rank
        else:
            break
    return current


# -------------------------------------------------
# Snapshot Builder (PURE, NO XP LOGIC)
# -------------------------------------------------
def build_snapshot(state=None):
    """
    Snapshot is a TRANSPORT FORMAT.
    XP is already derived elsewhere (stats.py).
    """
    if state is None:
        state = load_state()

    derived = load_stats()

    profile = state.get("profile") or {}
    progress = state.get("progress") or {}

    xp = derived.get("xp", 0)
    rank = derive_rank_from_xp(xp)

    return {
        "schema": "v3.3",

        # 🔐 Identity
        "email_hash": profile.get("email_hash"),
        "user_public_id": profile.get("user_public_id"),
        "username": profile.get("username"),
        "handle": profile.get("gamer"),

        # 🔢 Progress (DERIVED)
        "xp": xp,
        "rank": rank,
        "completed_challenges": progress.get("completed", []),
        "badges": state.get("badges", []),
        "by_stack": progress.get("by_stack", {}),
        "by_difficulty": progress.get("by_difficulty", {}),

        "updated_at": datetime.utcnow().isoformat() + "Z",
    }


# -------------------------------------------------
# Snapshot Signing (INTEGRITY ONLY)
# -------------------------------------------------
def sign_snapshot(snapshot, email_hash):
    """
    Snapshot signature protects STRUCTURE, not XP authority.
    """
    signing_view = {
        "schema": snapshot.get("schema"),
        "email_hash": snapshot.get("email_hash"),
        "rank": snapshot.get("rank"),
        "completed_challenges": snapshot.get("completed_challenges", []),
        "badges": snapshot.get("badges", []),
        "by_stack": snapshot.get("by_stack", {}),
        "by_difficulty": snapshot.get("by_difficulty", {}),
    }

    canonical = json.dumps(signing_view, sort_keys=True)
    digest = hashlib.sha256((canonical + email_hash).encode()).hexdigest()

    signed = dict(snapshot)
    signed["signature"] = digest

    # ✅ CORRECT leaderboard endpoint
    publish_to_leaderboard(signed)

    return signed


# -------------------------------------------------
# 📤 Leaderboard Publisher (INDEX ONLY)
# -------------------------------------------------
def publish_to_leaderboard(snapshot):
    """
    Pushes minimal snapshot data to leaderboard index.
    Leaderboard is NOT authoritative for XP.
    """
    try:
        payload = {
            "user_public_id": snapshot.get("user_public_id"),
            "handle": snapshot.get("handle"),
            "username": snapshot.get("username"),
            "xp": snapshot.get("xp"),
            "rank": snapshot.get("rank"),
        }

        requests.post(
            f"{RELAY_URL}/leaderboard/write",  # ✅ FIXED
            json=payload,
            timeout=5,
        )
    except Exception:
        # Leaderboard must NEVER block progress
        pass


# -------------------------------------------------
# 🔍 Snapshot existence probe (READ-ONLY)
# -------------------------------------------------
def snapshot_exists(user_public_id: str, email_hash: str = None) -> bool:
    try:
        if email_hash is None:
            state = load_state()
            email_hash = state.get("profile", {}).get("email_hash")

        payload = {"user_public_id": user_public_id}
        if email_hash:
            payload["email_hash"] = email_hash

        res = requests.post(
            f"{RELAY_URL}/snapshot/exists",
            json=payload,
            timeout=5,
        )
        if res.status_code != 200:
            return False

        data = res.json()
        return data.get("exists") is True
    except Exception:
        return False


# -------------------------------------------------
# 🔄 Snapshot restore (AUTHORITATIVE)
# -------------------------------------------------
def restore_snapshot(user_public_id: str, email_hash: str = None):
    state = load_state()

    preserved_auth = state.get("auth")

    email_hash = email_hash or state.get("profile", {}).get("email_hash")
    if not email_hash:
        raise RuntimeError("email_hash required for snapshot restore")

    res = requests.post(
        f"{RELAY_URL}/snapshot/get",
        json={
            "user_public_id": user_public_id,
            "email_hash": email_hash,
        },
        timeout=10,
    )

    if res.status_code != 200:
        raise RuntimeError("Failed to restore snapshot")

    snapshot = res.json()

    if not isinstance(snapshot, dict) or "schema" not in snapshot:
        return snapshot

    state["profile"] = {
        "username": snapshot.get("username"),
        "gamer": snapshot.get("handle"),
        "user_public_id": user_public_id,
        "email_hash": email_hash,
    }

    state["progress"] = {
        "completed": snapshot.get("completed_challenges", []),
        "by_stack": snapshot.get("by_stack", {}),
        "by_difficulty": snapshot.get("by_difficulty", {}),
    }

    state["badges"] = snapshot.get("badges", [])

    if preserved_auth is not None:
        state["auth"] = preserved_auth

    save_state(state)
    return snapshot
