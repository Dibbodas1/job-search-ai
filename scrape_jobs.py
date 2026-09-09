"""
Multi-Source Job Search Engine (Supports 24h, Last Week / 7-Day, & Custom Modes)
Pulls verified jobs from:
1. LinkedIn (via Direct Live Guest Search & Deep JD Enrichment) - Bangladesh & Global Remote
2. Remotive API - Verified Worldwide Remote Developer Jobs
3. Jobicy API - Fresh Worldwide Remote Jobs
4. RemoteOK API - Developer Remote Listings
5. Arbeitnow API - Global Remote Tech Jobs

Scores every job against Dibbo Das's CV and outputs a formatted Excel file + JSON summary.
"""

import requests
import json
import time
import os
import re
import sys
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import dateutil.parser
import bs4

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Resume skills for Dibbo Das matching ──────────────────────────────
RESUME_SKILLS = {
    "core": [
        "react", "react.js", "reactjs",
        "node", "node.js", "nodejs",
        "express", "express.js", "expressjs",
        "mongodb", "mongoose",
        "javascript", "js", "es6",
        "typescript", "ts",
        "next.js", "nextjs",
        "mern",
    ],
    "frontend": [
        "html", "css", "tailwind", "tailwindcss", "tailwind css",
        "framer motion", "gsap", "three.js", "threejs",
        "locomotive scroll", "lenis", "webgl", "vite", "redux", "zustand"
    ],
    "backend": [
        "rest api", "rest apis", "restful",
        "jwt", "authentication", "auth", "rbac",
        "websocket", "socket.io", "socket",
        "api integration", "payment gateway", "sql", "postgresql", "prisma"
    ],
    "tools": [
        "git", "github", "docker", "postman",
        "vercel", "netlify", "render",
        "ci/cd", "github actions", "agile", "scrum", "linux"
    ],
    "languages": [
        "python", "c", "c++",
    ],
}


def is_within_timeframe(date_val, max_hours=192):
    """Checks if a job was posted within the timeframe (default 192 hours ~ 8 days)."""
    if not date_val:
        return True

    date_str = str(date_val).strip()
    date_lower = date_str.lower()

    if any(kw in date_lower for kw in ["just now", "minute", "min", "sec", "second", "today", "yesterday"]):
        return True
    
    if "hour" in date_lower or "hr" in date_lower:
        m = re.search(r'(\d+)\s*(?:hour|hr)', date_lower)
        if m:
            return int(m.group(1)) <= max_hours
        return True

    if "day" in date_lower:
        m = re.search(r'(\d+)\s*day', date_lower)
        if m:
            return int(m.group(1)) * 24 <= max_hours
        return True

    if "week" in date_lower:
        m = re.search(r'(\d+)\s*week', date_lower)
        if m:
            weeks = int(m.group(1))
            return (weeks * 168) <= max_hours
        return True

    if any(kw in date_lower for kw in ["month", "year"]):
        return False

    # Unix timestamp
    if date_str.isdigit():
        ts = int(date_str)
        if ts > 1e11:
            ts /= 1000
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - dt).total_seconds() <= max_hours * 3600

    # Date-only string (YYYY-MM-DD)
    m_date = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date_str)
    if m_date:
        try:
            dt = datetime(int(m_date.group(1)), int(m_date.group(2)), int(m_date.group(3)), tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            diff_days = (now.date() - dt.date()).days
            max_days = int(max_hours / 24) + 1
            return 0 <= diff_days <= max_days
        except Exception:
            return True

    # Parse ISO / RFC date string with time
    try:
        dt = dateutil.parser.parse(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff_hours = (now - dt).total_seconds() / 3600
        return 0 <= diff_hours <= max_hours
    except Exception:
        return True


def format_date_str(date_val):
    """Clean date string to YYYY-MM-DD or readable relative format."""
    if not date_val:
        return "Past Week"
    date_str = str(date_val).strip()

    # If epoch timestamp
    if date_str.isdigit():
        ts = int(date_str)
        if ts > 1e11:
            ts /= 1000
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            pass

    m = re.search(r'\d{4}-\d{2}-\d{2}', date_str)
    if m:
        return m.group(0)
    if any(kw in date_str.lower() for kw in ["hour", "minute", "just now", "today"]):
        return f"Today ({date_str})"
    if "yesterday" in date_str.lower():
        return "1 day ago"
    return date_str[:15]


def extract_experience(title, description, exp_hint=""):
    """Extract experience level from title, description, or source hint."""
    text = f"{title} {description} {exp_hint}".lower()

    year_patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)',
        r'(?:experience|exp)\s*(?:of)?\s*(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)',
        r'(\d+)\s*to\s*(\d+)\s*(?:years?|yrs?)',
        r'minimum\s*(\d+)\s*(?:years?|yrs?)',
        r'at\s*least\s*(\d+)\s*(?:years?|yrs?)',
    ]
    for pattern in year_patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            if len(groups) >= 2 and groups[1]:
                return f"{groups[0]}-{groups[1]} yrs"
            return f"{groups[0]}+ yrs"

    if any(kw in text for kw in ["entry level", "entry-level", "fresher", "fresh graduate", "junior", "jr.", "jr "]):
        return "Entry Level"
    if any(kw in text for kw in ["mid level", "mid-level", "intermediate", "mid-senior"]):
        return "Mid Level"
    if any(kw in text for kw in ["senior", "sr.", "sr ", "lead", "principal", "staff"]):
        return "Senior"
    if any(kw in text for kw in ["intern", "internship", "trainee"]):
        return "Intern"
    if any(kw in text for kw in ["manager", "director", "head of", "vp "]):
        return "Manager+"

    return "1-3 yrs / Open"


def classify_workplace(title, location, description="", is_remote_source=False):
    """
    Accurately classifies a job as 'Remote', 'Hybrid', or 'Onsite'.
    Strictly verifies remote criteria:
    - Never classifies a job with a physical city/country as Remote unless explicitly declared.
    - Accurately identifies Hybrid jobs (days in office / hybrid model / hybrid title).
    - Accurately respects negative remote clauses (in-office only, must relocate, strictly on-site, etc.).
    """
    t_lower = (title or "").lower()
    l_lower = (location or "").lower()
    d_lower = (description or "").lower()
    full_text = f"{t_lower} {l_lower} {d_lower}"

    # 1. Negative override: explicit non-remote / in-office / relocation rules
    has_negative_remote = bool(re.search(
        r'\b(?:not\s+remote|no\s+remote|non-remote|un-remote|strictly\s+on-?site|only\s+on-?site|cannot\s+(?:work|be)\s+remotely|remote\s+work\s+is\s+not\s+(?:available|permitted|offered)|no\s+wfh|in-office\s+only|must\s+work\s+(?:in|from)\s+office|work\s+from\s+office\s+(?:only|mandatory)|in-person\s+only|relocation\s+required|must\s+relocate)\b',
        full_text
    ))
    if has_negative_remote:
        return "Onsite"

    # 2. Check for Hybrid in title, location, or description
    if any(k in t_lower for k in ["(hybrid)", "[hybrid]", " - hybrid", " / hybrid", "hybrid developer", "hybrid role", "hybrid engineer"]):
        return "Hybrid"
    if any(k in l_lower for k in ["hybrid", "(hybrid)"]):
        return "Hybrid"
    if re.search(r'\b(?:hybrid\s+work|hybrid\s+model|hybrid\s+schedule|hybrid\s+environment|\d+\s*days?\s+(?:in|at|from)\s+(?:the\s+)?office|\d+\s*days?\s+wfh|workplace\s*type\s*[:\-]\s*hybrid|work\s*model\s*[:\-]\s*hybrid)\b', d_lower):
        return "Hybrid"

    # 3. Explicit Onsite markers
    if any(k in t_lower for k in ["(onsite)", "(on-site)", "[onsite]", "[on-site]", "on site", "on-site only", "in-office"]):
        return "Onsite"
    if any(k in l_lower for k in ["(on-site)", "(onsite)", "on-site"]):
        return "Onsite"
    if re.search(r'\b(?:workplace\s*type|workplace|work\s*model)\s*[:\-]\s*on-?site\b', d_lower):
        return "Onsite"

    # 4. Check for True Remote declarations
    # In Title:
    has_remote_in_title = bool(re.search(r'\b\(?remote\)?\b|100%\s*remote|fully\s+remote|wfh|work\s+from\s+home', t_lower))
    # In Location:
    has_remote_in_location = bool(re.search(r'\b\(?remote\)?\b|worldwide|anywhere', l_lower))
    # In Description:
    has_remote_in_desc = bool(re.search(
        r'\b(?:100%\s*remote|fully\s+remote|remote[\s\-]+first|work\s+from\s+anywhere|work\s+from\s+home\s+permanently|workplace\s*type\s*[:\-]\s*remote|work\s*model\s*[:\-]\s*remote|remote\s+(?:position|role|job|opportunity|candidate|engineer|developer|work)|work\s+remotely|role\s+is\s+remote|position\s+is\s+remote|100%\s*wfh|entirely\s+remote|remote\s+friendly)\b',
        d_lower
    ))

    if has_remote_in_title or has_remote_in_location or has_remote_in_desc:
        return "Remote"

    # 5. Fallback: If location has a specific physical city/country and no remote proof -> ONSITE!
    return "Onsite"


# Aliased for backwards compatibility
classify_remote = classify_workplace


def generate_search_queries_from_skills(skills, location, is_remote=False):
    """Dynamically build targeted, relevant LinkedIn search queries from candidate skills and target location."""
    raw_skills = []
    if isinstance(skills, dict):
        for cat in ['core', 'frontend', 'backend', 'languages']:
            raw_skills.extend(skills.get(cat, []))
    elif isinstance(skills, list):
        raw_skills.extend(skills)

    skip_for_title = {
        'html', 'css', 'tailwind', 'tailwindcss', 'bootstrap', 'sass', 'scss',
        'git', 'github', 'postman', 'rest api', 'rest apis', 'jwt', 'agile',
        'scrum', 'jira', 'ci/cd', 'webpack', 'vite', 'redux', 'zustand', 'mongoose', 'prisma',
        'c', 'c++', 'sql'
    }

    core_techs = []
    seen = set()
    for s in raw_skills:
        clean_s = str(s).strip()
        if len(clean_s) < 2 or clean_s.lower() in skip_for_title:
            continue
        canon = clean_s.lower()
        if canon not in seen:
            seen.add(canon)
            core_techs.append(clean_s)

    queries = []
    is_rem = is_remote or any(w in str(location).lower() for w in ["remote", "worldwide", "global", "anywhere"])

    for tech in core_techs[:4]:
        if any(w in tech.lower() for w in ['developer', 'engineer', 'stack']):
            role = tech
        else:
            role = f"{tech} Developer"

        if is_rem and "remote" not in role.lower():
            role = f"{role} Remote"

        queries.append((role, location))

    # Standard high-match industry roles
    if is_rem:
        queries.append(("Full Stack Developer Remote", location))
        queries.append(("Frontend Developer Remote", location))
        queries.append(("Software Engineer Remote", location))
    else:
        queries.append(("Full Stack Developer", location))
        queries.append(("Frontend Developer", location))
        queries.append(("Software Engineer", location))

    # Clean duplicates preserving order
    deduped = []
    seen_q = set()
    for title, loc in queries:
        key = (title.lower(), loc.lower())
        if key not in seen_q:
            seen_q.add(key)
            deduped.append((title, loc))

    return deduped[:8]


def score_job(title, description, company_name=""):
    """Score a job listing against Dibbo Das's resume. Returns (score, reason)."""
    text = f"{title} {description} {company_name}".lower()

    matched = {"core": [], "frontend": [], "backend": [], "tools": []}
    for category in ["core", "frontend", "backend", "tools"]:
        for skill in RESUME_SKILLS[category]:
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text) and skill not in matched[category]:
                matched[category].append(skill)

    alias_groups = [
        {"react", "react.js", "reactjs"},
        {"node", "node.js", "nodejs"},
        {"express", "express.js", "expressjs"},
        {"next.js", "nextjs"},
        {"javascript", "js", "es6"},
        {"typescript", "ts"},
        {"tailwind", "tailwindcss", "tailwind css"},
        {"three.js", "threejs"},
        {"rest api", "rest apis", "restful"},
        {"websocket", "socket.io", "socket"},
        {"jwt", "authentication", "auth"},
        {"mongodb", "mongoose"},
    ]

    unique_matches = {}
    for category, skills_matched in matched.items():
        unique = set()
        for skill in skills_matched:
            canonical = skill
            for group in alias_groups:
                if skill in group:
                    canonical = sorted(group)[0]
                    break
            unique.add(canonical)
        unique_matches[category] = unique

    core_count = len(unique_matches["core"])
    frontend_count = len(unique_matches["frontend"])
    backend_count = len(unique_matches["backend"])
    tools_count = len(unique_matches["tools"])

    core_score = min(core_count * 9, 45)
    frontend_score = min(frontend_count * 5, 20)
    backend_score = min(backend_count * 5, 20)
    tools_score = min(tools_count * 3, 10)

    title_lower = title.lower()
    title_bonus = 0
    if any(kw in title_lower for kw in ["mern", "full stack", "full-stack", "fullstack"]):
        title_bonus += 20
    elif any(kw in title_lower for kw in ["next.js", "nextjs", "next js", "react"]):
        title_bonus += 18
    elif any(kw in title_lower for kw in ["frontend", "front-end", "front end", "ui/ux", "web developer"]):
        title_bonus += 15
    elif any(kw in title_lower for kw in ["backend", "back-end", "back end", "node"]):
        title_bonus += 15
    elif any(kw in title_lower for kw in ["developer", "software engineer", "programmer", "software dev"]):
        title_bonus += 12

    total = min(core_score + frontend_score + backend_score + tools_score + title_bonus, 100)

    if total < title_bonus:
        total = title_bonus

    reason_parts = []
    if unique_matches["core"]:
        reason_parts.append(f"Core: {', '.join(sorted(unique_matches['core']))}")
    if unique_matches["frontend"]:
        reason_parts.append(f"Frontend: {', '.join(sorted(unique_matches['frontend']))}")
    if unique_matches["backend"]:
        reason_parts.append(f"Backend: {', '.join(sorted(unique_matches['backend']))}")
    if unique_matches["tools"]:
        reason_parts.append(f"Tools: {', '.join(sorted(unique_matches['tools']))}")
    if title_bonus > 0:
        reason_parts.append(f"Role match (+{title_bonus})")
    reason = " | ".join(reason_parts) if reason_parts else "Software Developer role matching profile"

    return total, reason


# ── SOURCE 1: LinkedIn Crawlee & Playwright Engine + JD Enrichment ───

def normalize_linkedin_url(link, job_id=""):
    """Generate a clean, canonical, guaranteed-working LinkedIn job URL."""
    if job_id and str(job_id).strip().isdigit():
        return f"https://www.linkedin.com/jobs/view/{str(job_id).strip()}/"
    if not link:
        return "https://www.linkedin.com/jobs/"
    s = str(link).strip()
    m = re.search(r'(\d{7,})', s)
    if m:
        return f"https://www.linkedin.com/jobs/view/{m.group(1)}/"
    if s.startswith("/"):
        return f"https://www.linkedin.com{s}"
    if not s.startswith("http://") and not s.startswith("https://"):
        return f"https://{s}"
    return s


async def _crawl_linkedin_crawlee(urls, is_remote=False):
    """Internal Crawlee PlaywrightCrawler worker with controlled concurrency to prevent 429s."""
    from datetime import timedelta
    from crawlee import ConcurrencySettings
    from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext
    from crawlee.storage_clients import MemoryStorageClient

    jobs = []
    seen_ids = set()
    storage = MemoryStorageClient()
    crawler = PlaywrightCrawler(
        storage_client=storage,
        concurrency_settings=ConcurrencySettings(min_concurrency=1, max_concurrency=2, desired_concurrency=1),
        max_requests_per_crawl=len(urls),
        max_request_retries=1,
        headless=True,
        browser_type="chromium",
        request_handler_timeout=timedelta(seconds=25)
    )

    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext):
        page = context.page
        await page.wait_for_timeout(600)
        cards = await page.locator("div.base-card, ul.jobs-search__results-list > li").all()
        for card in cards:
            title_el = card.locator("h3.base-search-card__title, h3")
            if await title_el.count() == 0:
                continue
            title = (await title_el.first.inner_text()).strip()
            if not title:
                continue

            comp_el = card.locator("h4.base-search-card__subtitle, h4")
            comp = (await comp_el.first.inner_text()).strip() if await comp_el.count() > 0 else "Confidential"

            loc_el = card.locator("span.job-search-card__location")
            loc = (await loc_el.first.inner_text()).strip() if await loc_el.count() > 0 else ("Worldwide (Remote)" if is_remote else "Bangladesh")

            time_el = card.locator("time")
            date_raw = (await time_el.first.get_attribute("datetime") or await time_el.first.inner_text()) if await time_el.count() > 0 else ""

            link_el = card.locator("a.base-card__full-link, a")
            href = (await link_el.first.get_attribute("href")) if await link_el.count() > 0 else ""
            urn = (await card.get_attribute("data-entity-urn")) or ""

            m = re.search(r'(\d{7,})', urn) or re.search(r'(\d{7,})', href)
            job_id = m.group(1) if m else ""
            canonical_link = normalize_linkedin_url(href, job_id)

            if job_id and job_id in seen_ids:
                continue
            if job_id:
                seen_ids.add(job_id)

            jobs.append({
                "title": title,
                "company": comp,
                "location": loc,
                "job_id": job_id,
                "link": canonical_link,
                "date_posted": date_raw,
                "source": "LinkedIn",
                "remote_status": classify_workplace(title, loc, f"{title} at {comp} in {loc}", is_remote_source=is_remote),
                "description": f"{title} at {comp} in {loc}"
            })

    await crawler.run(urls)
    return jobs


async def _crawl_linkedin_batch(urls, is_remote=False):
    """Internal async Playwright worker with concurrency semaphore for scraping multiple feeds smoothly."""
    from playwright.async_api import async_playwright
    jobs = []
    seen_ids = set()
    sem = asyncio.Semaphore(2)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                locale="en-US"
            )

            async def scrape_single_url(target_url):
                async with sem:
                    page = await context.new_page()
                    try:
                        await page.goto(target_url, wait_until="domcontentloaded", timeout=18000)
                        await page.wait_for_timeout(800)
                        cards = await page.locator("div.base-card, ul.jobs-search__results-list > li").all()
                        for card in cards:
                            title_el = card.locator("h3.base-search-card__title, h3")
                            if await title_el.count() == 0:
                                continue
                            title = (await title_el.first.inner_text()).strip()
                            if not title:
                                continue

                            comp_el = card.locator("h4.base-search-card__subtitle, h4")
                            comp = (await comp_el.first.inner_text()).strip() if await comp_el.count() > 0 else "Confidential"

                            loc_el = card.locator("span.job-search-card__location")
                            loc = (await loc_el.first.inner_text()).strip() if await loc_el.count() > 0 else ("Worldwide (Remote)" if is_remote else "Bangladesh")

                            time_el = card.locator("time")
                            date_raw = (await time_el.first.get_attribute("datetime") or await time_el.first.inner_text()) if await time_el.count() > 0 else ""

                            link_el = card.locator("a.base-card__full-link, a")
                            href = (await link_el.first.get_attribute("href")) if await link_el.count() > 0 else ""
                            urn = (await card.get_attribute("data-entity-urn")) or ""

                            m = re.search(r'(\d{7,})', urn) or re.search(r'(\d{7,})', href)
                            job_id = m.group(1) if m else ""
                            canonical_link = normalize_linkedin_url(href, job_id)

                            if job_id and job_id in seen_ids:
                                continue
                            if job_id:
                                seen_ids.add(job_id)

                            jobs.append({
                                "title": title,
                                "company": comp,
                                "location": loc,
                                "job_id": job_id,
                                "link": canonical_link,
                                "date_posted": date_raw,
                                "source": "LinkedIn",
                                "remote_status": classify_workplace(title, loc, f"{title} at {comp} in {loc}", is_remote_source=is_remote),
                                "description": f"{title} at {comp} in {loc}"
                            })
                    except Exception as e:
                        print(f"     [Playwright] error scraping {target_url}: {e}")
                    finally:
                        await page.close()

            await asyncio.gather(*[scrape_single_url(u) for u in urls])
            await browser.close()
    except Exception as e:
        print(f"     [Playwright] browser execution error: {e}")

    return jobs


def fetch_linkedin_playwright_jobs(queries, timeframe="week", is_remote=False, workplace="all"):
    """Fetch LinkedIn jobs using Crawlee and Playwright scraper engine with automatic fallback."""
    import urllib.parse
    import asyncio

    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception:
            pass

    tpr = "r86400" if timeframe in ("24h", "day") else ("r2592000" if timeframe in ("biweek", "month") else "r604800")
    
    # LinkedIn workplace filter parameter: f_WT (1: Onsite, 2: Remote, 3: Hybrid)
    wp_lower = str(workplace).strip().lower()
    if wp_lower == "onsite":
        wt_param = "&f_WT=1"
    elif wp_lower == "remote" or is_remote:
        wt_param = "&f_WT=2"
    elif wp_lower == "hybrid":
        wt_param = "&f_WT=3"
    else:
        wt_param = ""

    urls = []
    for kw, loc in queries:
        is_geo_ww = is_remote or wp_lower == "remote" or any(w in loc.lower() for w in ["worldwide", "world wide", "global", "remote", "anywhere"])
        geo_param = "&geoId=92000000" if is_geo_ww else ""
        loc_str = "Worldwide" if is_geo_ww else loc
        u = f"https://www.linkedin.com/jobs/search?keywords={urllib.parse.quote(kw)}&location={urllib.parse.quote(loc_str)}{geo_param}&f_TPR={tpr}{wt_param}"
        urls.append(u)

    print(f">> [Crawlee & Playwright] Scraping {len(urls)} LinkedIn channels (workplace={wp_lower or 'all'})...")

    is_remote_flag = is_remote or (wp_lower == "remote")

    # Strategy 1: Direct Playwright parallel async worker with Semaphore(2)
    try:
        jobs = asyncio.run(_crawl_linkedin_batch(urls, is_remote=is_remote_flag))
        if jobs and len(jobs) >= 5:
            print(f">> [Playwright Engine] Successfully extracted {len(jobs)} live jobs from LinkedIn")
            return jobs
    except Exception as e:
        print(f"     [Playwright Engine] error: {e}")

    # Strategy 2: Crawlee PlaywrightCrawler with ConcurrencySettings
    try:
        jobs = asyncio.run(_crawl_linkedin_crawlee(urls, is_remote=is_remote_flag))
        if jobs and len(jobs) >= 5:
            print(f">> [Crawlee Engine] Successfully extracted {len(jobs)} live jobs from LinkedIn")
            return jobs
    except Exception as e:
        print(f"     [Crawlee Engine] notice: {e}")

    # Strategy 3: Direct guest API endpoint fallback
    print(">> [Fallback] Falling back to direct guest endpoint...")
    fallback_jobs = []
    for kw, loc in queries:
        batch = fetch_linkedin_guest_jobs(kw, loc, timeframe=timeframe, limit=25, workplace=wp_lower)
        for b in batch:
            b["link"] = normalize_linkedin_url(b.get("link"), b.get("job_id"))
            fallback_jobs.append(b)
    return fallback_jobs


def fetch_linkedin_guest_jobs(keyword, location, timeframe="week", limit=25, workplace="all"):
    """Fetch live LinkedIn jobs using LinkedIn's public guest search endpoint with clean URL normalization."""
    import urllib.parse
    jobs = []
    tpr = "r86400" if timeframe in ("24h", "day") else "r604800"

    wp_lower = str(workplace).strip().lower()
    if wp_lower == "onsite":
        wt_param = "&f_WT=1"
    elif wp_lower == "remote":
        wt_param = "&f_WT=2"
    elif wp_lower == "hybrid":
        wt_param = "&f_WT=3"
    else:
        wt_param = ""
    
    is_geo_ww = (wp_lower == "remote") or any(w in str(location).lower() for w in ["worldwide", "world wide", "global", "remote", "anywhere"])
    geo_param = "&geoId=92000000" if is_geo_ww else ""
    loc_str = "Worldwide" if is_geo_ww else location

    for start in range(0, limit, 25):
        try:
            kw_enc = urllib.parse.quote(keyword)
            loc_enc = urllib.parse.quote(loc_str)
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={kw_enc}&location={loc_enc}{geo_param}&f_TPR={tpr}{wt_param}&start={start}"
            resp = requests.get(url, headers=HEADERS, timeout=12)
            if resp.status_code != 200 or not resp.text.strip():
                break
                
            soup = bs4.BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all("div", class_="base-card")
            if not cards:
                cards = soup.find_all("li")

            count = 0
            for card in cards:
                title_el = card.find("h3", class_="base-search-card__title") or card.find("h3")
                comp_el = card.find("h4", class_="base-search-card__subtitle") or card.find("h4")
                loc_el = card.find("span", class_="job-search-card__location") or card.find("span", class_="base-search-card__metadata")
                time_el = card.find("time")
                link_el = card.find("a", class_="base-card__full-link") or card.find("a", href=True)

                if title_el and link_el and link_el.get("href"):
                    raw_title = title_el.text.strip()
                    raw_comp = comp_el.text.strip() if comp_el else "N/A"
                    raw_loc = loc_el.text.strip() if loc_el else location
                    raw_date = (time_el.get("datetime") or time_el.text.strip()) if time_el else ""
                    raw_link = link_el.get("href", "").strip()

                    job_id_match = re.search(r'(\d{7,})', raw_link) or re.search(r'-(\d{5,})(?:\?|$)', raw_link)
                    job_id = job_id_match.group(1) if job_id_match else ""
                    canonical_link = normalize_linkedin_url(raw_link, job_id)

                    jobs.append({
                        "title": raw_title,
                        "company": raw_comp,
                        "location": raw_loc,
                        "date_posted": raw_date,
                        "link": canonical_link,
                        "job_id": job_id,
                        "source": "LinkedIn",
                        "description": f"{raw_title} at {raw_comp} in {raw_loc}"
                    })
                    count += 1

            if count == 0:
                break
            time.sleep(0.2)
        except Exception as e:
            print(f"     [LinkedIn Guest] error for '{keyword}' ({location}): {e}")
            break

    return jobs


def fetch_linkedin_jobs(keyword, location, timeframe="week", limit=25):
    """Fetch LinkedIn jobs using Playwright & Crawlee scraper first, then guest endpoint."""
    batch = fetch_linkedin_playwright_jobs([(keyword, location)], timeframe=timeframe)
    if batch:
        return batch
    return fetch_linkedin_guest_jobs(keyword, location, timeframe, limit)



def enrich_linkedin_job(job):
    """Enrich a LinkedIn job by fetching its full job description HTML if not already available."""
    job_id = job.get("job_id")
    job["link"] = normalize_linkedin_url(job.get("link"), job_id)

    if len(job.get("description", "")) > 200:
        return job

    if not job_id:
        return job


    try:
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200 and resp.text.strip():
            soup = bs4.BeautifulSoup(resp.text, "html.parser")
            desc_el = soup.find("div", class_="show-more-less-html__markup") or soup.find("section", class_="description")
            if desc_el:
                full_desc = desc_el.text.strip()
                job["description"] = f"{job['title']} {full_desc}"
                
                # Check for clean direct company name inside JD if placeholder
                if job.get("company") in ("nextjobz", "N/A"):
                    m_comp = re.search(r'(?:Company Name|Organization|Hiring Company)\s*[:\-]\s*([A-Za-z0-9\s.,&\-\(\)]+?)(?:Location|Job Type|Workplace|Job ID|Position|Salary|We are|\n|\r|$)', full_desc, re.IGNORECASE)
                    if m_comp and len(m_comp.group(1).strip()) > 2:
                        cleaned_c = m_comp.group(1).strip()
                        if len(cleaned_c) <= 40:
                            job["company"] = cleaned_c
    except Exception:
        pass
    return job


# ── SOURCE 2: Remotive Public API ────────────────────────────────────
def fetch_remotive_jobs(max_hours=192):
    """Fetch developer jobs from Remotive within timeframe."""
    jobs = []
    try:
        print("  >> [Remotive] Fetching remote developer jobs...")
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=80"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("jobs", [])
            for item in data:
                title = item.get("title", "")
                pub_date = item.get("publication_date", "")
                
                if not is_within_timeframe(pub_date, max_hours=max_hours):
                    continue

                if any(kw in title.lower() for kw in ["full", "stack", "mern", "react", "node", "javascript", "typescript", "frontend", "backend", "web", "software", "engineer", "developer", "next"]):
                    jobs.append({
                        "title": title,
                        "company": item.get("company_name", "N/A"),
                        "location": item.get("candidate_required_location") or "Worldwide (Remote)",
                        "date_posted": format_date_str(pub_date),
                        "description": item.get("description", ""),
                        "link": item.get("url", ""),
                        "source": "Remotive",
                        "is_remote": True,
                    })
        print(f"     [Remotive] Found {len(jobs)} jobs matching timeframe")
    except Exception as e:
        print(f"     [Remotive] error: {e}")
    return jobs


# ── SOURCE 3: Jobicy Public API ──────────────────────────────────────
def fetch_jobicy_jobs(tag="react", max_hours=192):
    """Fetch developer jobs from Jobicy within timeframe."""
    jobs = []
    try:
        print(f"  >> [Jobicy] Fetching remote '{tag}' developer jobs...")
        url = f"https://jobicy.com/api/v2/remote-jobs?count=40&tag={tag}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("jobs", [])
            for item in data:
                pub_date = item.get("pubDate", "")
                
                if not is_within_timeframe(pub_date, max_hours=max_hours):
                    continue

                jobs.append({
                    "title": item.get("jobTitle", "N/A"),
                    "company": item.get("companyName", "N/A"),
                    "location": item.get("jobGeo") or "Worldwide (Remote)",
                    "date_posted": format_date_str(pub_date),
                    "description": item.get("jobDescription", ""),
                    "link": item.get("url", ""),
                    "source": "Jobicy",
                    "is_remote": True,
                })
        print(f"     [Jobicy] '{tag}': Found {len(jobs)} jobs")
    except Exception as e:
        print(f"     [Jobicy] error for '{tag}': {e}")
    return jobs


# ── SOURCE 4: RemoteOK Public API ────────────────────────────────────
def fetch_remoteok_jobs(tag="javascript", max_hours=192):
    """Fetch developer jobs from RemoteOK within timeframe."""
    jobs = []
    try:
        print(f"  >> [RemoteOK] Fetching remote '{tag}' developer jobs...")
        url = f"https://remoteok.com/api?tag={tag}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for item in data:
                if isinstance(item, dict) and item.get("position"):
                    raw_date = item.get("date") or item.get("epoch")
                    
                    if not is_within_timeframe(raw_date, max_hours=max_hours):
                        continue

                    jobs.append({
                        "title": item.get("position", "N/A"),
                        "company": item.get("company", "N/A"),
                        "location": item.get("location") or "Worldwide (Remote)",
                        "date_posted": format_date_str(raw_date),
                        "description": item.get("description", ""),
                        "link": item.get("url", ""),
                        "source": "RemoteOK",
                        "is_remote": True,
                    })
        print(f"     [RemoteOK] '{tag}': Found {len(jobs)} jobs")
    except Exception as e:
        print(f"     [RemoteOK] error for '{tag}': {e}")
    return jobs


# ── SOURCE 5: Arbeitnow Public API ───────────────────────────────────
def fetch_arbeitnow_jobs(max_hours=192):
    """Fetch global remote tech jobs from Arbeitnow."""
    jobs = []
    try:
        print("  >> [Arbeitnow] Fetching global remote developer jobs...")
        url = "https://www.arbeitnow.com/api/job-board-api"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            for item in data:
                title = item.get("title", "")
                created_at = item.get("created_at")
                is_remote = item.get("remote", False)

                if not is_within_timeframe(created_at, max_hours=max_hours):
                    continue

                if not is_tech_job(title, item.get("description", "")):
                    continue

                jobs.append({
                    "title": title,
                    "company": item.get("company_name", "N/A"),
                    "location": ("Worldwide (Remote)" if is_remote else item.get("location")) or "Remote",
                    "date_posted": format_date_str(str(created_at)),
                    "description": item.get("description", ""),
                    "link": item.get("url", ""),
                    "source": "Arbeitnow",
                    "is_remote": is_remote,
                })
        print(f"     [Arbeitnow] Found {len(jobs)} jobs matching timeframe")
    except Exception as e:
        print(f"     [Arbeitnow] error: {e}")
    return jobs


def is_tech_job(title, description=""):
    """Check if the job is genuinely a software/tech development role."""
    text = f"{title} {description}".lower()
    
    # Strictly filter out government/defense security clearance roles
    if any(k in text for k in [
        "top secret", "ci polygraph", "polygraph required", "security clearance required",
        "secret clearance", "ts/sci", "poly required", "us citizenship required"
    ]):
        return False

    # Exclude common non-English titles (French, German, Spanish, Italian)
    if any(k in title.lower() for k in [
        "développeur", "développeuse", "ingénieur", "entwickler", "desarrollador",
        "programmatore", "stage ", "stagiaire", "alternant", "alternance"
    ]):
        return False

    strictly_exclude = [
        "civil engineer", "civil site", "mechanical engineer", "electrical engineer",
        "merchandiser", "garment", "sales executive", "marketing officer", "receptionist",
        "front desk", "accountant", "audit", "driver", "cashier", "nurse", "doctor",
        "chef", "cook", "waiter", "security guard", "telecom technician", "call center"
    ]
    if any(ex in text for ex in strictly_exclude):
        if not any(kw in title.lower() for kw in ["mern", "full stack", "full-stack", "fullstack", "react", "node", "frontend", "backend", "software engineer", "web developer"]):
            return False

    tech_keywords = [
        "developer", "engineer", "programmer", "full stack", "full-stack", "fullstack",
        "mern", "react", "node", "javascript", "typescript", "frontend", "front-end",
        "backend", "back-end", "web", "software", "coder", "next.js", "nextjs", "vue", "angular", "python"
    ]
    return any(kw in text for kw in tech_keywords)


def normalize_dedup(job):
    """Generate normalized dedup keys."""
    link = job.get("link", "").strip()
    title = job.get("title", "").strip().lower()
    company = job.get("company", "").strip().lower()

    job_id_match = re.search(r'/(\d{5,})', link)
    url_id = job_id_match.group(1) if job_id_match else link

    title_clean = re.sub(r'[^a-z0-9]', '', title)[:30]
    comp_clean = re.sub(r'[^a-z0-9]', '', company)[:20]
    title_comp = f"{title_clean}|{comp_clean}"

    return url_id, title_comp


def run_job_search(timeframe="week", days=7, top_count=15):
    """Main multi-source job search pipeline."""
    max_hours = max(days * 24 + 36, 36)
    timeframe_label = "Past 24 Hours" if (timeframe == "24h" or days <= 1) else f"Past {days} Days (Last Week)"

    print("=" * 75)
    print(f"⚡ JOB SEARCH ENGINE — {timeframe_label.upper()}")
    print("Sources: LinkedIn Live Guest (Deep JD) | Remotive | Jobicy | RemoteOK | Arbeitnow")
    print("Candidate Profile: Dibbo Das (MERN / React / Next.js / Node.js)")
    print("=" * 75)

    seen_keys = set()
    raw_bd_jobs = []
    raw_remote_jobs = []

    # ═══════════════════════════════════════════════════════════════════
    # 🇧🇩 PART 1: BANGLADESH JOBS
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n--- [STEP 1] SEARCHING BANGLADESH ({timeframe_label}) ---")

    li_bd_queries = [
        ("MERN Stack Developer", "Bangladesh"),
        ("React Developer", "Bangladesh"),
        ("Next.js Developer", "Bangladesh"),
        ("Full Stack Developer", "Bangladesh"),
        ("Frontend Developer", "Bangladesh"),
        ("Node.js Developer", "Bangladesh"),
        ("Software Engineer", "Dhaka"),
        ("Software Engineer", "Bangladesh"),
        ("React Developer", "Chattogram"),
        ("Full Stack Developer", "Chattogram"),
        ("Web Developer", "Bangladesh"),
        ("JavaScript Developer", "Bangladesh"),
    ]

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(fetch_linkedin_jobs, kw, loc, timeframe, 30) for kw, loc in li_bd_queries]
        for fut in as_completed(futures):
            try:
                items = fut.result()
                for item in items:
                    if is_within_timeframe(item.get("date_posted"), max_hours=max_hours) and is_tech_job(item.get("title", "")):
                        u_key, t_key = normalize_dedup(item)
                        if (not u_key or u_key not in seen_keys) and t_key not in seen_keys:
                            if u_key: seen_keys.add(u_key)
                            seen_keys.add(t_key)
                            raw_bd_jobs.append(item)
            except Exception as e:
                print(f"Error fetching BD job batch: {e}")

    print(f">> Scraped {len(raw_bd_jobs)} raw Bangladesh job postings. Enriching full JDs...")

    # Deep JD Enrichment for BD jobs
    bd_jobs = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        enriched_futs = [executor.submit(enrich_linkedin_job, j) for j in raw_bd_jobs]
        for fut in as_completed(enriched_futs):
            try:
                job = fut.result()
                score, reason = score_job(job["title"], job.get("description", ""), job.get("company", ""))
                exp = extract_experience(job["title"], job.get("description", ""))
                remote_st = classify_remote(job["title"], job["location"], job.get("description", ""))

                bd_jobs.append({
                    "title": job["title"],
                    "company": job["company"],
                    "location": job["location"],
                    "date_posted": format_date_str(job.get("date_posted")),
                    "score": score,
                    "reason": reason,
                    "remote_status": remote_st,
                    "experience": exp,
                    "link": job["link"],
                    "source": job.get("source", "LinkedIn"),
                })
            except Exception as e:
                print(f"Error enriching BD job: {e}")

    print(f">> Total verified & scored Bangladesh jobs: {len(bd_jobs)}")

    # ═══════════════════════════════════════════════════════════════════
    # 🌍 PART 2: REMOTE JOBS WORLDWIDE
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n--- [STEP 2] SEARCHING REMOTE WORLDWIDE ({timeframe_label}) ---")

    remote_futures = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        for kw in ["MERN Stack Developer", "Full Stack Developer", "React Developer", "Next.js Developer", "Frontend Developer", "Node.js Developer", "JavaScript Developer", "Software Engineer"]:
            remote_futures.append(("linkedin_remote", executor.submit(fetch_linkedin_jobs, kw, "Worldwide", timeframe, 30)))

        for source_type, fut in remote_futures:
            try:
                items = fut.result()
                for item in items:
                    posted_raw = item.get("date_posted") or ""
                    if not is_within_timeframe(posted_raw, max_hours=max_hours):
                        continue

                    title = item.get("title", "")
                    company = item.get("company", "N/A")
                    loc_val = item.get("location", "Worldwide (Remote)")
                    link = item.get("link", "")
                    desc = item.get("description", "")
                    date_p = format_date_str(posted_raw)
                    is_rem = item.get("is_remote", True)

                    if not is_tech_job(title, desc):
                        continue

                    u_key, t_key = normalize_dedup(item)
                    if (not u_key or u_key not in seen_keys) and t_key not in seen_keys:
                        if u_key: seen_keys.add(u_key)
                        seen_keys.add(t_key)
                        raw_remote_jobs.append({
                            "title": title,
                            "company": company,
                            "location": loc_val,
                            "date_posted": date_p,
                            "link": link,
                            "description": desc,
                            "source": item.get("source", source_type.capitalize()),
                            "is_remote": is_rem,
                            "job_id": item.get("job_id", "")
                        })
            except Exception as e:
                print(f"Error processing Remote future: {e}")

    print(f">> Scraped {len(raw_remote_jobs)} raw Remote job postings. Enriching & scoring...")

    remote_jobs = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        enriched_remote = [executor.submit(enrich_linkedin_job, j) for j in raw_remote_jobs]
        for fut in as_completed(enriched_remote):
            try:
                job = fut.result()
                score, reason = score_job(job["title"], job.get("description", ""), job.get("company", ""))
                exp = extract_experience(job["title"], job.get("description", ""))
                remote_st = "Remote" if job.get("is_remote", True) else classify_remote(job["title"], job["location"], job.get("description", ""), source_is_remote=True)

                remote_jobs.append({
                    "title": job["title"],
                    "company": job["company"],
                    "location": job["location"],
                    "date_posted": job["date_posted"],
                    "score": score,
                    "reason": reason,
                    "remote_status": remote_st,
                    "experience": exp,
                    "link": job["link"],
                    "source": job["source"],
                })
            except Exception as e:
                print(f"Error scoring Remote job: {e}")

    print(f">> Total verified & scored Remote jobs: {len(remote_jobs)}")

    # ═════════════════════════════════════
def write_excel(bd_jobs, remote_jobs, timeframe_label="Past Week", location_label="Bangladesh", sections_data=None):
    """Write multi-source jobs to formatted Excel file with rich styling."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active

    today_str = datetime.now().strftime('%Y-%m-%d')
    ws.title = f"Jobs_{today_str}"

    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    title_font = Font(name="Calibri", bold=True, size=15, color="1B365D")
    subtitle_font = Font(name="Calibri", italic=True, size=10, color="555555")
    
    section_font = Font(name="Calibri", bold=True, size=12, color="FFFFFF")
    section_bd_fill = PatternFill(start_color="006A4E", end_color="006A4E", fill_type="solid")
    section_remote_fill = PatternFill(start_color="2B547E", end_color="2B547E", fill_type="solid")
    palette_fills = [
        PatternFill(start_color="006A4E", end_color="006A4E", fill_type="solid"),
        PatternFill(start_color="2B547E", end_color="2B547E", fill_type="solid"),
        PatternFill(start_color="6A1B9A", end_color="6A1B9A", fill_type="solid"),
        PatternFill(start_color="C25E00", end_color="C25E00", fill_type="solid"),
    ]

    data_font = Font(name="Calibri", size=10)
    data_bold = Font(name="Calibri", bold=True, size=10)
    data_align = Alignment(vertical="top", wrap_text=True)
    link_font = Font(name="Calibri", bold=True, size=10, color="0056B3", underline="single")

    score_high_fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
    score_mid_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
    score_low_fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
    score_high_font = Font(name="Calibri", bold=True, size=10, color="155724")
    score_mid_font = Font(name="Calibri", bold=True, size=10, color="856404")
    score_low_font = Font(name="Calibri", bold=True, size=10, color="721C24")

    remote_yes_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
    remote_hybrid_fill = PatternFill(start_color="D1ECF1", end_color="D1ECF1", fill_type="solid")
    remote_onsite_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")

    thin_border = Border(
        left=Side(style="thin", color="E0E0E0"),
        right=Side(style="thin", color="E0E0E0"),
        top=Side(style="thin", color="E0E0E0"),
        bottom=Side(style="thin", color="E0E0E0"),
    )
    even_row_fill = PatternFill(start_color="F9FAFC", end_color="F9FAFC", fill_type="solid")

    headers = [
        "#", "Job Title", "Company", "Location", "Date Posted",
        "Match Score", "Reason / Skills Matched", "Remote / Onsite", "Experience", "Source", "Direct Apply Link"
    ]
    col_widths = [5, 36, 26, 24, 16, 13, 48, 15, 14, 13, 20]
    num_cols = len(headers)
    last_col = get_column_letter(num_cols)

    ws.merge_cells(f"A1:{last_col}1")
    ws["A1"] = f"⚡ Job Matches ({timeframe_label}) — {today_str}"
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells(f"A2:{last_col}2")
    ws["A2"] = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Targets: {location_label} | Filter: Posted within {timeframe_label}"
    ws["A2"].font = subtitle_font
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")

    ws.row_dimensions[1].height = 32
    ws.row_dimensions[2].height = 20

    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    def write_section(start_row, section_title, section_fill, jobs):
        ws.merge_cells(f"A{start_row}:{last_col}{start_row}")
        ws.cell(row=start_row, column=1, value=section_title).font = section_font
        ws.cell(row=start_row, column=1).fill = section_fill
        ws.cell(row=start_row, column=1).alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[start_row].height = 28

        hdr_row = start_row + 1
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=hdr_row, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align
            cell.border = thin_border
        ws.row_dimensions[hdr_row].height = 26

        for idx, job in enumerate(jobs):
            row = hdr_row + 1 + idx
            ws.row_dimensions[row].height = 34

            c1 = ws.cell(row=row, column=1, value=idx + 1)
            c1.font = data_bold
            c1.alignment = Alignment(horizontal="center", vertical="top")

            c2 = ws.cell(row=row, column=2, value=job["title"])
            c2.font = data_bold
            c2.alignment = data_align

            c3 = ws.cell(row=row, column=3, value=job["company"])
            c3.font = data_font
            c3.alignment = data_align

            c4 = ws.cell(row=row, column=4, value=job["location"])
            c4.font = data_font
            c4.alignment = data_align

            c5 = ws.cell(row=row, column=5, value=str(job["date_posted"]))
            c5.font = data_font
            c5.alignment = Alignment(horizontal="center", vertical="top")

            score_cell = ws.cell(row=row, column=6, value=f'{job["score"]}/100')
            score_cell.alignment = Alignment(horizontal="center", vertical="top")
            if job["score"] >= 65:
                score_cell.fill = score_high_fill
                score_cell.font = score_high_font
            elif job["score"] >= 40:
                score_cell.fill = score_mid_fill
                score_cell.font = score_mid_font
            else:
                score_cell.fill = score_low_fill
                score_cell.font = score_low_font

            c7 = ws.cell(row=row, column=7, value=job["reason"])
            c7.font = data_font
            c7.alignment = data_align

            remote_cell = ws.cell(row=row, column=8, value=job["remote_status"])
            remote_cell.alignment = Alignment(horizontal="center", vertical="top")
            if job["remote_status"] == "Remote":
                remote_cell.fill = remote_yes_fill
                remote_cell.font = Font(name="Calibri", bold=True, size=10, color="004085")
            elif job["remote_status"] == "Hybrid":
                remote_cell.fill = remote_hybrid_fill
                remote_cell.font = Font(name="Calibri", bold=True, size=10, color="0C5460")
            else:
                remote_cell.fill = remote_onsite_fill
                remote_cell.font = Font(name="Calibri", bold=True, size=10, color="856404")

            c9 = ws.cell(row=row, column=9, value=job["experience"])
            c9.font = data_font
            c9.alignment = Alignment(horizontal="center", vertical="top")

            source_cell = ws.cell(row=row, column=10, value=job["source"])
            source_cell.font = Font(name="Calibri", bold=True, size=10, color="1B365D")
            source_cell.alignment = Alignment(horizontal="center", vertical="top")

            link_cell = ws.cell(row=row, column=11, value="Apply Link")
            if job.get("link"):
                link_cell.hyperlink = job["link"]
            link_cell.font = link_font
            link_cell.alignment = Alignment(horizontal="center", vertical="top")

            for col in range(1, num_cols + 1):
                ws.cell(row=row, column=col).border = thin_border
                if idx % 2 == 1 and col not in (6, 8):
                    ws.cell(row=row, column=col).fill = even_row_fill

        return hdr_row + 1 + len(jobs) + 1

    next_row = 4
    if sections_data and isinstance(sections_data, list):
        for s_idx, sec in enumerate(sections_data):
            sec_jobs = sec.get("jobs", [])
            sec_title = sec.get("title", f"Section {s_idx + 1}")
            sec_fill = palette_fills[s_idx % len(palette_fills)]
            next_row = write_section(next_row, f"  {sec_title} — {timeframe_label} ({len(sec_jobs)} Selected)", sec_fill, sec_jobs)
        all_jobs = []
        for sec in sections_data:
            all_jobs.extend(sec.get("jobs", []))
    else:
        loc_name = location_label or "Local"
        next_row = write_section(4, f"  📍 {loc_name} Jobs — {timeframe_label} ({len(bd_jobs)} Selected)", section_bd_fill, bd_jobs)
        next_row = write_section(next_row, f"  🌍 Remote Worldwide Jobs — {timeframe_label} ({len(remote_jobs)} Selected)", section_remote_fill, remote_jobs)
        all_jobs = bd_jobs + remote_jobs

    avg_score = sum(j["score"] for j in all_jobs) / len(all_jobs) if all_jobs else 0
    high_matches = sum(1 for j in all_jobs if j["score"] >= 60)
    ws.merge_cells(f"A{next_row}:{last_col}{next_row}")
    ws.cell(
        row=next_row, column=1,
        value=f"📊 Summary: {len(all_jobs)} Total Top Jobs | Bangladesh: {len(bd_jobs)} | Remote Worldwide: {len(remote_jobs)} | Avg Match Score: {avg_score:.0f}/100 | Strong Matches (≥60): {high_matches}"
    ).font = Font(name="Calibri", bold=True, size=11, color="1B365D")
    ws.cell(row=next_row, column=1).alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[next_row].height = 28

    ws.freeze_panes = "A4"

    date_filename = f"Job_Matches_Last_Week_{today_str}.xlsx" if "Week" in timeframe_label else f"Job_Matches_{today_str}.xlsx"
    output_path = os.path.join(OUTPUT_DIR, date_filename)
    try:
        wb.save(output_path)
        print(f"\n[SUCCESS] Saved dated Excel file: {output_path}")
    except PermissionError:
        date_filename = f"Job_Matches_{today_str}_{datetime.now().strftime('%H%M%S')}.xlsx"
        output_path = os.path.join(OUTPUT_DIR, date_filename)
        wb.save(output_path)
        print(f"\n[WARNING] Original file was open in Excel. Saved with timestamp: {output_path}")

    # Also save standard filenames for convenience
    try:
        wb.save(os.path.join(OUTPUT_DIR, "Job_Match last week.xlsx"))
        wb.save(os.path.join(OUTPUT_DIR, f"Job_Matches_{today_str}.xlsx"))
    except Exception:
        pass

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Multi-Source Job Search Engine")
    parser.add_argument("--timeframe", choices=["24h", "week", "month"], default="week", help="Search timeframe (default: week)")
    parser.add_argument("--days", type=int, default=7, help="Number of days to search (default: 7)")
    parser.add_argument("--top", type=int, default=15, help="Number of top jobs per section (default: 15)")
    args = parser.parse_args()

    run_job_search(timeframe=args.timeframe, days=args.days, top_count=args.top)


if __name__ == "__main__":
    main()
