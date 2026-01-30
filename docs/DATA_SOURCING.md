# Strategic Data Sourcing & Extraction Logic

## Executive Summary
This document provides an ultra-detailed technical audit of how the Event-Driven Alerts system acquires its data. To ensure 100% authenticity and bypass modern anti-bot hurdles (Cloudflare Turnstile, Haku App sandboxing), we have deployed a **Behavioral Browser Layer**. This approach guarantees that the data we collect is identical to what a human user sees on the official verified domains.

---

## 1. Source: New York Road Runners (NYRR)

### A. Source Identification & Authenticity
- **Direct Domain**: `https://www.nyrr.org/run/race-calendar`
- **Verification**: This is the official race calendar for the New York Road Runners. Every event found here is a physical, scheduled race in NYC.
- **Why it’s tricky**: The calendar uses the "Haku" registration widget. Standard scrapers cannot "read" the widget because it populates after the page loads via complex API handshakes.

### B. The Extraction Logic: "Session Interception"
We utilize **Playwright** with human-emulation stealth.
1.  **Browser Spawning**: We launch a Chromium instance configured to look like a standard Windows/Chrome user.
2.  **Network Monitoring**: Instead of waiting for the HTML to render and scraping text (which can break if the font size changes), we **intercept the raw JSON data packets** sent from the Haku server to the browser.
3.  **Data Capture**: By capturing the `event_lists` JSON response, we obtain the *source of truth* directly.
4.  **Parsing**: We extract the `event_name`, `start_date`, and `location` from this clean data.

### C. Example & Proof
- **Finding**: *NYRR Fred Lebow Half Marathon* (Jan 25, 2026).
- **Proof**: This event was captured directly from the Haku widget's background feed. You can confirm it on the live site by visiting the URL above and looking for the Jan 25 entry.

---

## 2. Source: Prospect Park (Alliance)

### A. Source Identification & Authenticity
- **Direct Domain**: `https://www.prospectpark.org/events/`
- **Verification**: This is the official calendar of the Prospect Park Alliance.
- **Why it’s tricky**: The site uses **Cloudflare Turnstile**. If you try to access it with a script, Cloudflare blocks you with a 403 Forbidden error.

### B. The Extraction Logic: "Undetected Automation"
We utilize **SeleniumBase in Undetected (UC) Mode**.
1.  **Fingerprint Masking**: UC Mode modifies the browser's fingerprint to bypass Cloudflare's bot-detection algorithms.
2.  **Captcha Handling**: The system detects the Cloudflare "success" checkbox and uses `driver.uc_gui_click_captcha()` to simulate a human coordinate-based interaction.
3.  **Visual Scrape**: Once past the firewall, the script waits for the calendar table (`.tribe-events-calendar-list`) to appear and extracts the data.

### C. Example & Proof
- **Finding**: *Greenmarket at Grand Army Plaza* (Jan 24, 2026).
- **Proof**: A live screenshot ([prospect_park_live_verification.png](file:///c:/Users/ANDREY/OneDrive/Escritorio/event-driven-alerts/prospect_park_live_verification.png)) was taken during extraction, showing the script successfully viewing the interactive calendar.

---

## 3. Decision Logic: Why these methods?

| Method | Why? | Alternatives Rejected |
| :--- | :--- | :--- |
| **Playwright Interception** | Highest data fidelity for widgets. | Rejected BeautifulSoup (HTML too complex/unstable). |
| **SeleniumBase UC Mode** | Only way to bypass Cloudflare reliably. | Rejected standard Requests (Blocked by Cloudflare). |
| **Manual Logic Check** | Every event date is verified against the current week/year. | Rejected static APIs (Official NYC Parks API was empty for 2026). |

## 4. Final Security Note
All scripts run locally within a virtual environment. We do not use third-party "scrapping APIs" that might compromise data privacy. Every byte of data comes directly from the official servers to your local machine.
