from playwright.sync_api import sync_playwright
import time

def reauth():
    with sync_playwright() as p:
        # Launch browser in non-headless mode so user can interact
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("\n" + "="*50)
        print("TRELLO RE-AUTHENTICATION")
        print("="*50)
        print("1. A browser window will open.")
        print("2. Please log in to your Trello account manually.")
        print("3. Once you see your boards or dashboard, this script will")
        print("   automatically detect it and save your session.")
        print("="*50 + "\n")
        
        page.goto("https://trello.com/login")
        
        # Wait for user to be logged in
        print("Waiting for login...")
        
        while True:
            try:
                # Check for elements that only appear when logged in
                # Header member menu is a reliable indicator
                if page.locator('button[data-testid="header-member-menu-button"]').is_visible() or \
                   page.locator('[data-testid="header-create-menu-button"]').is_visible() or \
                   "trello.com/u/" in page.url:
                    
                    print("\n[!] Login detected!")
                    # Give it a second to ensure all cookies are set
                    time.sleep(2)
                    break
            except Exception:
                pass
            
            if page.is_closed():
                print("\n[!] Browser closed. Re-authentication failed.")
                return
            time.sleep(1)

        # Save the storage state
        print("Saving authentication state to trello_auth.json...")
        context.storage_state(path="trello_auth.json")
        print("Successfully saved! You can now run main.py again.")
        print("="*50)
        browser.close()

if __name__ == "__main__":
    reauth()
