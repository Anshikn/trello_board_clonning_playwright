from playwright.sync_api import sync_playwright
from config import SOURCE_BOARD_URL
import json

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="trello_auth.json")
        page = context.new_page()
        page.goto(SOURCE_BOARD_URL)
        page.wait_for_load_state("networkidle")

        # Open Macbook Pro
        page.locator('[data-testid="card-name"]').filter(has_text="Macbook Pro").first.click()
        page.wait_for_selector('[data-testid="card-back-name"]')
        
        # Click sidebar Add button and then Labels (more reliable?)
        page.get_by_test_id("card-back-add-to-card-button").click()
        page.wait_for_timeout(1000)
        page.locator('button:has-text("Labels")').first.click()
        page.wait_for_timeout(1000)
        
        # Search something to show create
        search = page.locator('input[placeholder*="Search labels"], input[placeholder="Search"], [data-testid="labels-search-input"]').first
        if search.count() == 0:
            search = page.get_by_placeholder("Search labels...")
            
        search.fill("Does Not Exist")
        page.wait_for_timeout(1000)
        
        # Click Create a new label
        create_btn = page.locator('button:has-text("Create a new label")')
        if create_btn.count() > 0:
            create_btn.first.click()
            page.wait_for_timeout(1000)
            
            # Print html of popover container now
            popover = page.locator('[data-testid="popover-container"], [role="dialog"]').last
            html = popover.evaluate("el => el.outerHTML")
            with open("create_label_popover.html", "w") as f:
                f.write(html)
            page.screenshot(path="create_label_view.png")
            print("Successfully dumped create label view.")
        else:
            print("Create button not found!")
        browser.close()

if __name__ == "__main__":
    run()
