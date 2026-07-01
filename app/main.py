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
                status TEXT,
                pull_requests TEXT DEFAULT '',
                acus_consumed REAL DEFAULT 0.0,
                created_at INTEGER DEFAULT 0
            )
        """)
        # migrate existing DB if columns missing
        for col, definition in [("pull_requests", "TEXT DEFAULT ''"), ("acus_consumed", "REAL DEFAULT 0.0"), ("created_at", "INTEGER DEFAULT 0")]:
            try:
                conn.execute(f"ALTER TABLE sessions ADD COLUMN {col} {definition}")
            except Exception:
                pass


def save_session(record: SessionRecord):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?,?,?,?,?,?,?,?,?)",
            (record.issue_number, record.issue_title, record.issue_url,
             record.session_id, record.session_url, record.status,
             record.pull_requests, record.acus_consumed, record.created_at),
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

    print(f"📥 Webhook received: action={data.get('action')}, keys={list(data.keys())}")

    # Only process newly opened issues
    if data.get("action") != "opened":
        return {"status": "ignored"}

    payload = GitHubWebhookPayload(**data)
    labels = [l["name"] for l in payload.issue.labels]

    if "devin-fix" not in labels:
        print(f"⏭️  Skipping issue #{payload.issue.number} — no devin-fix label, labels={labels}")
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
        pull_requests="",
        acus_consumed=0.0,
        created_at=session.get("created_at", 0),
    )
    save_session(record)

    print(f"✅ Devin session started for issue #{payload.issue.number}: {session['url']}")
    return {"session_id": session["session_id"], "session_url": session["url"]}


@app.get("/status/{session_id}")
def status(session_id: str):
    session = get_session(session_id)
    prs = ", ".join(pr.get("url", "") for pr in session.get("pull_requests", []))
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE sessions SET status=?, pull_requests=?, acus_consumed=? WHERE session_id=?",
            (session["status"], prs, session.get("acus_consumed", 0.0), session_id),
        )
    return {"session_id": session_id, "status": session["status"], "pull_requests": session.get("pull_requests", [])}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    import datetime
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT * FROM sessions ORDER BY created_at DESC").fetchall()

    total = len(rows)
    finished = sum(1 for r in rows if r[5] == "finished")
    running = sum(1 for r in rows if r[5] == "running")
    failed = sum(1 for r in rows if r[5] == "failed")
    total_acus = sum(r[7] or 0 for r in rows)

    stats_html = f"""
    <div style="display:flex;gap:1rem;margin-bottom:1.5rem">
        <div class="stat"><div class="stat-val">{total}</div><div class="stat-label">Total Sessions</div></div>
        <div class="stat" style="border-color:#10b981"><div class="stat-val" style="color:#10b981">{finished}</div><div class="stat-label">Finished</div></div>
        <div class="stat" style="border-color:#f59e0b"><div class="stat-val" style="color:#f59e0b">{running}</div><div class="stat-label">Running</div></div>
        <div class="stat" style="border-color:#ef4444"><div class="stat-val" style="color:#ef4444">{failed}</div><div class="stat-label">Failed</div></div>
        <div class="stat" style="border-color:#6366f1"><div class="stat-val" style="color:#6366f1">{total_acus:.2f}</div><div class="stat-label">ACUs Consumed</div></div>
    </div>"""

    rows_html = ""
    for row in rows:
        issue_number, issue_title, issue_url, session_id, session_url, status, pull_requests, acus, created_at = row
        color = {"running": "#f59e0b", "finished": "#10b981", "failed": "#ef4444"}.get(status, "#6b7280")
        created = datetime.datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M") if created_at else "—"
        pr_links = ""
        if pull_requests:
            for pr_url in pull_requests.split(", "):
                if pr_url:
                    pr_num = pr_url.rstrip("/").split("/")[-1]
                    pr_links += f'<a href="{pr_url}" target="_blank">PR #{pr_num}</a> '
        pr_links = pr_links or "<span style='color:#9ca3af'>pending</span>"
        rows_html += f"""
        <tr>
            <td><a href="{issue_url}" target="_blank">#{issue_number}</a></td>
            <td>{issue_title}</td>
            <td><span style="color:{color};font-weight:bold">{status}</span></td>
            <td>{pr_links}</td>
            <td>{acus or 0:.2f}</td>
            <td>{created}</td>
            <td><a href="{session_url}" target="_blank">View</a> &nbsp; <a href="/status/{session_id}">↻ Refresh</a></td>
        </tr>"""

    return f"""
    <html>
    <head>
        <title>Devin Automation Dashboard</title>
        <style>
            body {{ font-family: sans-serif; padding: 2rem; background: #f9fafb; }}
            h1 {{ color: #111827; margin-bottom: 0.25rem; }}
            .subtitle {{ color: #6b7280; margin-bottom: 1.5rem; }}
            .stat {{ background: white; border-left: 4px solid #1f2937; border-radius: 8px; padding: 1rem 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); min-width: 120px; }}
            .stat-val {{ font-size: 2rem; font-weight: bold; color: #111827; }}
            .stat-label {{ font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }}
            table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            th {{ background: #1f2937; color: white; padding: 12px 16px; text-align: left; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }}
            td {{ padding: 12px 16px; border-bottom: 1px solid #e5e7eb; font-size: 0.9rem; }}
            tr:last-child td {{ border-bottom: none; }}
            a {{ color: #3b82f6; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>🤖 Devin Automation Dashboard</h1>
        <p class="subtitle">Repo: <a href="https://github.com/{os.getenv('GITHUB_REPO')}" target="_blank">{os.getenv('GITHUB_REPO')}</a></p>
        {stats_html}
        <table>
            <tr>
                <th>Issue</th><th>Title</th><th>Status</th><th>Pull Request</th><th>ACUs</th><th>Started</th><th>Actions</th>
            </tr>
            {rows_html if rows_html else '<tr><td colspan="7" style="text-align:center;color:#6b7280;padding:2rem">No sessions yet</td></tr>'}
        </table>
    </body>
    </html>
    """
