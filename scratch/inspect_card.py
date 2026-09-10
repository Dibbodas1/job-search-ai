import asyncio
from playwright.async_api import async_playwright
import bs4

async def inspect_cards():
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
        
        cards = soup.find_all(class_=lambda c: c and "cardlist-shadow" in c.lower())
        print(f"Cards with cardList-shadow: {len(cards)}")
        if not cards:
            cards = soup.find_all("div", class_="card-left")
            print(f"Cards with card-left: {len(cards)}")
            
        for i, card in enumerate(cards[:5]):
            print(f"\n--- CARD {i+1} ---")
            print("Card text:", card.get_text(separator=" | ", strip=True)[:250])
            links = card.find_all("a", href=True)
            for l in links:
                print("  Link:", l["href"], "->", l.get_text(strip=True)[:40])
                
        await browser.close()

asyncio.run(inspect_cards())
