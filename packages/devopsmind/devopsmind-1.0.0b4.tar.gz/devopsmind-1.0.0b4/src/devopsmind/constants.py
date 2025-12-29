from pathlib import Path
import os

VERSION = "1.0.0"

# -------------------------------------------------
# Relay / Backend (AUTHORITATIVE)
# -------------------------------------------------

# Single source of truth for DevOpsMind relay
RELAY_URL = "https://devopsmind-relay.infraforgelabs.workers.dev"

# -------------------------------------------------
# XP → Rank Mapping (Player Progression)
# -------------------------------------------------

XP_LEVELS = [
    (0, "Beginner"),
    (1000, "Apprentice"),
    (5000, "Operator"),
    (10000, "Engineer"),
    (20000, "Specialist"),
    (35000, "Advanced"),
    (55000, "Expert"),
    (80000, "Master"),
    (120000, "Architect"),
    (180000, "Grandmaster"),
    (260000, "Legend"),
    (370000, "Mythic"),
    (520000, "Eternal"),
    (750000, "Ascendant"),
    (1_000_000, "Vanguard"),
    (1_500_000, "Paragon"),
    (2_000_000, "Virtuoso"),
    (3_000_000, "Transcendent"),
    (5_000_000, "Celestial"),
    (10_000_000, "Infinite"),
]

# -------------------------------------------------
# Difficulty System (Challenge-Level)
# -------------------------------------------------

DIFFICULTY_ORDER = {
    "Easy": 1,
    "Medium": 2,
    "Hard": 3,
    "Expert": 4,
    "Master": 5,
    "Architect": 6,
    "Principal": 7,
    "Staff": 8,
    "Distinguished": 9,
    "Fellow": 10,
}

DIFFICULTY_XP = {
    "Easy": 50,
    "Medium": 100,
    "Hard": 150,
    "Expert": 300,
    "Master": 500,
    "Architect": 750,
    "Principal": 1000,
    "Staff": 1300,
    "Distinguished": 1600,
    "Fellow": 2000,
}

# -------------------------------------------------
# Stack System (CLI · Snapshot · Future Dashboard)
# -------------------------------------------------

STACKS = {
    "linux": "Linux",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "git": "Git",
    "ci_cd": "CI/CD",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "cloud": "Cloud",
    "security": "Security",
    "monitoring": "Monitoring",
    "bash": "Bash",
    "python": "Python",
    "networking": "Networking",
    "helm": "Helm",
    "k8s": "Kubernetes",
}

# -------------------------------------------------
# Stack Colors (CLI UI)
# -------------------------------------------------

STACK_COLORS = {
    "linux": "green",
    "docker": "blue",
    "kubernetes": "cyan",
    "k8s": "cyan",
    "git": "orange",
    "ci_cd": "magenta",
    "terraform": "purple",
    "ansible": "yellow",
    "cloud": "bright_blue",
    "security": "red",
    "monitoring": "bright_green",
    "bash": "white",
    "python": "yellow",
    "networking": "bright_cyan",
    "helm": "bright_magenta",
}

# -------------------------------------------------
# Stack Icons (CLI UI)
# -------------------------------------------------

STACK_ICONS = {
    "linux": "🐧",
    "docker": "🐳",
    "kubernetes": "☸️",
    "k8s": "☸️",
    "git": "🌱",
    "ci_cd": "🔁",
    "terraform": "🏗️",
    "ansible": "📜",
    "cloud": "☁️",
    "security": "🛡️",
    "monitoring": "📊",
    "bash": "💻",
    "python": "🐍",
    "networking": "🌐",
    "helm": "⛵",
}

# -------------------------------------------------
# Stack XP Weighting (INACTIVE – FUTURE USE)
# -------------------------------------------------

STACK_XP_WEIGHT = {
    "linux": 1.0,
    "docker": 1.1,
    "kubernetes": 1.2,
    "k8s": 1.2,
    "git": 0.8,
    "ci_cd": 1.0,
    "terraform": 1.2,
    "ansible": 1.0,
    "cloud": 1.3,
    "security": 1.4,
    "monitoring": 1.0,
    "bash": 0.9,
    "python": 1.0,
    "networking": 1.1,
    "helm": 1.0,
}

# -------------------------------------------------
# Paths & Storage (LOCAL ONLY)
# -------------------------------------------------

XDG = os.environ.get("XDG_DATA_HOME")
DATA_DIR = Path(XDG) / "devopsmind" if XDG else Path.home() / ".devopsmind"

PROFILE_DIR = DATA_DIR / "profiles"
PENDING_SYNC_DIR = DATA_DIR / "pending_sync"

BUNDLED_CHALLENGES = Path(__file__).resolve().parent / "challenges"

DATA_DIR.mkdir(parents=True, exist_ok=True)
PROFILE_DIR.mkdir(parents=True, exist_ok=True)
PENDING_SYNC_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------
# User Workspace (Visible)
# -------------------------------------------------

WORKSPACE_ROOT = Path.home() / "workspace"
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------
# UI Colors (CLI)
# -------------------------------------------------

PRIMARY_COLOR = "cyan"
SUCCESS_COLOR = "green"
ERROR_COLOR = "red"
