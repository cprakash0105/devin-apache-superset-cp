import httpx
import os


DEVIN_BASE_URL = "https://api.devin.ai/v3/organizations"


def _headers():
    return {"Authorization": f"Bearer {os.getenv('DEVIN_API_KEY')}"}


def create_session(prompt: str) -> dict:
    org_id = os.getenv("DEVIN_ORG_ID")
    response = httpx.post(
        f"{DEVIN_BASE_URL}/{org_id}/sessions",
        headers=_headers(),
        json={"prompt": prompt},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_session(session_id: str) -> dict:
    org_id = os.getenv("DEVIN_ORG_ID")
    response = httpx.get(
        f"{DEVIN_BASE_URL}/{org_id}/sessions/{session_id}",
        headers=_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
