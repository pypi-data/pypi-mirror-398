import requests
from devopsmind.constants import VERSION


VERSION_META_URL = (
    "https://raw.githubusercontent.com/"
    "InfraForgeLabs/DevOpsMind/main/meta/version.json"
)


def _parse(version: str):
    """
    Convert '1.2.3' -> (1, 2, 3)
    Non-numeric parts are ignored safely.
    """
    try:
        return tuple(int(p) for p in version.split("."))
    except Exception:
        return (0,)


def check_for_update(timeout: int = 5):
    """
    Returns:
      (update_available: bool, latest_version: str | None, notes: str | None)
    """
    try:
        r = requests.get(VERSION_META_URL, timeout=timeout)
        r.raise_for_status()
        meta = r.json()

        latest = meta.get("latest_version")
        notes = meta.get("notes", "")

        if not latest:
            return False, None, None

        if _parse(latest) > _parse(VERSION):
            return True, latest, notes

    except Exception:
        # Offline / GitHub unreachable → silent
        return False, None, None

    return False, None, None
