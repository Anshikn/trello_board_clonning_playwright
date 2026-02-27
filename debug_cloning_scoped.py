import json
import time
import sys
from playwright.sync_api import sync_playwright

SOURCE_BOARD_URL = "https://trello.com/b/0DGPOFgz/asset-tracker"

def run():
    print("STDOUT CHECK")
    sys.stdout.flush()
    with sync_playwright() as p:
        print("PLAYWRIGHT START")
        sys.stdout.flush()
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="trello_auth.json")
        page = context.new_page()
        page.goto(SOURCE_BOARD_URL)
        print("NAVIGATED")
        sys.stdout.flush()
        browser.close()

if __name__ == "__main__":
    run()
