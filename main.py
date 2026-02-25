#!/usr/bin/env python3
"""
main.py — Entry point for the Job Seeker AI Agent.

Run once manually:
    python main.py

Schedule with cron (8am daily):
    0 8 * * * cd /path/to/job-agent && python main.py >> ~/job-agent.log 2>&1
"""

import logging
import os
import sys

from scrapers import indeed, linkedin
from agents import filter as job_filter, company_check
from digest import send
import config



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run() -> None:
    logger.info("=== Job Seeker AI Agent starting ===")
    try:
        # ── 1. Scrape job boards ─────────────────────────────────────────────
        logger.info("Scraping Indeed…")
        indeed_listings = indeed.scrape(config.SEARCH_QUERIES)

        logger.info("Scraping LinkedIn…")
        linkedin_listings = linkedin.scrape(config.SEARCH_QUERIES)

        all_listings = indeed_listings + linkedin_listings
        logger.info("Total raw listings: %d", len(all_listings))

        if not all_listings:
            logger.info("No listings found — nothing to do.")
            return

        # ── 2. LLM relevance filter ──────────────────────────────────────────
        logger.info("Filtering listings with Claude…")
        relevant = job_filter.filter_listings(all_listings)
        logger.info("Relevant listings after filter: %d", len(relevant))

        if not relevant:
            logger.info("No relevant listings after filtering — skipping email.")
            return

        # ── 3. Ethics / culture check ────────────────────────────────────────
        logger.info("Running ethics checks…")
        checked = company_check.check_companies(relevant)

        # ── 4. Send digest email ─────────────────────────────────────────────
        logger.info("Sending digest email to %s…", config.EMAIL_TO)
        send.send_digest(checked)

        logger.info("=== Done ===")
    except Exception:
        logger.exception("Unhandled exception in Job Seeker AI Agent run()")
        # For a cron job, logging the full stack trace improves observability.
        # Depending on project conventions, you could additionally trigger a
        # notification here using existing email utilities.
if __name__ == "__main__":
    run()
