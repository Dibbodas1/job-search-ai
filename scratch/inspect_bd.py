import asyncio
from playwright.async_api import async_playwright
import bs4
import re

async def inspect_bd():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()
        url = "https://bdjobs.com/h/jobs?txtsearch=software&fdate=7"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        html = await page.content()
        soup = bs4.BeautifulSoup(html, "html.parser")
        
        # Look for cards or links with job
        all_links = soup.find_all("a", href=True)
        job_links = [a for a in all_links if "/job/" in a["href"] or "jobdetails" in a["href"] or "/jobs/" in a["href"]]
        print(f"Job links found: {len(job_links)}")
        for a in job_links[:10]:
            print("  HREF:", a["href"], "| TEXT:", a.get_text(strip=True)[:50])
            
        # Check text classes
        classes = set()
        for tag in soup.find_all(class_=True):
            for c in tag["class"]:
                if any(w in c.lower() for w in ["job", "title", "card", "item", "list"]):
                    classes.add(c)
        print("Relevant CSS classes:", sorted(list(classes))[:25])
        await browser.close()

asyncio.run(inspect_bd())
