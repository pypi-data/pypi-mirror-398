import subprocess, os

def validate(context=None):
    script = "analyze_firewall.sh"

    if not os.path.exists(script):
        return False, "analyze_firewall.sh missing."

    try:
        out = subprocess.check_output(["bash", script], text=True).strip()
    except Exception as e:
        return False, f"Script failed: {e}"

    if out != "Firewall correctly allows HTTP only":
        return False, "Incorrect firewall analysis."

    return True, "Firewall rules correctly analyzed."
