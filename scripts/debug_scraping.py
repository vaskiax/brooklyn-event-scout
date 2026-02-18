import asyncio
import httpx

async def main():
    url = "https://www.prospectpark.org/events/"
    print(f"Probing {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, verify=False) as client:
        resp = await client.get(url)
        print(f"Status: {resp.status_code}")
        print(f"Length: {len(resp.text)}")
        print(f"Review: {resp.text[:500]}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    asyncio.run(main())
