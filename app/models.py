from pydantic import BaseModel
from typing import Optional


class GitHubIssue(BaseModel):
    number: int
    title: str
    body: Optional[str] = ""
    html_url: str
    labels: list[dict]


class GitHubWebhookPayload(BaseModel):
    action: str
    issue: GitHubIssue


class SessionRecord(BaseModel):
    issue_number: int
    issue_title: str
    issue_url: str
    session_id: str
    session_url: str
    status: str
    pull_requests: str = ""
    acus_consumed: float = 0.0
    created_at: int = 0
    updated_at: int = 0
