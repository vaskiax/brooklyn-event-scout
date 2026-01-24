import asyncio
import httpx
from bs4 import BeautifulSoup

RSS_URL = "https://www.nycgovparks.org/parks/prospect-park/events/rss"

async def main():
    print(f"Fetching: {RSS_URL}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0"
    }
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        resp = await client.get(RSS_URL)
        print(f"Status: {resp.status_code}")
        print(f"Content Length: {len(resp.content)}")
        
        # Test 1: XML Parser
        soup_xml = BeautifulSoup(resp.content, "xml")
        items_xml = soup_xml.find_all("item")
        print(f"Items found with 'xml' parser: {len(items_xml)}")
        
        # Test 2: HTML Parser
        soup_html = BeautifulSoup(resp.content, "html.parser")
        items_html = soup_html.find_all("item")
        print(f"Items found with 'html.parser': {len(items_html)}")
        
        if len(items_xml) == 0 and len(items_html) == 0:
            print("DUMPING FIRST 500 CHARS:")
            print(resp.content[:500])

if __name__ == "__main__":
    asyncio.run(main())
