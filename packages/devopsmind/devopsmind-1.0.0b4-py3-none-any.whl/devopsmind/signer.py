import json
import hashlib


def _canonicalize(obj):
    """
    Deterministic canonicalization:
    - dict keys sorted
    - lists preserved
    """
    if isinstance(obj, dict):
        return {k: _canonicalize(obj[k]) for k in sorted(obj)}
    if isinstance(obj, list):
        return [_canonicalize(v) for v in obj]
    return obj


def sign_snapshot(snapshot: dict, email_hash: str) -> str:
    """
    Canonical signer shared by submit + sync + validate.

    Signature = SHA256(canonical(snapshot_view) + email_hash)

    MUST MATCH WORKER EXACTLY.
    """

    signing_view = {
        "schema": snapshot.get("schema"),
        "user_id": snapshot.get("user_id"),
        "username": snapshot.get("username"),
        "handle": snapshot.get("handle"),
        "xp": snapshot.get("xp"),
        "rank": snapshot.get("rank"),
        "completed_challenges": snapshot.get("completed_challenges", []),
        "badges": snapshot.get("badges", []),
        "by_stack": snapshot.get("by_stack", {}),
        "by_difficulty": snapshot.get("by_difficulty", {}),
        "nonce": snapshot.get("nonce"),
    }

    canonical = json.dumps(
        _canonicalize(signing_view),
        separators=(",", ":"),
    )

    return hashlib.sha256((canonical + email_hash).encode()).hexdigest()

