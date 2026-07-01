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

response = httpx.post(
    f"https://api.github.com/repos/{REPO}/issues",
    headers=HEADERS,
    json={
        "title": "[Test] Webhook trigger test",
        "body": "This is a test issue to verify the webhook → Devin pipeline is working end to end.",
        "labels": ["devin-fix"],
    },
)

print(response.status_code)
print(response.json().get("html_url"))
