# job_seeker_ai_agent

An AI-powered job search agent that scrapes Indeed and LinkedIn daily, uses Claude to filter listings against your criteria, checks companies for ethical concerns, and emails you a formatted digest.

---

## How It Works

```
┌──────────────┐    ┌──────────────┐
│  Indeed      │    │  LinkedIn    │   1. Scrape job boards
│  Scraper     │    │  Scraper     │      (Playwright headless Chromium)
└──────┬───────┘    └──────┬───────┘
       └────────┬──────────┘
                ▼
       ┌─────────────────┐
       │  LLM Filter     │            2. Claude (Haiku) checks each listing
       │  (Claude)       │               against your FILTER_CRITERIA in config.py
       └────────┬────────┘
                ▼
       ┌─────────────────┐
       │  Ethics Check   │            3. Claude flags any company with ethical concerns
       │  (Claude)       │               based on ETHICS_CONTEXT in config.py
       └────────┬────────┘
                ▼
       ┌─────────────────┐
       │  Email Digest   │            4. HTML + plain-text email sent via Gmail SMTP
       └─────────────────┘
```

Each morning you receive an email listing only the jobs that passed both the relevance filter and the ethics check, with any flagged companies highlighted.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11+ | Uses the `list[dict]` type-hint syntax |
| Anthropic API key | Used for both the relevance filter and ethics check |
| Gmail account | Needs an [App Password](https://myaccount.google.com/apppasswords), **not** your real password |

---

## Setup

### 1. Clone & install dependencies

```bash
git clone https://github.com/jmaddalena/job_seeker_ai_agent.git
cd job_seeker_ai_agent
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium      # needed for the LinkedIn scraper
```

### 2. Set environment variables

Create a `.env` file in the project root (it is already in `.gitignore`):

```
ANTHROPIC_API_KEY=sk-ant-...
SMTP_USER=you@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # Gmail App Password
```

Or export them in your shell:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export SMTP_USER="you@gmail.com"
export SMTP_PASSWORD="xxxx xxxx xxxx xxxx"
```

> **Note:** `python-dotenv` is listed in `requirements.txt` but is not auto-loaded.  
> If you prefer automatic loading, add `from dotenv import load_dotenv; load_dotenv()` at the top of `main.py`.

### 3. Customize your search

Edit `config.py` to match your situation:

- **`SEARCH_QUERIES`** – keywords sent to each job board.
- **`FILTER_CRITERIA`** – natural-language description of your ideal role (location, seniority, salary, industries, etc.).
- **`ETHICS_CONTEXT`** – what kinds of companies or behaviors Claude should flag.
- **`EMAIL_SUBJECT`** – subject line of the daily digest email.

---

## Running Manually

```bash
python main.py
```

Logs stream to stdout. On a successful run you will see lines like:

```
2024-05-01 08:00:00 [INFO] __main__: === Job Seeker AI Agent starting ===
2024-05-01 08:00:03 [INFO] scrapers.indeed: Indeed: collected 47 listings.
2024-05-01 08:00:05 [INFO] scrapers.linkedin: LinkedIn: collected 22 listings.
2024-05-01 08:00:12 [INFO] agents.filter: Filter: 9/69 listings passed.
2024-05-01 08:00:15 [INFO] __main__: Sending digest email to you@gmail.com…
2024-05-01 08:00:16 [INFO] __main__: === Done ===
```

---

## Testing

### Unit tests (no API key required)

The test suite uses `unittest.mock` to stub out all external calls (Anthropic API, SMTP, HTTP requests), so you can run tests locally without any credentials:

```bash
pip install pytest
pytest -v
```

### Smoke-testing a single component

You can exercise individual modules from a Python shell:

```python
# Test the filter with a fake listing (requires ANTHROPIC_API_KEY)
from agents import filter as job_filter
result = job_filter.filter_listings([{
    "title": "Senior Data Scientist",
    "company": "Acme Climate",
    "location": "Remote",
    "description": "Research role, fully remote, $160k.",
    "url": "https://example.com/job/1",
    "source": "Test",
}])
print(result)
```

### End-to-end dry run (no email)

Comment out the `send.send_digest(checked)` call in `main.py` temporarily and run:

```bash
python main.py
```

This exercises scraping and both Claude agents without sending an email.

---

## Scheduling

### Does cron require AWS or another cloud service?

**No — but it does require a machine that is running at the scheduled time.**

`cron` is a standard Unix/Linux/macOS scheduler. The right compute choice depends on your setup:

| Option | Best for | Cost |
|---|---|---|
| **Local machine cron** | Always-on desktops/servers | Free |
| **Cloud VM** (AWS EC2, GCP Compute Engine, DigitalOcean Droplet, etc.) | Reliable daily runs | ~$4–$10/month (smallest instance) |
| **GitHub Actions scheduled workflow** | Zero infrastructure | Free for public repos; ~2,000 min/month free for private repos |
| **AWS Lambda + EventBridge Scheduler** | Serverless, pay-per-use | Near-zero cost for once-daily runs |
| **Raspberry Pi / home server** | Self-hosted, always-on | One-time hardware cost |

### Option A: Local cron (macOS/Linux)

Add this line to your crontab (`crontab -e`) to run at 8 AM every day:

```cron
0 8 * * * cd /path/to/job_seeker_ai_agent && /path/to/.venv/bin/python main.py >> ~/job-agent.log 2>&1
```

### Option B: GitHub Actions (recommended — no server needed)

Create `.github/workflows/daily_digest.yml`:

```yaml
name: Daily Job Digest

on:
  schedule:
    - cron: "0 15 * * *"   # 8 AM US/Mountain Standard Time (UTC-7); use 0 14 * * * during MDT (UTC-6)
  workflow_dispatch:         # allows manual triggering from the Actions tab

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt && playwright install --with-deps chromium
      - run: python main.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
```

Store `ANTHROPIC_API_KEY`, `SMTP_USER`, and `SMTP_PASSWORD` as [repository secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets).

> **Tip:** Use `workflow_dispatch` to test your workflow on demand before relying on the schedule.

### Option C: AWS Lambda + EventBridge

For a fully serverless setup, package the project as a Lambda function (using a container image to include Playwright) and trigger it with an EventBridge Scheduler rule. This is cost-effective for infrequent runs but requires more setup than GitHub Actions.