from pathlib import Path
import shutil
import yaml

from .challenge_resolver import find_challenge_by_id

WORKSPACE_DIR = Path.home() / "workspace"

# Files / dirs to exclude from workspace
EXCLUDE_NAMES = {
    "challenge.yaml",
    "validator.py",
    "__pycache__",
    "description.md",
}

# 🔒 Play marker (additive)
PLAY_MARKER = ".devopsmind_played"


def _ignore_filter(dirpath, names):
    """
    Ignore framework/author files when copying to workspace.
    """
    return [n for n in names if n in EXCLUDE_NAMES]


def play(challenge_id: str):
    if not challenge_id:
        return "❌ Please provide a challenge id."

    source = find_challenge_by_id(challenge_id)
    if not source:
        return "❌ Challenge not found."

    meta = source / "challenge.yaml"
    data = yaml.safe_load(meta.read_text()) or {}

    lines = []

    goal = data.get("goal")
    if goal:
        lines.append("🎯 Goal:")
        lines.append(goal)
        lines.append("")

    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    dest = WORKSPACE_DIR / challenge_id

    if not dest.exists():
        shutil.copytree(
            source,
            dest,
            ignore=_ignore_filter,
        )

    # -------------------------------------------------
    # ✅ MARK CHALLENGE AS PLAYED (ADDITIVE)
    # -------------------------------------------------
    marker = dest / PLAY_MARKER
    if not marker.exists():
        marker.write_text("played")

    lines.append("📂 Workspace path:")
    lines.append(str(dest.resolve()))
    lines.append("")
    lines.append("✅ Workspace ready.")
    lines.append("Run `devopsmind describe <challenge>` for details.")
    lines.append("Run `devopsmind validate <challenge>` when ready.")

    return "\n".join(lines)
