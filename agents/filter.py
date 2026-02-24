"""agents/filter.py — LLM pass that keeps only relevant job listings."""

import logging

import anthropic

import config
from agents.client import get_client

logger = logging.getLogger(__name__)

# Number of listings evaluated per API call.  Larger batches reduce API calls
# (e.g. 249 listings ÷ 10 = ~25 calls instead of 249).  Keep it ≤ 20 so the
# response stays short and easy to parse reliably.
BATCH_SIZE = 10


def filter_listings(listings: list[dict]) -> list[dict]:
    """
    Run listings through Claude in batches and return only those that match
    FILTER_CRITERIA in config.py.

    Batching multiple listings per call dramatically reduces the number of
    API requests: 249 listings at BATCH_SIZE=10 requires only ~25 calls
    instead of 249.
    """
    if not listings:
        return []

    relevant: list[dict] = []
    api_errors = 0
    client = get_client()

    for batch_start in range(0, len(listings), BATCH_SIZE):
        batch = listings[batch_start : batch_start + BATCH_SIZE]
        try:
            kept_indices = _filter_batch(client, batch)
            for idx in kept_indices:
                job = batch[idx]
                relevant.append(job)
                logger.debug("KEEP  %s @ %s", job["title"], job["company"])
        except anthropic.APIError as exc:
            logger.warning(
                "Claude API error filtering batch starting at index %d: %s", batch_start, exc
            )
            api_errors += len(batch)

    if api_errors == len(listings):
        raise RuntimeError(
            f"Claude API failed for all {len(listings)} listings. "
            "Check your ANTHROPIC_API_KEY and account credits before running again."
        )
    if api_errors:
        logger.warning("Claude API errors: %d/%d listings were skipped.", api_errors, len(listings))

    logger.info("Filter: %d/%d listings passed.", len(relevant), len(listings))
    return relevant


def _filter_batch(client: anthropic.Anthropic, batch: list[dict]) -> list[int]:
    """
    Evaluate a batch of listings in a single API call.

    Returns a list of 0-based indices for listings that should be kept.
    """
    prompt = _build_batch_prompt(batch)
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=64,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_batch_response(message.content[0].text.strip(), len(batch))


def _parse_batch_response(response: str, batch_size: int) -> list[int]:
    """
    Parse Claude's comma-separated list of 1-based indices into 0-based indices.

    Expected formats: ``"2, 4, 5"`` or ``"NONE"``.
    An empty response is treated the same as ``"NONE"`` (no listings kept).
    Invalid or out-of-range tokens are silently skipped (fail-closed).
    """
    if response.strip().upper().rstrip(".") in {"NONE", ""}:
        return []

    kept: list[int] = []
    for token in response.split(","):
        token = token.strip().rstrip(".")
        try:
            idx = int(token) - 1  # convert 1-based to 0-based
        except ValueError:
            logger.debug("Unexpected token in batch filter response: %r", token)
            continue
        if 0 <= idx < batch_size:
            kept.append(idx)
        else:
            logger.debug("Out-of-range index in batch filter response: %d", idx + 1)
    return kept


def _build_batch_prompt(batch: list[dict]) -> str:
    listings_text = ""
    for i, job in enumerate(batch, start=1):
        listings_text += (
            f"[{i}] Title: {job['title']}\n"
            f"    Company: {job['company']}\n"
            f"    Location: {job['location']}\n"
            f"    Description: {job['description']}\n\n"
        )
    return (
        "You are a job-search assistant. Based on the criteria below, decide which of the "
        "following job listings are relevant.\n\n"
        f"## Criteria\n{config.FILTER_CRITERIA}\n\n"
        f"## Job Listings\n{listings_text}"
        "Reply with a comma-separated list of the numbers of the relevant listings "
        "(e.g. '1, 3, 5'). If none are relevant, reply with exactly: NONE"
    )
