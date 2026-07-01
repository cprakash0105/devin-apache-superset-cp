# Autonomous Issue Remediation using Devin

## Executive Summary

Engineering teams accumulate technical debt in the form of dependency upgrades, vulnerability fixes, and code quality issues. While these tasks are important, they often compete with feature delivery and remain unresolved for long periods.

This project demonstrates an event-driven automation that uses Devin as an autonomous software engineer. When an issue is created in a GitHub repository, the system automatically launches a Devin session, tracks remediation progress, and provides engineering leadership with visibility into outcomes through an observability dashboard.

The solution was built against a fork of Apache Superset and demonstrates how engineering organizations can operationalize Devin to reduce repetitive maintenance work.

---

## Problem Statement

Engineering teams frequently encounter:

- Dependency upgrades
- Security vulnerability remediation
- Code quality improvements
- Backlog maintenance tasks

These tasks are repetitive, important, and often deprioritized in favor of feature work.

The objective of this solution is to transform these engineering tasks into autonomous workflows executed by Devin.

---

## Why Devin?

Traditional automation tools can identify problems but cannot independently:

- Understand repository context
- Modify source code
- Adapt to test failures
- Produce pull requests

Devin acts as an autonomous engineering agent capable of reasoning about the repository, implementing fixes, validating changes, and contributing back via pull requests.

This solution positions Devin as the primary execution engine rather than a simple helper tool.

---

## Architecture

```
GitHub Issue Created (labeled "devin-fix")
         │
         ▼
  GitHub Webhook
         │
         ▼
  FastAPI Orchestrator  (Docker — Azure VM)
         │
         ▼
      Devin API
         │
         ▼
     Devin Session
         │  • Clones repo
         │  • Implements fix
         │  • Opens Pull Request
         ▼
  Observability Dashboard
  http://<your-vm-ip>/dashboard
```

---

## End-to-End Workflow

1. Engineer creates an issue in the Apache Superset fork
2. Issue is tagged with `devin-fix`
3. GitHub sends a webhook event to the FastAPI server
4. FastAPI receives the event and validates the signature
5. A Devin session is created automatically with a structured prompt
6. Devin analyzes the repository
7. Devin implements the remediation
8. Devin creates a pull request
9. The dashboard tracks task progress, completion, and business metrics

---

## Repository Structure

```
app/
├── main.py              # FastAPI webhook server + dashboard
├── devin_client.py      # Devin API wrapper
└── models.py            # Pydantic models

scanner/
├── create_issues.py     # Seed issues into the target repo
├── reset_issues.py      # Close test issues, recreate real ones
└── close_duplicates.py  # Cleanup utility

observability/
└── sessions.db          # SQLite — session tracking

Dockerfile
docker-compose.yml
.env.example
README.md
```

---

## Setup

### 1. Configure environment

```bash
cp .env.example .env
```

Fill in:

```
DEVIN_API_KEY=your_devin_api_key
DEVIN_ORG_ID=your_devin_org_id
GITHUB_TOKEN=your_github_pat
GITHUB_REPO=your-username/apache-superset-fork-cp
GITHUB_WEBHOOK_SECRET=your_webhook_secret
```

### 2. Start the server

```bash
docker-compose up --build
```

### 3. Create issues in the target repo (one-time)

```bash
pip install -r requirements.txt
python scanner/create_issues.py
```

### 4. Configure GitHub webhook

In your fork → Settings → Webhooks → Add webhook:
- Payload URL: `http://<your-server-ip>/webhook`
- Content type: `application/json`
- Secret: your `GITHUB_WEBHOOK_SECRET`
- Events: Issues only

### 5. View dashboard

```
http://<your-server-ip>/dashboard
```

---

## Observability

The dashboard answers the key question an engineering leader asks:

> "Is this actually working, and is it saving us time?"

Metrics provided:

| Metric | Description |
|--------|-------------|
| Tasks Submitted | Total issues dispatched to Devin |
| Tasks Completed | Sessions that finished with a PR |
| Tasks Failed | Sessions that errored |
| Success Rate | Completed / Submitted |
| PRs Created | Pull requests opened by Devin |
| Eng. Hours Saved | PRs × 2hrs estimated fix time |
| ACUs Consumed | Devin compute cost |

---

## Business Impact

This solution enables:

- Faster remediation of engineering backlog
- Continuous repository health improvement
- Reduced manual engineering effort
- Better visibility into autonomous work
- Increased adoption of Devin within engineering workflows

---

## Future Enhancements

- JIRA integration as an alternative trigger
- Dependabot / security scanner integration (fully automated issue creation)
- Slack notifications on PR creation
- PR review automation
- Multi-repository support
- Custom domain + HTTPS for dashboard
- Engineering productivity analytics and trend reporting

---

## Assignment Requirement Mapping

| Requirement | Implementation |
|-------------|----------------|
| Event Trigger | GitHub Issue Webhook |
| Devin Integration | Devin Session API v3 |
| Autonomous Execution | Issue → Devin → Pull Request |
| Observability | Live dashboard + session metrics |
| Containerization | Docker Compose |
| End-to-End Demo | Apache Superset fork |

---

## Presentation Narrative

### What
Engineering teams accumulate repetitive maintenance work — dependency upgrades, technical debt, vulnerability fixes. These tasks are important but consistently delayed because engineers prioritize feature development.

### How
This solution uses GitHub events to automatically trigger Devin sessions. Devin evaluates the issue, performs the remediation, and produces observable engineering outputs — pull requests and status updates — tracked in a live dashboard.

### Why
Traditional automation can detect problems but cannot independently understand codebases and implement fixes. Devin acts as an autonomous engineering agent capable of taking full ownership of engineering maintenance tasks end to end.

### When
The solution can be extended to support security scanning platforms, JIRA integration, Slack notifications, multi-repository orchestration, and engineering productivity reporting.
