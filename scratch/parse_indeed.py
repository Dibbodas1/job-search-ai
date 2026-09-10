import asyncio
from playwright.async_api import async_playwright
import bs4

async def parse_indeed():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()
        url = "https://www.indeed.com/jobs?q=software+developer&l=Bangladesh"
        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        soup = bs4.BeautifulSoup(html, "html.parser")
        
        # Check actual cards
        cards = soup.select("div.job_seen_beacon, .jobsearch-ResultsList > li, div.cardOutline")
        print(f"Indeed cards found: {len(cards)}")
        
        jobs = []
        for card in cards:
            title_el = card.select_one("h2.jobTitle span, h2.jobTitle a, a[data-jk]")
            comp_el = card.select_one("[data-testid='company-name'], .companyName")
            loc_el = card.select_one("[data-testid='text-location'], .companyLocation")
            link_el = card.select_one("h2.jobTitle a, a[data-jk]")
            
            if title_el and link_el:
                title = title_el.get_text(strip=True)
                comp = comp_el.get_text(strip=True) if comp_el else "Confidential"
                loc = loc_el.get_text(strip=True) if loc_el else "Bangladesh"
                jk = link_el.get("data-jk") or ""
                href = f"https://www.indeed.com/viewjob?jk={jk}" if jk else link_el.get("href", "")
                if href.startswith("/"):
                    href = "https://www.indeed.com" + href
                jobs.append({"title": title, "company": comp, "location": loc, "link": href})
                
        print(f"Extracted {len(jobs)} jobs from Indeed:")
        for j in jobs[:5]:
            print(" ", j["title"], "|", j["company"], "|", j["location"], "|", j["link"])
            
        await browser.close()

asyncio.run(parse_indeed())
