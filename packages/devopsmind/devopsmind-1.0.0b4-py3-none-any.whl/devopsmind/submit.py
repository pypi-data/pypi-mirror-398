import requests
import secrets

from devopsmind.progress import load_state
from devopsmind.snapshot import build_snapshot
from devopsmind.signer import sign_snapshot
from devopsmind.constants import RELAY_URL

SNAPSHOT_ENDPOINT = f"{RELAY_URL}/snapshot"


def submit_pending():
    """
    Submit the current snapshot to the relay.

    RULES:
    - Snapshot is rebuilt locally
    - XP is derived (never trusted)
    - Nonce is generated ONLY at submit time
    - Signature is required
    """

    state = load_state()
    profile = state.get("profile") or {}
    email_hash = profile.get("email_hash")

    if not email_hash:
        return "❌ Submit skipped: email hash missing."

    snapshot = build_snapshot(state)

    # 🔐 Nonce generated ONLY at submit time
    snapshot["nonce"] = secrets.token_hex(16)

    signature = sign_snapshot(snapshot, email_hash)
    snapshot["signature"] = signature

    headers = {
        "Content-Type": "application/json",
        "X-DevOpsMind-Signature": signature,
    }

    try:
        r = requests.post(
            SNAPSHOT_ENDPOINT,
            json=snapshot,
            headers=headers,
            timeout=10,
        )

        if r.status_code == 200:
            return "✔ Sync completed successfully."

        return f"❌ Sync failed ({r.status_code}): {r.text}"

    except Exception as e:
        return f"❌ Sync failed: {e}"
