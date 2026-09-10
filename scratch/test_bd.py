import asyncio
from playwright.async_api import async_playwright
import bs4

async def test_bd():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()
        # Test BDjobs URL
        url = "https://jobs.bdjobs.com/jobsearch.asp?txtsearch=software&fdate=7&Src=0"
        print("Navigating to:", url)
        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        print("Page HTML length:", len(html))
        soup = bs4.BeautifulSoup(html, "html.parser")
        print("Page title:", soup.title.string if soup.title else "No title")
        print("Final URL:", page.url)
        
        # Look for job links
        job_links = soup.find_all("a", href=True)
        job_details_links = [a for a in job_links if "jobdetails" in a["href"].lower()]
        print("Total jobdetails links found:", len(job_details_links))
        for a in job_details_links[:5]:
            print("  Title:", a.get_text(strip=True), "| URL:", a["href"])
            
        await browser.close()

asyncio.run(test_bd())
