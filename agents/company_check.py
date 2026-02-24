"""agents/company_check.py — Ethics and culture assessment via Claude."""

import copy
import logging

import anthropic

import config
from agents.client import get_client

logger = logging.getLogger(__name__)

# In-process cache: company name → ethics flag string.
# Avoids redundant API calls when the same company appears in multiple listings.
_company_cache: dict[str, str] = {}


def check_companies(listings: list[dict]) -> list[dict]:
    """
    For each listing, ask Claude to flag potential ethical concerns about the
    company based on ETHICS_CONTEXT in config.py.

    Adds an 'ethics_flag' key (str) to each listing dict.
    A flag value of "" means no concerns found.

    Results are cached per company name within a single run so the same
    company is never queried more than once.
    """
    if not listings:
        return []

    client = get_client()
    checked: list[dict] = []

    for job in listings:
        company = job["company"]

        if company in _company_cache:
            flag = _company_cache[company]
            logger.debug("Company check cache hit for %s", company)
        else:
            prompt = _build_prompt(company)
            try:
                message = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=256,
                    messages=[{"role": "user", "content": prompt}],
                )
                flag = message.content[0].text.strip()
                # Normalise: treat "NONE" / "NO CONCERNS" / empty as no flag
                if flag.upper() in {"NONE", "NO CONCERNS", "NO", ""}:
                    flag = ""
            except anthropic.APIError as exc:
                logger.warning(
                    "Claude API error while checking company '%s': %s", company, exc
                )
                flag = ""

            _company_cache[company] = flag
            logger.debug("Company check for %s: %s", company, flag if flag else "clean")

        job = copy.deepcopy(job)  # deep copy so we don't mutate the input
        job["ethics_flag"] = flag
        checked.append(job)

    return checked


def _build_prompt(company: str) -> str:
    return (
        "You are a research assistant helping a job seeker evaluate companies ethically.\n\n"
        f"## Company\n{company}\n\n"
        f"## Criteria for flagging\n{config.ETHICS_CONTEXT}\n\n"
        "If you have knowledge of any concerns matching the criteria above, briefly describe them "
        "in one or two sentences. If there are no concerns, reply with exactly: NONE"
    )
