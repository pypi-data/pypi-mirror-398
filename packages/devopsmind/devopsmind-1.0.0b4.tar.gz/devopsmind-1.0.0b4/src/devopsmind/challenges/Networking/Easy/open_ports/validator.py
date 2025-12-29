import os
import subprocess

def validate(context=None):
    script = "check_ports.sh"

    if not os.path.exists(script):
        return False, "Missing check_ports.sh script."

    if not os.access(script, os.X_OK):
        return False, "check_ports.sh must be executable."

    try:
        out = subprocess.check_output(
            ["bash", script],
            text=True,
            timeout=5
        )
    except Exception as e:
        return False, f"Script failed to run safely: {e}"

    for port in ["22", "80", "443"]:
        if f"Port {port}" not in out:
            return False, f"Output must reference port {port}."

    return True, "Port-checking logic validated safely."
