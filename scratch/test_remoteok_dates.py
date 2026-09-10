import requests
from scrape_jobs import is_within_timeframe, HEADERS

resp = requests.get("https://remoteok.com/api?tag=javascript", headers=HEADERS, timeout=15)
data = resp.json()
valid = 0
for item in data:
    if isinstance(item, dict) and item.get("position"):
        raw_date = item.get("date") or item.get("epoch")
        in_tf = is_within_timeframe(raw_date, max_hours=192)
        if in_tf:
            valid += 1
        print("pos:", item.get("position")[:30], "| date:", raw_date, "| in_tf:", in_tf)
print(f"Total valid in 192 hours: {valid}")
