from rich.console import Group
from rich.table import Table
from rich.text import Text
from rich.align import Align
import requests
from pathlib import Path
import json
import hashlib

from .constants import RELAY_URL


# ================= CONFIG =================

PAGE_SIZE = 20
STATE_PATH = Path.home() / ".devopsmind" / "state.json"

# ⚠️ MUST MATCH relay USER_ID_PEPPER
USER_ID_PEPPER = "devopsmind-user-id-v2"


# ================= IDENTITY =================

def get_email_hash():
    """
    Read email_hash from ~/.devopsmind/state.json
    """
    try:
        data = json.loads(STATE_PATH.read_text())
        return data.get("profile", {}).get("email_hash")
    except Exception:
        return None


def make_user_public_id(email_hash: str) -> str:
    """
    Must match relay algorithm exactly:
    SHA256("v2:" + USER_ID_PEPPER + email_hash)
    """
    raw = f"v2:{USER_ID_PEPPER}{email_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ================= LEADERBOARD =================

def show_leaderboard(page: int = 1):
    """
    Render global leaderboard with pagination (20 per page)
    and ALWAYS show pinned current user row.
    """

    try:
        resp = requests.get(f"{RELAY_URL}/leaderboard/public", timeout=5)
        resp.raise_for_status()
        data = resp.json()

        players = data.get("leaderboard", [])
        players = sorted(players, key=lambda p: p.get("xp", 0), reverse=True)

        if not players:
            return Text(
                "No public leaderboard entries yet.\n\n"
                "ℹ️ Your progress may be restored locally.\n"
                "To appear on the leaderboard, run:\n"
                "  devopsmind submit",
                style="yellow",
            )

        # Pagination
        total_players = len(players)
        total_pages = (total_players + PAGE_SIZE - 1) // PAGE_SIZE
        current_page = max(1, min(page, total_pages))

        start = (current_page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        paged_players = players[start:end]

        # Identify current user (by public ID)
        email_hash = get_email_hash()
        my_public_id = (
            make_user_public_id(email_hash) if email_hash else None
        )

        user_row = None
        if my_public_id:
            for i, player in enumerate(players, 1):
                if player.get("user_public_id") == my_public_id:
                    user_row = (i, player)
                    break

        table = Table(
            title="🌍 DevOpsMind Global Leaderboard",
            header_style="bold magenta",
        )

        table.add_column("#", style="dim", width=4)
        table.add_column("Gamer", style="cyan")
        table.add_column("Username", style="green")
        table.add_column("XP", justify="right")
        table.add_column("Rank", justify="center")

        # Render current page (global rank numbering)
        for i, player in enumerate(paged_players, start + 1):
            table.add_row(
                str(i),
                player.get("handle", "-"),
                player.get("username", "-"),
                str(player.get("xp", 0)),
                player.get("rank", "-"),
            )

        # Separator + pinned user row (ALWAYS)
        if user_row:
            rank, player = user_row

            table.add_row(
                "─" * 4,
                "─" * 12,
                "─" * 12,
                "─" * 6,
                "─" * 8,
                style="dim",
            )

            table.add_row(
                str(rank),
                f"👉 {player.get('handle', '-')}",
                player.get("username", "-"),
                str(player.get("xp", 0)),
                player.get("rank", "-"),
                style="bold yellow",
            )

        footer = Align.center(
            Text(
                f"Page {current_page} / {total_pages} · {total_players} players",
                style="dim",
            )
        )

        return Group(table, footer)

    except Exception:
        return Text(
            "Leaderboard not available yet.\n"
            "Run devopsmind submit and try again.",
            style="yellow",
        )


# Backward compatibility
show_leaderboards = show_leaderboard
