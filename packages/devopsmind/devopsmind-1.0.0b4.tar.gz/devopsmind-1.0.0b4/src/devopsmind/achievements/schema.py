ALLOWED_TOP_KEYS = {
    "id", "name", "description", "category", "icon", "condition"
}

ALLOWED_CONDITIONS = {
    "xp_gte",
    "completed_gte",
    "stack_completed_gte",
    "difficulty_completed_gte",
}


def validate_achievement(ach: dict, source: str):
    if not isinstance(ach, dict):
        raise ValueError(f"[{source}] Achievement must be a dict")

    extra = set(ach.keys()) - ALLOWED_TOP_KEYS
    if extra:
        raise ValueError(f"[{source}] Invalid keys: {extra}")

    for key in ("id", "name", "category", "condition"):
        if key not in ach:
            raise ValueError(f"[{source}] Missing key: {key}")

    cond = ach["condition"]
    if not isinstance(cond, dict):
        raise ValueError(f"[{source}] condition must be a dict")

    for c in cond:
        if c not in ALLOWED_CONDITIONS:
            raise ValueError(f"[{source}] Invalid condition: {c}")

    if "xp_gte" in cond and not isinstance(cond["xp_gte"], int):
        raise ValueError(f"[{source}] xp_gte must be int")

    if "completed_gte" in cond and not isinstance(cond["completed_gte"], int):
        raise ValueError(f"[{source}] completed_gte must be int")

    if "stack_completed_gte" in cond and not isinstance(cond["stack_completed_gte"], dict):
        raise ValueError(f"[{source}] stack_completed_gte must be dict")

    if "difficulty_completed_gte" in cond and not isinstance(cond["difficulty_completed_gte"], dict):
        raise ValueError(f"[{source}] difficulty_completed_gte must be dict")


def validate_achievement_file(data: list, source: str):
    if not isinstance(data, list):
        raise ValueError(f"[{source}] Root must be a list")

    seen = set()
    for ach in data:
        validate_achievement(ach, source)
        if ach["id"] in seen:
            raise ValueError(f"[{source}] Duplicate id: {ach['id']}")
        seen.add(ach["id"])

