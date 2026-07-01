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
