"""
Job Search Web Application — Flask API Server
Wraps the multi-source job scraper with Gemini AI for dynamic CV analysis.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import re
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

# Import scraper functions
from scrape_jobs import (
    fetch_linkedin_jobs, fetch_linkedin_guest_jobs, fetch_remotive_jobs, fetch_jobicy_jobs,
    fetch_remoteok_jobs, fetch_arbeitnow_jobs, enrich_linkedin_job,
    extract_experience, classify_remote, classify_workplace, is_tech_job,
    normalize_dedup, format_date_str, is_within_timeframe, write_excel,
    RESUME_SKILLS, normalize_linkedin_url, fetch_linkedin_playwright_jobs,
    generate_search_queries_from_skills
)

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")

# In-memory storage for search results (for Excel download)
search_results_store = {}


# ─── Gemini AI Helpers ────────────────────────────────────────────────

def get_gemini_client():
    """Get OpenAI-compatible client for Gemini."""
    from openai import OpenAI
    return OpenAI(api_key=GEMINI_API_KEY, base_url=GEMINI_BASE_URL)


def extract_cv_text(pdf_file):
    """Extract text from uploaded PDF."""
    import PyPDF2
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def parse_cv_with_gemini(cv_text):
    """Send CV text to Gemini AI to extract structured skills."""
    client = get_gemini_client()

    prompt = f"""You are a CV/Resume skills extractor. Analyze the following CV text and extract technical skills.

Return a JSON object with exactly this structure:
{{
    "name": "Candidate's full name",
    "title": "Professional title (e.g. Full Stack Developer)",
    "experience_summary": "Brief experience summary (1-2 sentences)",
    "skills": {{
        "core": ["list of core frameworks and languages - e.g. react, node.js, python, typescript"],
        "frontend": ["frontend-specific skills - e.g. html, css, tailwind, gsap, redux"],
        "backend": ["backend skills - e.g. rest api, jwt, sql, postgresql, websocket"],
        "tools": ["dev tools - e.g. git, docker, vercel, ci/cd, github actions"],
        "languages": ["programming languages only - e.g. python, c++, java"]
    }}
}}

Important:
- Include ALL technical skills you find
- Use lowercase for skill names
- Include common variations (e.g. both "react" and "react.js")
- Return ONLY the JSON, no markdown code blocks, no explanation

CV Text:
{cv_text[:8000]}"""

    try:
        response = client.chat.completions.create(
            model="gemini-3.6-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000,
        )

        result_text = response.choices[0].message.content.strip()
        # Clean up potential markdown formatting
        if result_text.startswith("```"):
            result_text = re.sub(r'^```\w*\n?', '', result_text)
            result_text = re.sub(r'\n?```$', '', result_text)

        return json.loads(result_text)
    except Exception as e:
        print(f"Gemini CV parsing error: {e}")
        traceback.print_exc()
        return None


def parse_cv_heuristic(cv_text):
    """Heuristic fallback parser for CV when AI quota or network limits occur."""
    text_lower = cv_text.lower()
    
    # Extract candidate name (first non-empty line or plausible string)
    lines = [line.strip() for line in cv_text.splitlines() if line.strip()]
    name = "Candidate"
    if lines:
        for candidate_line in lines[:5]:
            if "@" not in candidate_line and "http" not in candidate_line and len(candidate_line) < 35:
                name = candidate_line
                break

    title = "Full Stack Developer"
    if "mern" in text_lower:
        title = "MERN Stack Developer"
    elif "frontend" in text_lower or "front-end" in text_lower:
        title = "Frontend Developer"
    elif "backend" in text_lower or "back-end" in text_lower:
        title = "Backend Developer"

    common_skills = {
        "core": ["react", "javascript", "node.js", "express.js", "mongodb", "python", "typescript", "next.js"],
        "frontend": ["html", "css", "tailwind", "redux", "gsap", "bootstrap", "vue"],
        "backend": ["rest api", "jwt", "sql", "postgresql", "websocket", "fastapi", "django"],
        "tools": ["git", "github", "docker", "postman", "vercel", "linux", "aws"]
    }

    extracted = {"core": [], "frontend": [], "backend": [], "tools": []}
    for cat, sk_list in common_skills.items():
        for sk in sk_list:
            if re.search(r'\b' + re.escape(sk) + r'\b', text_lower):
                extracted[cat].append(sk.title() if len(sk) > 3 else sk.upper())

    if not extracted["core"]:
        extracted["core"] = ["React", "JavaScript", "Express.js", "MongoDB"]

    return {
        "name": name,
        "title": title,
        "experience_summary": f"Developer profile extracted from CV emphasizing {', '.join(extracted['core'][:3])}.",
        "skills": extracted,
        "source": "cv_heuristic"
    }


def generate_ai_summary(top_jobs, skills_profile=None):
    """Generate AI career advice based on top job matches."""
    client = get_gemini_client()
    profile = skills_profile or {"name": "Candidate", "title": "Developer", "skills": {}}

    jobs_text = "\n".join([
        f"- {j['title']} at {j['company']} (Score: {j['score']}/100, {j['remote_status']}, {j['experience']})"
        for j in top_jobs[:10]
    ])

    skills_text = json.dumps(profile.get('skills', {}), indent=2)

    prompt = f"""Based on these top job matches and the candidate's skills, provide a brief career insight.

Candidate: {profile.get('name', 'Candidate')} - {profile.get('title', 'Developer')}
Skills: {skills_text}

Top Job Matches:
{jobs_text}

Provide in 3-4 sentences:
1. How well the candidate's profile matches current market demand
2. Which skills give them the strongest advantage
3. One actionable suggestion to improve their job prospects

Keep it encouraging and specific. No markdown formatting."""

    try:
        response = client.chat.completions.create(
            model="gemini-3.6-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Gemini summary error: {e}")
        return None


# ─── Custom Scoring ──────────────────────────────────────────────────

def score_job_custom(title, description, company_name="", custom_skills=None):
    """Score a job listing against custom skills extracted from CV."""
    skills = custom_skills or RESUME_SKILLS
    text = f"{title} {description} {company_name}".lower()

    # Build matched dict from whatever categories exist in skills
    score_categories = ["core", "frontend", "backend", "tools", "languages"]
    matched = {}
    for category in score_categories:
        if category not in skills:
            continue
        matched[category] = []
        skill_list = skills[category] if isinstance(skills[category], list) else []
        for skill in skill_list:
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text) and skill not in matched[category]:
                matched[category].append(skill)

    # Alias groups for dedup
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

    core_count = len(unique_matches.get("core", set()))
    frontend_count = len(unique_matches.get("frontend", set()))
    backend_count = len(unique_matches.get("backend", set()))
    tools_count = len(unique_matches.get("tools", set()))

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
    for category, skills_set in unique_matches.items():
        if skills_set:
            reason_parts.append(f"{category.capitalize()}: {', '.join(sorted(skills_set))}")
    if title_bonus > 0:
        reason_parts.append(f"Role match (+{title_bonus})")
    reason = " | ".join(reason_parts) if reason_parts else "Developer role matching profile"

    return total, reason


# ─── API Endpoints ───────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "gemini_configured": bool(GEMINI_API_KEY)})


@app.route('/api/upload-cv', methods=['POST'])
def upload_cv():
    """Upload and parse CV PDF with Gemini AI."""
    if 'cv' not in request.files:
        return jsonify({"error": "No CV file uploaded"}), 400

    file = request.files['cv']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are supported"}), 400

    try:
        cv_text = extract_cv_text(file)
        if not cv_text.strip():
            return jsonify({"error": "Could not extract text from PDF. Ensure it's not a scanned image."}), 400

        profile = parse_cv_with_gemini(cv_text)
        if not profile:
            print(">> AI rate limit or error encountered. Falling back to heuristic CV parser...")
            profile = parse_cv_heuristic(cv_text)

        return jsonify({
            "success": True,
            "profile": profile,
            "text_length": len(cv_text)
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def is_worldwide_location(loc_str):
    """Detect if a location string represents Worldwide, Global, or Remote."""
    if not loc_str:
        return True
    s = str(loc_str).lower().strip()
    clean = re.sub(r'[^a-z0-9]', '', s)
    if clean in ('worldwide', 'worldwideremote', 'worldwideglobal', 'global', 'globalremote', 'remote', 'remoteworldwide', 'anywhere', 'anywhereinworld', 'international', 'wfh', 'workfromhome', 'all', 'world'):
        return True
    if any(k in s for k in ['worldwide', 'world wide', 'global remote', 'worldwide remote', 'remote global', 'work from anywhere', 'remote worldwide', 'global']):
        return True
    return False


@app.route('/api/search', methods=['POST'])
def search_jobs():
    """Run multi-source job search with multiple locations, custom skills, and per-location workplace filters."""
    data = request.json or {}
    skills = data.get('skills', RESUME_SKILLS)
    timeframe = data.get('timeframe', 'week')
    days = data.get('days', 7)
    top_count = data.get('top_count', 15)
    profile = data.get('profile', {})

    # Support multiple location targets: [{"location": "Bangladesh", "workplace": "onsite"}, {"location": "Worldwide", "workplace": "remote"}]
    raw_locations = data.get('locations')
    location_targets = []
    if raw_locations and isinstance(raw_locations, list):
        for loc_item in raw_locations:
            if isinstance(loc_item, dict):
                loc_name = (loc_item.get('location') or '').strip()
                loc_wp = (loc_item.get('workplace') or 'all').strip().lower()
                if loc_name:
                    location_targets.append({"location": loc_name, "workplace": loc_wp})
            elif isinstance(loc_item, str) and loc_item.strip():
                location_targets.append({"location": loc_item.strip(), "workplace": "all"})

    # Fallback for single location request
    if not location_targets:
        target_location = (data.get('location') or 'Bangladesh').strip()
        workplace_type = (data.get('workplace_type') or 'all').strip().lower()
        location_targets = [{"location": target_location, "workplace": workplace_type}]

    max_hours = max(days * 24 + 36, 36)

    try:
        def search_single_target(target):
            loc_name = target["location"]
            loc_wp = target["workplace"]  # 'onsite', 'hybrid', 'remote', or 'all'
            is_worldwide = is_worldwide_location(loc_name)
            if is_worldwide and loc_wp == 'all':
                loc_wp = 'remote'

            print(f"\n--- [API] Searching Target: '{loc_name}' (workplace={loc_wp}, is_worldwide={is_worldwide}) ---")

            if is_worldwide:
                loc_queries = generate_search_queries_from_skills(skills, "Worldwide", is_remote=True)
                loc_queries.append(('Full Stack Developer Remote', 'Worldwide'))
                loc_queries.append(('React Developer Remote', 'Worldwide'))
                loc_queries.append(('Software Engineer Remote', 'Worldwide'))
                loc_queries = list(dict.fromkeys(loc_queries))[:10]
                raw_candidates = fetch_linkedin_playwright_jobs(loc_queries, timeframe=timeframe, is_remote=True, workplace=loc_wp)
            else:
                loc_queries = generate_search_queries_from_skills(skills, loc_name, is_remote=(loc_wp == 'remote'))
                if loc_name.lower() in ('bangladesh', 'bd'):
                    if loc_wp == 'remote':
                        loc_queries.append(('Software Engineer Remote', 'Bangladesh'))
                        loc_queries.append(('Full Stack Developer Remote', 'Bangladesh'))
                    else:
                        loc_queries.append(('Software Engineer', 'Dhaka'))
                        loc_queries.append(('Full Stack Developer', 'Dhaka'))
                loc_queries = list(dict.fromkeys(loc_queries))[:10]
                raw_candidates = fetch_linkedin_playwright_jobs(loc_queries, timeframe=timeframe, is_remote=(loc_wp == 'remote'), workplace=loc_wp)

            raw_target_jobs = []
            target_seen = set()
            for item in raw_candidates:
                if is_within_timeframe(item.get("date_posted"), max_hours=max_hours) and is_tech_job(item.get("title", ""), item.get("description", "")):
                    u_key, t_key = normalize_dedup(item)
                    if (not u_key or u_key not in target_seen) and t_key not in target_seen:
                        if u_key:
                            target_seen.add(u_key)
                        target_seen.add(t_key)
                        raw_target_jobs.append(item)

            print(f">> Scraped {len(raw_target_jobs)} raw jobs for '{loc_name}'. Enriching top candidates...")
            for j in raw_target_jobs:
                score, _ = score_job_custom(j["title"], j.get("description", ""), j.get("company", ""), skills)
                # Priority bonus so desired workplace matches get enriched first
                pre_wp = classify_workplace(j.get("title", ""), j.get("location", ""), j.get("description", ""), is_remote_source=(is_worldwide or loc_wp == 'remote'))
                wp_bonus = 0
                if loc_wp == 'remote' and pre_wp == 'Remote':
                    wp_bonus = 50
                elif loc_wp == 'onsite' and pre_wp == 'Onsite':
                    wp_bonus = 50
                elif loc_wp == 'hybrid' and pre_wp == 'Hybrid':
                    wp_bonus = 50
                j["_pre_score"] = score + wp_bonus
            raw_target_jobs.sort(key=lambda x: x.get("_pre_score", 0), reverse=True)
            to_enrich = raw_target_jobs[:15]
            remaining = raw_target_jobs[15:35]

            target_jobs = []
            with ThreadPoolExecutor(max_workers=6) as executor:
                enriched_futs = [executor.submit(enrich_linkedin_job, j) for j in to_enrich]
                for fut in as_completed(enriched_futs):
                    try:
                        job = fut.result()
                        score, reason = score_job_custom(job["title"], job.get("description", ""), job.get("company", ""), skills)
                        exp = extract_experience(job["title"], job.get("description", ""))
                        remote_st = classify_workplace(job["title"], job["location"], job.get("description", ""), is_remote_source=(is_worldwide or loc_wp == 'remote'))

                        if loc_wp == 'onsite' and remote_st != 'Onsite':
                            continue
                        elif loc_wp == 'hybrid' and remote_st != 'Hybrid':
                            continue
                        elif loc_wp == 'remote' and remote_st != 'Remote':
                            continue

                        raw_loc = (job.get("location") or "").strip()
                        if is_worldwide:
                            if not raw_loc or raw_loc.lower() in ("worldwide", "remote", "anywhere"):
                                loc_display = "Worldwide (Remote)"
                            elif "worldwide" not in raw_loc.lower() and "remote" not in raw_loc.lower():
                                loc_display = f"Worldwide (Remote) · {raw_loc}"
                            else:
                                loc_display = raw_loc
                        elif loc_wp == 'remote':
                            if not raw_loc:
                                loc_display = f"{loc_name} (Remote)"
                            elif "remote" not in raw_loc.lower():
                                loc_display = f"{raw_loc} (Remote)"
                            else:
                                loc_display = raw_loc
                        elif loc_wp == 'hybrid':
                            if not raw_loc:
                                loc_display = f"{loc_name} (Hybrid)"
                            elif "hybrid" not in raw_loc.lower():
                                loc_display = f"{raw_loc} (Hybrid)"
                            else:
                                loc_display = raw_loc
                        else:
                            loc_display = raw_loc or loc_name

                        target_jobs.append({
                            "title": job["title"],
                            "company": job["company"],
                            "location": loc_display,
                            "date_posted": format_date_str(job.get("date_posted")),
                            "score": score,
                            "reason": reason,
                            "remote_status": remote_st,
                            "experience": exp,
                            "link": normalize_linkedin_url(job.get("link"), job.get("job_id")),
                            "job_id": job.get("job_id", ""),
                            "source": f"LinkedIn ({loc_name})",
                            "target_location": loc_name,
                            "workplace_filter": loc_wp,
                        })
                    except Exception as e:
                        print(f"Error enriching job for {loc_name}: {e}")

            for job in remaining:
                score, reason = score_job_custom(job["title"], job.get("description", ""), job.get("company", ""), skills)
                exp = extract_experience(job["title"], job.get("description", ""))
                remote_st = classify_workplace(job["title"], job["location"], job.get("description", ""), is_remote_source=(is_worldwide or loc_wp == 'remote'))

                if loc_wp == 'onsite' and remote_st != 'Onsite':
                    continue
                elif loc_wp == 'hybrid' and remote_st != 'Hybrid':
                    continue
                elif loc_wp == 'remote' and remote_st != 'Remote':
                    continue

                raw_loc = (job.get("location") or "").strip()
                if is_worldwide:
                    if not raw_loc or raw_loc.lower() in ("worldwide", "remote", "anywhere"):
                        loc_display = "Worldwide (Remote)"
                    elif "worldwide" not in raw_loc.lower() and "remote" not in raw_loc.lower():
                        loc_display = f"Worldwide (Remote) · {raw_loc}"
                    else:
                        loc_display = raw_loc
                elif loc_wp == 'remote':
                    if not raw_loc:
                        loc_display = f"{loc_name} (Remote)"
                    elif "remote" not in raw_loc.lower():
                        loc_display = f"{raw_loc} (Remote)"
                    else:
                        loc_display = raw_loc
                elif loc_wp == 'hybrid':
                    if not raw_loc:
                        loc_display = f"{loc_name} (Hybrid)"
                    elif "hybrid" not in raw_loc.lower():
                        loc_display = f"{raw_loc} (Hybrid)"
                    else:
                        loc_display = raw_loc
                else:
                    loc_display = raw_loc or loc_name

                target_jobs.append({
                    "title": job["title"],
                    "company": job["company"],
                    "location": loc_display,
                    "date_posted": format_date_str(job.get("date_posted")),
                    "score": score,
                    "reason": reason,
                    "remote_status": remote_st,
                    "experience": exp,
                    "link": normalize_linkedin_url(job.get("link"), job.get("job_id")),
                    "job_id": job.get("job_id", ""),
                    "source": f"LinkedIn ({loc_name})",
                    "target_location": loc_name,
                    "workplace_filter": loc_wp,
                })

            target_jobs.sort(key=lambda x: x["score"], reverse=True)
            print(f">> Total scored jobs for '{loc_name}': {len(target_jobs)}")
            return loc_name, target_jobs, len(raw_target_jobs)

        total_raw_scraped = 0
        jobs_by_target = {}

        # Parallel scraping across location targets for 2x faster results
        with ThreadPoolExecutor(max_workers=max(len(location_targets), 1)) as target_executor:
            futs = [target_executor.submit(search_single_target, t) for t in location_targets]
            for fut in as_completed(futs):
                loc_name, t_jobs, raw_count = fut.result()
                jobs_by_target[loc_name] = t_jobs
                total_raw_scraped += raw_count
                # Register canonical keys for robust tab lookup
                if is_worldwide_location(loc_name):
                    jobs_by_target["Worldwide"] = t_jobs
                    jobs_by_target["Worldwide (Remote)"] = t_jobs
                    jobs_by_target["world wide remote"] = t_jobs
                    jobs_by_target["global remote"] = t_jobs
                    jobs_by_target["remote"] = t_jobs

        top_jobs_by_target = {}
        all_top = []
        for target in location_targets:
            loc = target["location"]
            top_jobs_by_target[loc] = jobs_by_target.get(loc, [])[:top_count]
            all_top.extend(top_jobs_by_target[loc])
            if is_worldwide_location(loc):
                top_jobs_by_target["Worldwide"] = top_jobs_by_target[loc]
                top_jobs_by_target["Worldwide (Remote)"] = top_jobs_by_target[loc]
                top_jobs_by_target["world wide remote"] = top_jobs_by_target[loc]
                top_jobs_by_target["global remote"] = top_jobs_by_target[loc]
                top_jobs_by_target["remote"] = top_jobs_by_target[loc]

        all_top.sort(key=lambda x: x["score"], reverse=True)

        # Backwards compatibility partitions
        primary_local_jobs = []
        primary_remote_jobs = []
        for j in all_top:
            if j.get("target_location", "").lower() in ("worldwide", "global", "remote") or j.get("remote_status") == "Remote":
                primary_remote_jobs.append(j)
            else:
                primary_local_jobs.append(j)

        # Generate AI career summary
        ai_summary = None
        if GEMINI_API_KEY and all_top:
            try:
                ai_summary = generate_ai_summary(all_top, profile)
            except Exception:
                pass

        # Prepare summary label for locations
        targets_label = ", ".join([f"{t['location']} ({t['workplace'].title()})" for t in location_targets])
        result_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        timeframe_label = f"Past {days} Days" if days > 1 else "Past 24 Hours"

        search_results_store[result_id] = {
            "bangladesh_jobs": primary_local_jobs,
            "local_jobs": primary_local_jobs,
            "remote_jobs": primary_remote_jobs,
            "jobs_by_location": top_jobs_by_target,
            "location_targets": location_targets,
            "location_label": targets_label,
            "timeframe": timeframe_label,
        }

        print(f"\n>> Multi-target search complete: {len(all_top)} total jobs across {len(location_targets)} locations ({targets_label})")

        return jsonify({
            "success": True,
            "result_id": result_id,
            "all_jobs": all_top,
            "jobs_by_location": top_jobs_by_target,
            "location_targets": [
                {
                    "location": t["location"],
                    "workplace": t["workplace"],
                    "count": len(top_jobs_by_target.get(t["location"], []))
                }
                for t in location_targets
            ],
            "bangladesh_jobs": primary_local_jobs,  # Backwards compatibility
            "local_jobs": primary_local_jobs,
            "remote_jobs": primary_remote_jobs,
            "location_label": targets_label,
            "timeframe": timeframe_label,
            "stats": {
                "total_scraped": total_raw_scraped,
                "total_selected": len(all_top),
                "total_bd_selected": len(primary_local_jobs),
                "total_remote_selected": len(primary_remote_jobs),
                "avg_score": round(sum(j["score"] for j in all_top) / len(all_top), 1) if all_top else 0,
                "high_matches": sum(1 for j in all_top if j["score"] >= 60),
                "per_location": {t["location"]: len(top_jobs_by_target.get(t["location"], [])) for t in location_targets}
            },
            "ai_summary": ai_summary,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/download-excel', methods=['POST'])
def download_excel():
    """Generate and download formatted Excel file with sections for each target location."""
    data = request.json or {}
    result_id = data.get('result_id')

    sections_data = []
    timeframe_label = "Past Week"
    targets_label = "Job Matches"

    if result_id and result_id in search_results_store:
        stored = search_results_store[result_id]
        timeframe_label = stored.get("timeframe", "Past Week")
        targets_label = stored.get("location_label", "All Targets")
        jobs_by_loc = stored.get("jobs_by_location", {})
        loc_targets = stored.get("location_targets", [])

        if jobs_by_loc:
            for t in loc_targets:
                loc = t["location"]
                wp = t.get("workplace", "all")
                wp_str = f" ({wp.title()})" if wp != "all" else ""
                icon = "🌍" if is_worldwide_location(loc) else "📍"
                sections_data.append({
                    "title": f"{icon} {loc}{wp_str} Jobs",
                    "jobs": jobs_by_loc.get(loc, [])
                })
        else:
            bd_jobs = stored.get("bangladesh_jobs", [])
            remote_jobs = stored.get("remote_jobs", [])
            sections_data = [
                {"title": f"📍 {targets_label} Jobs", "jobs": bd_jobs},
                {"title": "🌍 Remote Worldwide Jobs", "jobs": remote_jobs},
            ]
    else:
        jobs_by_loc = data.get("jobs_by_location", {})
        loc_targets = data.get("location_targets", [])
        timeframe_label = data.get("timeframe", "Past Week")
        targets_label = data.get("location_label", "Jobs")

        if jobs_by_loc and loc_targets:
            for t in loc_targets:
                loc = t["location"]
                wp = t.get("workplace", "all")
                wp_str = f" ({wp.title()})" if wp != "all" else ""
                icon = "🌍" if is_worldwide_location(loc) else "📍"
                sections_data.append({
                    "title": f"{icon} {loc}{wp_str} Jobs",
                    "jobs": jobs_by_loc.get(loc, [])
                })
        else:
            bd_jobs = data.get('bangladesh_jobs', [])
            remote_jobs = data.get('remote_jobs', [])
            sections_data = [
                {"title": f"📍 {targets_label} Jobs", "jobs": bd_jobs},
                {"title": "🌍 Remote Worldwide Jobs", "jobs": remote_jobs},
            ]

    # Filter out empty sections
    sections_data = [s for s in sections_data if s.get("jobs")]
    if not sections_data:
        return jsonify({"error": "No job data available for export"}), 400

    try:
        output_path = write_excel([], [], timeframe_label=timeframe_label, location_label=targets_label, sections_data=sections_data)

        import io
        buffer = io.BytesIO()
        with open(output_path, 'rb') as f:
            buffer.write(f.read())
        buffer.seek(0)

        today_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"Job_Matches_{today_str}.xlsx"

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("⚡ JobPulse AI — API Server")
    print("=" * 60)
    print(f"  Gemini API: {'✅ Configured' if GEMINI_API_KEY else '❌ NOT configured'}")
    print(f"  Endpoints:")
    print(f"    GET  /api/health")
    print(f"    POST /api/upload-cv")
    print(f"    POST /api/search")
    print(f"    POST /api/download-excel")
    print(f"  Server: http://localhost:5000")
    app.run(debug=False, port=5000, host='0.0.0.0', threaded=True)

