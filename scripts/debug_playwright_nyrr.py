import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        try:
            print("Navigating to NYRR...")
            await page.goto("https://www.nyrr.org/run/race-calendar", timeout=60000, wait_until="domcontentloaded")
            print("Waiting for network idle...")
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass
            
            content = await page.content()
            with open("nyrr_playwright_dump.html", "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Dumped {len(content)} types.")
            
            # Screenshot for good measure (if I could see it, but I can't)
            # await page.screenshot(path="nyrr_debug.png")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
