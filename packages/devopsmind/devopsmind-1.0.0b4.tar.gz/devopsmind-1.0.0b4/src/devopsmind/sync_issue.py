from pathlib import Path
import yaml, requests
from rich.console import Console

console = Console()

def submit_to_issue():
    """Submit leaderboard progress to GitHub Issues (no token needed)."""
    repo = "InfraForgeLabs/DevOpsMind"
    pending_dir = Path.home() / ".devopsmind" / ".pending_sync"
    files = list(pending_dir.glob("*.yaml"))

    if not files:
        console.print("[yellow]⚠️ No pending leaderboard entries found.[/yellow]")
        return

    for f in files:
        try:
            data = yaml.safe_load(f.read_text())
        except Exception as e:
            console.print(f"[red]❌ Failed to read {f.name}: {e}[/red]")
            continue

        gamer = data.get("gamer", "unknown")
        title = f"Leaderboard submission: {gamer}"

        body = (
            "### 🧠 DevOpsMind Leaderboard Submission\n"
            f"**Gamer:** {gamer}\n"
            f"**XP:** {data.get('xp')}\n"
            f"**Rank:** {data.get('rank')}\n"
            "\n```yaml\n"
            f"{yaml.safe_dump(data)}"
            "```\n"
            "_Auto-submitted via DevOpsMind CLI_\n"
        )

        url = f"https://api.github.com/repos/{repo}/issues"
        payload = {"title": title, "body": body, "labels": ["leaderboard-submission"]}

        console.print(f"🧠 Submitting leaderboard entry for [cyan]{gamer}[/cyan]...")
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code in (200, 201):
                console.print(f"✅ Submitted successfully! View on GitHub → https://github.com/{repo}/issues")
                f.unlink()  # delete after submit
            else:
                console.print(f"[red]❌ Failed (HTTP {resp.status_code})[/red]")
                console.print(resp.text)
        except Exception as e:
            console.print(f"[red]⚠️ Error submitting for {gamer}: {e}[/red]")

