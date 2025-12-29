import subprocess
import os

EXPECTED_OUTPUT = "Network reachable but DNS resolution failing"

def validate(context=None):
    script = "diagnose_network.sh"

    if not os.path.exists(script):
        return False, "diagnose_network.sh is missing."

    try:
        output = subprocess.check_output(
            ["bash", script],
            text=True,
            timeout=5
        ).strip()
    except Exception as e:
        return False, f"Script execution failed: {e}"

    if output != EXPECTED_OUTPUT:
        return False, f"Expected output: '{EXPECTED_OUTPUT}'"

    return True, "Correct diagnosis of DNS vs network connectivity."
