from playwright.sync_api import sync_playwright

def run():
    print("LOG: Starting...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="trello_auth.json")
        page = context.new_page()
        page.goto("https://trello.com/b/0DGPOFgz/asset-tracker")
        page.wait_for_selector('[data-testid="card-name"]', timeout=30000)
        
        card = page.locator('[data-testid="card-name"]').filter(has_text="Macbook Pro").first
        card.click()
        page.wait_for_timeout(5000)
        
        text = page.locator('body').inner_text()
        print(f"RES: Attachment: {'Attachment' in text}")
        print(f"RES: Cover: {'Cover' in text}")
        browser.close()

if __name__ == "__main__":
    run()
