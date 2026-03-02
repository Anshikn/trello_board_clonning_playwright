import json
import os
from playwright.sync_api import sync_playwright
from config import *
from services.extractor import extract_board
from services.builder import create_board, rebuild_board

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=500)
        # Create context and start tracing
        context = browser.new_context(storage_state="trello_auth.json")
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        
        page = context.new_page()
        page.set_default_timeout(TIMEOUT)

        try:
            print("Navigating to source board...")
            page.goto(SOURCE_BOARD_URL)
            
            # Wait for board content instead of networkidle
            print("Waiting for board content to load...")
            page.locator('[data-testid="list"]').first.wait_for(state="visible", timeout=30000)

            # Final check to ensure we are logged in
            if "login" in page.url or "signup" in page.url:
                print("Error: Auth state potentially expired. Please re-authenticate.")
                return

            print("Taking initial screenshot...")
            page.screenshot(path="debug_start.png", full_page=True)

            print("Extracting board...")
            data = extract_board(page)

            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            with open("data/board_data.json", "w") as f:
                json.dump(data, f, indent=2)

            print("Creating new board...")
            create_board(page, NEW_BOARD_NAME)

            print("Rebuilding board...")
            rebuild_board(page, data)

            print("Clone complete!")
            
            # Stop tracing and save (optional: only on success if you want, but tracing is good for verification)
            context.tracing.stop(path="trace_success.zip")

        except Exception as e:
            print(f"AN ERROR OCCURRED: {e}")
            # Take a failure screenshot
            try:
                page.screenshot(path="failure_screenshot.png", full_page=True)
                print("Failure screenshot saved as failure_screenshot.png")
                # Save trace on failure
                context.tracing.stop(path="trace_failure.zip")
                print("Error trace saved as trace_failure.zip")
            except:
                pass
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run()
