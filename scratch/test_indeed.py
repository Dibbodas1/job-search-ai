import asyncio
from playwright.async_api import async_playwright

async def test_indeed():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()
        url = "https://www.indeed.com/jobs?q=software+developer&l=Bangladesh"
        print("Navigating to:", url)
        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        await page.wait_for_timeout(3000)
        print("Final URL:", page.url)
        print("Page title:", await page.title())
        content = await page.content()
        print("Content length:", len(content))
        await browser.close()

asyncio.run(test_indeed())
