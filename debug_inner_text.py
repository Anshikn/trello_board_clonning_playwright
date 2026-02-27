from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="trello_auth.json")
        page = context.new_page()
        page.goto("https://trello.com/b/0DGPOFgz/asset-tracker", wait_until="networkidle")
        page.wait_for_selector('[data-testid="list"]')
        
        list_loc = page.locator('[data-testid="list"]').first
        print("List found!")
        card_loc = list_loc.locator('[data-testid="card-name"]').first
        print(f"Card count: {card_loc.count()}")
        
        # Check if visible
        print(f"Is card visible? {card_loc.is_visible()}")
        
        try:
            print("Trying inner_text()...")
            text = card_loc.inner_text(timeout=5000)
            print(f"Text: {text}")
        except Exception as e:
            print(f"Error getting inner_text: {e}")
            
        try:
            print("Trying text_content()...")
            text = card_loc.text_content()
            print(f"Text raw: {text}")
        except Exception as e:
            print(f"Error getting text_content: {e}")

        href = card_loc.get_attribute("href")
        print(f"href = {href}")
        
        browser.close()

if __name__ == "__main__":
    run()
