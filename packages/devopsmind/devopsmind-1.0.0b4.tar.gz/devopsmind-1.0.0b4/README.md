# 🧠 DevOpsMind — Gamified DevOps Learning Simulator

[![Latest Tag](https://img.shields.io/github/v/tag/InfraForgeLabs/DevOpsMind?sort=semver&style=for-the-badge&color=8A2BE2)](https://github.com/InfraForgeLabs/DevOpsMind/tags)
> 🏷️ **Latest Release:** Continuously evolving — Free · Local · Open · Forever

![Banner](docs/banner.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Platforms](https://img.shields.io/badge/Platforms-Linux%20%7C%20macOS%20%7C%20WSL-purple)
[![InfraForgeLabs](https://img.shields.io/badge/Org-InfraForgeLabs-black.svg)](https://github.com/InfraForgeLabs)

DevOpsMind is an **offline-first, CLI-based, gamified DevOps simulator**.
Solve real DevOps tasks, validate your solutions, earn **XP**, unlock **ranks**, and build muscle memory with hands-on DevOps workflows.

You don’t watch DevOps.  
You **practice DevOps**.

_Part of the **InfraForgeLabs** open DevOps innovation ecosystem._

---

## 🔐 Official Ownership & Identity

InfraForge is an open-source infrastructure automation and DevSecOps platform developed and maintained by InfraForge Labs.

🌐 **Official Website:** [https://devopsmind.infraforgelabs.in](https://devopsmind.infraforgelabs.in)

🏢 **Organization:** [https://infraforgelabs.in](https://infraforgelabs.in)

---

# 🎥 Gameplay Demo


![Gameplay Demo](docs/demo.png)

---
# 📘 Table of Contents

* [About This Project](#-devopsmind--gamified-devops-learning-simulator)
* [Repository Overview](#-project-architecture)
* [Quick Start](#-quickstart)
* [Features](#-features)
* [Deployment Options](#-installation-methods)
* [Integrations](#-stacks-covered)
* [Contribution](#-contributing)
* [Roadmap](#-roadmap)
* [Support](#-support--sponsorship)

---

# ✨ Features

* 🎮 50 curated DevOps challenges (10 stacks × 5 difficulty levels)
- 🎮 **Gamified progression** — XP, ranks, badges, and achievements
- 🖥️ **CLI-first experience** — learn where DevOps actually runs
- 📴 **Offline-first by design** — no internet required to learn
- 🌐 **Optional online mode** — secure sync and global leaderboard
- 🔐 **Privacy-respecting** — progress stored locally, snapshots encrypted

> **Core principle:** *Learn DevOps by Playing DevOps.*

---

## 🔒 Offline-First Philosophy

DevOpsMind works fully **without internet**.

- All challenges run locally
- Progress is stored on your machine
- Validation never depends on cloud services

Online features are **optional** and include:
- Secure progress sync
- Global leaderboard
- Cross-device recovery

You stay in control at all times.

---

## 🚀 Who Is This For?

- Students learning DevOps hands-on
- Engineers sharpening real-world skills
- Self-learners who prefer practice over theory
- Teams running offline labs or workshops

No subscriptions.  
No cloud lock-in.  
No hidden requirements.

---

# 🚀 Installation Matrix

| OS                | Recommended Method       | Notes                             |
| ----------------- | ------------------------ | --------------------------------- |
| **Ubuntu/Debian** | pipx                     | Best experience (isolated Python) |
| **Fedora/RHEL**   | pip                     | Works natively                    |
| **macOS**         | pipx via Homebrew Python | Perfect cross-platform setup      |
| **Windows**       | pipx (or WSL preferred)  | Use WSL for best compatibility    |
| **WSL**           | pipx                     | Recommended Linux experience      |

---

# 🧩 Installation Method — pipx (Official)


## **1️⃣ Prerequisites**

### **Install Python 3.9+ and pipx**

#### Ubuntu / Debian

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip pipx
pip install --user pipx
pipx ensurepath
```

#### Fedora / RHEL / CentOS

```bash
sudo dnf install -y python3 python3-pip git
```
```bash
sudo ln -s "$HOME"/.local/bin/devopsmind /usr/local/bin/devopsmind
```

#### macOS (with Homebrew)

```bash
brew install python3 pipx
pipx ensurepath
```

#### Windows (PowerShell)

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
```

---

## **2️⃣ Install DevOpsMind via pipx**

```bash
pipx install devopsmind
```
* (remove the pip install fallback to avoid confusion — pipx is your locked official method.)

---

## **3️⃣ Verify Installation**

```bash
devopsmind version
devopsmind stacks
```

---

## **4️⃣ Update to the Latest Version**

```bash
pipx upgrade devopsmind
```
* (remove the pip upgrade fallback to avoid confusion — pipx is your locked official method.)

---

## **5️⃣ Uninstall (if needed)**

```bash
pipx uninstall devopsmind
```
* (remove the pip uninstall fallback to avoid confusion — pipx is your locked official method.)

---

# 🧠 Notes

* `pipx` ensures your DevOpsMind installation stays isolated from system Python.
* Works perfectly across Linux, macOS, and WSL.

---

## 📦 Progress Portability via Snapshots

DevOpsMind stores progress as **local snapshots fully owned by the user**.
These snapshots can be copied to another machine and restored manually, allowing users to continue their learning journey **without accounts or mandatory cloud sync**.

Publishing progress to the public leaderboard is **optional** and **never affects** local snapshots, recovery, or offline usage.

---

### 🔐 Authoritative vs Public Data

**Authoritative progress (local snapshots)**

* Stored locally on the user’s machine
* Includes full challenge state, XP, achievements, and history
* Used for recovery and continuity
* Remains fully under user control

**Public leaderboard data**

* Aggregated and non-authoritative
* Contains only XP, rank, and completion counts
* Cannot be used to restore or synchronize progress

> **Local snapshots are the single source of truth.**
> Public leaderboard data is informational only.


---

# 🧭 Quickstart

DevOpsMind is **offline‑first**.
You can learn, play, and validate challenges **without internet**.
Online features are **optional** and fully under your control.

---

## 1️⃣ Create your profile (optional but recommended)

```bash
devopsmind login
```

* Creates your local profile
* Enables optional cloud sync
* Required for leaderboards

To return to offline‑only mode:

```bash
devopsmind logout
```

---

## 2️⃣ Choose your mode (offline / online)

DevOpsMind works **offline by default**.

```bash
devopsmind mode offline
```

Offline mode:

* Learn & validate challenges
* Progress stored locally
* No network usage

Enable online mode anytime:

```bash
devopsmind mode online
```

Online mode:

* Secure progress sync
* Global leaderboard access
* Restore progress on new devices

> 💡 Learning always works — mode only affects syncing.

---

## 3️⃣ View all available stacks

```bash
devopsmind stacks
```

---

## 4️⃣ Filter challenges by stack

```bash
devopsmind --stack docker
```

or search directly:

```bash
devopsmind search docker
```

---

## 5️⃣ Play a challenge

```bash
devopsmind play basic_dockerfile
```

This creates a local workspace for the challenge.

---

## 6️⃣ Need help? Read the description or hint

```bash
devopsmind describe basic_dockerfile
devopsmind hint basic_dockerfile
```

Hints unlock automatically after multiple failed attempts.

---

## 7️⃣ Validate your work

```bash
devopsmind validate basic_dockerfile
```

On success:

* XP is awarded
* Achievements unlock
* Progress is synced (if online)

---

## 8️⃣ Check your progress and XP

```bash
devopsmind stats
```

---

## 9️⃣ Submit score to the global leaderboard (online only)

```bash
devopsmind submit
```

> ℹ️ Requires `devopsmind mode online`

Your private progress remains encrypted.
Only public leaderboard data is shared.

---

## 🔟 View achievements

```bash
devopsmind badges
```

---

## 1️⃣1️⃣ Global leaderboard

```bash
devopsmind leaderboard
```

Shows:

* Global rankings
* Your pinned position
* XP & rank tiers

---

## 🔐 Advanced: Recovery & Security (Optional)

DevOpsMind never stores your password locally.

A **recovery key** is used to restore your progress if needed.

### Rotate recovery key

```bash
devopsmind auth rotate-recovery
```

Use this if:

* Your recovery key was exposed
* You want to improve account security

⚠️ Store your recovery key safely.
Losing it may prevent account recovery.

---

## ✅ That’s It

You can now:

* Learn DevOps fully offline
* Sync safely when you choose
* Earn XP, badges, and ranks
* Compete globally without sacrificing privacy

> Free · Local · Offline‑First · Secure · Optional Cloud 

## 🌐 Live Leaderboard
* You can view the real-time global leaderboard for **DevOpsMind** here:

> 🌍 **Live Site:** [https://devopsmind.infraforgelabs.in](https://devopsmind.infraforgelabs.in/leaderboard)
> 🧱 **Backup (GitHub Pages):** [https://infraforgelabs.github.io/DevOpsMind/](https://infraforgelabs.github.io/DevOpsMind/)

* This leaderboard is automatically updated whenever players complete challenges and submit progress via the DevOpsMind CLI.


---

# 📚 Stacks Covered

* 🐧 Linux
* 💻 Bash
* 🌱 Git
* 🐍 Python
* ⚙️ Ansible
* 🐳 Docker
* ☸️ Kubernetes
* 🛳 Helm
* 🌍 Terraform
* 📈 Networking

---

# 🏗 Project Architecture

```
DevOpsMind/
├── src/devopsmind/              # Core CLI engine
│   ├── cli.py                   # CLI entry
│   ├── engine.py                # Challenge execution engine
│   ├── play.py                  # Run challenges
│   ├── progress.py              # XP, ranks, completion state
│   ├── snapshot.py              # Snapshot-based recovery & portability
│   ├── leaderboard.py           # Optional public leaderboard publishing
│   ├── update_check.py          # Version update detection
│   ├── validator.py             # Challenge validation framework
│   └── achievements/            # Ranks, difficulty, stacks metadata
│
├── src/devopsmind/challenges/   # Challenge packs
│   ├── Linux/
│   ├── Bash/
│   ├── Git/
│   ├── Python/
│   ├── Ansible/
│   ├── Docker/
│   ├── K8s/
│   ├── Helm/
│   ├── Terraform/
│   └── Networking/
│       └── Easy | Medium | Hard | Expert | Master
│
├── devopsmind-relay/            # Optional leaderboard relay (publish-only)
│   └── index.js
│
├── docs/                        # Images & diagrams
│   ├── roadmap.png
│   ├── banner.png
│   └── ArchitectureDiagram.png
│
├── vision/                      # Long-term project docs
│   ├── CHANGELOG.md
│   ├── PHILOSOPHY.md
│   ├── STRATEGY.md
│   └── BUSINESS_MODEL.md
│
├── scripts/
│   └── bootstrap.sh             # Local setup helpers
│
├── README.md
├── LICENSE
└── pyproject.toml
```

---

# 🛣 Roadmap

![Roadmap](docs/roadmap.png)

---

## 📘 Vision & Governance

These documents define the learning philosophy, strategy, and long-term roadmap of **DevOpsMind**, guiding its evolution from CLI simulator to offline Studio suite.

| File | Description |
|------|--------------|
| [`PHILOSOPHY`](vision/PHILOSOPHY.md) | Educational vision, core learning values, and open philosophy |
| [`STRATEGY`](vision/STRATEGY.md) | Development roadmap from CLI → Sandbox → Studio → AI |
| [`BUSINESS_MODEL`](vision/BUSINESS_MODEL.md) | Open education model and community-driven sustainability |
| [`CHANGELOG`](vision/CHANGELOG.md) | Full version roadmap (2026–2032) with release milestones |

---

# 🤝 Contributing

Pull requests welcome! Ensure validators remain deterministic.

---

# 📜 License

MIT License © 2025 **InfraForgeLabs**

---

# 💖 Support & Sponsorship

**DevOpsMind** is proudly built and maintained by **InfraForge Labs** as an open-source gamified DevOps learning platform.  

If you find this project valuable — whether you’re learning, teaching, or building with it — consider supporting its development.  
Your contribution helps keep **DevOpsMind** updated, free, and community-driven.

### ☕ Ways to Support

* 💎 GitHub Sponsors: [https://github.com/sponsors/gauravchile](https://github.com/sponsors/gauravchile)
* ☕ Buy Me a Coffee: [https://buymeacoffee.com/gauravchile](https://buymeacoffee.com/gauravchile)

> Every contribution — a coffee ☕, a star ⭐, or a pull request 🧩 — helps keep **DevOpsMind** alive, growing, and improving for everyone.

---

## ⭐ Support & Credits

Developed & maintained by [Gaurav Chile](https://github.com/gauravchile)

Founder, **InfraForgeLabs**

> 💡 DevOpsMind is fully modular — challenge packs, validators, and installers auto-update via GitHub.
>Ideal for DevOps learners, professionals, teams, and training environments.

[![Built with 💖 by InfraForgeLabs](https://img.shields.io/badge/Built_with_💖-InfraForgeLabs-blue)]()

---
