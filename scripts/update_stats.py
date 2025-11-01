#!/usr/bin/env python3
import os
import json
import requests
from datetime import datetime

# ---------- CONFIG ----------
# History file path
HISTORY_FILE = "data/traffic_history.json"
README_PATH = "README.md"
START_TAG = "<!--PROFILE_STATS_START-->"
END_TAG = "<!--PROFILE_STATS_END-->"
# ----------------------------

def get_env_token():
    # Use the personal token stored in the Actions secret PERSONAL_TOKEN (recommended)
    token = os.getenv("PERSONAL_TOKEN") or os.getenv("API_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Error: No token found. Set PERSONAL_TOKEN secret in repository.")
    return token

def fetch_traffic(owner, repo, token):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {token}"
    }
    url = f"https://api.github.com/repos/{owner}/{repo}/traffic/views"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise SystemExit(f"GitHub API error {r.status_code}: {r.text}")
    return r.json()

def load_history(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # if file corrupted, start fresh (avoid crash)
            return []
    else:
        return []

def save_history(path, history):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def update_readme(path, start_tag, end_tag, block_text):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if start_tag not in content or end_tag not in content:
        raise SystemExit("Placeholder tags not found in README.md. Add <!--PROFILE_STATS_START--> and <!--PROFILE_STATS_END-->.")

    before, rest = content.split(start_tag, 1)
    _, after = rest.split(end_tag, 1)

    new_content = before + start_tag + "\n" + block_text + "\n" + end_tag + after

    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("README.md updated.")
        return True
    else:
        print("No changes to README.md.")
        return False

def main():
    # Get repo info from environment (Actions sets this)
    owner = os.getenv("GITHUB_REPOSITORY_OWNER")
    repo = os.getenv("GITHUB_REPOSITORY", "").split("/", 1)[-1]

    if not owner or not repo:
        raise SystemExit("GITHUB_REPOSITORY_OWNER or GITHUB_REPOSITORY not set. This script is designed to run in GitHub Actions.")

    token = get_env_token()
    data = fetch_traffic(owner, repo, token)

    count = int(data.get("count", 0))
    uniques = int(data.get("uniques", 0))
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # update history
    history = load_history(HISTORY_FILE)

    # Avoid duplicate entry for same date
    if not history or history[-1].get("date") != today:
        history.append({"date": today, "views": count, "uniques": uniques})
        # Optionally keep only last N days to prevent enormous file:
        # history = history[-1000:]
        save_history(HISTORY_FILE, history)
        print(f"Appended history for {today}.")
    else:
        print(f"History already contains an entry for {today} — not appending.")

    # compute all-time totals (simple sum of saved daily values)
    total_views = sum(item.get("views", 0) for item in history)
    total_uniques = sum(item.get("uniques", 0) for item in history)

    # create the block to insert into README
    new_block = f"""
<p align="center">
  <img src="https://img.shields.io/badge/Views%20(14d)-{count}-1e90ff?style=flat-square&logo=github" alt="14-day views"/>
  <img src="https://img.shields.io/badge/Unique%20Visitors%20(14d)-{uniques}-8a2be2?style=flat-square&logo=github"/><br><br>
  <img src="https://img.shields.io/badge/All--Time%20Views-{total_views}-00c853?style=flat-square&logo=google-analytics"/>
  <img src="https://img.shields.io/badge/All--Time%20Visitors-{total_uniques}-2e7d32?style=flat-square&logo=google-analytics"/>
</p>

<p align="center"><sub>Last updated: {timestamp}</sub></p>
"""

    updated = update_readme(README_PATH, START_TAG, END_TAG, new_block)

    # exit code 0 indicates success; workflow will commit if files changed
    return 0

if __name__ == "__main__":
    main()
