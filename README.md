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

The agent is designed to run in the cloud via **GitHub Actions** so it fires reliably every day regardless of whether your local machine is on.

### GitHub Actions (recommended)

The workflow file `.github/workflows/daily_digest.yml` is already included in this repository. It runs automatically at **8 AM Mountain Time** every day.

#### Required repository secrets

Go to **Settings → Secrets and variables → Actions** in your GitHub repository and add the following secrets:

| Secret | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (`sk-ant-...`) |
| `SMTP_USER` | Gmail address used to send the digest (`you@gmail.com`) |
| `SMTP_PASSWORD` | [Gmail App Password](https://myaccount.google.com/apppasswords) (**not** your real password) |

> **Tip:** Use the **Actions → Daily Job Digest → Run workflow** button to trigger a manual run and verify everything works before the first scheduled execution.

#### Timezone note

GitHub Actions schedules run in UTC. The workflow uses `cron: "0 15 * * *"` (UTC 15:00 = 8 AM MST, UTC-7). If you are in a different timezone or want a different time, update the `cron` expression in `.github/workflows/daily_digest.yml` accordingly.

### Alternative: Local cron (macOS/Linux)

If you prefer to run the agent on your own always-on machine, add this line to your crontab (`crontab -e`):

```cron
0 8 * * * cd /path/to/job_seeker_ai_agent && /path/to/.venv/bin/python main.py >> ~/job-agent.log 2>&1
```

Make sure the required environment variables (`ANTHROPIC_API_KEY`, `SMTP_USER`, `SMTP_PASSWORD`) are available in the cron environment.
