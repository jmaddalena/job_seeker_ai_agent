"""
scrapers/indeed.py — Scrapes Indeed job listings using requests + BeautifulSoup.
"""

import time
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

INDEED_BASE = "https://www.indeed.com"


def scrape(queries: list[str], max_pages: int = 3) -> list[dict]:
    """
    Scrape Indeed for each query and return a deduplicated list of job dicts.

    Each dict contains: title, company, location, url, description, source.
    """
    seen_urls: set[str] = set()
    results: list[dict] = []

    for query in queries:
        for page in range(max_pages):
            start = page * 10
            params = {"q": query, "l": "remote", "start": start, "fromage": 1}
            url = f"{INDEED_BASE}/jobs"
            try:
                resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
                resp.raise_for_status()
            except requests.RequestException as exc:
                logger.warning("Indeed request failed for query=%r page=%d: %s", query, page, exc)
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            job_cards = soup.find_all("div", class_="job_seen_beacon")

            if not job_cards:
                # Try alternate card class used on some Indeed layouts
                job_cards = soup.find_all("div", attrs={"data-testid": "jobCard"})

            if not job_cards:
                logger.debug("No job cards found for query=%r page=%d; stopping.", query, page)
                break

            for card in job_cards:
                job = _parse_card(card)
                if job and job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    results.append(job)

            time.sleep(1)  # polite crawl delay

    logger.info("Indeed: collected %d listings.", len(results))
    return results


def _parse_card(card) -> dict | None:
    """Extract structured fields from a single Indeed job card."""
    try:
        title_tag = card.find("h2", class_="jobTitle") or card.find("a", {"data-jk": True})
        if not title_tag:
            return None
        title = title_tag.get_text(strip=True)

        # Build absolute URL
        link = title_tag.find("a") if title_tag.name != "a" else title_tag
        if link and link.get("href"):
            href = link["href"]
            job_url = href if href.startswith("http") else f"{INDEED_BASE}{href}"
        else:
            return None

        company_tag = card.find("span", attrs={"data-testid": "company-name"}) or card.find(
            "span", class_="companyName"
        )
        company = company_tag.get_text(strip=True) if company_tag else "Unknown"

        location_tag = card.find("div", attrs={"data-testid": "text-location"}) or card.find(
            "div", class_="companyLocation"
        )
        location = location_tag.get_text(strip=True) if location_tag else "Unknown"

        snippet_tag = card.find("div", class_="job-snippet") or card.find(
            "div", attrs={"data-testid": "jobDescription"}
        )
        description = snippet_tag.get_text(" ", strip=True) if snippet_tag else ""

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
