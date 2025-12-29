from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from .constants import PRIMARY_COLOR

console = Console()


def frame(title: str, content):
    """
    IDE-style single frame wrapper.
    All commands MUST return renderables.
    """
    return Panel(
        content,
        title=title,
        border_style=PRIMARY_COLOR,
        padding=(1, 2),
    )


# -----------------------------
# Explicit Profile Prompt ONLY
# -----------------------------

def prompt_new_profile():
    """
    Called ONLY when user runs:
    devopsmind profile create
    """
    username = Prompt.ask("👤 Choose a username").strip()
    gamer = Prompt.ask("🎮 Gamer tag (public nickname)").strip()
    email = Prompt.ask("📧 Email (hashed locally, never stored)").strip()
    return username, gamer, email
