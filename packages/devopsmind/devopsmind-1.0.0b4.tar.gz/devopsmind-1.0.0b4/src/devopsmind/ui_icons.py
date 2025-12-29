"""
DevOpsMind UI Icons
==================
Central, OS-safe emoji & ASCII symbol registry.

Rules:
- All CLI emojis must come from here
- Game data (achievements, stacks) MAY use emojis directly
- ASCII fallback always available
"""

import os
import sys

# -------------------------
# Environment detection
# -------------------------

def _plain_mode() -> bool:
    return any([
        os.getenv("DEVOPSMIND_PLAIN"),
        os.getenv("CI"),
        os.getenv("NO_COLOR"),
        not sys.stdout.isatty(),
    ])

PLAIN = _plain_mode()

# -------------------------
# ASCII fallback (100% safe)
# -------------------------

_ASCII = {
    # Core UI
    "ok": "[OK]",
    "fail": "[FAIL]",
    "warn": "[WARN]",
    "info": "[INFO]",
    "tip": "[TIP]",
    "play": ">",
    "arrow": "->",
    "bullet": "*",

    # Actions
    "search": "[SEARCH]",
    "sync": "[SYNC]",
    "submit": "[SUBMIT]",
    "stats": "[STATS]",

    # Security
    "lock": "[LOCK]",
    "unlock": "[UNLOCK]",

    # Status / flow
    "online": "[ONLINE]",
    "offline": "[OFFLINE]",
    "refresh": "[REFRESH]",

    # User / identity
    "user": "[USER]",
    "profile": "[PROFILE]",

    # Data / objects
    "stack": "[STACK]",
    "workspace": "[DIR]",
    "file": "[FILE]",

    # Progress
    "xp": "XP",
    "rank": "RANK",
    "achievement": "[ACH]",
}

# -------------------------
# Emoji UI (enhanced UX)
# -------------------------

_EMOJI = {
    # Core UI
    "ok": "✅",
    "fail": "❌",
    "warn": "⚠️",
    "info": "ℹ️",
    "tip": "💡",
    "play": "▶️",
    "arrow": "👉",
    "bullet": "🔹",

    # Actions
    "search": "🔍",
    "sync": "🔄",
    "submit": "📤",
    "stats": "📊",

    # Security
    "lock": "🔐",
    "unlock": "🔓",

    # Status / flow
    "online": "🌐",
    "offline": "📴",
    "refresh": "🔁",

    # User / identity
    "user": "👤",
    "profile": "👤",

    # Data / objects
    "stack": "📦",
    "workspace": "📂",
    "file": "📄",

    # Progress
    "xp": "🧠",
    "rank": "🏅",
    "achievement": "🎉",
}

# -------------------------
# Public API
# -------------------------

ICONS = _ASCII if PLAIN else _EMOJI

def icon(name: str) -> str:
    """Safe icon lookup"""
    return ICONS.get(name, "")

# Common exports (ergonomic)
OK = icon("ok")
FAIL = icon("fail")
WARN = icon("warn")
INFO = icon("info")
TIP = icon("tip")
PLAY = icon("play")

ONLINE = icon("online")
OFFLINE = icon("offline")

LOCK = icon("lock")
UNLOCK = icon("unlock")

XP = icon("xp")
RANK = icon("rank")
ACHIEVEMENT = icon("achievement")

__all__ = [
    "PLAIN",
    "ICONS",
    "icon",
    "OK",
    "FAIL",
    "WARN",
    "INFO",
    "TIP",
    "PLAY",
    "ONLINE",
    "OFFLINE",
    "LOCK",
    "UNLOCK",
    "XP",
    "RANK",
    "ACHIEVEMENT",
]
