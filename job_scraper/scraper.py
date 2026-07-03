"""
Async job scraper - pulls from Greenhouse, Lever, and Ashby ATS APIs.
Runs on a schedule; dashboard reads only from SQLite (zero rate-limit risk on refresh).
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Optional

import httpx

from .companies import COMPANIES
from .database import upsert_job

logger = logging.getLogger(__name__)

# ── Keywords ──────────────────────────────────────────────────────────────────

SKILL_KEYWORDS = [
    # Backend & infra
    "python", "fastapi", "backend", "distributed", "aws", "docker",
    "sql", "nosql", "postgresql", "redis", "kafka", "microservice",
    # AI / GenAI
    "ai engineer", "generative ai", "genai", "llm", "large language model",
    "rag", "retrieval augmented", "embedding", "vector database", "vector db",
    "langchain", "llamaindex", "sentence transformer", "fine-tun",
    "prompt engineer", "foundation model", "inference", "eval",
    # Titles
    "software engineer", "backend engineer", "ai engineer",
    "machine learning engineer", "ml engineer", "platform engineer",
    "api engineer", "data engineer",
]

BAY_AREA_TERMS = [
    "san francisco", "sf", "san jose", "mountain view", "sunnyvale",
    "cupertino", "santa clara", "palo alto", "menlo park", "redwood city",
    "san mateo", "foster city", "south san francisco", "fremont",
    "oakland", "berkeley", "bay area", "remote",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _job_id(company_slug: str, external_id: str) -> str:
    raw = f"{company_slug}::{external_id}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def _matches_skills(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in SKILL_KEYWORDS)


def _matches_location(location_text: str) -> bool:
    if not location_text:
        return True  # location unknown → include optimistically
    lower = location_text.lower()
    return any(term in lower for term in BAY_AREA_TERMS)


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def _from_epoch_ms(ms: Optional[int]) -> Optional[datetime]:
    if not ms:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    except Exception:
        return None


# ── Greenhouse ────────────────────────────────────────────────────────────────

async def _scrape_greenhouse(client: httpx.AsyncClient, company: dict) -> list[dict]:
    slug = company["slug"]
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        resp = await client.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("Greenhouse %s failed: %s", slug, e)
        return []

    jobs = []
    for job in data.get("jobs", []):
        title = job.get("title", "")
        location = job.get("location", {}).get("name", "")
        content = job.get("content", "")

        combined = f"{title} {location} {content}"
        if not _matches_skills(combined):
            continue
        if not _matches_location(location):
            continue

        jobs.append({
            "job_id": _job_id(slug, str(job["id"])),
            "company_name": company["name"],
            "company_tier": company["tier"],
            "title": title,
            "location": location,
            "job_url": job.get("absolute_url", ""),
            "posted_at": _parse_iso(job.get("updated_at")),
            "source": "greenhouse",
        })
    return jobs


# ── Lever ─────────────────────────────────────────────────────────────────────

async def _scrape_lever(client: httpx.AsyncClient, company: dict) -> list[dict]:
    slug = company["slug"]
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        resp = await client.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        postings = resp.json()
    except Exception as e:
        logger.warning("Lever %s failed: %s", slug, e)
        return []

    jobs = []
    for p in postings:
        title = p.get("text", "")
        location = p.get("categories", {}).get("location", "") or p.get("workplaceType", "")
        description = p.get("descriptionPlain", "") or p.get("description", "")

        combined = f"{title} {location} {description}"
        if not _matches_skills(combined):
            continue
        if not _matches_location(location):
            continue

        jobs.append({
            "job_id": _job_id(slug, p.get("id", title)),
            "company_name": company["name"],
            "company_tier": company["tier"],
            "title": title,
            "location": location,
            "job_url": p.get("hostedUrl", ""),
            "posted_at": _from_epoch_ms(p.get("createdAt")),
            "source": "lever",
        })
    return jobs


# ── Ashby ─────────────────────────────────────────────────────────────────────

ASHBY_QUERY = """
query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {
  jobBoard: jobBoardWithTeams(
    organizationHostedJobsPageName: $organizationHostedJobsPageName
  ) {
    jobPostings {
      id
      title
      locationName
      isRemote
      publishedDate
      jobRequisitionName
      externalLink
      organization { name }
    }
  }
}
"""


async def _scrape_ashby(client: httpx.AsyncClient, company: dict) -> list[dict]:
    slug = company["slug"]
    url = "https://jobs.ashbyhq.com/api/non-user-graphql"
    payload = {
        "operationName": "ApiJobBoardWithTeams",
        "query": ASHBY_QUERY,
        "variables": {"organizationHostedJobsPageName": slug},
    }
    try:
        resp = await client.post(url, json=payload, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("Ashby %s failed: %s", slug, e)
        return []

    postings = (
        data.get("data", {})
        .get("jobBoard", {})
        .get("jobPostings", [])
    )
    if postings is None:
        return []

    jobs = []
    for p in postings:
        title = p.get("title", "")
        location = p.get("locationName", "")
        if p.get("isRemote"):
            location = (location + " Remote").strip()

        combined = f"{title} {location}"
        if not _matches_skills(combined):
            continue
        if not _matches_location(location):
            continue

        job_url = p.get("externalLink") or f"https://jobs.ashbyhq.com/{slug}/{p.get('id', '')}"

        jobs.append({
            "job_id": _job_id(slug, p.get("id", title)),
            "company_name": company["name"],
            "company_tier": company["tier"],
            "title": title,
            "location": location,
            "job_url": job_url,
            "posted_at": _parse_iso(p.get("publishedDate")),
            "source": "ashby",
        })
    return jobs


# ── Google Careers ─────────────────────────────────────────────────────────────

async def _scrape_google(client: httpx.AsyncClient, company: dict) -> list[dict]:
    base = "https://careers.google.com/api/jobs/list/"
    params = {
        "page_size": 50,
        "q": "software engineer AI",
        "location": "San Francisco Bay Area, CA, USA",
    }
    try:
        resp = await client.get(base, params=params, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("Google careers failed: %s", e)
        return []

    jobs = []
    for job in data.get("jobs", []):
        title = job.get("title", "")
        locations = " ".join(
            loc.get("display", "") for loc in job.get("locations", [])
        )
        combined = f"{title} {locations}"

        if not _matches_skills(combined):
            continue
        if not _matches_location(locations):
            continue

        job_id_raw = job.get("job_id", title)
        job_url = f"https://careers.google.com/jobs/results/{job_id_raw}"

        jobs.append({
            "job_id": _job_id("google", str(job_id_raw)),
            "company_name": "Google",
            "company_tier": "FAANG",
            "title": title,
            "location": locations,
            "job_url": job_url,
            "posted_at": _parse_iso(job.get("publish_date")),
            "source": "google_careers",
        })
    return jobs


# ── Amazon ────────────────────────────────────────────────────────────────────

async def _scrape_amazon(client: httpx.AsyncClient, company: dict) -> list[dict]:
    url = "https://www.amazon.jobs/en/search.json"
    params = {
        "base_query": "software engineer AI",
        "loc_query": "San Francisco Bay Area",
        "job_count": 50,
        "result_limit": 50,
        "sort": "recent",
    }
    try:
        resp = await client.get(url, params=params, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("Amazon careers failed: %s", e)
        return []

    jobs = []
    for job in data.get("jobs", []):
        title = job.get("title", "")
        location = job.get("location", "")
        description = job.get("description", "")

        combined = f"{title} {location} {description}"
        if not _matches_skills(combined):
            continue
        if not _matches_location(location):
            continue

        job_url = "https://www.amazon.jobs" + job.get("job_path", "")
        jobs.append({
            "job_id": _job_id("amazon", job.get("id_icims", title)),
            "company_name": "Amazon",
            "company_tier": "FAANG",
            "title": title,
            "location": location,
            "job_url": job_url,
            "posted_at": _parse_iso(job.get("posted_date")),
            "source": "amazon_careers",
        })
    return jobs


# ── Microsoft ─────────────────────────────────────────────────────────────────

async def _scrape_microsoft(client: httpx.AsyncClient, company: dict) -> list[dict]:
    url = "https://gcsservices.careers.microsoft.com/search/api/v1/search"
    params = {
        "q": "software engineer AI",
        "l": "en_us",
        "pg": 1,
        "pgSz": 50,
        "o": "Recent",
        "flt": True,
    }
    try:
        resp = await client.get(url, params=params, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("Microsoft careers failed: %s", e)
        return []

    jobs = []
    for job in data.get("operationResult", {}).get("result", {}).get("jobs", []):
        title = job.get("title", "")
        location = " ".join(
            loc.get("l", "") for loc in job.get("locations", [])
        )
        combined = f"{title} {location}"

        if not _matches_skills(combined):
            continue
        if not _matches_location(location):
            continue

        job_url = f"https://careers.microsoft.com/us/en/job/{job.get('jobId', '')}"
        jobs.append({
            "job_id": _job_id("microsoft", str(job.get("jobId", title))),
            "company_name": "Microsoft",
            "company_tier": "FAANG",
            "title": title,
            "location": location,
            "job_url": job_url,
            "posted_at": _parse_iso(job.get("postingDate")),
            "source": "microsoft_careers",
        })
    return jobs


# ── Dispatch ──────────────────────────────────────────────────────────────────

_CUSTOM_SCRAPERS = {
    "google": _scrape_google,
    "amazon": _scrape_amazon,
    "microsoft": _scrape_microsoft,
}

_ATS_SCRAPERS = {
    "greenhouse": _scrape_greenhouse,
    "lever": _scrape_lever,
    "ashby": _scrape_ashby,
}


async def _scrape_company(client: httpx.AsyncClient, company: dict) -> list[dict]:
    ats = company["ats"]
    slug = company["slug"]

    if ats == "custom":
        fn = _CUSTOM_SCRAPERS.get(slug)
        if fn:
            return await fn(client, company)
        logger.debug("No custom scraper for %s — skipping", company["name"])
        return []

    fn = _ATS_SCRAPERS.get(ats)
    if fn:
        return await fn(client, company)

    logger.debug("Unknown ATS %s for %s", ats, company["name"])
    return []


# ── Main entry point ──────────────────────────────────────────────────────────

async def run_scrape() -> dict:
    """Scrape all companies concurrently and persist results to DB."""
    total_new = 0
    total_seen = 0
    errors = 0

    # Stagger requests slightly to be polite; max 20 concurrent connections.
    limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
    async with httpx.AsyncClient(limits=limits, follow_redirects=True) as client:
        semaphore = asyncio.Semaphore(15)

        async def bounded(company):
            async with semaphore:
                await asyncio.sleep(0.1)  # tiny stagger
                return await _scrape_company(client, company)

        tasks = [bounded(c) for c in COMPANIES]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            errors += 1
            logger.error("Scrape task error: %s", result)
            continue
        for job in result:
            total_seen += 1
            is_new = upsert_job(job)
            if is_new:
                total_new += 1

    summary = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "total_seen": total_seen,
        "new_jobs": total_new,
        "errors": errors,
    }
    logger.info("Scrape complete: %s", summary)
    return summary
