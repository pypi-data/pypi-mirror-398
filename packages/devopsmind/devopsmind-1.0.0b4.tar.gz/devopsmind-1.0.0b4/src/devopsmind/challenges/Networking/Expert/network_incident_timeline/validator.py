import subprocess
import os

EXPECTED = [
    "10:01 DNS failure detected",
    "10:02 Firewall rule change applied",
    "10:03 Application outage occurred",
]

def validate(context=None):
    script = "timeline.sh"

    if not os.path.exists(script):
        return False, "timeline.sh is missing."

    try:
        output = subprocess.check_output(
            ["bash", script],
            text=True,
            timeout=5
        ).strip().splitlines()
    except Exception as e:
        return False, f"Script execution failed: {e}"

    if output != EXPECTED:
        return False, "Timeline output does not match expected incident sequence."

    return True, "Incident timeline correctly reconstructed."
