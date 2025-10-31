import requests
import sys
import random
from datetime import datetime, date, timedelta
from rich.console import Console
from dotenv import load_dotenv
import os

# === LOAD TOKEN FROM .env ===
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# === CHECK IF TOKEN EXISTS ===
if not GITHUB_TOKEN:
    console = Console()
    console.print("[bold red]ERROR: GITHUB_TOKEN not found in .env file![/bold red]")
    console.print("[yellow]Create a .env file in this folder with:[/yellow]")
    console.print("[yellow]GITHUB_TOKEN=your_token_here[/yellow]")
    sys.exit(1)

console = Console()

# === QUOTES (fallback) ===
QUOTES = [
    "Streak = your superpower.",
    "Keep the fire alive!",
    "Consistency > intensity.",
    "One commit a day keeps the 0 away.",
    "You're on fire!"
]

def get_contributions(username):
    query = """
    query($user: String!) {
      user(login: $user) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    variables = {"user": username}
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=headers
    )
    if response.status_code != 200:
        console.print(f"[red]API Error: {response.json().get('message', 'Failed')}[/red]")
        return None
    data = response.json().get("data", {}).get("user")
    if not data:
        console.print(f"[red]User '{username}' not found[/red]")
        return None
    weeks = data["contributionsCollection"]["contributionCalendar"]["weeks"]
    contributions = []
    for week in weeks:
        for day in week["contributionDays"]:
            contributions.append({
                "date": datetime.strptime(day["date"], "%Y-%m-%d").date(),
                "count": day["contributionCount"]
            })
    return contributions[-365:]

def calculate_streak(contributions):
    if not contributions:
        return 0, 0
    today = date.today()
    streak = 0
    week_commits = 0
    week_start = today - timedelta(days=today.weekday())
    current = today
    i = len(contributions) - 1
    while i >= 0:
        day = contributions[i]
        if day["date"] > today:
            i -= 1
            continue
        if day["date"] == current:
            if day["count"] > 0:
                streak += 1
                if week_start <= day["date"] <= today:
                    week_commits += day["count"]
            else:
                break
            current -= timedelta(days=1)
        elif day["date"] < current:
            if (current - day["date"]).days > 1:
                break
        i -= 1
    return streak, week_commits

def get_quote():
    try:
        with open("quotes.txt", "r", encoding="utf-8") as f:
            quotes = [q.strip() for q in f.readlines() if q.strip()]
        return random.choice(quotes) if quotes else "Keep coding!"
    except:
        return random.choice(QUOTES)

def main():
    if len(sys.argv) != 2:
        console.print("[bold red]Usage: python streak.py <username>[/bold red]")
        sys.exit(1)
    
    username = sys.argv[1].strip()
    console.print(f"Fetching [bold cyan]{username}[/bold cyan]'s GitHub streak...\n")

    data = get_contributions(username)
    if not data:
        sys.exit(1)

    streak, week_commits = calculate_streak(data)
    quote = get_quote()

    # === DISPLAY ===
    name = username.upper()
    console.print(f"[bold yellow]{name}'S CONTRIBUTION STREAK[/bold yellow]\n")

    if streak == 0:
        status = "[bold red]SPARK[/bold red]"
        msg = "0-day streak! Keep pushing!"
    elif streak < 7:
        status = "[bold yellow]SPARK[/bold yellow]"
        msg = f"{streak}-day streak! Keep pushing!"
    else:
        status = "[bold green]FIRE[/bold green]"
        msg = f"{streak}-day streak! You're on fire!"

    console.print(f"{status} [bold]{msg}[/bold]\n")

    # === PROGRESS BAR (FIXED) ===
    bar_width = 20
    filled = min(week_commits, 10)
    bar = "█" * int((filled / 10) * bar_width) + "░" * (bar_width - int((filled / 10) * bar_width))
    console.print(f"[bold cyan]Week:[/] [bold]{bar}[/] [bold green]{week_commits}/10[/] commits this week")

    console.print(f"\n[bold green]\"{quote}\"[/bold green]\n")

if __name__ == "__main__":
    main()