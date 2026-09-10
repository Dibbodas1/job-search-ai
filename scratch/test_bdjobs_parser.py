import asyncio
from playwright.async_api import async_playwright
import bs4
import re

async def test_bdjobs_parser(keyword):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()
        import urllib.parse
        url = f"https://bdjobs.com/h/jobs?txtsearch={urllib.parse.quote(keyword)}"
        print(f"Testing BDjobs search for: {keyword} -> {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        try:
            await page.wait_for_selector("a[href*='/h/details/']", timeout=12000)
        except Exception:
            pass
        await page.wait_for_timeout(2000)
        html = await page.content()
        soup = bs4.BeautifulSoup(html, "html.parser")
        
        detail_links = soup.find_all("a", href=lambda h: h and "/h/details/" in h)
        print(f"Found {len(detail_links)} detail links for '{keyword}'")
        
        jobs = []
        seen_urls = set()
        for a in detail_links:
            raw_href = a["href"]
            if raw_href in seen_urls:
                continue
            seen_urls.add(raw_href)
            
            href = "https://bdjobs.com" + raw_href if raw_href.startswith("/") else raw_href
            
            # Extract title and company from the card
            paragraphs = a.find_all("p")
            title = paragraphs[0].get_text(strip=True) if len(paragraphs) > 0 else ""
            comp = paragraphs[1].get_text(strip=True) if len(paragraphs) > 1 else "Confidential"
            
            # Clean title formatting if joined
            title = re.sub(r'([a-z])([A-Z])', r'\1 \2', title).strip()
            
            # Location
            loc = "Bangladesh"
            for p_tag in paragraphs[2:]:
                t = p_tag.get_text(strip=True)
                if any(c in t.lower() for c in ["dhaka", "chittagong", "sylhet", "mirpur", "gulshan", "banani", "uttara", "bangladesh", "mohakhali", "dhanmondi", "tejgaon", "khulna", "rajshahi"]):
                    loc = t
                    break
                    
            # Experience
            exp_el = a.find(class_="exp-test")
            exp = exp_el.get_text(strip=True) if exp_el else "1-3 yrs"
            
            if title:
                jobs.append({"title": title, "company": comp, "location": loc, "experience": exp, "link": href})
                
        for j in jobs[:6]:
            print(f"  -> {j['title']} | {j['company']} | {j['location']} | {j['link']}")
            
        await browser.close()
        return jobs

asyncio.run(test_bdjobs_parser("react"))
asyncio.run(test_bdjobs_parser("software engineer"))
