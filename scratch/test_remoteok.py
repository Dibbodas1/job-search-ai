import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

url = "https://remoteok.com/api"
print("Fetching:", url)
try:
    resp = requests.get(url, headers=headers, timeout=15)
    print("Status code:", resp.status_code)
    print("Content type:", resp.headers.get("content-type"))
    print("Text length:", len(resp.text))
    if resp.status_code == 200:
        data = resp.json()
        print("Total items:", len(data))
        if len(data) > 1:
            print("Sample item 1:", data[1].get("position"), "| date:", data[1].get("date"), "| epoch:", data[1].get("epoch"))
            print("Sample tags:", data[1].get("tags"))
    else:
        print("Sample body:", resp.text[:200])
except Exception as e:
    print("Error:", e)
