from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.console import Group

from .progress import load_state
from .constants import STACKS, STACK_COLORS, STACK_ICONS, BUNDLED_CHALLENGES
from .sync import check_for_update   # ✅ FIXED IMPORT


def render_bar(done: int, total: int, width: int = 5) -> str:
    """
    Render a simple textual progress bar.
    UI-only, deterministic, no state.
    """
    if total <= 0:
        return "░" * width

    filled = int((done / total) * width)
    return "█" * filled + "░" * (width - filled)


def show_my_stack_progress():
    """
    CLI View:
    - Available stacks (local challenge registry)
    - User stack progress (derived from snapshot / local state cache)
    """

    # ---------------------------------------
    # Load local cached state (snapshot-derived)
    # ---------------------------------------
    state = load_state() or {}
    completed = set(
        state.get("progress", {}).get("completed", [])
    )

    # ---------------------------------------
    # Discover available stacks + derive completion counts
    # ---------------------------------------
    available = {}
    completed_by_stack = {}

    for stack_dir in BUNDLED_CHALLENGES.iterdir():
        if not stack_dir.is_dir() or stack_dir.name.startswith("__"):
            continue

        total = 0
        done = 0

        for level_dir in stack_dir.iterdir():
            if not level_dir.is_dir():
                continue

            for ch_dir in level_dir.iterdir():
                if not (ch_dir / "challenge.yaml").exists():
                    continue

                total += 1

                # Challenge ID is directory name
                if ch_dir.name in completed:
                    done += 1

        if total:
            available[stack_dir.name] = total
            completed_by_stack[stack_dir.name] = done

    # ---------------------------------------
    # Build table
    # ---------------------------------------
    table = Table(
        title="🧠 My Stack Progress",
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Stack")
    table.add_column("Challenges", justify="right")
    table.add_column("Completed", justify="right")
    table.add_column("Progress")

    for stack, total in sorted(available.items()):
        done = completed_by_stack.get(stack, 0)
        bar = render_bar(done, total)

        color = STACK_COLORS.get(stack, "white")
        icon = STACK_ICONS.get(stack, "📦")
        label = f"{icon} {STACKS.get(stack, stack.title())}"

        table.add_row(
            Text(label, style=color),
            str(total),
            f"{done} / {total}",
            Text(bar, style=color),
        )

    # ---------------------------------------
    # 🔔 Update check (ADDITIVE, NON-BLOCKING)
    # ---------------------------------------
    notes = []
    update_available, latest, release_notes = check_for_update()

    if update_available:
        notes.append(
            Text(
                f"⬆ New version available: {latest}\n"
                f"Run `pipx upgrade devopsmind` to get new challenges.",
                style="cyan",
            )
        )
        if release_notes:
            notes.append(Text(f"📝 {release_notes}", style="dim"))

    # ---------------------------------------
    # Return UI
    # ---------------------------------------
    if notes:
        return Panel(Group(table, *notes), border_style="blue")

    return Panel(table, border_style="blue")
