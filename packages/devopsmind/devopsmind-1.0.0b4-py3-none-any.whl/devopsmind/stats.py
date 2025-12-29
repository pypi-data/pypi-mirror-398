from pathlib import Path
import json
import yaml

from .progress import load_state
from .challenge_resolver import find_challenge_by_id
from .constants import XP_LEVELS

SNAPSHOT_PATH = Path.home() / ".devopsmind" / "snapshot.json"


def _load_snapshot():
    if not SNAPSHOT_PATH.exists():
        return {}

    try:
        return json.loads(SNAPSHOT_PATH.read_text())
    except Exception:
        return {}


def _derive_xp_from_progress(progress):
    """
    XP is DERIVED, never trusted from snapshot.
    """
    completed = progress.get("completed", [])
    xp = 0

    for cid in completed:
        challenge_dir = find_challenge_by_id(cid)
        if not challenge_dir:
            continue

        meta_file = challenge_dir / "challenge.yaml"
        if not meta_file.exists():
            continue

        try:
            meta = yaml.safe_load(meta_file.read_text()) or {}
        except Exception:
            meta = {}

        xp += int(meta.get("xp", 0))

    return xp


def _derive_rank(xp: int) -> str:
    rank = XP_LEVELS[0][1]
    for threshold, name in XP_LEVELS:
        if xp >= threshold:
            rank = name
    return rank


def stats():
    """
    Unified stats for CLI display.

    Rules:
    - XP is DERIVED from completed challenges
    - Snapshot may cache XP but is not authoritative
    - Rank is derived from XP
    - Identity comes from snapshot if available
    """

    state = load_state()
    snapshot = _load_snapshot()

    # -----------------------------
    # XP (DERIVED)
    # -----------------------------
    xp = _derive_xp_from_progress(state.get("progress", {}))
    state["xp"] = xp

    # -----------------------------
    # Rank (DERIVED)
    # -----------------------------
    state.setdefault("profile", {})
    state["profile"]["rank"] = _derive_rank(xp)

    # -----------------------------
    # Identity (snapshot wins)
    # -----------------------------
    if snapshot:
        state["username"] = snapshot.get("username", state.get("username"))
        state["gamer"] = snapshot.get("handle", state.get("gamer"))

    return state
