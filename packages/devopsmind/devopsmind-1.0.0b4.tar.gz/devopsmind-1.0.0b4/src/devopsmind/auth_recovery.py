import requests
import sys

from devopsmind.state import load_state
from devopsmind.remote import WORKER_BASE_URL


# -------------------------------------------------
# Recovery Key Rotation (ONLINE ONLY)
# -------------------------------------------------

def rotate_recovery_key():
    """
    Rotate the account recovery key.

    Rules:
    - Requires ONLINE mode
    - Requires valid Worker session
    - Does NOT ask for password
    - Does NOT store recovery key locally
    - Displays recovery key ONCE
    """

    state = load_state()

    if state.get("mode") != "online":
        print("❌ Recovery key rotation requires ONLINE mode")
        sys.exit(1)

    # 🔑 Session token is the real source of truth
    session = state.get("auth", {}).get("session")
    if not session or not session.get("token"):
        print("❌ You must be logged in to rotate recovery key")
        sys.exit(1)

    token = session["token"]

    url = f"{WORKER_BASE_URL}/auth/rotate-recovery"

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"confirm": True},
            timeout=15,
        )
    except requests.RequestException as e:
        print("❌ Failed to contact auth server")
        print(str(e))
        sys.exit(1)

    if response.status_code != 200:
        try:
            err = response.json()
        except Exception:
            err = response.text
        print("❌ Recovery key rotation failed")
        print(err)
        sys.exit(1)

    data = response.json()
    recovery_key = data.get("recovery_key")

    if not recovery_key:
        print("❌ Server did not return a recovery key")
        sys.exit(1)

    print("\n🔑 Recovery key rotated successfully\n")
    print(recovery_key)
    print(
        "\n⚠️  SAVE THIS KEY SECURELY.\n"
        "It will NOT be shown again.\n"
        "If you lose it, your account cannot be recovered.\n"
    )
