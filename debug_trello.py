from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="trello_auth.json")
        page = context.new_page()
        page.goto("https://trello.com/b/0DGPOFgz/asset-tracker", wait_until="networkidle")
        page.wait_for_selector('[data-testid="list"]')
        
        list_html = page.locator('[data-testid="list"]').first.inner_html()
        with open("debug_list.html", "w") as f:
            f.write(list_html)
        
        browser.close()

if __name__ == "__main__":
    run()
