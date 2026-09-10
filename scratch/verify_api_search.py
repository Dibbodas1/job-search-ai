import urllib.request
import json
from collections import Counter

url = "http://localhost:5000/api/search"
payload = {
    "locations": [
        {"location": "Bangladesh", "workplace": "onsite"},
        {"location": "Worldwide", "workplace": "remote"}
    ],
    "days": 30,
    "top_count": 25
}

print(">> Sending search request to Flask API...")
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=90) as res:
        data = json.loads(res.read().decode("utf-8"))
        jobs = data.get("all_jobs", [])
        print(f"\n============================================================")
        print(f"SEARCH COMPLETED: {len(jobs)} total jobs returned")
        print(f"============================================================")
        
        counts = Counter(j.get("source", "Unknown") for j in jobs)
        print("\nBreakdown by Source:")
        for src, cnt in counts.most_common():
            print(f"  {src:18}: {cnt} jobs")
            
        print("\nSample Jobs from each source:")
        seen_src = set()
        for j in jobs:
            src = j.get("source", "Unknown")
            if src not in seen_src:
                seen_src.add(src)
                print(f"\n  [{src}]")
                print(f"    Title   : {j.get('title')}")
                print(f"    Company : {j.get('company')}")
                print(f"    Location: {j.get('location')}")
                print(f"    Link    : {j.get('link')}")
                print(f"    Score   : {j.get('score')}")
except Exception as e:
    print("Error querying API:", e)
