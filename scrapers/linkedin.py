"""
scrapers/linkedin.py — Scrapes LinkedIn job listings using Playwright.

LinkedIn blocks simple HTTP requests, so we use a headless Chromium browser.
"""

import logging
import time
from urllib.parse import urlencode, urlparse, urlunparse

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

logger = logging.getLogger(__name__)

LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/search/?"


def scrape(queries: list[str], max_pages: int = 3) -> list[dict]:
    """
    Scrape LinkedIn for each query and return a deduplicated list of job dicts.

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
                start = page_num * 25
                params = {
                    "keywords": query,
                    "f_WT": "2",  # remote filter
                    "start": start,
                }
                url = LINKEDIN_JOBS_URL + urlencode(params)

                try:
                    page.goto(url, timeout=30_000, wait_until="domcontentloaded")
                    page.wait_for_selector(
                        "ul.jobs-search__results-list, .jobs-search-results-list",
                        timeout=10_000,
                    )
                except PWTimeoutError:
                    logger.warning(
                        "LinkedIn page timed out for query=%r page=%d", query, page_num
                    )
                    break

                cards = page.query_selector_all("li.jobs-search-results__list-item")
                if not cards:
                    cards = page.query_selector_all("div.base-card")

                if not cards:
                    logger.debug(
                        "No LinkedIn cards found for query=%r page=%d; stopping.", query, page_num
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
                        "LinkedIn: %d/%d cards failed to parse for query=%r page=%d — "
                        "the site layout may have changed.",
                        parse_failures, len(cards), query, page_num,
                    )

                time.sleep(2)  # polite crawl delay

        browser.close()

    logger.info("LinkedIn: collected %d listings.", len(results))
    return results


def _parse_card(card) -> dict | None:
    """Extract structured fields from a single LinkedIn job card element."""
    try:
        title_el = card.query_selector("h3.base-search-card__title, h3.job-card-list__title")
        title = title_el.inner_text().strip() if title_el else None
        if not title:
            return None

        link_el = card.query_selector("a.base-card__full-link, a.job-card-list__title")
        job_url = link_el.get_attribute("href") if link_el else None
        if not job_url:
            return None
        # Strip query params and fragments for a clean, canonical URL
        parsed = urlparse(job_url)
        job_url = urlunparse(parsed._replace(query="", fragment=""))

        company_el = card.query_selector(
            "h4.base-search-card__subtitle, span.job-card-container__primary-description"
        )
        company = company_el.inner_text().strip() if company_el else "Unknown"

        location_el = card.query_selector(
            "span.job-search-card__location, li.job-card-container__metadata-item"
        )
        location = location_el.inner_text().strip() if location_el else "Unknown"

        return {
            "title": title,
            "company": company,
            "location": location,
            "url": job_url,
            "description": "",
            "source": "LinkedIn",
        }
    except (AttributeError, TypeError, KeyError) as exc:  # noqa: BLE001
        logger.debug("Failed to parse LinkedIn card: %s", exc)
        return None
