# ============================================================
# config.py — Edit this file to customize your job search
# ============================================================

# Job search queries sent to each board
import os


SEARCH_QUERIES = [
    "data scientist",
    "data researcher",
    "reinforcement learning",
    "machine learning",
    "artificial intelligence",
]

# Natural-language description of the ideal role.
# Claude uses this to decide whether a listing is relevant.
FILTER_CRITERIA = """
I am a senior data scientist and statistician with 10 years of experience. 
I am looking for:
- Remote-first or fully-remote positions, or located in Fort Collins or Boulder, Colorado
- Roles that involve research, experimentation, and/or building novel data products
- Competitive compensation (ideally $150k+ USD)
- Small-to-mid size companies or fast-growing start-ups
- A mission-driven organization with a positive impact on society, ideally in the climate, energy, or scientific research space

I am open to transitioning to an artificial intelligence role, but am limited in my skills around AI agents. 

I do not want to work in:
- Advertising or marketing
- Social media, e-commerce
- Oil and gas
- Defence or weapons manufacturing
"""

# Context used by the ethics / culture check agent.
# List the kinds of companies or behaviours you want flagged.
ETHICS_CONTEXT = """
Please flag this company if any of the following apply:
- The company has a history of unethical behavior.
- The company or its customers are in industries that are harmful to the environment.
"""

# ── Email settings ──────────────────────────────────────────
# Use a Gmail App Password, NOT your real Google password.
# See: https://myaccount.google.com/apppasswords
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USER")  # Load from .env for security
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # Load from .env for security
EMAIL_FROM = os.getenv("SMTP_USER")  # Load from .env for security
EMAIL_TO = os.getenv("SMTP_USER")  # Load from .env for security
EMAIL_SUBJECT = "🤖 Daily Job Digest"
