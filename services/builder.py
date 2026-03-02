from utils.retry import retry
import re
import os


def create_board(page, board_name):
    """Creates a new Trello board with the given name."""
    page.goto("https://trello.com/")
    page.get_by_test_id("header-create-menu-button").wait_for(state="visible")
    page.get_by_test_id("header-create-menu-button").click()
    page.wait_for_timeout(1000)

    # Click "Create board"
    create_btn = page.get_by_test_id("header-create-board-button")
    if create_btn.count() == 0:
        create_btn = page.get_by_text("Create board").first
    create_btn.click(force=True)

    page.get_by_test_id("create-board-title-input").wait_for(state="visible")
    page.get_by_test_id("create-board-title-input").fill(board_name)
    page.get_by_test_id("create-board-submit-button").click()
    page.get_by_test_id("board-name-display").wait_for(state="visible", timeout=30000)


def rebuild_board(page, board_data):
    """Rebuilds a board from extracted data."""
    for lst in board_data:
        # Click "Add another list" button if the input is collapsed
        add_btn = page.get_by_role("button", name="Add another list", exact=True)
        if add_btn.count() > 0 and add_btn.is_visible():
            add_btn.click(force=True)

        add_list_input = page.get_by_placeholder("Enter list name...")
        if add_list_input.count() == 0:
            add_list_input = page.locator('[placeholder*="Enter list name"]')
        add_list_input.first.fill(lst["list_title"])
        page.keyboard.press("Enter")

        # Wait for list to appear
        page.locator('[data-testid="list"]').filter(
            has_text=lst["list_title"]
        ).first.wait_for(state="visible")

        list_container = page.locator('[data-testid="list"]').filter(
            has_text=lst["list_title"]
        ).first

        for card in lst["cards"]:
            create_card(page, list_container, card)


def _open_card_modal(page, list_container, card_title):
    """Opens the card modal and returns the dialog locator."""
    # First try scoped to the list
    card = list_container.locator('[data-testid="card-name"]').filter(
        has_text=card_title
    ).first
    if card.count() > 0 and card.is_visible():
        card.click()
    else:
        # Fallback: search anywhere
        fallback_card = page.locator('[data-testid="card-name"]').filter(has_text=card_title).first
        if fallback_card.count() > 0:
            fallback_card.click()
        else:
            page.get_by_text(card_title).first.click()

    # The modal root element: data-testid="card-back-name" with role="dialog"
    dialog = page.locator('[data-testid="card-back-name"]')
    dialog.wait_for(state="visible", timeout=15000)
    page.wait_for_timeout(500)
    return dialog


def _close_card_modal(page):
    """Closes the card modal reliably."""
    close_btn = page.locator('button[aria-label="Close dialog"]')
    if close_btn.count() > 0 and close_btn.first.is_visible():
        close_btn.first.click(force=True)
    else:
        page.keyboard.press("Escape")
    page.wait_for_timeout(500)

    # Wait for modal to disappear
    try:
        page.locator('[data-testid="card-back-name"]').wait_for(state="hidden", timeout=5000)
    except:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)


def _close_popover(page):
    """Closes any open popover safely without pressing ESC (which might close the modal)."""
    close_btn = page.locator('[data-testid="popover-close-button"]')
    if close_btn.count() > 0 and close_btn.first.is_visible():
        close_btn.first.click(force=True)
        page.wait_for_timeout(300)
    else:
        # Click the card title area to dismiss any open dropdown safely
        header = page.locator('[data-testid="card-back-name"]')
        if header.count() > 0 and header.first.is_visible():
            header.first.click(force=True)
            page.wait_for_timeout(300)
        
        # If any popover-like generic containers are still open (e.g. Actions menu)
        # press Escape as a last resort, but carefully.
        if page.locator('[role="menu"]').count() > 0:
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)


def _add_description(page, dialog, description):
    """Adds a description to the card."""
    try:
        # On a NEW card, description section shows a clickable placeholder area
        # Look for the "Add a more detailed description" text/button area
        desc_placeholder = page.locator('[data-testid="click-wrapper"]')
        desc_edit_btn = page.locator('[data-testid="description-edit-button"]')

        if desc_placeholder.count() > 0 and desc_placeholder.first.is_visible():
            desc_placeholder.first.click()
        elif desc_edit_btn.count() > 0 and desc_edit_btn.first.is_visible():
            desc_edit_btn.first.click()
        else:
            # Fallback: click the description content area or any area near "Description"
            desc_area = page.get_by_text("Add a more detailed description")
            if desc_area.count() > 0:
                desc_area.first.click()
            else:
                print(f"    × Could not find description editor trigger")
                return

        page.wait_for_timeout(800)

        # The editor is a rich text ProseMirror/Atlassian editor
        # MUST scope within the dialog to avoid hitting the board-name textbox
        editor = dialog.locator('[role="textbox"]')
        if editor.count() == 0:
            editor = dialog.locator('.ak-editor-content-area [role="textbox"]')
        if editor.count() == 0:
            editor = page.locator('.ak-editor-content-area [role="textbox"]')

        if editor.count() > 0 and editor.first.is_visible():
            editor.first.click(force=True)
            editor.first.fill(description)
            page.wait_for_timeout(300)
        else:
            # Fallback to any visible textarea that's not the title
            textarea = page.locator('textarea:visible').last
            if textarea.count() > 0:
                textarea.fill(description)
            else:
                print(f"    × No editor found for description")
                return

        # Click Save
        save_btn = page.locator('[data-testid="description-save-button"]')
        if save_btn.count() == 0:
            save_btn = page.locator('button:has-text("Save")').first
        if save_btn.count() > 0 and save_btn.first.is_visible():
            save_btn.first.click()
            page.wait_for_timeout(500)

        print(f"    ✓ Description added")
    except Exception as e:
        print(f"    × Description failed: {e}")


def _add_labels(page, dialog, labels):
    """Adds labels to the card."""
    try:
        for label_data in labels:
            label_name = label_data["name"] if isinstance(label_data, dict) else label_data
            label_color = label_data.get("color", "") if isinstance(label_data, dict) else ""

            opened = False
            search_placeholder_query = 'input[placeholder*="Search labels"]'

            # Method 1: The inline toolbar "Labels" button
            labels_toolbar_btns = page.locator('button:has-text("Labels")')
            for idx in range(labels_toolbar_btns.count()):
                btn = labels_toolbar_btns.nth(idx)
                if btn.is_visible():
                    btn.click(force=True)
                    page.wait_for_timeout(800)
                    if page.locator(search_placeholder_query).count() > 0:
                        opened = True
                        break
                    _close_popover(page)

            # Method 1b: Sidebar "Labels" button with data-testid
            if not opened:
                labels_sidebars = page.locator('[data-testid="card-back-labels-button"]')
                for idx in range(labels_sidebars.count()):
                    btn = labels_sidebars.nth(idx)
                    if btn.is_visible():
                        btn.click(force=True)
                        page.wait_for_timeout(800)
                        if page.locator(search_placeholder_query).count() > 0:
                            opened = True
                            break
                        _close_popover(page)

            # Method 1c: "Add a label" button (+ button inside existing labels row)
            if not opened:
                add_label_btns = page.locator('button[aria-label="Add a label"]')
                for idx in range(add_label_btns.count()):
                    btn = add_label_btns.nth(idx)
                    if btn.is_visible():
                        btn.click(force=True)
                        page.wait_for_timeout(800)
                        if page.locator(search_placeholder_query).count() > 0:
                            opened = True
                            break
                        _close_popover(page)

            # Method 2: Use the Actions menu (3-dot button at top of card) → Labels
            if not opened:
                actions_btn = page.locator('[data-testid="card-back-actions-button"]')
                if actions_btn.count() > 0 and actions_btn.first.is_visible():
                    actions_btn.first.click(force=True)
                    page.wait_for_timeout(800)
                    popover = page.locator('[role="menu"], [data-testid="popover-container"], [role="dialog"]').last
                    if popover.count() > 0 and popover.is_visible():
                        label_opt = popover.get_by_text("Labels")
                        if label_opt.count() > 0:
                            label_opt.first.click(force=True)
                            page.wait_for_timeout(800)
                            if page.locator(search_placeholder_query).count() > 0:
                                opened = True
                        if not opened:
                            _close_popover(page)

            # Method 3: Click inline "Add" button → popover → Labels
            if not opened:
                add_to_card = page.locator('[data-testid="card-back-add-to-card-button"]')
                if add_to_card.count() > 0 and add_to_card.first.is_visible():
                    add_to_card.first.click(force=True)
                    page.wait_for_timeout(800)
                    popover = page.locator('[data-testid="popover-container"]')
                    if popover.count() > 0 and popover.first.is_visible():
                        label_opt = popover.get_by_text("Labels")
                        if label_opt.count() > 0:
                            label_opt.first.click(force=True)
                            page.wait_for_timeout(800)
                            opened = True
                        else:
                            _close_popover(page)

            if not opened:
                page.screenshot(path="debug_labels_fail.png", full_page=True)
                print(f"    × Could not open labels popover (screenshot saved)")
                continue

            # Search and select the label
            search_input = page.locator(search_placeholder_query).first
            if search_input.count() > 0 and search_input.is_visible():
                search_input.fill(label_name)
                page.wait_for_timeout(800)

                # Look for matching label in popover scope
                popover = page.locator('[data-testid="popover-container"], [role="dialog"]').last
                
                # Use a filter for exact name matching to avoid "different label is adding" issue
                label_el = popover.locator('[data-testid="card-label"]').filter(has_text=re.compile(f'^{re.escape(label_name)}$'))
                if label_el.count() == 0:
                    label_el = popover.locator(f':text("{label_name}")').filter(has_text=re.compile(f'^{re.escape(label_name)}$'))

                if label_el.count() > 0:
                    # Check if already selected to avoid toggling it OFF
                    # Selected labels usually have a checkmark icon
                    is_selected = label_el.first.locator('[data-testid="card-label-checkmark"]').count() > 0 or \
                                  label_el.first.locator('svg[data-testid="CheckIcon"]').count() > 0
                    
                    if not is_selected:
                        label_el.first.click(force=True)
                        page.wait_for_timeout(300)
                        print(f"    ✓ Label '{label_name}' selected")
                    else:
                        print(f"    - Label '{label_name}' already selected")
                else:
                    # Create a new label
                    create_label_btn = popover.get_by_text("Create a new label")
                    if create_label_btn.count() > 0:
                        create_label_btn.first.click()
                        page.wait_for_timeout(500)

                        # Fill name
                        name_input = popover.locator('input').first
                        if name_input.count() > 0:
                            name_input.fill(label_name)

                        # Select color
                        if label_color:
                            # Try the test-id pattern first as seen in codegen
                            color_btn = popover.get_by_test_id(f"color-tile-{label_color}").first
                            if color_btn.count() == 0:
                                color_btn = popover.locator(f'button[data-color="{label_color}"]').first
                                
                            if color_btn.count() > 0:
                                color_btn.click(force=True)

                        # Submit
                        submit = popover.locator('button').filter(has_text=re.compile(r"^Create$"))
                        if submit.count() > 0:
                            submit.first.click(force=True)
                            page.wait_for_timeout(500)
                            print(f"    ✓ Created label '{label_name}'")
                        else:
                            print(f"    × No Create button for label")

            _close_popover(page)

        print(f"    Labels done")
    except Exception as e:
        print(f"    × Labels failed: {e}")
        _close_popover(page)


def _add_checklist(page, dialog, checklist_items):
    """Adds a checklist to the card."""
    try:
        # Find the Checklist button
        checklist_btn = page.locator('button:has([data-testid="ChecklistIcon"])')
        if checklist_btn.count() == 0:
            checklist_btn = page.get_by_role("button", name="Checklist")

        if checklist_btn.count() == 0:
            print(f"    × No Checklist button found")
            return

        checklist_btn.first.click(force=True)
        page.wait_for_timeout(800)

        # A popover appears asking for checklist title
        popover = page.locator('[data-testid="popover-container"], [role="dialog"]').last
        title_input = popover.locator('input[placeholder*="Checklist"], input[id*="checklist"]').first
        if title_input.count() == 0:
            title_input = popover.locator('input').first

        if title_input.count() > 0:
            # We can use default 'Checklist' or set a custom name if we had one
            # The Add button confirms it
            add_btn = popover.locator('button').filter(has_text=re.compile(r"^(Add|Create)$"))
            if add_btn.count() > 0:
                add_btn.first.click()
                page.wait_for_timeout(1000)

        # Now checklist section should be visible in the card
        # Look for the "Add an item" button/input inside the checklist section
        for item in checklist_items:
            item_name = item["name"] if isinstance(item, dict) else item
            is_checked = item.get("checked", False) if isinstance(item, dict) else False

            # Trello usually autofocuses the "Add an item" input after checklist creation
            # or after adding an item.
            item_input = page.get_by_placeholder("Add an item")
            if item_input.count() == 0 or not item_input.first.is_visible():
                add_item_btn = page.get_by_role("button", name="Add an item")
                if add_item_btn.count() > 0 and add_item_btn.first.is_visible():
                    add_item_btn.first.click()
                    page.wait_for_timeout(300)
                item_input = page.get_by_placeholder("Add an item")

            if item_input.count() > 0:
                item_input.first.fill(item_name)
                page.wait_for_timeout(200)
                page.keyboard.press("Enter")
                page.wait_for_timeout(500)

                # Check the item if needed
                if is_checked:
                    # Look for the recently added item to check it
                    item_row = page.locator('[data-testid="check-item-container"]').filter(has_text=item_name).last
                    if item_row.count() > 0:
                        checkbox = item_row.locator('[data-testid="clickable-checkbox"]')
                        if checkbox.count() > 0:
                            checkbox.click()
                            page.wait_for_timeout(300)
                            print(f"      ✓ Checked: '{item_name}'")

        # We don't press Escape here as it might close the entire card modal.
        # Instead, we just wait a bit.
        page.wait_for_timeout(300)

        print(f"    ✓ Checklist done ({len(checklist_items)} items)")
    except Exception as e:
        print(f"    × Checklist failed: {e}")


def _add_attachments(page, dialog, attachments):
    """Adds attachments to the card."""
    try:
        for att in attachments:
            att_name = att.get("name", "") if isinstance(att, dict) else att
            att_url = att.get("url", "") if isinstance(att, dict) else ""
            local_path = att.get("local_path", "") if isinstance(att, dict) else ""

            if not att_url and not local_path:
                continue

            # Find and click the Attachment button using exact text/role from codegen
            opened = False
            paste_link_query = 'input[placeholder*="Paste any link"]'
            
            # Ensure dialog is open!
            if dialog.count() == 0 or not dialog.is_visible():
                print("    ! Card modal closed unexpectedly, re-opening...")
                page.get_by_text(att_name).first.click(force=True) # This is a bit risky, but let's try
                page.wait_for_timeout(1000)

            # Use Playwright's canonical get_by_role matching text "Attachment"
            att_btn = page.get_by_role("button", name="Attachment", exact=True).first
            if att_btn.count() > 0 and att_btn.is_visible():
                att_btn.click(force=True)
                page.wait_for_timeout(1000)
                if page.locator(paste_link_query).count() > 0 or page.get_by_role("button", name="Choose a file").count() > 0:
                    opened = True

            # If it's still not found, try getting by testid just in case
            if not opened:
                att_btn_icon = page.locator('button:has([data-testid="AttachmentIcon"])').first
                if att_btn_icon.count() > 0 and att_btn_icon.is_visible():
                    att_btn_icon.click(force=True)
                    page.wait_for_timeout(1000)
                    if page.locator(paste_link_query).count() > 0 or page.get_by_role("button", name="Choose a file").count() > 0:
                        opened = True

            if not opened:
                # One last try: "+ Add" button
                add_btn = page.locator('button:has-text("Add")').filter(has_not=page.locator('[data-testid="card-back-name"]')).first
                if add_btn.count() > 0:
                    add_btn.click(force=True)
                    page.wait_for_timeout(800)
                    att_opt = page.get_by_text("Attachment")
                    if att_opt.count() > 0:
                        att_opt.first.click(force=True)
                        page.wait_for_timeout(800)
                        opened = True

            if not opened:
                page.screenshot(path="debug_attachment_fail.png", full_page=True)
                print(f"    × No Attachment button found/popover didn't open (screenshot saved)")
                continue

            popover = page.locator('[data-testid="popover-container"], [role="dialog"]').last

            if local_path and os.path.exists(local_path):
                # Upload local file
                try:
                    # The element is a <label> with role="button", so we can't `set_input_files` on it directly.
                    # We must use Playwright's file chooser interception.
                    choose_file_btn = page.get_by_role("button", name="Choose a file")
                    if choose_file_btn.count() > 0:
                        with page.expect_file_chooser(timeout=5000) as fc:
                            choose_file_btn.first.click(force=True)
                        fc.value.set_files(local_path)
                    else:
                        # Fallback to hidden file input
                        file_input = page.locator('input[type="file"]')
                        if file_input.count() > 0:
                            file_input.first.set_input_files(local_path)
                        else:
                            print(f"    × Could not find 'Choose a file' button or input")
                            _close_popover(page)
                            continue

                    # Wait for upload to complete by waiting for the attachment to appear in the card
                    # Trello shows a progress bar, then the thumbnail appears.
                    print(f"    - Uploading '{att_name}'...")
                    try:
                        # Wait for the item to appear in the attachment list with matching name
                        # We use a 30s timeout for larger uploads
                        page.locator('[data-testid="attachment-list"]').locator(f'text="{att_name}"').wait_for(state="visible", timeout=30000)
                        print(f"    ✓ Uploaded: {att_name}")
                    except:
                        # Fallback simple wait if locator fails
                        page.wait_for_timeout(5000)
                        print(f"    ✓ Uploaded: {att_name} (wait fallback)")
                except Exception as e:
                    print(f"    × Upload failed for '{att_name}': {e}")
                    _close_popover(page)
            else:
                # Paste link
                link_input = popover.get_by_placeholder("Paste any link here...")
                if link_input.count() > 0 and link_input.first.is_visible():
                    link_input.first.fill(att_url)
                    page.wait_for_timeout(300)

                    insert_btn = popover.locator('button').filter(has_text=re.compile(r"(Insert|Attach)"))
                    if insert_btn.count() > 0:
                        insert_btn.first.click()
                        page.wait_for_timeout(2000)
                        print(f"    ✓ Link attached: {att_name}")
                    else:
                        print(f"    × No Insert/Attach button")
                        _close_popover(page)
                else:
                    print(f"    × No link input in attachment popover")
                    _close_popover(page)

        print(f"    Attachments done")
    except Exception as e:
        print(f"    × Attachments failed: {e}")
        _close_popover(page)


def _add_comments(page, dialog, comments):
    """Adds comments to the card."""
    try:
        for comment_text in comments:
            # Click the "Write a comment…" skeleton button
            comment_btn = page.locator('[data-testid="card-back-new-comment-input-skeleton"]')
            if comment_btn.count() == 0 or not comment_btn.first.is_visible():
                comment_btn = page.get_by_role("textbox", name="Write a comment")
            if comment_btn.count() == 0 or not comment_btn.first.is_visible():
                comment_btn = page.get_by_text("Write a comment")

            if comment_btn.count() > 0 and comment_btn.first.is_visible():
                comment_btn.first.click()
                page.wait_for_timeout(1000)

                # The rich text editor replaces the button
                # Look for a role="textbox" or contenteditable element
                editor = page.locator('[role="textbox"]').last
                if editor.count() > 0 and editor.first.is_visible():
                    editor.first.click()
                    page.wait_for_timeout(200)
                    page.keyboard.type(comment_text, delay=20)
                    page.wait_for_timeout(300)
                else:
                    print(f"    × Comment editor not found")
                    continue

                # Click Save
                save_btn = page.locator('[data-testid="card-back-comment-save-button"]')
                if save_btn.count() == 0:
                    save_btn = page.get_by_role("button", name="Save")
                if save_btn.count() > 0 and save_btn.first.is_visible():
                    save_btn.first.click()
                    page.wait_for_timeout(1000)
                    print(f"    ✓ Comment posted")
                else:
                    print(f"    × Save button not found for comment")
            else:
                print(f"    × 'Write a comment' button not found")

        print(f"    Comments done ({len(comments)})")
    except Exception as e:
        print(f"    × Comments failed: {e}")


def _add_cover(page, dialog, cover_data):
    """Sets the card cover."""
    try:
        cover_btn = page.locator('[data-testid="card-back-cover-button"]')
        if cover_btn.count() == 0:
            cover_btn = page.locator('button[aria-label="Cover"]')
        if cover_btn.count() == 0:
            return

        cover_btn.first.click(force=True)
        page.wait_for_timeout(1000)

        popover = page.locator('[data-testid="popover-container"]').last

        if cover_data.get("type") == "color":
            color_val = cover_data.get("value", "")
            if color_val:
                color_btn = popover.locator(f'button[data-color="{color_val}"]').first
                if color_btn.count() > 0:
                    color_btn.click(force=True)
                    print(f"    ✓ Color cover set: {color_val}")

        elif cover_data.get("type") == "image":
            # Wait for attachment thumbnails to load in cover popover
            page.wait_for_timeout(2000)
            popover = page.locator('[data-testid="popover-container"]').last
            att_covers = popover.locator('[data-testid="cover-attachment-item"]')
            if att_covers.count() > 0:
                att_covers.first.click()
                print(f"    ✓ Image cover set")
            else:
                img_btns = popover.locator('button[style*="background-image"]')
                if img_btns.count() > 0:
                    img_btns.first.click()
                    print(f"    ✓ Image cover set (fallback)")

        _close_popover(page)
    except Exception as e:
        print(f"    × Cover failed: {e}")
        _close_popover(page)


@retry(times=2, delay=2)
def create_card(page, list_container, card_data):
    """Creates a card and fills in all its details."""
    title = card_data["title"]
    has_details = (
        card_data.get("description")
        or card_data.get("checklist")
        or card_data.get("comments")
        or card_data.get("labels")
        or card_data.get("attachments")
        or card_data.get("cover")
    )

    # Create the card
    list_container.get_by_test_id("list-add-card-button").click()
    composer = list_container.get_by_test_id("list-card-composer-textarea")
    composer.wait_for(state="visible")
    composer.fill(title)
    
    # Use explicit button click instead of Enter, as per codegen
    add_button = list_container.get_by_test_id("list-card-composer-add-card-button")
    if add_button.count() > 0:
        add_button.click()
    else:
        composer.press("Enter")
        
    page.wait_for_timeout(500)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

    if not has_details:
        print(f"  Card '{title}' created (no details)")
        return

    # Open card modal
    print(f"  Opening card '{title}'...")
    dialog = _open_card_modal(page, list_container, title)

    # Add details in order
    if card_data.get("description"):
        _add_description(page, dialog, card_data["description"])

    if card_data.get("labels"):
        _add_labels(page, dialog, card_data["labels"])

    if card_data.get("checklist"):
        _add_checklist(page, dialog, card_data["checklist"])

    if card_data.get("attachments"):
        _add_attachments(page, dialog, card_data["attachments"])

    if card_data.get("cover"):
        _add_cover(page, dialog, card_data["cover"])

    if card_data.get("comments"):
        _add_comments(page, dialog, card_data["comments"])

    # Close modal
    _close_card_modal(page)

    print(f"  ✓ Card '{title}' complete!")
