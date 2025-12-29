from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group


def _format_sync_status(sync_status):
    """
    Convert sync response into human-readable text.
    UI ONLY.
    """

    if not sync_status:
        return "—"

    if isinstance(sync_status, str):
        return sync_status

    if isinstance(sync_status, dict):
        if sync_status.get("ok") is True:
            return "✅ Sync complete"
        if sync_status.get("pending") is True:
            return "⏳ Sync pending"
        if sync_status.get("already") is True:
            return "🏆 Already on leaderboard"
        if sync_status.get("error"):
            return "⚠️ Sync failed"

    return "—"


def show_validation_result(
    challenge_id,
    stack=None,
    difficulty=None,
    skills=None,
    earned_badges=None,
    sync_status=None,
):
    """
    Render validation result.

    Returns:
        rich.console.Group (renderable)
    """

    skills = skills or []
    earned_badges = earned_badges or []

    renderables = []

    # -------------------------------------------------
    # ✅ Challenge Validated Panel
    # -------------------------------------------------
    table = Table(show_header=False, box=None, expand=True)
    table.add_column("Key", style="dim", width=14)
    table.add_column("Value", overflow="fold")

    table.add_row("Challenge", challenge_id)

    if stack:
        table.add_row("Stack", f"🛠️ {stack}")

    if difficulty:
        table.add_row("Difficulty", f"🎯 {difficulty}")

    if skills:
        table.add_row(
            "Skills",
            " · ".join(f"🔹 {s}" for s in skills),
        )

    table.add_row("Sync", _format_sync_status(sync_status))

    renderables.append(
        Panel(
            table,
            title="✅ Challenge Validated",
            border_style="green",
        )
    )

    # -------------------------------------------------
    # 🎉 Achievement Panel (BELOW validation)
    # -------------------------------------------------
    if earned_badges:
        text = Text()
        for badge in earned_badges:
            text.append(f"🏅 {badge}\n")

        renderables.append(
            Panel(
                text,
                title="🎉 New Achievements Unlocked",
                border_style="yellow",
            )
        )

    # -------------------------------------------------
    # Return as ONE renderable
    # -------------------------------------------------
    return Group(*renderables)
