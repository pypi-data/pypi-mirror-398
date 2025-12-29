import os
import requests
import time

from devopsmind.state import load_state, save_state

WORKER_BASE_URL = os.getenv(
    "DEVOPSMIND_WORKER_URL",
    "https://devopsmind-relay.infraforgelabs.workers.dev",
)


class AuthError(Exception):
    pass


# =====================================================
# AUTHENTICATION (LOGIN / RESET WITH RECOVERY KEY)
# =====================================================

def authenticate_with_worker(
    *,
    email: str,
    mode: str,
    password: str | None = None,
    recovery_key: str | None = None,
    new_password: str | None = None,
):
    """
    mode:
      - "login"
      - "reset"
    """

    # ------------------------------
    # LOGIN
    # ------------------------------
    if mode == "login":
        if not password:
            raise ValueError("password required for login")

        endpoint = "/auth/login"
        payload = {
            "email": email,
            "password": password,
            "mode": "login",
        }

    # ------------------------------
    # RESET (RECOVERY KEY)
    # ------------------------------
    elif mode == "reset":
        if not recovery_key or not new_password:
            raise ValueError("recovery_key and new_password required for reset")

        # 🔒 FORCE correct endpoint + mode
        endpoint = "/auth/login"
        payload = {
            "email": email,
            "mode": "reset",
            "recovery_key": recovery_key,
            "new_password": new_password,
        }

    else:
        raise ValueError(f"Unknown auth mode: {mode}")

    # ------------------------------
    # REQUEST
    # ------------------------------
    try:
        r = requests.post(
            f"{WORKER_BASE_URL}{endpoint}",
            json=payload,
            timeout=10,
        )
    except requests.RequestException as e:
        raise AuthError("Unable to reach auth server") from e

    if r.status_code != 200:
        return {"ok": False}

    data = r.json()
    if not data.get("ok"):
        return {"ok": False}

    # ------------------------------
    # SESSION TOKEN (LOGIN ONLY)
    # ------------------------------
    token = data.get("token")
    if token:
        state = load_state()
        state.setdefault("auth", {})
        state["auth"]["session"] = {
            "token": token,
            "created_at": time.time(),
        }
        save_state(state)

    return data


# =====================================================
# OTP — REQUEST (EMAIL)
# =====================================================

def request_recovery_otp(email: str) -> bool:
    """
    Requests an email OTP for account recovery.
    Silent success by design.
    """
    try:
        requests.post(
            f"{WORKER_BASE_URL}/auth/recovery/request",
            json={"email": email},
            timeout=10,
        )
        return True
    except requests.RequestException:
        return False


# =====================================================
# OTP — VERIFY + RESET
# =====================================================

def verify_recovery_otp(
    *,
    email: str,
    otp: str,
    new_password: str,
) -> dict:
    """
    Verifies OTP and resets password.
    """
    try:
        r = requests.post(
            f"{WORKER_BASE_URL}/auth/recovery/verify",
            json={
                "email": email,
                "otp": otp,
                "new_password": new_password,
            },
            timeout=10,
        )
    except requests.RequestException:
        return {"ok": False}

    if r.status_code != 200:
        return {"ok": False}

    return r.json()
