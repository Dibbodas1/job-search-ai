import asyncio
from playwright.async_api import async_playwright
import bs4
import json

async def inspect_cards():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()
        # BDjobs search URL
        url = "https://bdjobs.com/h/jobs?txtsearch=developer"
        print("Loading:", url)
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        soup = bs4.BeautifulSoup(html, "html.parser")
        
        cards = soup.find_all("div", class_=lambda c: c and "cardlist-shadow" in c.lower())
        print(f"Cards with cardList-shadow: {len(cards)}")
        
        extracted = []
        for i, card in enumerate(cards[:10]):
            card_info = {}
            # Title
            title_el = card.find("h2") or card.find("h3") or card.find("a", class_=lambda c: c and "title" in c.lower()) or card.find(class_=lambda c: c and "text-title" in c.lower())
            card_info["title"] = title_el.get_text(strip=True) if title_el else ""
            
            # Links
            links = [a["href"] for a in card.find_all("a", href=True)]
            card_info["links"] = links
            
            # Text lines
            text_lines = [t.strip() for t in card.stripped_strings]
            card_info["text_lines"] = text_lines[:8]
            extracted.append(card_info)
            
        with open("scratch/bdjobs_extracted.json", "w", encoding="utf-8") as f:
            json.dump(extracted, f, indent=2, ensure_ascii=False)
            
        print("Saved scratch/bdjobs_extracted.json with", len(extracted), "cards")
        await browser.close()

asyncio.run(inspect_cards())
