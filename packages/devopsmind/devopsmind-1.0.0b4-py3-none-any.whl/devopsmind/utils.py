from pathlib import Path

from .constants import BUNDLED_CHALLENGES, DATA_DIR


def challenges_exist() -> bool:
    """
    Check if bundled challenges directory exists and is non-empty.
    """
    try:
        return BUNDLED_CHALLENGES.exists() and any(BUNDLED_CHALLENGES.iterdir())
    except Exception:
        return False


def data_dir_writable() -> bool:
    """
    Check if DevOpsMind data directory is writable.
    """
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        test_file = DATA_DIR / ".write_test"
        test_file.write_text("ok")
        test_file.unlink(missing_ok=True)
        return True
    except Exception:
        return False
