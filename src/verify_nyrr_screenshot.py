from playwright.sync_api import sync_playwright

def verify_nyrr():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating to NYRR Calendar...")
        page.goto("https://www.nyrr.org/run/race-calendar")
        page.wait_for_selector(".haku_widget_event_list", timeout=30000)
        print("Taking screenshot...")
        page.screenshot(path="nyrr_live_verification.png", full_page=True)
        browser.close()

if __name__ == "__main__":
    verify_nyrr()
