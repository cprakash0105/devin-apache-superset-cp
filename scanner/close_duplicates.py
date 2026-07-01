import httpx
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPO")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}
BASE_URL = f"https://api.github.com/repos/{REPO}"

# Close issues #9, #10, #11 — keep #12, #13, #14 (latest set)
ISSUES_TO_CLOSE = [9, 10, 11]

for number in ISSUES_TO_CLOSE:
    r = httpx.patch(f"{BASE_URL}/issues/{number}", headers=HEADERS, json={"state": "closed"})
    if r.status_code == 200:
        print(f"🔒 Closed #{number}")
    else:
        print(f"❌ Failed to close #{number}: {r.status_code}")
