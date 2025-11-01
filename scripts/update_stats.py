#!/usr/bin/env python3
import os
import requests
from datetime import datetime

# Get repo info automatically
OWNER = os.getenv("GITHUB_REPOSITORY_OWNER")
REPO = os.getenv("GITHUB_REPOSITORY", "").split("/", 1)[-1]
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise SystemExit("GITHUB_TOKEN is missing")

# Ask GitHub for traffic data
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
url = f"https://api.github.com/repos/{OWNER}/{REPO}/traffic/views"
response = requests.get(url, headers=headers)

if response.status_code != 200:
    raise SystemExit(f"Error {response.status_code}: {response.text}")

data = response.json()
count = data.get("count", 0)
uniques = data.get("uniques", 0)
timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

# Read README.md
with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()

start = "<!--PROFILE_STATS_START-->"
end = "<!--PROFILE_STATS_END-->"

if start not in content or end not in content:
    raise SystemExit("Missing placeholder tags in README.md")

new_block = (
    f"**Total views (last 14 days):** {count}  \n"
    f"**Unique visitors (last 14 days):** {uniques}  \n"
    f"*(last updated: {timestamp})*"
)

before, middle = content.split(start)
middle, after = middle.split(end)
updated = before + start + "\n" + new_block + "\n" + end + after

# Save new content if changed
if updated != content:
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated)
    print("README updated.")
else:
    print("No update needed.")
