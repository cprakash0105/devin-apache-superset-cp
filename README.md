# Devin Apache Superset Automation

Event-driven automation that uses the Devin API to autonomously remediate GitHub issues in [apache-superset-fork-cp](https://github.com/cprakash0105/apache-superset-fork-cp).

## How It Works

```
Issue created with label "devin-fix"
        ↓
GitHub webhook → FastAPI server
        ↓
Devin session dispatched with issue context
        ↓
Devin fixes the code and opens a PR
        ↓
Observability dashboard tracks session status
```

## Setup

```bash
cp .env.example .env
# Fill in your values in .env
```

## Run

```bash
docker-compose up --build
```

## Create Issues (one-time setup)

```bash
pip install -r requirements.txt
python scanner/create_issues.py
```

## Observability

Visit `http://localhost:8000/dashboard` to see session status.
