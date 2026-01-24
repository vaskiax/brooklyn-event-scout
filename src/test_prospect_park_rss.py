import asyncio
import httpx
from bs4 import BeautifulSoup

def parse_rss(xml_content):
    soup = BeautifulSoup(xml_content, 'xml')
    items = soup.find_all('item')
    print(f"Found {len(items)} RSS items.")
    for item in items:
        title = item.find('title').get_text() if item.find('title') else "No Title"
        link = item.find('link').get_text() if item.find('link') else "No Link"
        print(f" - {title}: {link}")

async def main():
    print("=== Testing Prospect Park RSS Feeds ===")
    
    urls = [
        "https://www.nycgovparks.org/parks/prospect-park/events/rss",
        "https://www.nycgovparks.org/xml/events_300_rss.xml" 
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=10.0) as client:
        for url in urls:
            print(f"\nChecking: {url}")
            try:
                resp = await client.get(url)
                print(f"Status: {resp.status_code}")
                # Check if it's XML/RSS
                if resp.status_code == 200:
                    if "xml" in resp.headers.get("content-type", "") or resp.text.strip().startswith("<?xml"):
                        print("SUCCESS: Found RSS Feed!")
                        parse_rss(resp.content)
                    elif "Just a moment" in resp.text:
                        print("Result: Blocked by Cloudflare.")
                    else:
                        print(f"Result: Content type {resp.headers.get('content-type')}, length {len(resp.text)}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
