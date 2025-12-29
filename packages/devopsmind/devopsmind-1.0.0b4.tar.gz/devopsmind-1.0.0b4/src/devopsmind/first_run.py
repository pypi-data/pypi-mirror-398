from rich.panel import Panel
from rich.text import Text
from rich.console import Console
import getpass
import time

from devopsmind.state import (
    is_first_run,
    save_state,
    load_state,
    mark_session_unlocked,
    get_restore_decision,
    set_restore_decision,
)
from devopsmind.snapshot import snapshot_exists, restore_snapshot
from devopsmind.remote import (
    authenticate_with_worker,
)
from devopsmind.cloud_restore import maybe_prompt_cloud_restore

console = Console()


def ensure_first_run(force: bool = False) -> bool:
    """
    Returns:
      True  -> success
      False -> failed / cancelled
    """

    if not force and not is_first_run():
        return True

    console.print(
        Panel(
            Text(
                "Welcome to DevOpsMind 🚀\n\n"
                "DevOpsMind works fully offline by default.\n"
                "You decide if and when anything goes online.",
                justify="center",
            ),
            title="🧠 First Run Setup",
            border_style="cyan",
        )
    )

    choice = input("Enable ONLINE mode now? [y/N]: ").strip().lower()

    # -------------------------------------------------
    # OFFLINE MODE
    # -------------------------------------------------
    if choice != "y":
        username = input("👤 Choose a local username: ").strip()
        handle = input("🎮 Choose a handle: ").strip()
        gamer = handle  # ✅ FIX: define gamer

        state = {
            "mode": "offline",
            "auth": {"lock_enabled": False},
            "profile": {
                "username": username,
                "gamer": gamer,
            },
        }

        save_state(state)
        return True

    # -------------------------------------------------
    # ONLINE MODE
    # -------------------------------------------------
    console.print(
        Panel(
            Text(
                "Online account options:\n\n"
                "1) Login\n"
                "2) Reset password (Recovery key)\n\n"
                "👉 For Email OTP reset, please use the DevOpsMind website.",
                justify="center",
            ),
            title="🔐 Online Account",
            border_style="cyan",
        )
    )

    action = input("Choose [1/2]: ").strip()

    # -------------------------------------------------
    # VALIDATION
    # -------------------------------------------------
    if action not in ("1", "2"):
        console.print(
            Panel(
                Text("❌ Invalid option selected."),
                title="Error",
                border_style="red",
            )
        )
        return False

    # -------------------------------------------------
    # EMAIL REQUIRED FOR LOGIN & RESET
    # -------------------------------------------------
    email = input("📧 Email: ").strip().lower()

    # =================================================
    # RESET — RECOVERY KEY (CLI ONLY)
    # =================================================
    if action == "2":
        console.print(
            Panel(
                Text(
                    "Recovery Key Reset\n\n"
                    "If you do not have your recovery key,\n"
                    "please reset your password via Email OTP\n"
                    "on the DevOpsMind website.",
                    justify="center",
                ),
                title="🔑 Password Reset",
                border_style="yellow",
            )
        )

        recovery_key = getpass.getpass("🔑 Enter recovery key: ")
        new_password = getpass.getpass("🔒 New password: ")

        result = authenticate_with_worker(
            email=email,
            mode="reset",
            recovery_key=recovery_key,
            new_password=new_password,
        )

        if not result or not result.get("ok"):
            console.print(
                Panel(
                    Text("❌ Password reset failed"),
                    title="Access Denied",
                    border_style="red",
                )
            )
            return False

        console.print(
            Panel(
                Text("✔ Password reset successful\nPlease login again."),
                title="Reset Complete",
                border_style="green",
            )
        )
        return False

    # =================================================
    # LOGIN
    # =================================================
    password = getpass.getpass("🔒 Enter password: ")

    result = authenticate_with_worker(
        email=email,
        password=password,
        mode="login",
    )

    if not result or not result.get("ok"):
        console.print(
            Panel(
                Text("❌ Invalid email or password"),
                title="Access Denied",
                border_style="red",
            )
        )
        return False

    # -------------------------------------------------
    # AUTH SUCCESS
    # -------------------------------------------------
    email_hash = result["email_hash"]
    user_public_id = result["user_public_id"]

    if "recovery_key" in result:
        console.print(
            Panel(
                Text(
                    "IMPORTANT — SAVE THIS RECOVERY KEY\n\n"
                    f"{result['recovery_key']}\n\n"
                    "This key is shown ONCE.\n"
                    "If you lose it, password reset is impossible.",
                    justify="center",
                ),
                title="🔑 Recovery Key",
                border_style="yellow",
            )
        )
        input("Press Enter after saving the recovery key...")

    username = input("👤 Choose a public username: ").strip()
    handle = input("🎮 Choose a handle: ").strip()
    gamer = handle  # ✅ FIX: define gamer

    snapshot_existed = snapshot_exists(user_public_id)

    # -------------------------------------------------
    # MERGE STATE
    # -------------------------------------------------
    state = load_state()
    state["mode"] = "online"

    auth = state.setdefault("auth", {})
    auth["lock_enabled"] = True

    state["profile"] = {
        "username": username,
        "gamer": gamer,
        "email_hash": email_hash,
        "user_public_id": user_public_id,
    }

    save_state(state)
    mark_session_unlocked()

    # -------------------------------------------------
    # CLOUD RESTORE
    # -------------------------------------------------
    maybe_prompt_cloud_restore(user_public_id)

    if snapshot_existed:
        decision = get_restore_decision(user_public_id)

        if decision is None:
            choice = input(
                "☁️ Cloud progress found.\n"
                "Restore cloud progress now? [Y/n]: "
            ).strip().lower()

            decision = choice in ("", "y", "yes")
            set_restore_decision(user_public_id, decision)

        if decision:
            restore_snapshot(user_public_id)

    console.print(
        Panel(
            Text(
                "✔ Online Successful\n"
                "✔ Identity verified\n"
                "✔ Secure session active",
                justify="center",
            ),
            title="✅ Setup Complete",
            border_style="green",
        )
    )

    return True
