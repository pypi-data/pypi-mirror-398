from pathlib import Path
import yaml


def find_challenge_by_id(challenge_id: str) -> Path | None:
    """
    Find a challenge directory by `id` from challenge.yaml.
    Searches recursively under devopsmind/challenges/.
    """

    base = Path(__file__).parent / "challenges"

    for meta in base.rglob("challenge.yaml"):
        try:
            data = yaml.safe_load(meta.read_text()) or {}
        except Exception:
            continue

        if data.get("id") == challenge_id:
            return meta.parent

    return None
