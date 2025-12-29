from rich.text import Text

from devopsmind.first_run import ensure_first_run
from devopsmind.state import load_state, save_state


def set_mode_online():
    """
    Enable online mode using the SAME flow as `devopsmind login`.
    """
    ensure_first_run(force=True)
    return Text("✔ Online mode enabled", style="green")


def set_mode_offline():
    """
    Switch to offline mode (no password required).
    """
    state = load_state()
    state["mode"] = "offline"
    save_state(state)
    return Text("✔ Offline mode enabled", style="yellow")
