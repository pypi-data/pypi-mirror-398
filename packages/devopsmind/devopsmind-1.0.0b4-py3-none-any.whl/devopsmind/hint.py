from pathlib import Path
import yaml
from rich.text import Text

CHALLENGES_ROOT = Path(__file__).resolve().parent / "challenges"


def show_hint(challenge_id: str):
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

            meta_file = ch / "challenge.yaml"
            if not meta_file.exists():
                continue

            meta = yaml.safe_load(meta_file.read_text()) or {}
            hint = meta.get("hint")

            if hint:
                return Text(f"💡 Hint:\n\n{hint}")

            return Text("ℹ️ No hint available.")

    return Text("❌ Challenge not found.", style="red")
