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


def close_test_issues():
    response = httpx.get(f"{BASE_URL}/issues?state=open&per_page=20", headers=HEADERS)
    for issue in response.json():
        if "[Test]" in issue["title"]:
            httpx.patch(f"{BASE_URL}/issues/{issue['number']}", headers=HEADERS, json={"state": "closed"})
            print(f"🔒 Closed #{issue['number']}: {issue['title']}")


def create_real_issues():
    issues = [
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
    for issue in issues:
        r = httpx.post(f"{BASE_URL}/issues", headers=HEADERS, json=issue)
        if r.status_code == 201:
            data = r.json()
            print(f"✅ Created #{data['number']}: {data['title']}")
            print(f"   {data['html_url']}")
        else:
            print(f"❌ Failed: {issue['title']} — {r.status_code}: {r.text}")


if __name__ == "__main__":
    close_test_issues()
    create_real_issues()
