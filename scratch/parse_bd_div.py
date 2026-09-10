import asyncio
from playwright.async_api import async_playwright
import bs4

async def parse_div_children():
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
        for a in detail_links[6:7]:
            top_div = a.find("div", class_=lambda c: c and "relative" in c)
            for el in top_div.find_all(True):
                c = el.get("class", [])
                t = el.get_text(strip=True)
                if c and t and len(t) < 50:
                    print(f"Tag <{el.name}> class={c}: {t}")
        await browser.close()

asyncio.run(parse_div_children())
