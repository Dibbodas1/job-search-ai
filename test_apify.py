import os
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

apify_token = os.environ.get("APIFY_API_TOKEN") or os.environ.get("APIFY_API_KEY")
print(f"Token present: {bool(apify_token)}")

client = ApifyClient(apify_token)

run_input = {
    "title": "Software Engineer",
    "location": "United States",
    "rows": 10,
    "publishedAt": "r86400"
}

print(f"Starting Apify Actor bebity/linkedin-jobs-scraper with input: {run_input}")
try:
    run = client.actor("bebity/linkedin-jobs-scraper").call(run_input=run_input)
    print("Run status:", run.status)
    jobs = []
    for item in client.dataset(run.default_dataset_id).iterate_items():
        jobs.append(item)
    print(f"Apify fetch complete. Found {len(jobs)} jobs.")
    if jobs:
        print("Sample:", jobs[0])
except Exception as e:
    print(f"Apify run failed: {e}")
