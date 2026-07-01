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
        "title": "[Code Quality] Add missing __all__ to superset/utils/__init__.py",
        "body": (
            "The file `superset/utils/__init__.py` does not define an `__all__` list.\n\n"
            "**Exact change required:**\n"
            "- Open the file `superset/utils/__init__.py`\n"
            "- Add the following line at the top of the file:\n"
            "```python\n"
            "__all__ = []\n"
            "```\n\n"
            "**Acceptance Criteria:**\n"
            "- The file `superset/utils/__init__.py` contains `__all__ = []` at the top\n"
            "- Open a pull request with this single change\n"
            "- Do not modify any other files\n"
            "- Do not ask for confirmation — make the change and open the PR immediately"
        ),
        "labels": ["devin-fix"],
    },
)

if response.status_code == 201:
    data = response.json()
    print(f"✅ Created #{data['number']}: {data['title']}")
    print(f"   {data['html_url']}")
else:
    print(f"❌ {response.status_code}: {response.text}")
