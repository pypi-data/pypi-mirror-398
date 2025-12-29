import subprocess, os

def validate(context=None):
    script = "diagnose_dns.sh"

    if not os.path.exists(script):
        return False, "diagnose_dns.sh missing."

    try:
        out = subprocess.check_output(["bash", script], text=True).strip()
    except Exception as e:
        return False, f"Script failed: {e}"

    if out != "No DNS servers reachable":
        return False, "Incorrect diagnosis."

    return True, "DNS issue correctly diagnosed."
