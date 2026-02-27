from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="trello_auth.json")
        page = context.new_page()
        
        # Go to Trello home
        page.goto("https://trello.com/")
        
        # Create a new board
        page.get_by_test_id("header-create-menu-button").click()
        page.get_by_test_id("header-create-board-button").click()
        
        test_board_name = f"Test Board {int(time.time())}"
        page.get_by_test_id("create-board-title-input").fill(test_board_name)
        page.get_by_test_id("create-board-submit-button").click()
        page.get_by_test_id("board-name-display").wait_for()
        print("Board created:", test_board_name)
        
        # Try to add a list
        add_list_input = page.get_by_placeholder("Enter list name...")
        if add_list_input.count() == 0:
            add_list_input = page.locator('[placeholder*="Enter list name"]')
            
        print("Input box found? count =", add_list_input.count())
        
        if add_list_input.count() > 0:
            add_list_input.fill("My New List")
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
            
            # Check lists
            lists = page.locator('[data-testid="list"]')
            print("Total lists:", lists.count())
            
            for i in range(lists.count()):
                print(f"List {i}: {lists.nth(i).inner_text()}")
                
            list_container = lists.first
            print("Looking for list-add-card-button...")
            add_card_btn = list_container.get_by_test_id("list-add-card-button")
            print(f"list-add-card-button count: {add_card_btn.count()}")
            
            if add_card_btn.count() > 0:
                add_card_btn.click()
                print("Clicked add card button")
                
                composer = list_container.get_by_test_id("list-card-composer-textarea")
                composer.fill("My Test Card")
                composer.press("Enter")
                page.wait_for_timeout(1000)
                print("Card created")
            else:
                print("Could not find Add Card button. Checking HTML of list...")
                print(list_container.inner_html())
        
        page.screenshot(path="board_after_list.png")
        
        browser.close()

if __name__ == "__main__":
    run()
