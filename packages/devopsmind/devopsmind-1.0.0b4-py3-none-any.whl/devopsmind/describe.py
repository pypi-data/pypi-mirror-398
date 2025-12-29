from pathlib import Path
from rich.markdown import Markdown
from rich.text import Text

CHALLENGES_ROOT = Path(__file__).resolve().parent / "challenges"


def describe_challenge(challenge_id: str):
    for s in CHALLENGES_ROOT.iterdir():
        # 🚫 Skip files like __init__.py
        if not s.is_dir():
            continue

        for l in s.iterdir():
            # 🚫 Skip non-directories
            if not l.is_dir():
                continue

            ch = l / challenge_id
            if not ch.exists() or not ch.is_dir():
                continue

            desc = ch / "description.md"
            if desc.exists():
                return Markdown(desc.read_text())

            return Text("❌ description.md missing.")

    return Text("❌ Challenge not found.")
