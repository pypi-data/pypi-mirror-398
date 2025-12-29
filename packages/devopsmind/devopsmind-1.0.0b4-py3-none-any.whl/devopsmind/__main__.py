import argparse
import sys
import shutil
from pathlib import Path
from rich.console import Console, Group
from rich.text import Text
from rich.panel import Panel

from devopsmind.first_run import ensure_first_run
from devopsmind.state import (
    load_state,
    reset_session,
)
from devopsmind.mode import set_mode_online, set_mode_offline

from .cli import frame
from .engine import play, validate_only, stats as render_stats
from .list import list_challenges, search_challenges
from .profiles import show_profile, list_profiles
from .hint import show_hint
from .describe import describe_challenge
from .doctor import run_doctor
from .leaderboard import show_leaderboards
from .sync import sync_default
from .submit import submit_pending
from .constants import XP_LEVELS, VERSION
from devopsmind.stacks import show_my_stack_progress
from devopsmind.ui import show_validation_result
from .stats import stats as load_stats
from devopsmind.achievements import list_badges

# 🔐 Auth
from devopsmind.auth_recovery import rotate_recovery_key

console = Console()


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def compute_rank(xp: int) -> str:
    rank = XP_LEVELS[0][1]
    for threshold, name in XP_LEVELS:
        if xp >= threshold:
            rank = name
    return rank


def profile_bar():
    state = load_stats()
    profile = state.get("profile", {})
    xp = state.get("xp", 0)

    mode = state.get("mode", "offline")
    mode_label = "🌐 ONLINE" if mode == "online" else "📴 OFFLINE"
    mode_style = "green" if mode == "online" else "dim"

    text = (
        f"🎮 {profile.get('gamer', '—')} · "
        f"👤 {profile.get('username', '—')} · "
        f"🏅 {compute_rank(xp)} · "
        f"🧠 XP {xp} · "
        f"{mode_label}"
    )

    return Text(text, style=mode_style)


def boxed(title: str, body):
    return frame(
        title,
        Group(profile_bar(), Text(""), body),
    )


def cancelled():
    console.print(
        Panel(
            Text("❌ Command cancelled", style="red"),
            title="Cancelled",
            border_style="red",
        )
    )
    sys.exit(0)


def resolve_badge_line(line: str) -> str:
    """
    Resolve badge ID to human-readable name for UI.
    LEGACY SUPPORT — DO NOT REMOVE.
    """
    if "ach_" not in line:
        return line

    try:
        badges = list_badges(raw=True)
        badge_map = {b["id"]: b for b in badges}

        for badge_id, meta in badge_map.items():
            if badge_id in line:
                name = meta.get("name", badge_id)
                icon = meta.get("icon", "🏅")
                return f"{icon} New badge unlocked: {name}"
    except Exception:
        pass

    return line


# -------------------------------------------------
# 🔥 Logout purge helper (ADDITIVE)
# -------------------------------------------------

def confirm_and_purge_local_state():
    """
    Warn user and delete ~/.devopsmind across OSes.
    """
    devopsmind_dir = Path.home() / ".devopsmind"

    if not devopsmind_dir.exists():
        return True

    console.print(
        Panel(
            Text(
                "⚠️ You are about to log out.\n\n"
                "This will DELETE all local DevOpsMind data:\n\n"
                f"  {devopsmind_dir}\n\n"
                "Including:\n"
                "- progress\n"
                "- XP\n"
                "- achievements\n"
                "- offline state\n\n"
                "You may back up this directory before continuing.\n",
                style="yellow",
            ),
            title="Logout Warning",
            border_style="yellow",
        )
    )

    answer = input("Continue? [y/N]: ").strip().lower()
    if answer != "y":
        console.print("❌ Logout cancelled.", style="dim")
        return False

    try:
        shutil.rmtree(devopsmind_dir)
        console.print("🗑️ Local DevOpsMind data removed.", style="green")
        return True
    except Exception as e:
        console.print(
            Panel(
                Text(f"Failed to delete {devopsmind_dir}\n\n{e}", style="red"),
                title="Logout Error",
                border_style="red",
            )
        )
        return False


# -------------------------------------------------
# Main
# -------------------------------------------------

def main():
    try:
        cmd = sys.argv[1] if len(sys.argv) > 1 else ""

        # -------------------------------------------------
        # First-run
        # -------------------------------------------------
        if not (len(sys.argv) >= 2 and sys.argv[1] == "login"):
            ensure_first_run()

        # -------------------------------------------------
        # LOGIN / LOGOUT
        # -------------------------------------------------
        if cmd == "login":
            ensure_first_run(force=True)
            return

        if len(sys.argv) >= 2 and sys.argv[1] == "logout":
            if not confirm_and_purge_local_state():
                return

            reset_session()
            console.print(
                boxed(
                    "🔓 Logout",
                    Text("Logged out. Local state cleared.", style="green"),
                )
            )
            return

        # -------------------------------------------------
        # Mode
        # -------------------------------------------------
        if len(sys.argv) >= 3 and sys.argv[1] == "mode":
            if sys.argv[2] == "online":
                console.print(boxed("🌐 Mode", set_mode_online()))
            elif sys.argv[2] == "offline":
                console.print(boxed("🌐 Mode", set_mode_offline()))
            else:
                console.print(
                    boxed(
                        "🌐 Mode",
                        Text("Usage: devopsmind mode [online|offline]", style="yellow"),
                    )
                )
            return

        # -------------------------------------------------
        # Argument parsing
        # -------------------------------------------------
        parser = argparse.ArgumentParser(prog="devopsmind")
        parser.add_argument("--version", action="store_true")
        parser.add_argument("--stack", help="Filter by stack")
        sub = parser.add_subparsers(dest="cmd")

        for c in [
            "list",
            "stats",
            "leaderboard",
            "doctor",
            "badges",
            "submit",
            "sync",
            "stacks",
            "my-stacks",
        ]:
            sub.add_parser(c)

        p_play = sub.add_parser("play")
        p_play.add_argument("id")

        p_val = sub.add_parser("validate")
        p_val.add_argument("id")

        p_desc = sub.add_parser("describe")
        p_desc.add_argument("id")

        p_hint = sub.add_parser("hint")
        p_hint.add_argument("id")

        p_search = sub.add_parser("search")
        p_search.add_argument("term")

        p_profile = sub.add_parser("profile")
        profile_sub = p_profile.add_subparsers(dest="action", required=True)
        profile_sub.add_parser("show")
        profile_sub.add_parser("list")

        # 🔐 Auth
        p_auth = sub.add_parser("auth")
        auth_sub = p_auth.add_subparsers(dest="action", required=True)
        auth_sub.add_parser("rotate-recovery")

        args = parser.parse_args()

        # -------------------------------------------------
        # Version
        # -------------------------------------------------
        if args.version:
            console.print(
                boxed(
                    "ℹ️ Version",
                    Text(f"DevOpsMind v{VERSION}", style="bold green"),
                )
            )
            return

        # -------------------------------------------------
        # Stack filter
        # -------------------------------------------------
        if args.stack:
            console.print(
                boxed(
                    f"📦 Stack · {args.stack}",
                    list_challenges(stack=args.stack),
                )
            )
            return

        # -------------------------------------------------
        # Gameplay
        # -------------------------------------------------
        if args.cmd == "play":
            console.print(boxed(f"🎮 Play · {args.id}", play(args.id)))
            return

        # -------------------------------------------------
        # VALIDATE
        # -------------------------------------------------
        if args.cmd == "validate":
            result = validate_only(args.id)

            if isinstance(result, dict) and result.get("error"):
                body = [Text(result["error"], style="red")]

                attempts = result.get("attempts")
                limit = result.get("fail_limit")
                if attempts and limit:
                    body.append(Text(f"\nAttempts: {attempts}/{limit}", style="yellow"))

                if result.get("auto_hint"):
                    hint = result["auto_hint"]
                    body.append(hint if isinstance(hint, Text) else Text(hint, style="cyan"))

                console.print(
                    boxed(
                        "❌ Validation Failed",
                        Group(*body),
                    )
                )
                return

            base_panel = show_validation_result(
                challenge_id=result.get("challenge_id"),
                stack=result.get("stack"),
                difficulty=result.get("difficulty"),
                skills=result.get("skills"),
                earned_badges=result.get("achievements"),
                sync_status=result.get("sync_status"),
            )

            panel_lines = [base_panel]

            if result.get("achievement_banner"):
                panel_lines.append(Text(""))
                panel_lines.append(Text("🏅 New Achievements Unlocked", style="bold yellow"))
                panel_lines.append(Text("────────────────────────────"))
                for line in result["achievement_banner"].splitlines():
                    panel_lines.append(Text(resolve_badge_line(line)))

            console.print(
                boxed(
                    f"🧪 Validate · {args.id}",
                    Group(*panel_lines),
                )
            )
            return

        # -------------------------------------------------
        # Remaining commands (UNCHANGED)
        # -------------------------------------------------
        if args.cmd == "auth":
            if args.action == "rotate-recovery":
                rotate_recovery_key()
                return

        if args.cmd == "describe":
            console.print(boxed(f"📖 Describe · {args.id}", describe_challenge(args.id)))
            return

        if args.cmd == "hint":
            console.print(boxed(f"💡 Hint · {args.id}", show_hint(args.id)))
            return

        if args.cmd == "search":
            console.print(boxed("🔍 Search", search_challenges(args.term)))
            return

        if args.cmd == "stats":
            console.print(boxed("📊 Stats", render_stats()))
            return

        if args.cmd == "leaderboard":
            console.print(boxed("🏆 Leaderboard", show_leaderboards()))
            return

        if args.cmd == "doctor":
            console.print(boxed("🩺 Doctor", run_doctor()))
            return

        if args.cmd == "badges":
            console.print(boxed("🏅 Badges", list_badges()))
            return

        if args.cmd in ("stacks", "my-stacks"):
            console.print(
                boxed(
                    "📦 My Stack Progress",
                    show_my_stack_progress(),
                )
            )
            return

        if args.cmd == "sync":
            console.print(boxed("🔄 Sync", sync_default()))
            return

        if args.cmd == "submit":
            console.print(boxed("📤 Submit", submit_pending()))
            return

        if args.cmd == "profile":
            if args.action == "show":
                console.print(boxed("👤 Profile", show_profile()))
            elif args.action == "list":
                console.print(boxed("👤 Profiles", list_profiles()))
            return

        console.print(
            boxed(
                "📋 Available Challenges",
                list_challenges(),
            )
        )

    except KeyboardInterrupt:
        cancelled()


if __name__ == "__main__":
    main()
