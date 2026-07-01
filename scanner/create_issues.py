import httpx
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPO")
BASE_URL = f"https://api.github.com/repos/{REPO}"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

ISSUES = [
    {
        "title": "[Security] Upgrade Pillow to patch CVE-2024-28219",
        "body": (
            "The current pinned version of Pillow in requirements files is vulnerable "
            "to CVE-2024-28219 (buffer overflow in image processing).\n\n"
            "**Acceptance Criteria:**\n"
            "- Upgrade Pillow to >= 10.3.0 in all relevant requirements files\n"
            "- Confirm no breaking changes in existing image-related imports"
        ),
        "labels": ["devin-fix"],
    },
    {
        "title": "[Tech Debt] Replace deprecated datetime.utcnow() calls",
        "body": (
            "Python 3.12 deprecated `datetime.utcnow()`. Superset has several "
            "occurrences across the codebase.\n\n"
            "**Acceptance Criteria:**\n"
            "- Replace all `datetime.utcnow()` with `datetime.now(timezone.utc)`\n"
            "- Ensure imports are updated accordingly"
        ),
        "labels": ["devin-fix"],
    },
    {
        "title": "[Code Quality] Add type hints to superset/utils/core.py",
        "body": (
            "Several functions in `superset/utils/core.py` lack type annotations, "
            "reducing IDE support and making the codebase harder to maintain.\n\n"
            "**Acceptance Criteria:**\n"
            "- Add type hints to the top 5 functions in the file\n"
            "- Ensure mypy passes on the modified functions"
        ),
        "labels": ["devin-fix"],
    },
]


def create_label():
    response = httpx.post(
        f"{BASE_URL}/labels",
        headers=HEADERS,
        json={"name": "devin-fix", "color": "e11d48"},
    )
    if response.status_code == 201:
        print("✅ Label 'devin-fix' created")
    elif response.status_code == 422:
        print("ℹ️  Label 'devin-fix' already exists")
    else:
        print(f"⚠️  Label creation returned {response.status_code}: {response.text}")


def create_issues():
    for issue in ISSUES:
        response = httpx.post(f"{BASE_URL}/issues", headers=HEADERS, json=issue)
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Created: #{data['number']} — {data['title']}")
            print(f"   URL: {data['html_url']}")
        else:
            print(f"❌ Failed: {issue['title']}")
            print(f"   {response.status_code}: {response.text}")


if __name__ == "__main__":
    create_label()
    create_issues()
