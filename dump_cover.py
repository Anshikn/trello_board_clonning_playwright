import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="trello_auth.json")
        page = context.new_page()
        page.goto("https://trello.com/")
        
        # Open the first board
        board_link = page.locator('.board-tile').first
        if board_link.count() > 0:
            board_link.click()
            page.wait_for_timeout(3000)
            
            card = page.locator('[data-testid="card-name"]').first
            card.click()
            page.wait_for_timeout(2000)
            
            cover_btn = page.locator('[data-testid="card-back-cover-button"]')
            if cover_btn.count() > 0:
                cover_btn.click()
                page.wait_for_timeout(2000)
                
                popover = page.locator('[data-testid="popover-container"]').last
                if popover.count() > 0:
                    with open("cover_popover.html", "w") as f:
                        f.write(popover.inner_html())
                    page.screenshot(path="cover_popover_view.png")
                    print("Dumped cover popover")
                
        browser.close()

if __name__ == "__main__":
    run()
