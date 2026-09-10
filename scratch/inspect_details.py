import asyncio
from playwright.async_api import async_playwright
import bs4
import json

async def inspect_details():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()
        url = "https://bdjobs.com/h/jobs?txtsearch=developer"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        html = await page.content()
        soup = bs4.BeautifulSoup(html, "html.parser")
        
        detail_links = soup.find_all("a", href=lambda h: h and "/h/details/" in h)
        print(f"Total details links: {len(detail_links)}")
        
        results = []
        for a in detail_links[:10]:
            title = a.get_text(strip=True)
            href = "https://bdjobs.com" + a["href"] if a["href"].startswith("/") else a["href"]
            
            # Find the job card container: walk up parents
            parent = a.find_parent("div", class_=lambda c: c and any(w in c.lower() for w in ["card", "item", "row", "job", "shadow"]))
            if not parent:
                parent = a.parent.parent
                
            text = " | ".join([s for s in parent.stripped_strings if s != "✖"])
            results.append({
                "title": title,
                "href": href,
                "parent_text": text[:300]
            })
            
        with open("scratch/bdjobs_sample_jobs.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        print("Wrote scratch/bdjobs_sample_jobs.json")
        await browser.close()

asyncio.run(inspect_details())
