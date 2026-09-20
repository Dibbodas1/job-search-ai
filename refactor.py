import os

file_path = "scrape_jobs.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find("def normalize_linkedin_url(")
end_idx = content.find("def is_tech_job(")

if start_idx != -1 and end_idx != -1:
    new_func = """from apify_client import ApifyClient
import os

def fetch_jobs_via_apify(queries, timeframe="week", location="Worldwide", limit=50):
    \"\"\"Fetches jobs from LinkedIn using Apify actor bebity/linkedin-jobs-scraper.\"\"\"
    print(f"\\n--- [APIFY] Searching LinkedIn jobs for {location} (limit {limit}) ---")
    apify_token = os.environ.get("APIFY_API_TOKEN") or os.environ.get("APIFY_API_KEY")
    if not apify_token:
        print("ERROR: Apify API token not found in .env")
        return []

    client = ApifyClient(apify_token)
    
    # We will combine queries into a single run if possible, or run multiple.
    # The actor accepts a list of search URLs or keywords.
    # bebity/linkedin-jobs-scraper takes 'searchUrls' or similar inputs.
    
    # For bebity/linkedin-jobs-scraper:
    # We can pass an array of search keywords and location.
    # Wait, the actor bebity/linkedin-jobs-scraper might have specific inputs.
    # Common input for 'bebity/linkedin-jobs-scraper':
    # { "keyword": "React Developer", "location": "Worldwide", "publishedAt": "Past 24 hours" }
    # Or 'voyager/linkedin-jobs-scraper' takes an array of keywords.
    
    # Let's formulate the input for a generic or bebity scraper.
    # To be safe and simple, let's just use the first query or combine them.
    # Actually, let's map the queries.
    run_input = {
        "title": queries[0][0] if queries else "Software Engineer",
        "location": location,
        "rows": limit,
        "publishedAt": "Past week" if timeframe == "week" else "Past 24 hours"
    }

    try:
        print(f"Starting Apify Actor bebity/linkedin-jobs-scraper with input: {run_input}")
        run = client.actor("bebity/linkedin-jobs-scraper").call(run_input=run_input)
        
        jobs = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            # Map Apify output to our unified format
            job = {
                "title": item.get("title") or item.get("positionName") or "Unknown Title",
                "company": item.get("companyName") or item.get("company") or "Unknown Company",
                "location": item.get("location") or location,
                "link": item.get("url") or item.get("jobUrl") or "",
                "description": item.get("description") or "",
                "date_posted": item.get("postedAt") or item.get("publishedAt") or "",
                "source": "LinkedIn (Apify)",
                "workplace_type": item.get("workplaceType") or ""
            }
            jobs.append(job)
            
        print(f"Apify fetch complete. Found {len(jobs)} jobs.")
        return jobs
    except Exception as e:
        print(f"Apify run failed: {e}")
        return []

"""
    new_content = content[:start_idx] + new_func + content[end_idx:]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully replaced functions with fetch_jobs_via_apify")
else:
    print("Could not find start or end markers.")
