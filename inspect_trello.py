from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://trello.com/b/0DGPOFgz/asset-tracker")
    page.wait_for_selector('[data-testid="list"]')
    
    html = page.locator('[data-testid="list"]').first.inner_html()
    with open("list_html.txt", "w") as f:
        f.write(html)
    browser.close()
