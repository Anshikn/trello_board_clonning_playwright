import json
import time
import sys
from playwright.sync_api import sync_playwright

SOURCE_BOARD_URL = "https://trello.com/b/0DGPOFgz/asset-tracker"

def run():
    print("Starting debug script...")
    sys.stdout.flush()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state="trello_auth.json")
            page = context.new_page()
            
            print(f"Navigating to {SOURCE_BOARD_URL}")
            sys.stdout.flush()
            page.goto(SOURCE_BOARD_URL)
            page.wait_for_selector('[data-testid="card-name"]', timeout=30000)
            
            card_locator = page.locator('[data-testid="card-name"]').filter(has_text="Macbook Pro").first
            print(f"Card found: {card_locator.text_content().strip()}")
            sys.stdout.flush()
            
            card_locator.click(force=True)
            page.get_by_test_id("card-back-name").wait_for(state="visible", timeout=10000)
            print("Modal opened")
            sys.stdout.flush()
            
            dialog = page.get_by_test_id("card-back-name")
            att_section = dialog.locator('[data-testid="attachment-list"]')
            print(f"Attachment section count: {att_section.count()}")
            sys.stdout.flush()
            
            if att_section.count() > 0:
                att_elements = att_section.locator('[data-testid="attachment-thumbnail"]')
                print(f"Attachments found: {att_elements.count()}")
                sys.stdout.flush()
                for a in range(att_elements.count()):
                    print(f"Attachment {a} url: {att_elements.nth(a).get_attribute('href')}")
                    sys.stdout.flush()

            page.screenshot(path="debug_extraction.png")
            print("Finished exploration.")
            sys.stdout.flush()
            browser.close()
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.stdout.flush()

if __name__ == "__main__":
    run()
