"""
Cloud restore decision logic

Rules:
- Restore is tied to USER ID, not installation
- Prompt only if:
  - cloud snapshot exists
  - user has not decided before
- Decision is stored locally
"""

from devopsmind.snapshot import snapshot_exists, restore_snapshot
from devopsmind.state import get_restore_decision, set_restore_decision


def maybe_prompt_cloud_restore(user_public_id: str):
    """
    Ask user whether to restore cloud snapshot if:
    - snapshot exists
    - no prior decision stored
    """

    # No cloud data → nothing to do
    if not snapshot_exists(user_public_id):
        return

    # Decision already made → respect it
    decision = get_restore_decision(user_public_id)
    if decision is not None:
        return

    # Ask user
    choice = input(
        "☁️ Cloud progress found.\n"
        "Restore cloud progress now? [Y/n]: "
    ).strip().lower()

    decision = choice in ("", "y", "yes")
    set_restore_decision(user_public_id, decision)

    if decision:
        restore_snapshot(user_public_id)
