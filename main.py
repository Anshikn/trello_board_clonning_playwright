import json
from playwright.sync_api import sync_playwright
from config import *
from services.extractor import extract_board
from services.builder import create_board, rebuild_board

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(storage_state="trello_auth.json")
        page = context.new_page()

        page.set_default_timeout(TIMEOUT)

        page.goto(SOURCE_BOARD_URL)
        page.wait_for_load_state("networkidle")

        print("Taking screenshot...")
        page.screenshot(path="screenshot.png", full_page=True)

        print("Extracting board...")
        data = extract_board(page)

        with open("data/board_data.json", "w") as f:
            json.dump(data, f, indent=2)

        print("Creating new board...")
        create_board(page, NEW_BOARD_NAME)

        print("Rebuilding board...")
        rebuild_board(page, data)

        print("Clone complete!")

        browser.close()

if __name__ == "__main__":
    run()
