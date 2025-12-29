import json
import requests
import secrets
from pathlib import Path

from rich.text import Text
from rich.table import Table
from rich.console import Group

from devopsmind.cli import frame
from devopsmind.constants import DATA_DIR, RELAY_URL
from devopsmind.progress import load_state, save_state
from devopsmind.update_check import check_for_update
from devopsmind.snapshot import build_snapshot
from devopsmind.signer import sign_snapshot


SNAPSHOT_PATH = DATA_DIR / "snapshot.json"
SNAPSHOT_RELAY_URL = f"{RELAY_URL}/snapshot"
SNAPSHOT_GET_URL = f"{RELAY_URL}/snapshot/get"
SNAPSHOT_EXISTS_URL = f"{RELAY_URL}/snapshot/exists"


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _snapshot_changed(new_snapshot: dict) -> bool:
    if not SNAPSHOT_PATH.exists():
        return True

    try:
        old = json.loads(SNAPSHOT_PATH.read_text())
    except Exception:
        return True

    for k in ("updated_at", "signature", "nonce"):
        old.pop(k, None)
        new_snapshot.pop(k, None)

    return old != new_snapshot


# -------------------------------------------------
# 🔍 CLOUD EXISTENCE CHECK (READ-ONLY)
# -------------------------------------------------
def cloud_snapshot_exists(email_hash: str) -> bool:
    try:
        r = requests.post(
            SNAPSHOT_EXISTS_URL,
            json={"email_hash": email_hash},
            timeout=5,
        )
        if r.status_code == 200:
            return bool(r.json().get("exists"))
    except Exception:
        pass
    return False


# -------------------------------------------------
# 📥 FETCH SNAPSHOT (READ-ONLY)
# -------------------------------------------------
def fetch_snapshot(email_hash: str):
    try:
        r = requests.post(
            SNAPSHOT_GET_URL,
            json={"email_hash": email_hash},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


# -------------------------------------------------
# Restore from REMOTE snapshot (AUTHORITATIVE)
# -------------------------------------------------
def restore_from_remote(state: dict) -> dict:
    profile = state.get("profile") or {}
    email_hash = profile.get("email_hash")

    if not email_hash:
        return state

    decisions = state.get("restore_decision", {})
    decision = decisions.get(email_hash)

    # Ask once, only if snapshot exists
    if decision is None and cloud_snapshot_exists(email_hash):
        choice = input(
            "⚠️ Existing progress found for this account.\n"
            "Restore cloud progress now? [Y/n]: "
        ).strip().lower()

        decision = choice in ("", "y", "yes")
        decisions[email_hash] = decision
        state["restore_decision"] = decisions
        save_state(state)

    if decision is not True:
        return state

    snapshot = fetch_snapshot(email_hash)
    if not isinstance(snapshot, dict) or "schema" not in snapshot:
        state["restore_error"] = "Snapshot fetch failed"
        save_state(state)
        return state

    # -------------------------------------------------
    # Apply snapshot locally
    # -------------------------------------------------
    state["profile"] = {
        "username": snapshot.get("username"),
        "gamer": snapshot.get("handle"),
        "user_id": snapshot.get("user_id"),
        "email_hash": snapshot.get("email_hash"),
        "rank": snapshot.get("rank"),
    }

    state["progress"] = {
        "completed": snapshot.get("completed_challenges", []),
        "by_stack": snapshot.get("by_stack", {}),
        "by_difficulty": snapshot.get("by_difficulty", {}),
    }

    state["badges"] = snapshot.get("badges", [])
    state["achievements_unlocked"] = snapshot.get("badges", [])

    state["xp"] = snapshot.get("xp", 0)
    state["last_synced"] = snapshot.get("updated_at")

    save_state(state)
    _save_json(SNAPSHOT_PATH, snapshot)

    return state


# -------------------------------------------------
# Sync snapshot to relay (WRITE PATH)
# -------------------------------------------------
def attempt_sync():
    state = load_state()
    profile = state.get("profile") or {}
    email_hash = profile.get("email_hash")

    if not email_hash:
        return {"error": "email hash missing"}

    snapshot = build_snapshot(state)

    if not _snapshot_changed(snapshot):
        return {"already": True}

    snapshot["nonce"] = secrets.token_hex(16)
    signature = sign_snapshot(snapshot, email_hash)
    snapshot["signature"] = signature

    _save_json(SNAPSHOT_PATH, snapshot)

    state["xp"] = snapshot.get("xp", 0)
    state.setdefault("profile", {})
    state["profile"]["rank"] = snapshot.get("rank", "Beginner")
    save_state(state)

    headers = {
        "Content-Type": "application/json",
        "X-DevOpsMind-Signature": signature,
    }

    try:
        r = requests.post(
            SNAPSHOT_RELAY_URL,
            json=snapshot,
            headers=headers,
            timeout=10,
        )
        return r.json()
    except Exception:
        return {"pending": True}


# -------------------------------------------------
# Default sync command
# -------------------------------------------------
def sync_default(local: bool = False):
    state = load_state()
    state = restore_from_remote(state)

    profile = state.get("profile", {})
    xp = int(state.get("xp", 0))
    rank = profile.get("rank", "Beginner")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Source")
    table.add_column("XP", justify="right")
    table.add_column("Rank")
    table.add_row("Snapshot", str(xp), rank)

    notes = []
    decisions = state.get("restore_decision", {})
    email_hash = profile.get("email_hash")

    if decisions.get(email_hash) is True:
        if "restore_error" in state:
            notes.append(
                Text(
                    "⚠ Cloud restore failed. You can retry later using `devopsmind sync`.",
                    style="yellow",
                )
            )
        else:
            notes.append(
                Text(
                    "✔ Snapshot restored using email identity.",
                    style="green",
                )
            )
    elif decisions.get(email_hash) is False:
        notes.append(
            Text(
                "ℹ Snapshot restore skipped by user choice.",
                style="dim",
            )
        )

    update_available, latest, release_notes = check_for_update()
    if update_available:
        notes.append(
            Text(
                f"⬆ New version available: {latest}\n"
                f"Run `pipx upgrade devopsmind` to get new version and new challenges.",
                style="cyan",
            )
        )
        if release_notes:
            notes.append(Text(f"📝 {release_notes}", style="dim"))

    return frame("🔄 Sync", Group(table, *notes))
