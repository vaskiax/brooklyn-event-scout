import asyncio
import httpx
from bs4 import BeautifulSoup

# NYRR Race Calendar Page
URL = "https://www.nyrr.org/run/race-calendar"

async def main():
    print(f"Testing NYRR HTML Fallback: {URL}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0"
    }
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        try:
            resp = await client.get(URL)
            print(f"Status: {resp.status_code}")
            
            # Save debug HTML to see what raw requests get
            with open("nyrr_debug.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
                
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Check for common static elements
            # Often race names are in <h3> or specific classes
            races = soup.find_all(class_="race-name") or soup.find_all(class_="card__title") or soup.find_all("h3")
            
            print(f"Found {len(races)} potential race items in static HTML.")
            for r in races[:5]:
                print(f" - {r.get_text(strip=True)}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
