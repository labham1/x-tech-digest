"""One-time interactive setup script to log into X and save your session.

Run this script once:
    python setup_auth.py

It will open a visible Chromium browser window where you can log in securely.
Once you see your home feed, press Enter in the terminal to save your session.
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from config.settings import SESSION_FILE, BASE_DIR
from extractor.session import is_session_available


def main():
    print("=" * 65)
    print("      X (Twitter) Session Setup Utility (100% Free)      ")
    print("=" * 65)
    print("\nThis script will launch a visible browser window.")
    print("1. Log in to your X (Twitter) account as usual.")
    print("2. Complete any 2FA or verification prompt.")
    print("3. Once your home timeline appears, return to this terminal.")
    print("4. Press Enter to save your session cookies for automated runs.\n")

    input("Press Enter to launch the browser...")

    with sync_playwright() as p:
        # Launch non-headless browser with anti-detection flags
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("\nOpening X login page...")
        try:
            # Use domcontentloaded and 60s timeout so background tracking scripts don't hang execution
            page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=60000)
        except Exception as err:
            # Even if full page load times out, the browser window stays open for the user
            print(f"Browser ready (Notice: {err})")

        print("\nWaiting for you to log in...")
        print(">> In the opened browser window, log in to your X account.")
        print(">> If the page didn't load, you can also navigate to https://x.com/login directly.")
        print(">> Once you see your home feed / timeline, return here and press Enter.")

        input("\n[Press Enter here AFTER you are logged in to X] ")

        # Save cookies & local storage
        print(f"\nSaving session state to {SESSION_FILE}...")
        context.storage_state(path=str(SESSION_FILE))

        browser.close()

    if is_session_available(SESSION_FILE):
        print("\n" + "=" * 65)
        print("✅ SUCCESS: Your X session has been saved successfully!")
        print(f"File location: {SESSION_FILE}")
        print("The daily scraper can now run headlessly without prompting for login.")
        print("=" * 65)
    else:
        print("\n" + "=" * 65)
        print("⚠️ WARNING: Session file was saved, but auth cookies were not detected.")
        print("Please ensure you were fully logged into your feed before pressing Enter.")
        print("You can run 'python setup_auth.py' again anytime.")
        print("=" * 65)


if __name__ == "__main__":
    main()
