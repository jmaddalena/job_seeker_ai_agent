# ============================================================
# config.py — Edit this file to customize your job search
# ============================================================

# Job search queries sent to each board
SEARCH_QUERIES = [
    "software engineer remote",
    "python developer remote",
]

# Natural-language description of the ideal role.
# Claude uses this to decide whether a listing is relevant.
FILTER_CRITERIA = """
I am a senior software engineer with 8+ years of experience in Python and
distributed systems. I am looking for:
- Remote-first or fully-remote positions
- Backend / platform / infrastructure roles
- Competitive compensation (ideally $150k+ USD)
- Small-to-mid size companies or fast-growing start-ups
- Companies that use modern tooling (Python, Go, Kubernetes, AWS/GCP)

I am NOT interested in:
- Front-end or mobile-only roles
- Defense / military contractors
- Crypto / Web3 projects
- Roles that require relocation or are on-site only
"""

# Context used by the ethics / culture check agent.
# List the kinds of companies or behaviours you want flagged.
ETHICS_CONTEXT = """
Please flag this company if any of the following apply:
- Involved in weapons manufacturing or military contracting
- Known for unethical data practices or major privacy violations
- Associated with predatory financial products
- Has significant recent news about layoffs, toxic culture, or labour violations
- Active involvement in fossil-fuel extraction
"""

# ── Email settings ──────────────────────────────────────────
# Use a Gmail App Password, NOT your real Google password.
# See: https://myaccount.google.com/apppasswords
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password_here"
EMAIL_FROM = "your_email@gmail.com"
EMAIL_TO = "your_email@gmail.com"
EMAIL_SUBJECT = "🤖 Daily Job Digest"
