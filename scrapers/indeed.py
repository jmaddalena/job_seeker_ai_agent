"""
scrapers/indeed.py — Scrapes Indeed job listings using Playwright.

Indeed blocks plain HTTP requests, so we use a headless Chromium browser
(the same approach already used for LinkedIn).
"""

import logging
import time
from urllib.parse import urlencode, urlparse, urlunparse

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

logger = logging.getLogger(__name__)

INDEED_BASE = "https://www.indeed.com"
INDEED_JOBS_URL = f"{INDEED_BASE}/jobs?"


def scrape(queries: list[str], max_pages: int = 3) -> list[dict]:
    """
    Scrape Indeed for each query and return a deduplicated list of job dicts.

    Each dict contains: title, company, location, url, description, source.
    """
    seen_urls: set[str] = set()
    results: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        for query in queries:
            for page_num in range(max_pages):
                start = page_num * 10
                params = {"q": query, "l": "remote", "start": start, "fromage": 1}
                url = INDEED_JOBS_URL + urlencode(params)

                try:
                    page.goto(url, timeout=30_000, wait_until="domcontentloaded")
                    page.wait_for_selector(
                        "div.job_seen_beacon, div[data-testid='jobCard']",
                        timeout=10_000,
                    )
                except PWTimeoutError:
                    logger.warning(
                        "Indeed page timed out for query=%r page=%d", query, page_num
                    )
                    break

                cards = page.query_selector_all("div.job_seen_beacon")
                if not cards:
                    cards = page.query_selector_all("div[data-testid='jobCard']")

                if not cards:
                    logger.debug(
                        "No Indeed cards found for query=%r page=%d; stopping.", query, page_num
                    )
                    break

                parse_failures = 0
                for card in cards:
                    job = _parse_card(card)
                    if job is None:
                        parse_failures += 1
                    elif job["url"] not in seen_urls:
                        seen_urls.add(job["url"])
                        results.append(job)

                if parse_failures:
                    logger.warning(
                        "Indeed: %d/%d cards failed to parse for query=%r page=%d — "
                        "the site layout may have changed.",
                        parse_failures, len(cards), query, page_num,
                    )

                time.sleep(2)  # polite crawl delay

        browser.close()

    logger.info("Indeed: collected %d listings.", len(results))
    return results


def _parse_card(card) -> dict | None:
    """Extract structured fields from a single Indeed job card element."""
    try:
        title_el = card.query_selector("h2.jobTitle a span, h2.jobTitle span")
        title = title_el.inner_text().strip() if title_el else None
        if not title:
            return None

        link_el = card.query_selector("h2.jobTitle a[href], a[data-jk]")
        job_url = link_el.get_attribute("href") if link_el else None
        if not job_url:
            return None
        # Resolve relative URLs and strip tracking params to get a stable canonical URL
        if not job_url.startswith("http"):
            job_url = f"{INDEED_BASE}{job_url}"
        parsed = urlparse(job_url)
        job_url = urlunparse(parsed._replace(query="", fragment=""))

        company_el = card.query_selector(
            "[data-testid='company-name'], span.companyName"
        )
        company = company_el.inner_text().strip() if company_el else "Unknown"

        location_el = card.query_selector(
            "[data-testid='text-location'], div.companyLocation"
        )
        location = location_el.inner_text().strip() if location_el else "Unknown"

        description_el = card.query_selector(
            "div.job-snippet, [data-testid='jobDescription']"
        )
        description = description_el.inner_text().strip() if description_el else ""

        return {
            "title": title,
            "company": company,
            "location": location,
            "url": job_url,
            "description": description,
            "source": "Indeed",
        }
    except (AttributeError, TypeError, KeyError) as exc:  # noqa: BLE001
        logger.debug("Failed to parse Indeed card: %s", exc)
        return None
