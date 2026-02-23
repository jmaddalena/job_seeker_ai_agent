"""agents/filter.py — LLM pass that keeps only relevant job listings."""

import logging
import os

import anthropic

import config

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Export it before running: export ANTHROPIC_API_KEY='sk-ant-...'"
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def filter_listings(listings: list[dict]) -> list[dict]:
    """
    Run each listing through Claude and return only those that match
    FILTER_CRITERIA in config.py.
    """
    if not listings:
        return []

    relevant: list[dict] = []
    client = _get_client()

    for job in listings:
        prompt = _build_prompt(job)
        try:
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=64,
                messages=[{"role": "user", "content": prompt}],
            )
            answer = message.content[0].text.strip().upper()
            if answer.startswith("YES"):
                relevant.append(job)
                logger.debug("KEEP  %s @ %s", job["title"], job["company"])
            else:
                logger.debug("SKIP  %s @ %s", job["title"], job["company"])
        except anthropic.APIError as exc:
            logger.warning("Claude API error while filtering '%s': %s", job["title"], exc)
            # On API error keep the listing so nothing is silently dropped
            relevant.append(job)

    logger.info("Filter: %d/%d listings passed.", len(relevant), len(listings))
    return relevant


def _build_prompt(job: dict) -> str:
    return (
        "You are a job-search assistant. Based on the criteria below, decide whether the "
        "following job listing is relevant.\n\n"
        f"## Criteria\n{config.FILTER_CRITERIA}\n\n"
        f"## Job Listing\n"
        f"Title: {job['title']}\n"
        f"Company: {job['company']}\n"
        f"Location: {job['location']}\n"
        f"Description: {job['description']}\n\n"
        "Reply with exactly YES or NO (one word only)."
    )
