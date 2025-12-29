from pathlib import Path
import importlib.util
import os
import yaml

from .progress import record_completion, load_state, save_state
from .sync import attempt_sync
from devopsmind.badges import evaluate_badges_delta
from .hint import show_hint
from .challenge_resolver import find_challenge_by_id


WORKSPACE_DIR = Path.home() / "workspace"
PLAY_MARKER = ".devopsmind_played"
FAIL_LIMIT = 3

ACHIEVEMENTS_DIR = Path(__file__).parent / "achievements"


# -------------------------------------------------
# Achievement Registry (YAML → id → name/icon)
# -------------------------------------------------
def _load_achievement_registry():
    registry = {}

    if not ACHIEVEMENTS_DIR.exists():
        return registry

    for file in ACHIEVEMENTS_DIR.glob("*.yaml"):
        data = yaml.safe_load(file.read_text()) or []
        for ach in data:
            registry[ach["id"]] = {
                "name": ach.get("name", ach["id"]),
                "icon": ach.get("icon", ""),
            }

    return registry


_ACHIEVEMENT_REGISTRY = _load_achievement_registry()


def _resolve_achievement_display(ids):
    resolved = []
    for ach_id in ids:
        meta = _ACHIEVEMENT_REGISTRY.get(ach_id)
        if meta:
            label = f"{meta['icon']} {meta['name']}".strip()
            resolved.append(label)
        else:
            resolved.append(ach_id)
    return resolved


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _workspace(challenge_id: str) -> Path:
    return WORKSPACE_DIR / challenge_id


def _cwd_matches_workspace(challenge_id: str) -> bool:
    try:
        return Path.cwd().resolve() == _workspace(challenge_id).resolve()
    except Exception:
        return False


def _was_played(challenge_id: str) -> bool:
    return (_workspace(challenge_id) / PLAY_MARKER).exists()


def _increment_fail(challenge_id: str) -> int:
    state = load_state()
    failures = state.setdefault("validation_failures", {})
    failures[challenge_id] = failures.get(challenge_id, 0) + 1
    save_state(state)
    return failures[challenge_id]


def _reset_fail(challenge_id: str):
    state = load_state()
    failures = state.get("validation_failures", {})
    if challenge_id in failures:
        del failures[challenge_id]
        save_state(state)


def _run_challenge_validator(challenge_id: str):
    ws = _workspace(challenge_id)
    challenge_dir = find_challenge_by_id(challenge_id)

    if not challenge_dir:
        return False, "Challenge source not found."

    validator_file = challenge_dir / "validator.py"
    if not validator_file.exists():
        return False, "Challenge validator not found."

    try:
        spec = importlib.util.spec_from_file_location(
            f"validator_{challenge_id}", validator_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "validate"):
            return False, "Validator must define validate()"

        cwd = os.getcwd()
        try:
            os.chdir(ws)
            result = module.validate()
        finally:
            os.chdir(cwd)

        if not isinstance(result, tuple) or len(result) != 2:
            return False, "Validator must return (bool, message)"

        return bool(result[0]), str(result[1])

    except Exception as e:
        return False, f"Validator error: {e}"


# -------------------------------------------------
# Validator (CORE)
# -------------------------------------------------
def validate_only(
    challenge_id,
    stack=None,
    difficulty=None,
    skills=None,
    xp=None,
):
    ws = _workspace(challenge_id)

    if not ws.exists():
        return {"error": "Workspace not found.\nRun: devopsmind play <challenge_id>"}

    if not _was_played(challenge_id):
        return {"error": "Challenge not started.\nRun: devopsmind play <challenge_id>"}

    if not _cwd_matches_workspace(challenge_id):
        return {
            "error": f"Validation must be run from the challenge workspace.\ncd {ws}"
        }

    success, message = _run_challenge_validator(challenge_id)

    # -----------------------------
    # FAILURE PATH
    # -----------------------------
    if not success:
        attempts = _increment_fail(challenge_id)
        auto_hint = show_hint(challenge_id) if attempts >= FAIL_LIMIT else None

        return {
            "error": message,
            "attempts": attempts,
            "fail_limit": FAIL_LIMIT,
            "auto_hint": auto_hint,
        }

    # -----------------------------
    # SUCCESS PATH
    # -----------------------------
    _reset_fail(challenge_id)

    new_badges = evaluate_badges_delta(
        record_completion,
        challenge_id=challenge_id,
        stack=stack,
        difficulty=difficulty,
    )

    # ✅ ONLY resolve and return if NEW badges exist
    achievements = (
        _resolve_achievement_display(new_badges)
        if new_badges
        else []
    )

    raw_sync = attempt_sync()
    sync_status = (
        {"info": "No changes to sync. Progress already up to date."}
        if isinstance(raw_sync, dict) and raw_sync.get("already")
        else raw_sync
    )

    return {
        "challenge_id": challenge_id,
        "stack": stack,
        "difficulty": difficulty,
        "skills": skills or [],
        "xp_awarded": xp,
        "message": message,
        "achievements": achievements,  # ✅ UI shows this inside the box
        "sync_status": sync_status,
    }
