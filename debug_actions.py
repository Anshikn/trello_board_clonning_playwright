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
        dialog = page.get_by_test_id("card-back-name")
        
        # LABEL
        page.get_by_test_id("card-back-add-to-card-button").click(force=True)
        page.wait_for_timeout(1000)
        page.locator('button:has-text("Labels")').first.click(force=True)
        page.wait_for_timeout(1000)
        
        search = page.locator('input[placeholder*="Search labels"], input[placeholder="Search"], [data-testid="labels-search-input"]').first
        search.fill("MyNewTestLabel")
        page.wait_for_timeout(1500)
        
        page.screenshot(path="debug_labels_1_search.png")
        
        create_btn = page.locator('button:has-text("Create a new label")')
        create_btn.first.click(force=True)
        page.wait_for_timeout(1000)
        
        page.screenshot(path="debug_labels_2_create_form.png")
        
        name_in = page.locator('label:has-text("Title")').locator("..").locator("input[type='text']").first
        if name_in.count() == 0:
            name_in = page.locator('input[type="text"]').last
        if name_in.count() > 0:
            name_in.fill("MyNewTestLabel")
        page.wait_for_timeout(500)
        
        # click create
        submit_btn = page.get_by_test_id("create-label-submit-button")
        if submit_btn.count() == 0:
            submit_btn = page.locator('button:has-text("Create")')
        submit_btn.first.click(force=True)
        page.wait_for_timeout(1500)
        
        page.screenshot(path="debug_labels_3_after_submit.png")
        
        page.keyboard.press("Escape")
        page.wait_for_timeout(1000)

        # CHECKLIST
        checklist_btn = dialog.locator('button:has([data-testid="ChecklistIcon"])').first
        if checklist_btn.count() == 0:
            checklist_btn = dialog.locator('button:has-text("Checklist")').first
        checklist_btn.click(force=True)
        page.wait_for_timeout(1500)
        page.screenshot(path="debug_checklist_1_popover.png")
        
        add_checklist = page.locator('[data-testid="checklist-add-button"]')
        if add_checklist.count() > 0:
            add_checklist.click(force=True)
            page.wait_for_timeout(1500)
        page.screenshot(path="debug_checklist_2_after_add.png")
        
        browser.close()

if __name__ == "__main__":
    run()
