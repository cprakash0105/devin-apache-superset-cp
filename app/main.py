import hashlib
import hmac
import json
import os
import sqlite3

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.devin_client import create_session, get_session
from app.models import GitHubWebhookPayload, SessionRecord

load_dotenv()

app = FastAPI()
DB_PATH = "observability/sessions.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                issue_number INTEGER,
                issue_title TEXT,
                issue_url TEXT,
                session_id TEXT PRIMARY KEY,
                session_url TEXT,
                status TEXT
            )
        """)


def save_session(record: SessionRecord):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?,?,?,?,?,?)",
            (record.issue_number, record.issue_title, record.issue_url,
             record.session_id, record.session_url, record.status),
        )


def verify_signature(payload: bytes, signature: str) -> bool:
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(expected, signature)


@app.on_event("startup")
def startup():
    init_db()


@app.post("/webhook")
async def webhook(request: Request, x_hub_signature_256: str = Header(None)):
    payload_bytes = await request.body()

    if x_hub_signature_256 and not verify_signature(payload_bytes, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = json.loads(payload_bytes)

    # Only process newly opened issues
    if data.get("action") != "opened":
        return {"status": "ignored"}

    payload = GitHubWebhookPayload(**data)
    labels = [l["name"] for l in payload.issue.labels]

    if "devin-fix" not in labels:
        return {"status": "ignored", "reason": "no devin-fix label"}

    prompt = (
        f"You are working on the GitHub repository: https://github.com/{os.getenv('GITHUB_REPO')}.\n"
        f"Please fix the following issue and open a pull request:\n\n"
        f"Issue #{payload.issue.number}: {payload.issue.title}\n\n"
        f"{payload.issue.body}"
    )

    session = create_session(prompt)

    record = SessionRecord(
        issue_number=payload.issue.number,
        issue_title=payload.issue.title,
        issue_url=payload.issue.html_url,
        session_id=session["session_id"],
        session_url=session["url"],
        status=session["status"],
    )
    save_session(record)

    print(f"✅ Devin session started for issue #{payload.issue.number}: {session['url']}")
    return {"session_id": session["session_id"], "session_url": session["url"]}


@app.get("/status/{session_id}")
def status(session_id: str):
    session = get_session(session_id)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE sessions SET status=? WHERE session_id=?",
            (session["status"], session_id),
        )
    return {"session_id": session_id, "status": session["status"], "pull_requests": session.get("pull_requests", [])}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT * FROM sessions").fetchall()

    rows_html = ""
    for row in rows:
        issue_number, issue_title, issue_url, session_id, session_url, status = row
        color = {"running": "#f59e0b", "finished": "#10b981", "failed": "#ef4444"}.get(status, "#6b7280")
        rows_html += f"""
        <tr>
            <td><a href="{issue_url}" target="_blank">#{issue_number}</a></td>
            <td>{issue_title}</td>
            <td><span style="color:{color};font-weight:bold">{status}</span></td>
            <td><a href="{session_url}" target="_blank">View Session</a></td>
            <td><a href="/status/{session_id}">Refresh</a></td>
        </tr>"""

    return f"""
    <html>
    <head>
        <title>Devin Automation Dashboard</title>
        <style>
            body {{ font-family: sans-serif; padding: 2rem; background: #f9fafb; }}
            h1 {{ color: #111827; }}
            table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            th {{ background: #1f2937; color: white; padding: 12px 16px; text-align: left; }}
            td {{ padding: 12px 16px; border-bottom: 1px solid #e5e7eb; }}
            a {{ color: #3b82f6; text-decoration: none; }}
        </style>
    </head>
    <body>
        <h1>🤖 Devin Automation Dashboard</h1>
        <p>Tracking Devin sessions dispatched from GitHub issues in
           <a href="https://github.com/{os.getenv('GITHUB_REPO')}" target="_blank">{os.getenv('GITHUB_REPO')}</a>
        </p>
        <table>
            <tr>
                <th>Issue</th><th>Title</th><th>Status</th><th>Devin Session</th><th>Refresh</th>
            </tr>
            {rows_html if rows_html else '<tr><td colspan="5" style="text-align:center;color:#6b7280">No sessions yet</td></tr>'}
        </table>
    </body>
    </html>
    """
