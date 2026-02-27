from utils.retry import retry
import re


def create_board(page, board_name):
    page.goto("https://trello.com/")
    page.get_by_test_id("header-create-menu-button").wait_for(state="visible")
    page.get_by_test_id("header-create-menu-button").click()
    
    # Wait for the popover/menu to stabilize
    page.wait_for_timeout(1000)
    
    # Wait for the popover/menu to appear
    # Trello header can be tricky. Let's look for any button that looks like 'Create board'
    create_menu_options = [
        page.get_by_test_id("header-create-board-button"),
        page.locator('button').filter(has_text="Create board"),
        page.locator('span').filter(has_text="Create board"),
        page.get_by_text("Create board")
    ]
    
    found_opt = None
    for opt in create_menu_options:
        if opt.count() > 0 and opt.first.is_visible():
            found_opt = opt.first
            break
            
    if not found_opt:
        # Wait a bit longer if not found immediately
        page.wait_for_timeout(2000)
        for opt in create_menu_options:
            if opt.count() > 0:
                found_opt = opt.first
                break
                
    if found_opt:
        found_opt.click(force=True)
    else:
        # Final attempt with broad search
        page.locator('button:has-text("Create board")').first.click()
    
    page.get_by_test_id("create-board-title-input").wait_for(state="visible")
    page.get_by_test_id("create-board-title-input").fill(board_name)
    page.get_by_test_id("create-board-submit-button").click()
    
    # Wait for the board name to appear in the header (indicates board is ready)
    page.get_by_test_id("board-name-display").wait_for(state="visible", timeout=30000)


def rebuild_board(page, board_data):

    for lst in board_data:

        # Add list
        # Sometimes Trello shows "Add another list" button if the input is closed
        add_btn = page.get_by_role("button", name="Add another list", exact=True)
        if add_btn.count() > 0 and add_btn.is_visible():
            add_btn.click(force=True)

        add_list_input = page.get_by_placeholder("Enter list name...")
        if add_list_input.count() == 0:
            add_list_input = page.locator('[placeholder*="Enter list name"]')

        add_list_input.first.fill(lst["list_title"])
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)

        # Find the list container by its title
        list_container = page.locator('[data-testid="list"]').filter(
            has_text=lst["list_title"]
        ).first

        for card in lst["cards"]:
            create_card(page, list_container, card)


@retry(times=3, delay=2)
def create_card(page, list_container, card_data):

    has_details = (
        card_data.get("description")
        or card_data.get("checklist")
        or card_data.get("comments")
        or card_data.get("labels")
        or card_data.get("attachments")
    )

    # Activate composer if needed
    list_container.get_by_test_id("list-add-card-button").click()

    composer = list_container.get_by_test_id("list-card-composer-textarea")
    composer.wait_for()

    # ---- CREATE CARD ----
    composer.fill(card_data["title"])
    composer.press("Enter")
    page.wait_for_timeout(500)

    # Close the composer so it doesn't interfere
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

    # If card has no extra details, skip opening the modal
    if not has_details:
        print(f"  Card '{card_data['title']}' created (no details to add)")
        return

    # Open the newly created card by clicking it
    card = list_container.locator('[data-testid="card-name"]').filter(
        has_text=card_data["title"]
    ).first
    card.click()

    # Wait for the card modal to load
    page.get_by_test_id("card-back-name").wait_for(state="visible", timeout=10000)
    page.wait_for_timeout(1000)

    dialog = page.get_by_test_id("card-back-name")

    # ---- DESCRIPTION ----
    if card_data.get("description"):
        try:
            # Click the "Add a more detailed description..." button
            desc_btn = dialog.locator('[data-testid="description-button"]')
            if desc_btn.count() > 0:
                desc_btn.click()
                page.wait_for_timeout(500)

                # Find the description textarea/editor and type
                # We explicitly exclude the title input to avoid overwriting it
                desc_editor = dialog.locator('textarea:not([data-testid="card-back-title-input"]), [data-testid="editor-input"]')
                if desc_editor.count() == 0:
                    desc_editor = dialog.locator('[role="textbox"]:not([data-testid="card-back-title-input"])')
                
                if desc_editor.count() > 0:
                    desc_editor.first.fill(card_data["description"])
                    page.wait_for_timeout(300)

                    # Click Save button
                    save_btn = dialog.locator('[data-testid="description-save-button"]')
                    if save_btn.count() > 0:
                        save_btn.click()
                    else:
                        # Fallback: find any Save button near the description
                        save_btn = dialog.locator('button:has-text("Save")').first
                        save_btn.click()
                    page.wait_for_timeout(500)

                print(f"  Description added for '{card_data['title']}'")
        except Exception as e:
            print(f"  Warning: Failed to add description for '{card_data['title']}': {e}")

    # ---- LABELS ----
    if card_data.get("labels"):
        try:
            for label in card_data["labels"]:
                label_name = label if isinstance(label, str) else label.get("name")
                
                # Robustly find the button to open labels popover
                # Try sidebar 'Labels' button first, then inline '+' button, then 'Add to card' menu
                selectors = [
                    '[data-testid="card-back-labels-button"]',
                    'button:has-text("Labels")',
                    'button[aria-label="Add a label"]',
                    'button[aria-label="Labels"]'
                ]
                
                opened = False
                for sel in selectors:
                    btn = dialog.locator(sel).first
                    if btn.count() > 0:
                        btn.click(force=True)
                        page.wait_for_timeout(1000)
                        if page.locator('[data-testid="popover-container"]').count() > 0:
                            opened = True
                            break
                
                if not opened:
                    # Try 'Add to card' menu as last resort
                    add_btn = page.get_by_test_id("card-back-add-to-card-button")
                    if add_btn.count() > 0:
                        add_btn.click()
                        page.wait_for_timeout(500)
                        label_opt = page.locator('button:has-text("Labels")')
                        if label_opt.count() > 0:
                            label_opt.first.click()
                            page.wait_for_timeout(1000)
                            opened = True
                
                if not opened:
                    print(f"  Warning: Could not open labels popover for '{card_data['title']}'")
                    continue

                # Search and select in popover
                # Be VERY patient and thorough here
                # Try multiple possible search inputs
                search_input = page.locator('input[placeholder*="Search labels"], input[placeholder="Search"], [data-testid="labels-search-input"]').first
                if search_input.count() == 0:
                    search_input = page.get_by_placeholder("Search labels...")
                
                if search_input.count() > 0:
                    search_input.wait_for(state="visible", timeout=5000)
                    search_input.fill(label_name)
                    page.wait_for_timeout(1500) # Wait for search results to populate
                    
                    # 1. Try to find a button with exact label name
                    selectors = [
                        f'button:has-text("{label_name}")',
                        f'span:has-text("{label_name}")',
                        f'div:has-text("{label_name}")',
                        f'[data-testid="card-label"]:has-text("{label_name}")',
                        f'[aria-label*="{label_name}"]'
                    ]
                    
                    found = False
                    # Look inside the popover explicitly
                    container = page.locator('[data-testid="popover-container"], [role="dialog"]').last
                    
                    for sel in selectors:
                        # Use a more flexible text match
                        # Trello labels can have surrounding icons or extra spaces
                        target = container.locator(sel).first
                        if target.count() > 0 and target.is_visible():
                            print(f"    ✓ Found label element via {sel}")
                            target.click()
                            page.wait_for_timeout(500)
                            found = True
                            break
                    
                    if not found:
                        # 1.5 Try any button/span containing text (case insensitive)
                        # This is very broad but helpful
                        try:
                            # Use regex for case-insensitive match
                            res = container.get_by_role("button").filter(has_text=re.compile(f"^{re.escape(label_name)}$", re.IGNORECASE)).first
                            if res.count() == 0:
                                res = container.locator(f':text-is("{label_name}")').first
                                
                            if res.count() > 0 and res.is_visible():
                                print(f"    ✓ Found label by flexible text match")
                                res.click(force=True)
                                page.wait_for_timeout(500)
                                found = True
                        except Exception:
                            pass
                    
                    if not found:
                        # 2. Try to find any element with the name
                        # Trello sometimes has it in a div or span
                        res = container.locator(f':text("{label_name}")').first
                        if res.count() > 0 and res.is_visible():
                            print(f"    ✓ Found label text element for '{label_name}'")
                            res.click(force=True)
                            page.wait_for_timeout(500)
                            found = True
                    
                    if not found:
                        print(f"    × Label '{label_name}' not found in search results, attempting to create...")
                        # 3. Create if not found
                        create_btn = page.locator('button:has-text("Create a new label")')
                        if create_btn.count() > 0:
                            create_btn.click()
                            page.wait_for_timeout(500)
                            name_in = page.get_by_placeholder("Enter a name for this label")
                            if name_in.count() > 0:
                                name_in.fill(label_name)
                            
                            if not isinstance(label, str) and label.get("color"):
                                color_btn = page.locator(f'button[data-color="{label["color"]}"]')
                                if color_btn.count() > 0:
                                    color_btn.click()
                            
                            submit_btn = page.get_by_test_id("create-label-submit-button")
                            if submit_btn.count() > 0:
                                submit_btn.click()
                                page.wait_for_timeout(500)
                                found = True
                else:
                    print(f"    × Search input not found in labels popover for '{label_name}'")
                    
                # Close popover after each label to be safe
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
                # If popover still there, try again
                if page.locator('[data-testid="popover-container"]').count() > 0:
                     page.locator('[data-testid="popover-close-button"]').first.click() if page.locator('[data-testid="popover-close-button"]').count() > 0 else None
                     page.wait_for_timeout(500)
            
            print(f"  Labels added for '{card_data['title']}'")
        except Exception as e:
            print(f"  Warning: Failed to add labels for '{card_data['title']}': {e}")

    # ---- CHECKLIST ----
    if card_data.get("checklist"):
        try:
            # Click the "Checklist" button (sidebar button with ChecklistIcon)
            checklist_btn = dialog.locator('button:has([data-testid="ChecklistIcon"])').first
            if checklist_btn.count() == 0:
                 checklist_btn = dialog.locator('button:has-text("Checklist")').first
            
            if checklist_btn.count() > 0:
                checklist_btn.click(force=True)
                page.wait_for_timeout(1000)

                # Click the "Add" button in the checklist popover
                add_checklist = page.locator('[data-testid="checklist-add-button"]')
                if add_checklist.count() > 0:
                    add_checklist.click()
                    page.wait_for_timeout(1000)

                # Add items to the checklist
                for item in card_data["checklist"]:
                    item_name = item["name"] if isinstance(item, dict) else item
                    is_checked = item.get("checked", False) if isinstance(item, dict) else False

                    item_input = dialog.get_by_placeholder("Add an item")
                    if item_input.count() > 0:
                        item_input.fill(item_name)
                        item_input.press("Enter")
                        page.wait_for_timeout(700)  # Wait for item to render

                        # If the item was checked in the source board, tick it now
                        if is_checked:
                            # Find the checkbox container for this specific item
                            item_container = dialog.locator('[data-testid="check-item-container"]').filter(
                                has_text=item_name
                            ).first
                            
                            checkbox = item_container.locator('[data-testid="clickable-checkbox"]')
                            if checkbox.count() > 0:
                                checkbox.click()
                                page.wait_for_timeout(500)
                                print(f"    ✓ Checked: '{item_name}'")

                # Close the "Add an item" input
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)

            print(f"  Checklist added for '{card_data['title']}' ({len(card_data['checklist'])} items)")
        except Exception as e:
            print(f"  Warning: Failed to add checklist for '{card_data['title']}': {e}")

    # ---- ATTACHMENTS ----
    if card_data.get("attachments"):
        try:
            for att in card_data["attachments"]:
                att_name = att.get("name") if isinstance(att, dict) else att
                att_url = att.get("url") if isinstance(att, dict) else ""
                
                if not att_url:
                    continue
                
                # Click the "Attachment" button (sidebar or main)
                att_btn = dialog.locator('button:has-text("Attachment")')
                if att_btn.count() == 0:
                    att_btn = dialog.locator('button:has([data-testid="AttachmentIcon"])')
                
                if att_btn.count() > 0:
                    att_btn.first.click(force=True)
                    page.wait_for_timeout(1000)
                    
                    search_input_att = page.get_by_placeholder("Paste any link here...")
                    if search_input_att.count() > 0:
                        search_input_att.fill(att_url)
                        page.wait_for_timeout(500)
                        
                        # Optionally fill the name
                        name_in_att = page.locator('input[id="attachmentName"]')
                        if name_in_att.count() > 0 and att_name:
                            name_in_att.fill(att_name)
                        
                        # Click Add / Insert - be very specific
                        # The button usually has text "Add" or "Insert"
                        possible_btns = page.locator('button').filter(has_text="Add")
                        insert_btns = page.locator('button').filter(has_text="Insert")
                        
                        target_btn = None
                        if insert_btns.count() > 0:
                             target_btn = insert_btns.last
                        elif possible_btns.count() > 0:
                             target_btn = possible_btns.last
                             
                        if target_btn:
                            target_btn.click()
                            page.wait_for_timeout(2000)
                        else:
                            # Fallback to general search
                            page.locator('button:has-text("Insert"), button:has-text("Add")').last.click()
                            page.wait_for_timeout(2000)
            
            print(f"  Attachments added for '{card_data['title']}'")
        except Exception as e:
            print(f"  Warning: Failed to add attachments for '{card_data['title']}': {e}")

    # ---- COMMENTS ----
    if card_data.get("comments"):
        try:
            for comment in card_data["comments"]:
                # Click the "Write a comment..." skeleton button
                comment_input = dialog.locator('[data-testid="card-back-new-comment-input-skeleton"]')
                if comment_input.count() > 0:
                    comment_input.click()
                    page.wait_for_timeout(500)

                    # Type in the comment editor
                    comment_editor = dialog.locator('[role="textbox"]').last
                    if comment_editor.count() > 0:
                        comment_editor.fill(comment)
                        page.wait_for_timeout(300)

                        # Submit comment with Save button
                        save_btn = dialog.locator('button:has-text("Save")').first
                        if save_btn.count() > 0:
                            save_btn.click()
                            page.wait_for_timeout(500)

            print(f"  Comments added for '{card_data['title']}' ({len(card_data['comments'])} comments)")
        except Exception as e:
            print(f"  Warning: Failed to add comments for '{card_data['title']}': {e}")

    # ---- CLOSE DIALOG ----
    close_btn = dialog.locator('[aria-label="Close dialog"]')
    if close_btn.count() > 0:
        close_btn.click()
    else:
        page.keyboard.press("Escape")

    page.wait_for_timeout(500)

    # Wait for card-back-name to close
    try:
        page.get_by_test_id("card-back-name").wait_for(state="hidden", timeout=10000)
    except Exception:
        # Fallback: press Escape again in case a sub-dialog was open
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        try:
            page.get_by_test_id("card-back-name").wait_for(state="hidden", timeout=5000)
        except Exception:
            pass

    print(f"  Card '{card_data['title']}' complete!")
