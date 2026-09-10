import asyncio
from playwright.async_api import async_playwright
import bs4

async def parse_single_card():
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
        for a in detail_links[5:8]:
            print("\n================== A TAG ==================")
            print("HREF:", a["href"])
            for child in a.find_all(True, recursive=False):
                print(f"Child <{child.name}> class={child.get('class')}: {child.get_text(strip=True)[:60]}")
            # print all text nodes
            print("Stripped strings:", list(a.stripped_strings)[:8])
        await browser.close()

asyncio.run(parse_single_card())
