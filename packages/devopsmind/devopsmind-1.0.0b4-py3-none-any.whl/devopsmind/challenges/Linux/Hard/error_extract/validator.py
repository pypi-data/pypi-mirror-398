from pathlib import Path

def validate(context=None):
    """
    Validates the challenge:
    - app.log must exist
    - errors.txt must exist
    - errors.txt must contain unique, sorted ERROR entries (timestamp + message)
    """

    app_log = Path("app.log")
    output = Path("errors.txt")

    # 1️⃣ Check for required files
    if not app_log.exists():
        return False, "app.log not found."
    if not output.exists():
        return False, "errors.txt not found. Please create it."

    # 2️⃣ Read input and output
    app_lines = [l.strip() for l in app_log.read_text().splitlines() if l.strip()]
    out_lines = [l.strip() for l in output.read_text().splitlines() if l.strip()]

    # 3️⃣ Extract expected ERROR lines from app.log
    expected = []
    for line in app_lines:
        parts = line.split(maxsplit=3)
        if len(parts) < 4:
            continue
        ts = f"{parts[0]} {parts[1]}"
        level = parts[2]
        msg = parts[3]
        if level == "ERROR":
            expected.append(f"{ts} {msg}")

    # 4️⃣ Deduplicate + sort
    expected = sorted(list(dict.fromkeys(expected)))  # unique + sorted

    # 5️⃣ Validation checks
    if not out_lines:
        return False, "errors.txt is empty."

    if out_lines != expected:
        # Compute simple difference summary
        missing = [e for e in expected if e not in out_lines]
        extra = [o for o in out_lines if o not in expected]
        msg = []
        if missing:
            msg.append(f"Missing {len(missing)} expected line(s).")
        if extra:
            msg.append(f"Found {len(extra)} unexpected line(s).")
        return False, " ".join(msg) or "Output does not match expected ERROR lines."

    # 6️⃣ Success!
    return True, "Great job! All ERROR lines extracted, unique, and sorted."
