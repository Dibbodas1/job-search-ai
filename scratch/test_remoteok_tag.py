import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

for tag in ["javascript", "react", "engineer", "dev", ""]:
    url = f"https://remoteok.com/api?tag={tag}" if tag else "https://remoteok.com/api"
    resp = requests.get(url, headers=headers, timeout=15)
    data = resp.json() if resp.status_code == 200 else []
    print(f"Tag '{tag}': status {resp.status_code}, items: {len(data)}")
    if len(data) > 1:
        tech_titles = [d.get("position") for d in data[1:6] if isinstance(d, dict)]
        print("  Sample positions:", tech_titles[:3])
